"""Docling adapter (ADR-0002) — ``DoclingDocument`` -> canonical ``BlockNode`` tree.

This is the *replaceable internal* behind the fixed ``schema.BlockNode`` contract. It does three
things the design names (parsing-layer.md §3 step 2):

1. **Map** ``DocItemLabel`` -> ``NodeType`` (text->paragraph, section_header->section/subsection,
   formula->equation, picture->figure, …).
2. **Build the recursive containment tree** from heading levels using a section-header stack — so an
   abstract nests shallow and a thesis nests deep, both as the *same* tree.
3. **Carry ``item.prov`` through** into ``Provenance`` (page + bbox + char-span) — the step TracEx
   skipped. Docling's bbox is BOTTOMLEFT origin; we convert to the contract's TOPLEFT. ``char_span``
   is assigned against a ``text.txt`` coordinate stream we build here (concatenated leaf text in
   reading order), so spans are self-consistent within one parse. (Reconciling this stream with
   GROBID's is the M6 open problem; not needed for the structural parse.)

Returns ``(root, text_txt, figure_saves)`` — the tree, the plain coordinate stream, and a list of
``(image_path, PIL.Image)`` for the caller to write under ``figures/``.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from .ids import PathBuilder
from .render import figure_note_rel
from .schema import BlockNode, Edge, Provenance

# Latin accented letters Docling tends to space out ("Jos é", "Kl ä ui"). Deliberately EXCLUDES
# Greek and math symbols (α, ξ, Ω, μ …), which legitimately stand alone in scientific text and must
# never be merged into neighbouring tokens.
_LATIN_ACCENTED = "àáâãäåæèéêëìíîïñòóôõöøùúûüýÿçčćđłńřšșțžÀÁÂÃÄÅÆÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝÇČĆĐŁŃŘŠȘȚŽ"
# 1) drop a space *before* an accented letter that follows a word char  ("Jos é" -> "José")
_RE_JOIN_LEFT = re.compile(r"(?<=\w) (?=[" + _LATIN_ACCENTED + r"])")
# 2) drop a space *after* an accented letter when a lowercase continuation follows ("Klä ui" -> "Kläui")
_RE_JOIN_RIGHT = re.compile(r"(?<=[" + _LATIN_ACCENTED + r"]) (?=[a-zà-ÿ])")

# A *spacing* diacritic that floated off its letter ("N´ eel" -> "Néel"): map it to the combining
# form and recompose onto the following vowel. Common in magnetism text (Néel walls/temperature).
_SPACING_TO_COMBINING = {"´": "́", "`": "̀", "¨": "̈", "ˆ": "̂", "˜": "̃", "¸": "̧"}
_RE_FLOAT_ACCENT = re.compile(r"([´`¨ˆ˜¸])\s+([A-Za-z])")

# Pictures smaller than this fraction of the page area are treated as decorative (logos, journal
# branding, icons) and dropped — they are not real figures.
_MIN_FIGURE_AREA_FRACTION = 0.03

# A caption's leading label ("Figure 2.5:", "Table 3") — the real, chapter-prefixed number, used to
# label the figure/table it belongs to instead of a fabricated sequential counter.
_RE_FIG_LABEL = re.compile(
    r"^\s*(Figure|Fig\.?|Table|Tab\.?)\s+(\d+(?:\.\d+)*[a-z]?)", re.IGNORECASE
)


def _compose_accent(m: "re.Match") -> str:
    return unicodedata.normalize("NFC", m.group(2) + _SPACING_TO_COMBINING.get(m.group(1), ""))


def normalize_text(s: Optional[str]) -> Optional[str]:
    """Repair Docling's spaced-out diacritics without touching Greek/math glyphs.

    Handles both *precomposed* spaced letters ("Jos é" -> "José") and *floating spacing accents*
    ("N´ eel" -> "Néel"). Greek/units (α, ξ, Ω, μ) are never matched, so physics notation is safe.
    """
    if not s:
        return s
    s = _RE_FLOAT_ACCENT.sub(_compose_accent, s)
    s = _RE_JOIN_LEFT.sub("", s)
    s = _RE_JOIN_RIGHT.sub("", s)
    return s


# Docling DocItemLabel.value -> our NodeType. Labels not listed are dropped as page furniture.
_LABEL_MAP: dict[str, str] = {
    "text": "paragraph",
    "paragraph": "paragraph",
    "caption": "caption",
    "formula": "equation",
    "picture": "figure",
    "table": "table",
    "list_item": "list-item",
    "footnote": "footnote",
    "reference": "reference",
    "title": "section",  # document title handled separately, but be safe
    # front/back matter that Docling sometimes labels:
    "checkbox_selected": "paragraph",
    "checkbox_unselected": "paragraph",
    "code": "paragraph",
}

# Page-furniture labels we deliberately drop (noise, not body content).
_DROP_LABELS = {"page_header", "page_footer", "page_number"}


def _label(item) -> Optional[str]:
    lab = getattr(item, "label", None)
    return getattr(lab, "value", lab)


def _page_heights(doc) -> dict[int, float]:
    heights: dict[int, float] = {}
    pages = getattr(doc, "pages", {}) or {}
    items = pages.items() if hasattr(pages, "items") else enumerate(pages)
    for page_no, page in items:
        size = getattr(page, "size", None)
        if size is not None and getattr(size, "height", None):
            heights[int(page_no)] = float(size.height)
    return heights


def _provenance(
    item, page_heights: dict[int, float], char_span: tuple[int, int]
) -> list[Provenance]:
    """Convert Docling prov (BOTTOMLEFT bbox) into TOPLEFT ``Provenance`` carrying our char_span."""
    out: list[Provenance] = []
    for pv in getattr(item, "prov", []) or []:
        page_no = int(pv.page_no)
        bb = pv.bbox
        h = page_heights.get(page_no)
        try:
            tl = bb.to_top_left_origin(h) if h else bb
            box = (float(tl.l), float(tl.t), float(tl.r), float(tl.b))
        except Exception:
            # fall back to raw coords if conversion is unavailable
            box = (float(bb.l), float(bb.t), float(bb.r), float(bb.b))
        out.append(Provenance(page_no=page_no, bbox=box, char_span=char_span))
    return out


def _page_areas(doc) -> dict[int, float]:
    out: dict[int, float] = {}
    pages = getattr(doc, "pages", {}) or {}
    items = pages.items() if hasattr(pages, "items") else enumerate(pages)
    for page_no, page in items:
        size = getattr(page, "size", None)
        if size is not None and getattr(size, "width", None) and getattr(size, "height", None):
            out[int(page_no)] = float(size.width) * float(size.height)
    return out


def _is_decorative_picture(item, page_areas: dict[int, float]) -> bool:
    """A picture covering a tiny fraction of its page is a logo/icon, not a real figure."""
    pv = getattr(item, "prov", []) or []
    if not pv:
        return False  # no geometry to judge by -> keep
    p = pv[0]
    bb = p.bbox
    area = abs((bb.r - bb.l) * (bb.t - bb.b))
    page_area = page_areas.get(int(p.page_no))
    if not page_area:
        return False
    return (area / page_area) < _MIN_FIGURE_AREA_FRACTION


def _figure_image(doc, item):
    """Best-effort extraction of a picture's PIL image across Docling versions."""
    try:
        img = item.get_image(doc)
        if img is not None:
            return img
    except Exception:
        pass
    ref = getattr(item, "image", None)
    return getattr(ref, "pil_image", None) if ref is not None else None


