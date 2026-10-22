"""``parse_pdf``: PDF -> Docling -> ``BlockNode`` tree -> artifacts.

Trimmed for iopic-Bond: structure, figures with captions, figure notes, and intra-document
``references-figure`` edges. No formula VLM, no GROBID, no citation normalisation, no chemistry
tagging. Those passes exist upstream and can be re-enabled later; here the goal is "which panel
shows the Raman spectrum", which needs figures, captions and the paragraphs that mention them.

Speed choices, all of which keep that goal:

* Table-structure recognition is off. The layout model still finds figures and captions; reading
  cell grids was most of the remaining CPU time and is not used to pick a spectrum panel.
* OCR, formula enrichment, picture description and page-image rendering stay off.
* When a paper's figures sit on a minority of pages, only those pages (plus one neighbour each)
  go through Docling. Text from the other pages is taken from the PDF text layer so "Fig. N"
  mentions still resolve. A cached ``tree.json`` is returned without loading Docling.

Output layout::

    <out_dir>/<content_hash>/
    ├── tree.json   the single source of truth
    ├── text.txt    coordinate stream that char_spans index into
    ├── paper.md    Markdown render with figures embedded
    └── figures/    figN.png crops and figN.md notes

Docling model load is lazy and cached, one converter per process.
"""
from __future__ import annotations

import os
from pathlib import Path

from .docling_adapter import tree_from_docling
from .ids import content_hash
from .pages import (
    append_text_pages,
    doc_page_map,
    remap_pages,
    scan_pages,
    select_layout_pages,
    write_page_subset,
)
from .render import render_markdown
from .schema import SCHEMA_VERSION, BlockNode, to_json
from .xref import resolve_internal_refs

# Stored with every parse; the store re-parses a paper whose recorded version differs.
# Not bumped for the speed settings: a tree already on disk is still valid, and bumping would
# force every cached paper through Docling again.
PARSER_VERSION = "iopic-bond-0.1.0"
DEFAULT_IMAGES_SCALE = 2.0
DEFAULT_VRAM_FRACTION = 0.4
_CONVERTER_CACHE: dict[tuple, object] = {}


def _cap_vram(fraction: float) -> None:
    import torch

    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(fraction, 0)


def _thread_count() -> int:
    return max(1, min(8, os.cpu_count() or 4))


def _build_converter(
    images_scale: float,
    device: str,
    vram_fraction: float,
    *,
    tables: bool = False,
):
    threads = _thread_count()
    key = (images_scale, device, vram_fraction, tables, threads)
    if key in _CONVERTER_CACHE:
        return _CONVERTER_CACHE[key]
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    try:
        from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    except ImportError:  # older docling layout
        from docling.datamodel.pipeline_options import AcceleratorDevice, AcceleratorOptions

    opts = PdfPipelineOptions()
    opts.images_scale = images_scale
    opts.generate_picture_images = True
    # These enrichments are the slow optional stages. Missing attributes mean an older Docling
    # that never ran that stage.
    for name, value in (
        ("do_ocr", False),
        ("do_table_structure", tables),
        ("do_formula_enrichment", False),
        ("do_code_enrichment", False),
        ("do_picture_classification", False),
        ("do_picture_description", False),
        ("do_chart_extraction", False),
        ("generate_page_images", False),
        ("generate_table_images", False),
        ("generate_parsed_pages", False),
    ):
        if hasattr(opts, name):
            setattr(opts, name, value)
    # Larger batches help the GPU. On CPU the default is already small; leave it so a laptop
    # parse does not hold several page tensors at once.
    if device == "cuda" and hasattr(opts, "layout_batch_size"):
        opts.layout_batch_size = 16
    if device == "cuda":
        _cap_vram(vram_fraction)
        accel = AcceleratorDevice.CUDA
    else:
        accel = AcceleratorDevice.CPU
    opts.accelerator_options = AcceleratorOptions(device=accel, num_threads=threads)
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    _CONVERTER_CACHE[key] = conv
    return conv


def load_converter(device: str) -> object:
    """Build the converter ``parse_pdf`` uses, so warmup loads the same models."""
    return _build_converter(DEFAULT_IMAGES_SCALE, device, DEFAULT_VRAM_FRACTION)


def _parse_stamp(device: str) -> dict:
    from importlib.metadata import PackageNotFoundError, version

    try:
        docling_version = version("docling")
    except PackageNotFoundError:
        docling_version = "unknown"
    return {
        "parser_version": PARSER_VERSION,
        "docling_version": docling_version,
        "schema_version": SCHEMA_VERSION,
        "do_formula": False,
        "device": device,
    }


