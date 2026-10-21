"""``parse_pdf`` — the structural-parse orchestrator (M2).

PDF -> Docling (OCR off, formula + picture enrichment) -> ``BlockNode`` tree -> artifacts:

    <out_dir>/<content_hash>/
    ├── tree.json   the single source of truth
    ├── text.txt    plain coordinate stream char_span indexes into (NOT markdown, by design)
    ├── paper.md    derived Obsidian-vault render (figures embedded)
    └── figures/    extracted figure crops referenced from tree.json / paper.md

Docling model load is lazy + cached (one converter per process); OCR is disabled because the corpus
is born-digital and the bundled OCR engine is unused (and currently version-broken). Pass
``do_formula=False`` to skip the formula VLM on very large/slow documents.
"""

from __future__ import annotations

from pathlib import Path

from .docling_adapter import tree_from_docling
from .ids import content_hash
from .render import render_markdown
from .schema import SCHEMA_VERSION, BlockNode, to_json
from .xref import resolve_internal_refs

_CONVERTER_CACHE: dict[tuple, object] = {}


def _cap_vram(fraction: float) -> None:
    """Cap this process to a fraction of total VRAM so we can never OOM another user's GPU job.

    The cap makes *our* allocations fail past the ceiling rather than starving co-tenants — the
    shared-machine rule. The formula VLM is small (~1.7 GB peak), so a 0.4 cap on a 12 GB card is
    generous headroom while staying well clear of a neighbour's resident job.
    """
    import torch

    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(fraction, 0)


def _run_pass(manifest: dict[str, str], name: str, fn):
    """Run a best-effort enrichment pass, recording its outcome in the parse manifest.

    An enrichment pass must never crash the parse (structure + provenance are already captured), but a
    pass that silently swallows its exception makes a *degraded* tree byte-indistinguishable from a
    clean one — at corpus scale nobody reads stdout. So every best-effort pass records ``ok`` /
    ``error: …`` into ``root.attrs['passes']``, turning parse health into a queryable artifact QA and
    the eval can assert on. Returns ``fn()``'s result on success, ``None`` on failure.
    """
    try:
        result = fn()
        manifest[name] = "ok"
        return result
    except Exception as exc:  # noqa: BLE001 — best-effort by contract; the outcome is recorded
        manifest[name] = f"error: {type(exc).__name__}: {exc}"
        print(f"  {name} skipped ({type(exc).__name__}: {exc})")
        return None


def _parse_stamp(*, do_formula: bool, device: str) -> dict:
    """The derived-data provenance stamp written to ``root.attrs['parse']`` (review F4).

    Answers "how was this tree produced, and is it stale?" without re-deriving it: which parser
    code, which Docling, which tree-contract version, and the config that changes the artifact's
    *content* (``do_formula=False`` yields empty equation LaTeX — previously indistinguishable from
    a full parse). Trees from before this stamp simply lack the key — read as "unknown".
    """
    from importlib.metadata import PackageNotFoundError, version

    from .. import __version__

    try:
        docling_version = version("docling")
    except PackageNotFoundError:  # pragma: no cover — docling is a hard dep of the parse
        docling_version = "unknown"
    return {
        "parser_version": __version__,
        "docling_version": docling_version,
        "schema_version": SCHEMA_VERSION,
        "do_formula": do_formula,
        "device": device,
    }


def _build_converter(do_formula: bool, images_scale: float, device: str, vram_fraction: float):
    key = (do_formula, images_scale, device, vram_fraction)
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
    opts.do_ocr = False  # born-digital corpus; bundled OCR is unused (and version-broken)
    opts.generate_picture_images = True
    opts.images_scale = images_scale
    opts.do_formula_enrichment = do_formula
    opts.do_table_structure = True
    if device == "cuda":
        _cap_vram(vram_fraction)
        opts.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CUDA, num_threads=4)
    else:
        opts.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU, num_threads=4)
    conv = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )
    _CONVERTER_CACHE[key] = conv
    return conv


