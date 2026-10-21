"""Chunker — project a ``BlockNode`` tree into embedding units (M5, "search small, resolve large").

The retrieval law is *search small, resolve large*: embed fine-grained leaves so a query matches the
**smallest** faithful unit (a paragraph, a caption, an equation), then resolve *out* to its enclosing
section when you need context. This module is the "search small" half — it walks the canonical tree
and emits one :class:`Chunk` per embeddable leaf, denormalizing the two things a retrieved hit needs
that aren't in the leaf itself: its **page range** (for "p. 4" citations) and its **heading path**
(the section trail, the handle for "resolve large").

Pure and offline by design — no DB, no embedding model. It turns a tree into rows; ``ingest.py``
embeds those rows and writes them. That split is what keeps ``make check`` fast: this is unit-tested
against hand-built trees, the heavy I/O lives behind thin adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from ..parsing.chemistry import nontechnical_section_ids
from ..parsing.schema import BlockNode
from .projection import edge_marker

# Leaf types that carry retrievable meaning. ``abstract`` is included — M6 relabels the abstract
# paragraph to its own type, and it is a prime retrieval target (ADR-0007 embeds body + abstract).
# Captions are represented *through their figure* (the figure chunk bundles label + caption), so a
# standalone caption with a ``caption-of`` edge is skipped to avoid embedding the same text twice.
_EMBEDDABLE = frozenset(
    {"abstract", "paragraph", "list-item", "table", "equation", "figure", "footnote", "caption"}
)
_HEADING_TYPES = frozenset({"chapter", "section", "subsection"})


@dataclass(frozen=True)
class Chunk:
    """One embedding unit: the denormalized projection of a leaf node for the ``chunks`` table."""

    citable_key: str
    node_path: str  # the leaf's hierarchical id within the tree
    node_type: str
    heading_path: str  # "Methods > Sample growth" — enclosing section trail (for resolve-large)
    text: str
    page_start: int | None
    page_end: int | None
    # (cited DOI, in-text marker) for each work THIS chunk cites — the chunk_cites relation (ADR-0007).
    # Stored, not embedded: hydrated by id at serve time, never fuzzy-matched.
    cites: tuple[tuple[str, str | None], ...] = field(default=())


def _page_range(node: BlockNode) -> tuple[int | None, int | None]:
    pages = [p.page_no for p in node.prov]
    return (min(pages), max(pages)) if pages else (None, None)


def _embeddable_text(node: BlockNode) -> str:
    """The text we actually embed for a leaf — the 'search small' representation.

    Equations embed their LaTeX; figures embed ``label + caption`` (the caption is the figure's
    searchable text now; a VLM description can be appended to this unit later); tables embed their
    flattened cells when present. Everything else embeds its plain ``text``.
    """
    if node.type == "equation":
        return (node.attrs.get("latex") or node.text or "").strip()
    if node.type == "figure":
        label = (node.attrs.get("label") or "").strip()
        caption = (node.attrs.get("caption") or "").strip()
        return f"{label}. {caption}".strip(" .") if (label or caption) else ""
    if node.type == "table":
        cells = node.attrs.get("cells")
        if cells:
            rows = [" | ".join(str(c) for c in row) for row in cells]
            return "\n".join(rows).strip()
        return (node.text or "").strip()
    return (node.text or "").strip()


def _is_caption_of_figure(node: BlockNode) -> bool:
    return node.type == "caption" and any(e.type == "caption-of" for e in node.edges)


def _masthead_ids(root: BlockNode) -> set[str]:
    """Ids of leading front-matter leaves — everything before the first ``abstract`` node in document
    order (ADR-0007). Author lists, affiliations, dates, and PACS lines sit under *no* heading, so no
    heading-based seam catches them. Anchor **only** on the abstract: a headingless intro (common in
    physics letters) must never be mistaken for masthead. No abstract node ⇒ empty — precision-first,
    a miss costs a little noise while over-dropping would lose real body. The set is closed under
    descendants (pre-order), so a per-node membership check suffices in the walk."""
    order = list(root.walk())
    anchor = next((i for i, n in enumerate(order) if n.type == "abstract"), None)
    return set() if anchor is None else {n.id for n in order[:anchor]}


def iter_chunks(root: BlockNode) -> Iterator[Chunk]:
    """Yield one :class:`Chunk` per embeddable **body** leaf, carrying its heading trail, page range,
    and the references it cites.

    Embeds only the paper's own science (ADR-0007): front-matter masthead (:func:`_masthead_ids`) and
    back-matter — references + boilerplate (:func:`nontechnical_section_ids`, ADR-0006) — are excluded
    from the index by construction. Their cited works are not lost: each body chunk carries the DOIs it
    cites (``cites``), joined to the catalog at serve time. Empty leaves are dropped — an empty vector
    is noise, not signal.
    """
    citable_key = root.attrs.get("citable_key") or root.id
    skip = _masthead_ids(root) | nontechnical_section_ids(root)
    ref_doi = {n.id: n.attrs.get("doi") for n in root.walk() if n.type == "reference"}

    def _cites_of(node: BlockNode) -> tuple[tuple[str, str | None], ...]:
        seen: set[str] = set()
        out: list[tuple[str, str | None]] = []
        for e in node.edges:
            if e.type != "cites":
                continue
            doi = ref_doi.get(e.target)
            if doi and doi not in seen:  # abstain on unresolved refs — no DOI, no join key
                seen.add(doi)
                out.append((doi, edge_marker(node, e)))
        return tuple(out)

    def _walk(node: BlockNode, trail: tuple[str, ...]) -> Iterator[Chunk]:
        if node.type in _HEADING_TYPES:
            heading = (node.text or "").strip()
            child_trail = trail + (heading,) if heading else trail
        else:
            child_trail = trail

        if node.id not in skip and node.type in _EMBEDDABLE and not _is_caption_of_figure(node):
            # Strip NUL (0x00): some parses carry stray NULs that PostgreSQL text columns reject.
            # Do it here so the embedded text and the stored text stay byte-identical.
            text = _embeddable_text(node).replace("\x00", "")
            if text:
                page_start, page_end = _page_range(node)
                yield Chunk(
                    citable_key=citable_key,
                    node_path=node.id,
                    node_type=node.type,
                    heading_path=" > ".join(child_trail),
                    text=text,
                    page_start=page_start,
                    page_end=page_end,
                    cites=_cites_of(node),
                )

        for child in node.children:
            yield from _walk(child, child_trail)

    yield from _walk(root, ())
