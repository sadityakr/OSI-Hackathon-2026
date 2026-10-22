"""Decide which PDF pages need the layout model, and keep text from the rest.

Docling's layout model and table recogniser dominate parse time, and they run per page. A Raman
paper's figures occupy a few pages. Those pages (and their neighbours, in case a caption sits
across the boundary) go through Docling. The other pages are read from the PDF text layer, which
is enough for "see Fig. 2" mentions and takes milliseconds.

If the selection would still send most of the document to Docling, or if the PDF cannot be
scanned, the caller parses every page. A wrong skip is worse than a slow parse.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .schema import BlockNode, Provenance

# A caption starts a line ("Figure 2. ..."). A body mention ("see Fig. 2.") does not, so that
# page stays on the text-layer path. Image and path counts catch a figure whose caption is missing.
_CAPTIONISH = re.compile(
    r"(?:^|\n)\s*(?:Figure|Fig\.|Table|Tab\.)\s+\d+",
    re.IGNORECASE,
)

# About one inch on a side. Journal logos and icons are smaller; a spectrum panel is not.
_MIN_IMAGE_PT = 100.0
# Axes, curves and tick marks. A text page has few path objects.
_MIN_DRAWING_PATHS = 30
# Below this fraction of pages saved, building a subset PDF is not worth the risk.
_MIN_SKIP_FRACTION = 0.25


@dataclass(frozen=True)
class PageScan:
    """One page, as the text layer and object counts describe it. ``number`` is 1-based."""

    number: int
    text: str
    n_images: int
    n_paths: int


def counts_as_figure_image(width: float, height: float) -> bool:
    """True for an embedded image large enough to be a panel rather than a logo."""
    return width >= _MIN_IMAGE_PT and height >= _MIN_IMAGE_PT


def select_layout_pages(pages: list[PageScan]) -> list[int]:
    """1-based page numbers to send to Docling.

    Returns every page when nothing looks like a figure, or when skipping would save less than
    a quarter of the document. The caller treats "every page" as "do not build a subset".
    """
    if not pages:
        return []
    numbers = [p.number for p in pages]
    chosen: set[int] = set()
    for page in pages:
        if page.n_images > 0 or page.n_paths >= _MIN_DRAWING_PATHS or _CAPTIONISH.search(page.text or ""):
            chosen.add(page.number)
    if not chosen:
        return numbers
    index = {num: i for i, num in enumerate(numbers)}
    expanded = set(chosen)
    for num in chosen:
        i = index[num]
        if i > 0:
            expanded.add(numbers[i - 1])
        if i + 1 < len(numbers):
            expanded.add(numbers[i + 1])
    ordered = [num for num in numbers if num in expanded]
    saved = 1 - (len(ordered) / len(numbers))
    if saved < _MIN_SKIP_FRACTION:
        return numbers
    return ordered


def scan_pages(pdf_path) -> list[PageScan] | None:
    """Scan a PDF with pypdfium2. ``None`` means the scan is unavailable; parse every page."""
    try:
        import pypdfium2 as pdfium
    except Exception:
        return None
    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
    except Exception:
        return None
    out: list[PageScan] = []
    try:
        image = pdfium.raw.FPDF_PAGEOBJ_IMAGE
        path = pdfium.raw.FPDF_PAGEOBJ_PATH
        for i in range(len(pdf)):
            page = pdf[i]
            try:
                text = ""
                textpage = page.get_textpage()
                try:
                    text = textpage.get_text_bounded() or ""
                finally:
                    textpage.close()
                n_images, n_paths = _count_objects(page, image, path)
                out.append(PageScan(i + 1, text, n_images, n_paths))
            finally:
                page.close()
    except Exception:
        return None
    finally:
        pdf.close()
    return out


def write_page_subset(pdf_path, dest, page_numbers: list[int]) -> None:
    """Write a PDF containing ``page_numbers`` (1-based, in that order) from ``pdf_path``."""
    import pypdfium2 as pdfium

    src = pdfium.PdfDocument(str(pdf_path))
    try:
        dst = pdfium.PdfDocument.new()
        try:
            dst.import_pages(src, pages=[n - 1 for n in page_numbers])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dst.save(str(dest))
        finally:
            dst.close()
    finally:
        src.close()


def doc_page_map(doc, original_pages: list[int]) -> dict[int, int] | None:
    """Map a subset document's page numbers back to the original PDF.

    ``None`` when the document does not have one page per selected original page, so the caller
    can discard the subset and parse the whole file.
    """
    pages = getattr(doc, "pages", None) or {}
    keys = sorted(int(k) for k in pages.keys()) if hasattr(pages, "keys") else []
    if len(keys) != len(original_pages):
        return None
    return dict(zip(keys, original_pages))


def remap_pages(root: BlockNode, page_map: dict[int, int]) -> None:
    """Rewrite page numbers in provenance, caption pages and edge markers."""
    for node in root.walk():
        if node.prov:
            node.prov = [_moved(p, page_map) for p in node.prov]
        if node.edges:
            moved = []
            for edge in node.edges:
                prov = edge.marker_prov
                if prov is not None:
                    prov = _moved(prov, page_map)
                    edge = type(edge)(
                        type=edge.type,
                        target=edge.target,
                        marker_span=edge.marker_span,
                        marker_prov=prov,
                    )
                moved.append(edge)
            node.edges = moved
        cap = node.attrs.get("caption_page")
        if cap is not None:
            node.attrs["caption_page"] = int(page_map.get(int(cap), cap))


def append_text_pages(root: BlockNode, pages: list[PageScan], text_txt: str) -> str:
    """Add one paragraph per block of text from pages Docling did not see.

    Returns the coordinate stream with those paragraphs appended, so char spans stay valid.
    """
    blocks: list[tuple[int, str]] = []
    for page in pages:
        for para in _paragraphs(page.text):
            blocks.append((page.number, para))
    if not blocks:
        return text_txt
    parts = [text_txt]
    cursor = len(text_txt)
    for i, (page_no, para) in enumerate(blocks, start=1):
        start = cursor
        parts.append(para + "\n")
        cursor += len(para) + 1
        # Direct children, not a synthetic section: the outline would otherwise show a heading
        # that is not in the paper.
        root.children.append(BlockNode(
            id=f"{root.id}/textlayer/p{i}",
            type="paragraph",
            text=para,
            prov=[Provenance(page_no, (0.0, 0.0, 0.0, 0.0), (start, start + len(para)))],
        ))
    return "".join(parts)


def _moved(prov: Provenance, page_map: dict[int, int]) -> Provenance:
    return Provenance(
        int(page_map.get(int(prov.page_no), prov.page_no)),
        prov.bbox,
        prov.char_span,
    )


def _count_objects(page, image: int, path: int) -> tuple[int, int]:
    """Count figure-sized images and path objects.

    A nested object in some PDFs makes pypdfium2 raise mid-walk. Retry one level shallower, and
    if both walks fail, treat the page as having a figure so it is not skipped.
    """
    for depth in (2, 1):
        n_images = 0
        n_paths = 0
        try:
            for obj in page.get_objects(max_depth=depth):
                try:
                    kind = obj.type
                    if kind == image and _image_is_large(obj):
                        n_images += 1
                    elif kind == path:
                        n_paths += 1
                finally:
                    try:
                        obj.close()
                    except Exception:
                        pass
            return n_images, n_paths
        except Exception:
            continue
    return 1, 0


def _image_is_large(obj) -> bool:
    try:
        left, bottom, right, top = obj.get_pos()
    except Exception:
        return True
    return counts_as_figure_image(right - left, top - bottom)


def _paragraphs(text: str) -> list[str]:
    text = (text or "").replace("\x00", "").strip()
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts or [text]