def tree_from_docling(doc, root_id: str):
    """Build the canonical tree from a ``DoclingDocument``.

    Returns ``(root, text_txt, figure_saves)``.
    """
    page_heights = _page_heights(doc)
    page_areas = _page_areas(doc)
    pb = PathBuilder(root_id)

    root = BlockNode(id=root_id, type="document", attrs={"citable_key": root_id})
    n_pages = doc.num_pages() if hasattr(doc, "num_pages") else None
    if n_pages:
        root.attrs["n_pages"] = n_pages

    # container stack of (heading_level, node); root sits at level 0
    stack: list[tuple[int, BlockNode]] = [(0, root)]
    text_parts: list[str] = []
    cursor = 0
    reading_order: list[BlockNode] = []  # leaves in order, for caption proximity linking
    figure_saves: list[tuple[str, object]] = []
    fig_count = 0
    title_set = False

    for item, _lvl in doc.iterate_items():
        lab = _label(item)
        if lab in _DROP_LABELS:
            continue

        # --- headings: open/close containers by level -------------------------------------------
        if lab == "section_header":
            heading_text = normalize_text((getattr(item, "text", None) or "").strip())
            level = int(getattr(item, "level", 1) or 1)
            # The first level-1 header is taken as the document title; don't also emit it as a
            # section (that would duplicate the H1 the renderer makes from the root title).
            if not title_set and level == 1 and heading_text:
                root.attrs["title"] = heading_text
                title_set = True
                continue
            while len(stack) > 1 and stack[-1][0] >= level:
                stack.pop()
            parent = stack[-1][1]
            node_type = "section" if level <= 1 else "subsection"
            node = BlockNode(id=pb.child(parent.id, node_type), type=node_type, text=heading_text)
            start = cursor
            text_parts.append(heading_text + "\n")
            cursor += len(heading_text) + 1
            node.prov = _provenance(item, page_heights, (start, cursor - 1))
            parent.children.append(node)
            stack.append((level, node))
            continue

        node_type = _LABEL_MAP.get(lab)
        if node_type is None:
            continue  # unknown / unmapped label -> drop quietly
        if node_type == "figure" and _is_decorative_picture(item, page_areas):
            continue  # logo/icon, not a real figure

        parent = stack[-1][1]
        text = getattr(item, "text", None)
        text = normalize_text(text.strip() if text else None)

        # assign char span against the text.txt stream
        start = cursor
        if text:
            text_parts.append(text + "\n")
            cursor += len(text) + 1
        span = (start, cursor - 1 if text else start)

        node = BlockNode(id=pb.child(parent.id, node_type), type=node_type, text=text)
        node.prov = _provenance(item, page_heights, span)

        if node_type == "equation":
            node.attrs["latex"] = text or ""
        elif node_type == "figure":
            fig_count += 1
            img = _figure_image(doc, item)
            if img is not None:
                # fig{N}.png is just a unique *filename*; the displayed label is set later from the
                # caption (the real chapter-prefixed "Figure 2.5"), never a fabricated counter.
                rel = f"figures/fig{fig_count}.png"
                node.attrs["image_path"] = rel
                # note_path is recorded in the tree so the figure<->note link is explicit in JSON
                node.attrs["note_path"] = figure_note_rel(rel)
                figure_saves.append((rel, img))
        elif node_type == "table":
            node.attrs["cells"] = _table_cells(item)

        parent.children.append(node)
        reading_order.append(node)

    _link_captions(reading_order)
    text_txt = "".join(text_parts)
    return root, text_txt, figure_saves