def parse_pdf(
    pdf_path,
    out_dir,
    *,
    images_scale: float = DEFAULT_IMAGES_SCALE,
    device: str = "cpu",
    vram_fraction: float = DEFAULT_VRAM_FRACTION,
    tables: bool = False,
    force: bool = False,
) -> BlockNode:
    """Parse ``pdf_path`` into ``<out_dir>/<hash>/`` and return the document-root ``BlockNode``.

    If ``<out_dir>/<hash>/tree.json`` already exists and ``force`` is False, the cached tree is
    returned without touching Docling. ``tables=True`` runs table-structure recognition, which is
    much slower and only needed when cell text itself must be recovered.
    """
    from .schema import from_json

    pdf_path = Path(pdf_path)
    pdf_bytes = pdf_path.read_bytes()
    chash = content_hash(pdf_bytes)
    doc_dir = Path(out_dir) / chash
    tree_path = doc_dir / "tree.json"
    if tree_path.exists() and not force:
        return from_json(tree_path.read_text(encoding="utf-8"))

    fig_dir = doc_dir / "figures"
    doc_dir.mkdir(parents=True, exist_ok=True)

    converter = _build_converter(images_scale, device, vram_fraction, tables=tables)
    doc, text_extra, layout_note = _convert(converter, pdf_path, doc_dir)
    root, text_txt, figure_saves = tree_from_docling(doc, root_id=chash)
    if text_extra is not None:
        page_map, skipped, n_pages = text_extra
        remap_pages(root, page_map)
        text_txt = append_text_pages(root, skipped, text_txt)
        root.attrs["n_pages"] = n_pages
    root.attrs.setdefault("source_pdf", pdf_path.name)
    root.attrs["parse"] = _parse_stamp(device)
    root.attrs["parse"]["tables"] = tables
    root.attrs["parse"]["layout_pages"] = layout_note

    passes: dict[str, str] = {}
    try:
        n = resolve_internal_refs(root)
        passes["xref"] = f"ok ({n} edges)"
    except Exception as exc:  # best effort by contract
        passes["xref"] = f"error: {type(exc).__name__}: {exc}"
    root.attrs["passes"] = passes

    if figure_saves:
        fig_dir.mkdir(parents=True, exist_ok=True)
        for rel, img in figure_saves:
            try:
                img.save(doc_dir / rel)
            except Exception:
                _drop_missing_image(root, rel)

    tree_path.write_text(to_json(root), encoding="utf-8")
    (doc_dir / "text.txt").write_text(text_txt, encoding="utf-8")
    (doc_dir / "paper.md").write_text(render_markdown(root), encoding="utf-8")
    _write_figure_notes(root, doc_dir)
    return root


def _convert(converter, pdf_path: Path, doc_dir: Path):
    """Run Docling, restricting it to figure pages when that skips a useful fraction of the file.

    Returns ``(doc, extra, layout_note)``. ``extra`` is ``(page_map, skipped_scans, n_pages)``
    when a subset was used, else ``None``. On any subset failure the whole PDF is parsed.
    """
    scanned = scan_pages(pdf_path)
    layout_pages = select_layout_pages(scanned) if scanned else []
    use_subset = bool(scanned) and len(layout_pages) < len(scanned)
    if not use_subset:
        result = converter.convert(str(pdf_path))
        note = f"all ({len(scanned)} pages)" if scanned else "all"
        return result.document, None, note

    subset = doc_dir / "_layout_pages.pdf"
    try:
        write_page_subset(pdf_path, subset, layout_pages)
        result = converter.convert(str(subset))
        page_map = doc_page_map(result.document, layout_pages)
        if page_map is None:
            raise RuntimeError("subset page count does not match the selected pages")
    except Exception:
        result = converter.convert(str(pdf_path))
        return result.document, None, f"all ({len(scanned)} pages, subset failed)"
    finally:
        subset.unlink(missing_ok=True)

    kept = set(layout_pages)
    skipped = [page for page in scanned if page.number not in kept]
    extra = (page_map, skipped, len(scanned))
    return result.document, extra, f"{len(layout_pages)} of {len(scanned)}"


def _drop_missing_image(root: BlockNode, rel: str) -> None:
    for node in root.walk():
        if node.attrs.get("image_path") == rel:
            node.attrs.pop("image_path", None)
            node.attrs.pop("note_path", None)
            node.attrs["image_missing"] = True


def _write_figure_notes(root: BlockNode, doc_dir: Path) -> None:
    for f in root.walk():
        if f.type != "figure" or not f.attrs.get("note_path") or not f.attrs.get("image_path"):
            continue
        img = f.attrs["image_path"]
        label = f.attrs.get("label", "")
        page = f.attrs.get("caption_page") or (f.prov[0].page_no if f.prov else "")
        caption = (f.attrs.get("caption") or "").strip()
        note = [
            "---",
            "type: figure",
            f"label: {label}",
            f"source: {root.id}",
            f"node_id: {f.id}",
            f"page: {page}",
            f"image: {img.rsplit('/', 1)[-1]}",
            "---",
            "",
            f"![[{img}]]",
            "",
            f"**Caption:** {caption}" if caption else "**Caption:** (none in source)",
            "",
            "**Description:**",
            "(vision-generated summary goes here)",
            "",
        ]
        (doc_dir / f.attrs["note_path"]).write_text("\n".join(note), encoding="utf-8")
