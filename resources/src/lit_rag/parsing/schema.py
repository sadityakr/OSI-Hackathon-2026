"""The canonical ``BlockNode`` tree — the parser's single source of truth (the normalized IR).

This module is the *fixed contract* both parsing adapters satisfy (Docling for structure,
GROBID+CrossRef for bibliography). The shape here is the spec in
``docs/design/parsing-layer.md`` §1; everything downstream reads this tree, never the PDF.

Design constraints honoured here:

* **Lossless JSON round-trip.** ``from_json(to_json(t)) == t`` must hold, so the tree can be
  persisted to ``tree.json`` (the truth) and rebuilt without drift. ``Provenance`` and ``Edge`` are
  frozen dataclasses whose tuples survive the JSON ``tuple -> list -> tuple`` trip exactly.
* **Provenance is mandatory on located content.** Every leaf carries ≥1 ``Provenance`` (page + bbox
  + char-span). External metadata that is *not* located in the PDF (``published_date``; the
  catalog-only citation count) lives in ``attrs`` and carries no provenance — see the invariant note
  in the design doc §1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal, Optional

# The tree contract's version, stamped into every artifact's `attrs["parse"]` (pipeline). Bump on
# any change to the node/edge/provenance shape so stale trees are SELECTABLE, not just suspected.
SCHEMA_VERSION = 1

# --- type taxonomy (docs/design/parsing-layer.md §1) --------------------------------------------

NodeType = Literal[
    # containers (recursive — arbitrary depth: abstract bottoms out shallow, thesis nests deep)
    "document",
    "chapter",
    "section",
    "subsection",
    # front / back matter (first-class nodes, not just root fields)
    "abstract",  # the located abstract paragraph (a body paragraph relabeled via GROBID, prov kept)
    "author",
    "affiliation",
    "funding",
    "acknowledgement",
    "supplementary-material",
    # content leaves
    "paragraph",
    "figure",
    "caption",
    "table",
    "equation",
    "footnote",
    "list",
    "list-item",
    # data & references (citable entities — see §4)
    "dataset",
    "data-availability",
    "reference",
]

EdgeType = Literal[
    "parent",  # structural containment (the tree backbone)
    "caption-of",  # caption <-> figure/table (Docling RefItem)
    # internal cross-references (intra-document; ADR-0002, our resolver)
    "references-figure",
    "references-table",
    "references-section",
    "references-equation",
    # external citations (inter-document; ADR-0003, GROBID+CrossRef)
    "cites",  # in-text marker -> reference node (an external Work)
    "cites-dataset",  # -> dataset node (an external Data entity)
    "author-affiliation",  # author -> affiliation
]

# A node type carries located content (and so must have provenance + may have text).
# Pure containers organise the tree and need not carry text of their own.
CONTAINER_TYPES: frozenset[str] = frozenset({"document", "chapter", "section", "subsection"})

BBox = tuple[float, float, float, float]
Span = tuple[int, int]

# Sentinel char_span for a *region-only* Provenance — a handle that has a real page + bbox but is
# NOT present in the text.txt stream, so no character offset can point at it. Superscript citation
# markers are the motivating case: Docling drops the raised digits from its text stream, yet the
# glyph still has a locatable page+bbox (recovered from the PDF) worth keeping for highlighting.
REGION_ONLY_SPAN: Span = (-1, -1)


@dataclass(frozen=True)
class Provenance:
    """Physical handle back into the source PDF — page + region + character span.

    This is the thing TracEx threw away (Docling's ``item.prov``). It is what makes a citation open
    to a highlighted region rather than the top of a 40-page PDF.
    """

    page_no: int
    bbox: BBox  # (l, t, r, b), TOPLEFT origin
    char_span: Span  # [start, end) into the source text stream (text.txt)


@dataclass(frozen=True)
class Edge:
    type: EdgeType
    target: str  # node id (intra-doc) OR DOI/accession (inter-doc)
    marker_span: Optional[Span] = None  # char-span of the in-text marker (when it IS in text.txt)
    marker_prov: Optional["Provenance"] = (
        None  # page+bbox handle when the marker is NOT in text.txt
    )
    # marker_span anchors textual markers ("[17]", "Fig. 4" — present in the stream); marker_prov
    # anchors geometric markers (superscript citation digits Docling dropped) by page+bbox. A cites
    # edge carries one or the other depending on the citation style; both may be None for a bare link.


@dataclass
class BlockNode:
    id: str  # stable hierarchical-path id (see ids.py / design §2)
    type: NodeType
    text: Optional[str] = None  # leaf content; None for pure containers
    prov: list[Provenance] = field(default_factory=list)  # ≥1 on located content
    edges: list[Edge] = field(default_factory=list)  # outgoing
    children: list["BlockNode"] = field(default_factory=list)  # recursion -> the tree
    attrs: dict = field(default_factory=dict)
    # attrs holds type-specific data: figure image_path, table cells, equation LaTeX,
    # label ("Figure 4"), and — on the document root — citable identity (title, authors,
    # journal, year, published_date, volume, issue, pages, doi, citable_key).
    # Citation count is NOT here: it is a drifting external metric, catalog-only (design §3.7).

    # -- traversal helpers -----------------------------------------------------------------------

    def walk(self):
        """Yield this node then every descendant, depth-first in reading order."""
        yield self
        for child in self.children:
            yield from child.walk()

    def is_container(self) -> bool:
        return self.type in CONTAINER_TYPES


# --- serialization (lossless round-trip) --------------------------------------------------------


def _prov_to_dict(p: Provenance) -> dict:
    return {"page_no": p.page_no, "bbox": list(p.bbox), "char_span": list(p.char_span)}


def _prov_from_dict(d: dict) -> Provenance:
    return Provenance(
        page_no=d["page_no"],
        bbox=tuple(d["bbox"]),  # type: ignore[arg-type]
        char_span=tuple(d["char_span"]),  # type: ignore[arg-type]
    )


def _edge_to_dict(e: Edge) -> dict:
    out: dict = {"type": e.type, "target": e.target}
    if e.marker_span is not None:
        out["marker_span"] = list(e.marker_span)
    if e.marker_prov is not None:
        out["marker_prov"] = _prov_to_dict(e.marker_prov)
    return out


def _edge_from_dict(d: dict) -> Edge:
    ms = d.get("marker_span")
    mp = d.get("marker_prov")
    return Edge(
        type=d["type"],
        target=d["target"],
        marker_span=tuple(ms) if ms is not None else None,  # type: ignore[arg-type]
        marker_prov=_prov_from_dict(mp) if mp is not None else None,
    )


def to_dict(node: BlockNode) -> dict:
    """Plain-dict projection of a node (JSON-ready). Keys omitted when empty for a compact file."""
    out: dict = {"id": node.id, "type": node.type}
    if node.text is not None:
        out["text"] = node.text
    if node.prov:
        out["prov"] = [_prov_to_dict(p) for p in node.prov]
    if node.edges:
        out["edges"] = [_edge_to_dict(e) for e in node.edges]
    if node.attrs:
        out["attrs"] = node.attrs
    if node.children:
        out["children"] = [to_dict(c) for c in node.children]
    return out


def from_dict(d: dict) -> BlockNode:
    return BlockNode(
        id=d["id"],
        type=d["type"],
        text=d.get("text"),
        prov=[_prov_from_dict(p) for p in d.get("prov", [])],
        edges=[_edge_from_dict(e) for e in d.get("edges", [])],
        children=[from_dict(c) for c in d.get("children", [])],
        attrs=d.get("attrs", {}) or {},
    )


def to_json(node: BlockNode, *, indent: int | None = 2) -> str:
    return json.dumps(to_dict(node), indent=indent, ensure_ascii=False)


def from_json(s: str) -> BlockNode:
    return from_dict(json.loads(s))