def _table_cells(item) -> list[list[str]]:
    """Extract a Docling table into a list-of-rows-of-strings grid (best effort)."""
    data = getattr(item, "data", None)
    grid = getattr(data, "grid", None)
    if not grid:
        return []
    out: list[list[str]] = []
    for row in grid:
        out.append([(getattr(cell, "text", "") or "").strip() for cell in row])
    return out


def _link_captions(reading_order: list[BlockNode]) -> None:
    """Link each caption to the nearest preceding figure/table, and lift the caption's real label.

    The ``caption-of`` edge anchors the pair; the caption's leading "Figure 2.5"/"Table 3" becomes
    the figure's ``label`` — the actual, chapter-prefixed number, not a fabricated sequential one.
    """
    last_figural: Optional[BlockNode] = None
    for node in reading_order:
        if node.type in ("figure", "table"):
            last_figural = node
        elif node.type == "caption" and last_figural is not None:
            # link both ways so the pair is navigable from either node in tree.json:
            #   caption --caption-of--> figure   and   figure.attrs.caption_id --> caption
            node.edges.append(Edge(type="caption-of", target=last_figural.id))
            last_figural.attrs["caption_id"] = node.id
            # denormalize the caption onto the figure so figure+caption is one embeddable unit
            last_figural.attrs["caption"] = node.text or ""
            if node.prov:
                last_figural.attrs["caption_page"] = node.prov[0].page_no
            m = _RE_FIG_LABEL.match(node.text or "")
            if m:
                last_figural.attrs["label"] = f"{m.group(1).rstrip('.').title()} {m.group(2)}"
            last_figural = None  # one caption per figure; don't reattach the next caption
