"""MCP server — the agent-facing transport over :mod:`tools` (ADR-0009).

Thin adapter only: it opens **one** connection + a lazy embedder and maps each core tool straight
through, so a structured ``status != "ok"`` is returned as *data* (the MCP way to say "I do not have
this" without raising). All logic lives in :mod:`tools`, which is live-testable without an MCP client;
this file is swappable transport — stdio today, HTTP/SSE later if KI-Chat's integration needs it.

``mcp`` is an optional dependency (the ``serve`` extra) so the offline gate never needs it. Run::

    make serve                        # uv run --extra serve python -m lit_rag.store.mcp_server
    python -m lit_rag.store.mcp_server

Needs the compose Postgres up (``make db-up``); the SciNCL model loads lazily on the first semantic
call. Device via ``LITRAG_DEVICE`` (default ``cpu``); on the shared box the embedder caps its own VRAM.
"""

from __future__ import annotations

import os

try:
    from mcp.server.fastmcp import FastMCP
except (
    ImportError
) as e:  # pragma: no cover — surfaced only when someone runs the server without the extra
    raise SystemExit(
        "MCP SDK not installed — run `uv sync --extra serve` (or `make serve`, which passes it)."
    ) from e

from . import db, tools

mcp = FastMCP("lit-rag")

_conn = None
_embedder = None


def _get_conn():
    global _conn
    if _conn is None:
        _conn = db.connect()
        db.apply_schema(_conn)
    return _conn


def _get_embedder():
    global _embedder
    if _embedder is None:
        from .embed import SciNCLEmbedder

        _embedder = SciNCLEmbedder(device=os.environ.get("LITRAG_DEVICE", "cpu"))
    return _embedder


@mcp.tool()
def search(query: str, mode: str = "hybrid", k: int = 5, hydrate_citations: bool = True) -> dict:
    """Search the literature corpus for the most relevant chunks (hybrid semantic+lexical by default).

    mode: "hybrid" (default, RRF of semantic and lexical), "semantic" (embedding ANN), or "lexical"
    (exact full-text). Each hit also returns the references it cites, each carrying an "availability"
    ("full_text" = openable here, "identity" = known but not held -> lookup_external); pass
    hydrate_citations=false to omit them. Each hit
    carries full provenance (citable_key, node_path, page, section) and a unified score — use its
    citable_key + node_path with get_paper or follow_citation.
    """
    embedder = None if mode == "lexical" else _get_embedder()
    return tools.search(
        _get_conn(), embedder, query, mode=mode, k=k, hydrate_citations=hydrate_citations
    )


@mcp.tool()
def get_paper(citable_key: str, include: str = "note", section: str | None = None) -> dict:
    """Look up a paper by its citable_key (a DOI, or a content hash for unresolved works).

    include="note" (default): metadata + abstract + the section list + pdf_path/tree_path handles.
    include="body": the parsed body as provenance-carrying blocks; pass section (an entry from the
    note's section list) to read just that section. include="markdown": the full rendered paper. A work
    that isn't parsed in the corpus returns its reference stub metadata only.
    """
    return tools.get_paper(_get_conn(), citable_key, include=include, section=section)


@mcp.tool()
def follow_citation(citing_key: str, node_path: str, k_per_ref: int = 3) -> dict:
    """Follow the chain of provenance from a citing chunk to the passages that support its claims.

    Given a chunk (citable_key + node_path, e.g. from a search hit that makes a cited claim), returns,
    for each work it cites: the in-text marker (e.g. "[17]"), the resolved reference details, and the
    best-matching supporting chunk(s) in that cited paper — found via the citing chunk's own indexed
    embedding, so a claim is traced to the exact passage that backs it. Cited works absent from the
    corpus abstain cleanly (status "cited_work_not_in_corpus") while still returning their reference
    details.
    """
    return tools.follow_citation(_get_conn(), citing_key, node_path, k_per_ref=k_per_ref)


@mcp.tool()
def graph_walk(citable_key: str, direction: str = "out", depth: int = 1, limit: int = 50) -> dict:
    """Walk the paper-level citation graph from a paper (by citable_key).

    direction="out": the works this paper cites; direction="in": the works that cite it. depth is the
    transitive hop count (1..3; walk one hop at a time and drive the traversal yourself). Each neighbour
    carries its identity + is_parsed (can it be opened with get_paper/follow_citation?) and
    citation_count (an importance signal). truncated=true means the limit capped the result.
    """
    return tools.graph_walk(_get_conn(), citable_key, direction=direction, depth=depth, limit=limit)


@mcp.tool()
def get_figures(citable_key: str) -> dict:
    """Return a paper's figures as per-figure notes: label, caption, page, and file-path handles to the
    image and note. The caption is the readable, information-dense part; image_path is a handle a
    vision-capable client or a human opens. A parsed paper with no figures returns an empty list.
    """
    return tools.get_figures(_get_conn(), citable_key)


@mcp.tool()
def report_issue(
    kind: str,
    note: str,
    citable_key: str | None = None,
    node_path: str | None = None,
    ref_key: str | None = None,
    marker: str | None = None,
) -> dict:
    """Report a data-quality issue (e.g. a broken/wrong reference, a garbled parse) for human review.

    Append-only: the report is queued for a human to triage; it never changes retrieval results. kind is
    a free-form category (broken_reference | wrong_reference | bad_parse | other); the target fields
    (citable_key, node_path, ref_key, marker — e.g. straight from a search hit or follow_citation entry)
    pin what the issue is about.
    """
    return tools.report_issue(
        kind, note, citable_key=citable_key, node_path=node_path, ref_key=ref_key, marker=marker
    )


@mcp.tool()
def lookup_external(doi: str) -> dict:
    """Look up a cited work that is NOT in this corpus, live from OpenAlex (title, authors, year,
    venue, abstract when published, citation count, open-access URL).

    This is where an "identity" availability points. The result is marked source="openalex" — it is
    a different kind of evidence from a passage in our own index (not parsed here, not
    page-locatable), so attribute it as such. status="no_abstract" still returns the bibliographic
    details.
    """
    return tools.lookup_external(doi)


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
