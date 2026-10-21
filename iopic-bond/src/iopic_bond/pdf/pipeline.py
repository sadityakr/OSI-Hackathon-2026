"""``parse_pdf``: PDF -> Docling -> ``BlockNode`` tree -> artifacts.

Trimmed for iopic-Bond: structure, figures with captions, figure notes, and intra-document
``references-figure`` edges. No formula VLM, no GROBID, no citation normalisation, no chemistry
tagging. Those passes exist upstream and can be re-enabled later; here the goal is "which panel
shows the Raman spectrum", which needs figures, captions and the paragraphs that mention them.

Output layout::

    <out_dir>/<content_hash>/
    ├── tree.json   the single source of truth
    ├── text.txt    coordinate stream that char_spans index into
    ├── paper.md    Markdown render with figures embedded
    └── figures/    figN.png crops and figN.md notes

Docling model load is lazy and cached, one converter per process.
"""
from __future__ import annotations

from pathlib import Path

from .docling_adapter import tree_from_docling
from .ids import content_hash
from .render import render_markdown
from .schema import SCHEMA_VERSION, BlockNode, to_json
from .xref import resolve_internal_refs

# Stored with every parse; the store re-parses a paper whose recorded version differs.
PARSER_VERSION = "iopic-bond-0.1.0"
_CONVERTER_CACHE: dict[tuple, object] = {}


def _cap_vram(fraction: float) -> None:
    import torch

    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(fraction, 0)


def _build_converter(images_scale: float, device: str, vram_fraction: float):
    key = (images_scale, device, vram_fraction)
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
    opts.do_ocr = False
    opts.generate_picture_images = True
    opts.images_scale = images_scale
    opts.do_formula_enrichment = False
    opts.do_table_structure = True
    if device == "cuda":
        _cap_vram(vram_fraction)
        opts.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CUDA, num_threads=4)
    else:
        opts.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU, num_threads=4)
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    _CONVERTER_CACHE[key] = conv
    return conv


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
    images_scale: float = 2.0,
    device: str = "cpu",
    vram_fraction: float = 0.4,
    force: bool = False,
) -> BlockNode:
    """Parse ``pdf_path`` into ``<out_dir>/<hash>/`` and return the document-root ``BlockNode``.

    If ``<out_dir>/<hash>/tree.json`` already exists and ``force`` is False, the cached tree is
    returned without touching Docling.
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

    converter = _build_converter(images_scale, device, vram_fraction)
    result = converter.convert(str(pdf_path))
    doc = result.document

    root, text_txt, figure_saves = tree_from_docling(doc, root_id=chash)
    root.attrs.setdefault("source_pdf", pdf_path.name)
    root.attrs["parse"] = _parse_stamp(device)

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
