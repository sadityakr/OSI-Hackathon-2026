"""Projection — derive the relational rows (catalog + cites edges) from a ``BlockNode`` tree (M5).

The structural sibling of :mod:`chunker`: where the chunker emits the *vector* rows, this emits the
*relational* rows — the catalog identity row for the parsed root, the catalog stubs for any resolved
reference, and the ``cites`` edges between them. Pure tree→dict mapping, no DB; ``ingest.py`` writes
what this returns.

Why reference stubs are catalog rows too: a parsed paper and a work it merely cites are the same kind
of thing — a citable entity keyed by DOI (design §4). Putting resolved references in the catalog is
what lets the importance prior read a cited work's ``citation_count`` even though we never parsed its
PDF. Pre-M6 a structural-only tree carries no resolved references, so :func:`reference_rows` and
:func:`cites_edges` return ``[]`` — they light up once the GROBID/CrossRef adapter fills the tree.
"""

from __future__ import annotations

import re

from ..parsing.schema import BlockNode

_YEAR_RE = re.compile(
    r"\b(1[5-9]\d{2}|20\d{2})\b"
)  # a 4-digit year inside a partial-precision date


def _year_from_date(published_date: str | None) -> int | None:
    if not published_date:
        return None
    m = _YEAR_RE.search(published_date)
    return int(m.group(1)) if m else None


def _kind(root: BlockNode) -> str:
    """paper vs thesis — a thesis is the deep-nesting genre (has chapter containers)."""
    if root.attrs.get("kind"):
        return root.attrs["kind"]
    return "thesis" if any(n.type == "chapter" for n in root.walk()) else "paper"


def catalog_row(
    root: BlockNode, *, pdf_path: str | None = None, tree_path: str | None = None
) -> dict:
    """The catalog identity row for the parsed document root (``is_parsed = True``).

    Reads identity from ``root.attrs`` — ``citable_key`` always present; ``doi``, ``title``,
    ``authors``, ``journal``, ``published_date`` are filled by M6 (GROBID/CrossRef) and may be absent
    on a structural-only tree. ``citation_count`` is **not** read from the tree (it is catalog-only,
    drifting) — M6's enrichment upserts it straight into the catalog with its as-of date.
    """
    a = root.attrs
    published_date = a.get("published_date")
    return {
        "citable_key": a.get("citable_key") or root.id,
        "doi": a.get("doi"),
        "title": a.get("title"),
        "authors": a.get("authors"),
        "journal": a.get("journal"),
        "year": _year_from_date(published_date) or a.get("year"),
        "published_date": published_date,
        "kind": _kind(root),
        "is_parsed": True,
        "pdf_path": pdf_path or a.get("source_pdf"),
        "tree_path": tree_path,
        "n_pages": a.get("n_pages"),
        "parse_status": a.get("parse_status", "ok"),
    }


def reference_rows(root: BlockNode) -> list[dict]:
    """Catalog stub rows for every *resolved* reference node (``is_parsed = False``).

    A reference resolves when M6 attaches a DOI in its ``attrs``; abstained references (no DOI) are
    deliberately omitted — there is no corpus-wide key to dedupe them on, and a guessed key would be
    a fabricated identity. Citation-count signals, when M6 attached them, ride along here.
    """
    rows: list[dict] = []
    for n in root.walk():
        if n.type != "reference":
            continue
        doi = n.attrs.get("doi")
        if not doi:
            continue  # abstain: unresolved reference gets no catalog row
        published_date = n.attrs.get("published_date")
        rows.append(
            {
                "citable_key": doi,
                "doi": doi,
                "title": n.attrs.get("title"),
                "authors": n.attrs.get("authors"),
                "journal": n.attrs.get("journal"),
                "year": _year_from_date(published_date) or n.attrs.get("year"),
                "published_date": published_date,
                "kind": "reference",
                "is_parsed": False,
                "citation_count": n.attrs.get("citation_count"),
                "citation_count_as_of": n.attrs.get("citation_count_as_of"),
            }
        )
    return rows


def edge_marker(node: BlockNode, edge) -> str | None:
    """The in-text marker string an edge anchored on, e.g. ``"[17]"`` — sliced from the node's text
    via the edge's ``marker_span`` (absolute char offsets rebased to the node's own text). ``None``
    when the edge carries no span or the node no text. Shared by the paper-level ``cites`` projection
    and the chunk-level ``chunk_cites`` (ADR-0007) so both read the marker the same way."""
    if not (edge.marker_span and node.prov and node.text):
        return None
    base = node.prov[0].char_span[0]
    s, t = edge.marker_span
    return node.text[s - base : t - base] or None


def cites_edges(root: BlockNode) -> list[dict]:
    """``cites`` edges from the root to each cited work's DOI (one per resolved citation).

    A ``cites`` edge in the tree targets a local ``reference`` node id; the corpus edge we store
    targets that reference's **DOI**. Unresolved references (no DOI) yield no edge — abstain over a
    dangling corpus link. Deduped on (from_key, to_key); the in-text marker is kept for provenance.
    """
    from_key = root.attrs.get("citable_key") or root.id
    ref_doi = {n.id: n.attrs.get("doi") for n in root.walk() if n.type == "reference"}
    seen: set[str] = set()
    edges: list[dict] = []
    for n in root.walk():
        for e in n.edges:
            if e.type != "cites":
                continue
            to_key = ref_doi.get(e.target)
            if not to_key or to_key in seen:
                continue
            seen.add(to_key)
            edges.append({"from_key": from_key, "to_key": to_key, "marker": edge_marker(n, e)})
    return edges