def parse_pdf(
    pdf_path,
    out_dir,
    *,
    do_formula: bool = True,
    images_scale: float = 2.0,
    device: str = "cpu",
    vram_fraction: float = 0.4,
    normalize_citations: bool = True,
) -> BlockNode:
    """Parse ``pdf_path`` into ``<out_dir>/<hash>/`` and return the document-root ``BlockNode``.

    ``do_formula`` (default on) toggles Docling's formula VLM — the **dominant cost** of the parse
    (~95%% of wall time; ~2-3s per equation crop on GPU, autoregressive, scales with equation count
    not pages). With it **off**, structure, provenance, equation **numbers**, and ``Eq. (N)``
    cross-references are still recovered (numbers come from the PDF glyph layer in
    :mod:`equation_numbers`, independent of the VLM); only the equation LaTeX *body* is lost. So
    ``do_formula=False`` is a real fast mode (sub-second/page) for bulk/structure-first parsing, not
    just a debug flag.

    ``device``: ``"cpu"`` (default) or ``"cuda"``. On ``"cuda"`` the formula VLM runs on the GPU and
    VRAM is capped to ``vram_fraction`` of the card so co-tenants are safe.
    ``normalize_citations`` (default on) rewrites superscript citations to canonical ``[N]`` form so
    every citation style is uniform in the tree (see :mod:`citation_normalize`).
    """
    pdf_path = Path(pdf_path)
    pdf_bytes = pdf_path.read_bytes()
    chash = content_hash(pdf_bytes)

    doc_dir = Path(out_dir) / chash
    fig_dir = doc_dir / "figures"
    doc_dir.mkdir(parents=True, exist_ok=True)

    converter = _build_converter(do_formula, images_scale, device, vram_fraction)
    result = converter.convert(str(pdf_path))
    doc = result.document

    root, text_txt, figure_saves = tree_from_docling(doc, root_id=chash)
    root.attrs.setdefault("source_pdf", pdf_path.name)
    root.attrs["parse"] = _parse_stamp(do_formula=do_formula, device=device)

    # Enrichment passes are best-effort and ORDER-DEPENDENT (each comment states its precondition);
    # every outcome is recorded in `passes` so a degraded parse is visible, never silent.
    passes: dict[str, str] = {}

    # Standardize citations to canonical [N] BEFORE anything anchors char-spans: superscript markers
    # Docling left as bare numbers ("topology 1-4") are rewritten to "topology [1-4]" and text.txt +
    # char-spans are rebuilt to match.
    def _normalize_cites():
        from .citation_normalize import normalize_superscript_citations

        return normalize_superscript_citations(root, pdf_path)[0]

    if normalize_citations:
        new_text = _run_pass(passes, "citation_normalize", _normalize_cites)
        if new_text is not None:
            text_txt = new_text
    else:
        passes["citation_normalize"] = "skipped (disabled)"

    # Recover right-aligned equation numbers from the PDF text layer (issue 0001) BEFORE xref, so
    # `references-equation` edges can resolve. The formula VLM drops/renumbers these; the real number
    # is plain typeset text pypdfium reads with fidelity.
    def _equation_numbers():
        from .equation_numbers import recover_equation_numbers

        recover_equation_numbers(root, pdf_path)

    _run_pass(passes, "equation_numbers", _equation_numbers)

    # Tag material formulas (precision-gated pymatgen canonicalisation) onto node attrs, then recover
    # formulas Docling dropped from live PDF text (issue 0009) from the glyph layer. Post-citation-
    # normalisation by construction; the optional pymatgen dep is imported lazily inside the pass.
    def _chemistry():
        from .chemistry import recover_dropped_formulas, tag_materials

        tag_materials(root)
        recover_dropped_formulas(root, pdf_path)

    _run_pass(passes, "chemistry", _chemistry)

    # M4: add references-{figure,table,section,equation} edges. Best-effort like the other passes —
    # a tree without xref edges is degraded, not worthless — and honestly ledgered (review F6: the
    # old code hardcoded "ok" even though this pass can raise).
    _run_pass(passes, "xref", lambda: resolve_internal_refs(root))
    root.attrs["passes"] = passes

    # write figure crops, then the artifacts
    if figure_saves:
        fig_dir.mkdir(parents=True, exist_ok=True)
        for rel, img in figure_saves:
            try:
                img.save(doc_dir / rel)
            except Exception:
                # drop the image_path on nodes whose crop failed to save
                _drop_missing_image(root, rel)

    (doc_dir / "tree.json").write_text(to_json(root), encoding="utf-8")
    (doc_dir / "text.txt").write_text(text_txt, encoding="utf-8")
    (doc_dir / "paper.md").write_text(render_markdown(root), encoding="utf-8")
    _write_figure_notes(root, doc_dir)
    return root


def _drop_missing_image(root: BlockNode, rel: str) -> None:
    for node in root.walk():
        if node.attrs.get("image_path") == rel:
            node.attrs.pop("image_path", None)
            node.attrs.pop("note_path", None)  # no image -> no note to transclude
            node.attrs["image_missing"] = True


def _write_figure_notes(root: BlockNode, doc_dir: Path) -> None:
    """Write one note per figure (``figures/figN.md``) — the per-figure embeddable unit.

    Each note bundles the figure crop with its caption and a reserved **Description** slot for a
    later VLM-generated summary. This is the unit we will embed into the vector space: it carries a
    caption now, and a VLM can fill (or add) the description later. The figure node in ``tree.json``
    points here via ``attrs.note_path``, and the caption reaches it through its ``caption-of`` edge,
    so the figure<->caption<->note link is explicit in the canonical tree, not just on disk.
    """
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
            f"**Caption:** {caption}"
            if caption
            else "**Caption:** <!-- none in source; a VLM can generate one -->",
            "",
            "**Description:**",
            "<!-- VLM-generated summary goes here — this is what gets embedded into the vector space -->",
            "",
        ]
        (doc_dir / f.attrs["note_path"]).write_text("\n".join(note), encoding="utf-8")
