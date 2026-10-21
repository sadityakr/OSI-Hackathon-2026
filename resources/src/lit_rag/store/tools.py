"""Agent-facing tool layer over the store — the MCP serving surface's core (ADR-0009).

Pure-ish functions taking a live ``conn`` (and, for semantic search, an ``embedder``) and returning
**JSON-serialisable dicts with an explicit** ``status``. The MCP transport (:mod:`mcp_server`) is a thin
adapter over these; keeping the logic here means it is live-testable (``test_store_live.py``) without
standing up an MCP client, and the transport stays swappable — the same core/adapter seam as the Docling
/ GROBID adapters.

The contract every tool honours:

* **Provenance on every result** — ``citable_key`` + ``node_path`` + page + ``heading_path``.
* **Structured abstention** — a target that isn't in the corpus is *data*, not an exception. Tools return
  an explicit ``status`` drawn from the CLOSED vocabulary in :data:`TOOL_STATUSES` below (``ok`` |
  ``not_found`` | ``no_citations`` | ``cited_work_not_in_corpus`` | ``citing_chunk_not_found`` |
  ``citing_chunk_not_embedded`` | ``no_body_unparsed`` | ``section_not_found`` | ``artifact_missing`` |
  ``bad_request`` | ``queued``). The agent reasons about "I do not have this" instead of catching errors —
  *abstention is cheaper than fabrication*, carried from the design spine into the tool contract.

* **Membership is stated, never discovered by failing** — every cited work / neighbour the agent can see
  carries an ``availability`` drawn from the CLOSED vocabulary in :data:`AVAILABILITIES`
  (``full_text`` | ``identity`` | ``unresolved``). The corpus is a *closed set embedded in an open one*
  (226 of 5,401 catalog entities are papers we hold; only 785 of 8,277 ``chunk_cites`` land on one), so
  ~90% of citation hops would otherwise be a speculative call that abstains. This is the closed-world
  assumption made explicit: "not in the corpus" is a **known fact carried in the metadata**, so the agent
  routes — open it here, or look it up externally — without ever attempting a hop it cannot complete.

The crux is :func:`follow_citation`: it walks the *chain of provenance* a claim in paper B → the sentence
that makes it → the passage in cited paper A that backs it, reusing the citing chunk's **already-stored**
embedding (so it needs no embedder), which is the payoff of the metadata + embedding architecture.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ..parsing.schema import from_json
from . import openalex
from .ingest import (
    _CATALOG_COLS,
    _HIT_COLS,
    hybrid_query,
    lexical_query,
    semantic_query,
)

# The CLOSED status vocabulary — the abstention half of the tool contract (ADR-0009). Every tool
# response carries exactly one of these. Adding a value is a CONTRACT CHANGE for every MCP client:
# route it through this block (and the module docstring), never an inline literal.
STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"
STATUS_NO_CITATIONS = "no_citations"
STATUS_CITED_WORK_NOT_IN_CORPUS = "cited_work_not_in_corpus"
STATUS_CITING_CHUNK_NOT_FOUND = "citing_chunk_not_found"
STATUS_CITING_CHUNK_NOT_EMBEDDED = "citing_chunk_not_embedded"
STATUS_NO_BODY_UNPARSED = "no_body_unparsed"
STATUS_SECTION_NOT_FOUND = "section_not_found"
STATUS_ARTIFACT_MISSING = "artifact_missing"
STATUS_BAD_REQUEST = "bad_request"
STATUS_QUEUED = "queued"
TOOL_STATUSES = frozenset(
    {
        STATUS_OK,
        STATUS_NOT_FOUND,
        STATUS_NO_CITATIONS,
        STATUS_CITED_WORK_NOT_IN_CORPUS,
        STATUS_CITING_CHUNK_NOT_FOUND,
        STATUS_CITING_CHUNK_NOT_EMBEDDED,
        STATUS_NO_BODY_UNPARSED,
        STATUS_SECTION_NOT_FOUND,
        STATUS_ARTIFACT_MISSING,
        STATUS_BAD_REQUEST,
        STATUS_QUEUED,
    }
)

# Image types a chat client can render — what `get_figures` could actually show, and therefore what
# `figure_counts` counts. Narrower than `artifacts.ALLOWED_SUFFIXES`, which also serves PDFs.
_SHOWABLE_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})

# The CLOSED membership vocabulary — the *routing* half of the tool contract, the companion to
# STATUS_* above. Every cited work / graph neighbour the agent sees carries exactly one of these, so it
# can decide where to go BEFORE calling anything (see the module docstring). Same rule as the statuses:
# adding a value is a CONTRACT CHANGE for every client — route it through this block, never an inline
# literal.
AVAIL_FULL_TEXT = (
    "full_text"  # parsed in the corpus: get_paper / follow_citation / search inside it
)
AVAIL_IDENTITY = "identity"  # DOI + bibliographic identity known, no full text: use lookup_external
AVAIL_UNRESOLVED = "unresolved"  # no ref_key/DOI at all — nothing to follow, abstain
# RESERVED, deliberately NOT emitted today: ``"abstract"`` — a locally stored abstract for a work whose
# full text we lack. There is no abstract stored for an unparsed stub (ADR-0007 indexes only parsed
# papers' own science), so emitting it would be dead vocabulary an agent could route on and be wrong. It
# is named here so a future local abstract backfill does not have to re-litigate the word; the live
# external route (:mod:`openalex`, ``lookup_external``) is what serves that need now.
AVAIL_ABSTRACT_RESERVED = "abstract"
AVAILABILITIES = frozenset({AVAIL_FULL_TEXT, AVAIL_IDENTITY, AVAIL_UNRESOLVED})


def availability_of(ref_key: str | None, is_parsed: bool | None) -> str:
    """Map a cited work's catalog facts to its :data:`AVAILABILITIES` membership — pure, offline-tested.

    ``ref_key`` is the cited work's ``citable_key`` (a bare DOI wherever a reference resolved; ADR-0003
    /ADR-0005 abstain rather than mint a key, so an unresolved reference has *no* key at all).
    ``is_parsed`` is the catalog's authority on whether we hold the full text.

    The three outcomes are the agent's routing table: ``full_text`` → open it (:func:`get_paper`,
    :func:`follow_citation`); ``identity`` → we know *which* work it is but not its content, so hand the
    DOI to :func:`lookup_external`; ``unresolved`` → there is nothing to follow, abstain.
    """
    if is_parsed:
        return AVAIL_FULL_TEXT
    if ref_key:
        return AVAIL_IDENTITY
    return AVAIL_UNRESOLVED


# Append-only review queue for agent-reported issues (ADR-0009). The agent *proposes*; a human
# triages into docs/issues/. Never mutates retrieval state. The queue is NOT regenerable, so it must
# not live under the wipeable `output/` tree — the default sits under `data/` (gitignored, on /data
# per ADR-0009, survives artifact cleanups); `LITRAG_ISSUE_QUEUE` overrides it.
_DEFAULT_ISSUE_QUEUE = "data/issues/queue.jsonl"

# Catalog fields surfaced to the agent (a subset of the row, JSON-friendly). `pdf_path` / `tree_path`
# are HANDLES: an agent hands them to a human or a PDF-native tool; reading is served from the parse.
_PAPER_COLS = (
    "citable_key",
    "doi",
    "title",
    "authors",
    "journal",
    "year",
    "published_date",
    "kind",
    "is_parsed",
    "n_pages",
    "citation_count",
    "citation_count_as_of",
    "pdf_path",
    "tree_path",
)


# ── small presenters ────────────────────────────────────────────────────────────────────────────────


def _pages(start, end) -> str | None:
    """A compact page tag: ``p.4`` or ``p.4-5`` (``None`` when a chunk carries no page)."""
    if start is None:
        return None
    return f"p.{start}" + (f"-{end}" if end is not None and end != start else "")


def _present_hit(h: dict) -> dict:
    """Normalise a retrieval hit into a stable agent-facing shape: provenance + a unified ``score`` and
    the channel(s) that voted for it, whichever channel (or fusion) produced it."""
    out = {
        "citable_key": h["citable_key"],
        "node_path": h["node_path"],
        "node_type": h["node_type"],
        "heading_path": h["heading_path"],
        "pages": _pages(h["page_start"], h["page_end"]),
        "text": h["text"],
    }
    if "rrf_score" in h:  # hybrid (RRF)
        out["score"] = round(h["rrf_score"], 6)
        out["channels"] = [
            name for i, name in ((0, "semantic"), (1, "lexical")) if i in h.get("channel_ranks", {})
        ]
    elif "distance" in h:  # semantic (cosine distance → similarity)
        out["score"] = round(1.0 - h["distance"], 6)
        out["channels"] = ["semantic"]
    elif "lexical_score" in h:  # lexical (ts_rank_cd)
        out["score"] = round(h["lexical_score"], 6)
        out["channels"] = ["lexical"]
    if "citations" in h:
        out["citations"] = h["citations"]
    return out


def _present_block(b: dict) -> dict:
    """A body block for reading (no score) — same provenance handles as a hit."""
    return {
        "node_path": b["node_path"],
        "node_type": b["node_type"],
        "heading_path": b["heading_path"],
        "pages": _pages(b["page_start"], b["page_end"]),
        "text": b["text"],
    }


def _present_catalog(row: dict) -> dict:
    """The agent-facing catalog view; the drifting-count timestamp is stringified for JSON."""
    paper = {k: row.get(k) for k in _PAPER_COLS}
    if paper.get("citation_count_as_of") is not None:
        paper["citation_count_as_of"] = str(paper["citation_count_as_of"])
    return paper


# ── point lookups + the within-paper ANN (live SQL — covered by test_store_live.py) ──────────────────


def _catalog_row(conn, citable_key: str) -> dict | None:
    cur = conn.execute(
        f"SELECT {', '.join(_CATALOG_COLS)} FROM catalog WHERE citable_key = %s",
        [citable_key],
    )
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip([d[0] for d in cur.description], row))


def _semantic_within(
    conn, source_key: str, source_node: str, within_key: str, limit: int
) -> list[dict]:
    """The ``limit`` chunks in paper ``within_key`` nearest the citing chunk's STORED embedding.

    The query vector is the citing chunk's own indexed embedding, referenced as a scalar subquery — so
    the whole hop is server-side, needs no embedder, and compares in the exact space the corpus was
    indexed in. Guard the caller so ``within_key`` is a parsed paper and the source chunk is embedded;
    a NULL source embedding would make every distance NULL and the ordering meaningless.
    """
    cur = conn.execute(
        f"SELECT {_HIT_COLS}, "
        "(embedding <=> (SELECT embedding FROM chunks WHERE citable_key = %s AND node_path = %s)) "
        "AS distance "
        "FROM chunks WHERE citable_key = %s AND embedding IS NOT NULL "
        "ORDER BY distance LIMIT %s",
        [source_key, source_node, within_key, limit],
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


# ── the three tools ──────────────────────────────────────────────────────────────────────────────────


# ── figure availability: telling the agent that figures exist at all ────────────────────────────


def figure_counts(conn, citable_keys: list[str]) -> dict[str, int]:
    """How many showable figure images each of ``citable_keys`` has. Papers with none are omitted.

    This exists because of a measured failure, not a hypothetical one. Asked for a STEM image, the
    agent searched, received text passages, and told the member "the corpus returned only text
    passages, not the figures themselves" — then pointed at the publisher's DOI. It never called
    :func:`get_figures`. The inference was sound given what it was shown: **nothing in a search
    result revealed that figures existed at all**, so a capability the corpus has was invisible at
    the moment it was needed. Availability has to be *stated*, exactly as ``availability`` states
    corpus membership for cited works (ADR-0018) rather than letting the agent discover it by
    failing.

    Counted from the figure files on disk rather than by walking ``tree.json``: this is called on
    every search, some documents are 280-page theses, and what matters here is what can actually be
    *shown* — an image file — not how many figure nodes the parse recorded.
    """
    keys = sorted({k for k in citable_keys if k})
    if not keys:
        return {}
    cur = conn.execute(
        "SELECT citable_key, tree_path FROM catalog WHERE citable_key = ANY(%s) AND tree_path IS NOT NULL",
        [keys],
    )
    counts: dict[str, int] = {}
    for citable_key, tree_path in cur.fetchall():
        figures_dir = Path(tree_path).parent / "figures"
        try:
            n = sum(
                1
                for e in os.scandir(figures_dir)
                if e.is_file() and Path(e.name).suffix.lower() in _SHOWABLE_IMAGE_SUFFIXES
            )
        except OSError:
            n = 0  # unparsed, moved, or not mounted — absence of a signal, not an error
        if n:
            counts[citable_key] = n
    return counts


def search(
    conn,
    embedder,
    query: str,
    *,
    mode: str = "hybrid",
    k: int = 5,
    hydrate_citations: bool = True,
) -> dict:
    """Front door: retrieve the ``k`` most relevant chunks (hybrid RRF by default).

    ``mode``: ``hybrid`` (semantic ⊕ lexical, RRF), ``semantic`` (ANN only), or ``lexical`` (full-text
    only). Every hit carries full provenance and a unified ``score``.

    ``hydrate_citations`` is **on by default** (the ADR-0007 join, off at the library level): a hit
    arrives already carrying the works it cites *and each one's* ``availability``, so the agent's next
    hop is a routing decision on metadata it already holds rather than a speculative call. The cost is
    the reason this default is affordable — hydration is ONE extra indexed query over exactly the ``k``
    returned chunks (``_attach_citations``' ``unnest`` join), i.e. O(k) rows and O(1) round-trips, never
    an N+1 per-hit lookup. Pass ``False`` to trade the citation context back for tokens.
    """
    if mode not in ("hybrid", "semantic", "lexical"):
        return {
            "status": STATUS_BAD_REQUEST,
            "error": f"unknown mode {mode!r}",
            "modes": ["hybrid", "semantic", "lexical"],
        }
    if mode in ("hybrid", "semantic") and embedder is None:
        return {"status": STATUS_BAD_REQUEST, "error": f"mode {mode!r} requires an embedder"}
    if mode == "lexical":
        hits = lexical_query(conn, query, k, hydrate_citations=hydrate_citations)
    elif mode == "semantic":
        hits = semantic_query(conn, embedder, query, k, hydrate_citations=hydrate_citations)
    else:
        hits = hybrid_query(conn, embedder, query, k, hydrate_citations=hydrate_citations)
    return {
        "status": STATUS_OK,
        "mode": mode,
        "query": query,
        "hits": [_present_hit(h) for h in hits],
    }


def get_paper(conn, citable_key: str, *, include: str = "note", section: str | None = None) -> dict:
    """Look up a paper by ``citable_key`` (DOI when resolved, else content hash) — the "paper note".

    Graduated depth (*search small, resolve large* at document scale, so a whole thesis never lands in
    the agent's context unasked):

    * ``include="note"`` (default) — metadata + abstract + the section list + ``pdf_path``/``tree_path``
      handles.
    * ``include="body"`` — the parsed body as provenance-carrying blocks; pass ``section`` (one entry
      from the note's section list) to scope to that section subtree.
    * ``include="markdown"`` — the full rendered ``paper.md``.

    A reference not parsed in the corpus returns its stub metadata under ``note``; ``body``/``markdown``
    on it abstain (``no_body_unparsed``).
    """
    if include not in ("note", "body", "markdown"):
        return {
            "status": STATUS_BAD_REQUEST,
            "error": f"unknown include {include!r}",
            "include": ["note", "body", "markdown"],
        }
    row = _catalog_row(conn, citable_key)
    if row is None:
        return {"status": STATUS_NOT_FOUND, "citable_key": citable_key}
    paper = _present_catalog(row)
    if not row["is_parsed"]:
        if include in ("body", "markdown"):
            return {"status": STATUS_NO_BODY_UNPARSED, "citable_key": citable_key, "paper": paper}
        return {"status": STATUS_OK, "paper": paper}

    if include == "note":
        _attach_note(conn, citable_key, paper)
    elif include == "body":
        err = _attach_body(conn, citable_key, paper, section)
        if err is not None:
            return err
    else:  # markdown
        err = _attach_markdown(row, paper)
        if err is not None:
            return err
    return {"status": STATUS_OK, "paper": paper}


def _attach_note(conn, citable_key: str, paper: dict) -> None:
    secs = conn.execute(
        "SELECT heading_path, MIN(page_start) AS p FROM chunks "
        "WHERE citable_key = %s AND heading_path IS NOT NULL AND heading_path <> '' "
        "GROUP BY heading_path ORDER BY p",
        [citable_key],
    ).fetchall()
    paper["sections"] = [s[0] for s in secs]
    abstract = conn.execute(
        "SELECT text FROM chunks WHERE citable_key = %s AND node_type = 'abstract' "
        "ORDER BY node_path LIMIT 1",
        [citable_key],
    ).fetchone()
    paper["abstract"] = abstract[0] if abstract else None


def _attach_body(conn, citable_key: str, paper: dict, section: str | None) -> dict | None:
    if section:
        cur = conn.execute(
            f"SELECT {_HIT_COLS} FROM chunks "
            "WHERE citable_key = %s AND (heading_path = %s OR heading_path LIKE %s) "
            "ORDER BY page_start, node_path",
            [citable_key, section, section + " > %"],
        )
    else:
        cur = conn.execute(
            f"SELECT {_HIT_COLS} FROM chunks WHERE citable_key = %s ORDER BY page_start, node_path",
            [citable_key],
        )
    cols = [d[0] for d in cur.description]
    blocks = [dict(zip(cols, r)) for r in cur.fetchall()]
    if section and not blocks:
        return {"status": STATUS_SECTION_NOT_FOUND, "citable_key": citable_key, "section": section}
    paper["body"] = [_present_block(b) for b in blocks]
    return None


def _attach_markdown(row: dict, paper: dict) -> dict | None:
    if not row.get("tree_path"):
        return {
            "status": STATUS_ARTIFACT_MISSING,
            "citable_key": row["citable_key"],
            "reason": "no tree_path",
        }
    md_path = Path(row["tree_path"]).with_name("paper.md")
    if not md_path.exists():
        return {
            "status": STATUS_ARTIFACT_MISSING,
            "citable_key": row["citable_key"],
            "path": str(md_path),
        }
    paper["markdown"] = md_path.read_text(encoding="utf-8")
    return None


def follow_citation(conn, citing_key: str, node_path: str, *, k_per_ref: int = 3) -> dict:
    """Follow the chain of provenance from one citing chunk to the passages that back its claims.

    Given a chunk (``citing_key`` + ``node_path``, e.g. from a :func:`search` hit), return, for each work
    it cites::

        chunk ──[17]──▶ reference details ──ref_key(DOI)──▶ cited paper ──▶ supporting chunk(s)

    the in-text marker (``[17]``), the resolved reference details, and the best-matching supporting
    chunk(s) in that cited paper. The support search reuses the citing chunk's **stored** embedding
    (:func:`_semantic_within`), so it needs no embedder and matches in the indexed vector space.

    A cited work not parsed in the corpus abstains (``cited_work_not_in_corpus``) but still returns its
    reference details — the marker→details hop works even when the details→paper hop cannot.
    """
    src = conn.execute(
        "SELECT text, heading_path, page_start, page_end, (embedding IS NOT NULL) AS has_emb "
        "FROM chunks WHERE citable_key = %s AND node_path = %s",
        [citing_key, node_path],
    ).fetchone()
    if src is None:
        return {
            "status": STATUS_CITING_CHUNK_NOT_FOUND,
            "citable_key": citing_key,
            "node_path": node_path,
        }
    text, heading_path, p_start, p_end, has_emb = src
    citing = {
        "citable_key": citing_key,
        "node_path": node_path,
        "heading_path": heading_path,
        "pages": _pages(p_start, p_end),
        "text": text,
    }

    refs = conn.execute(
        "SELECT cc.ref_key, cc.marker, c.title, c.authors, c.year, "
        "COALESCE(c.is_parsed, FALSE) AS is_parsed "
        "FROM chunk_cites cc LEFT JOIN catalog c ON c.citable_key = cc.ref_key "
        "WHERE cc.citable_key = %s AND cc.node_path = %s ORDER BY cc.marker",
        [citing_key, node_path],
    ).fetchall()
    if not refs:
        return {"status": STATUS_NO_CITATIONS, "citing": citing, "cited": []}

    cited = []
    for ref_key, marker, title, authors, year, is_parsed in refs:
        entry = {
            "marker": marker,
            "ref_key": ref_key,
            "title": title,
            "authors": authors,
            "year": year,
            # Stated membership, so the agent routes instead of guessing: `identity` here means the
            # abstain below is a KNOWN fact about the corpus, and the DOI in `ref_key` is what
            # `lookup_external` needs to get the work's abstract from OpenAlex.
            "availability": availability_of(ref_key, is_parsed),
        }
        if not ref_key or not is_parsed:
            entry["status"] = STATUS_CITED_WORK_NOT_IN_CORPUS
            entry["support"] = []
        elif not has_emb:
            entry["status"] = STATUS_CITING_CHUNK_NOT_EMBEDDED
            entry["support"] = []
        else:
            support = _semantic_within(conn, citing_key, node_path, ref_key, k_per_ref)
            entry["status"] = STATUS_OK
            entry["support"] = [_present_hit(h) for h in support]
        cited.append(entry)
    return {"status": STATUS_OK, "citing": citing, "cited": cited}


# ── graph_walk: traverse the paper-level citation graph (recursive CTE over `cites`) ─────────────────

# One row per distinct neighbour, resolved to its catalog identity. Marker is a *chunk*-level detail
# (get it from follow_citation / hydrate_citations); graph_walk is about paper-graph topology.
_WALK_OUT = (  # "what this paper cites", forward along from_key → to_key
    "WITH RECURSIVE walk(neighbor, depth) AS ("
    "  SELECT to_key, 1 FROM cites WHERE from_key = %s"
    "  UNION ALL"
    "  SELECT c.to_key, w.depth + 1 FROM cites c JOIN walk w ON c.from_key = w.neighbor"
    "  WHERE w.depth < %s"
    ")"
)
_WALK_IN = (  # "who cites this paper", backward along to_key → from_key
    "WITH RECURSIVE walk(neighbor, depth) AS ("
    "  SELECT from_key, 1 FROM cites WHERE to_key = %s"
    "  UNION ALL"
    "  SELECT c.from_key, w.depth + 1 FROM cites c JOIN walk w ON c.to_key = w.neighbor"
    "  WHERE w.depth < %s"
    ")"
)
_WALK_SELECT = (
    " SELECT w.neighbor, MIN(w.depth) AS depth, c.title, c.authors, c.year, "
    " COALESCE(c.is_parsed, FALSE) AS is_parsed, c.citation_count "
    " FROM walk w LEFT JOIN catalog c ON c.citable_key = w.neighbor "
    " GROUP BY w.neighbor, c.title, c.authors, c.year, c.is_parsed, c.citation_count "
    " ORDER BY depth, w.neighbor LIMIT %s"
)


def graph_walk(
    conn, citable_key: str, *, direction: str = "out", depth: int = 1, limit: int = 50
) -> dict:
    """Walk the paper-level citation graph from ``citable_key`` (recursive CTE over ``cites``).

    ``direction="out"`` = the works this paper cites; ``"in"`` = the works that cite it. ``depth`` is
    the transitive hop count (clamped 1..3 — the agent is meant to walk one hop at a time, driving the
    traversal itself). Each neighbour carries its resolved identity, ``is_parsed`` (can it be opened
    with :func:`get_paper` / :func:`follow_citation`?), the ``availability`` that says so in the closed
    routing vocabulary, and ``citation_count`` (an importance signal).
    ``truncated`` flags that ``limit`` capped the result.
    """
    if direction not in ("out", "in"):
        return {
            "status": STATUS_BAD_REQUEST,
            "error": f"unknown direction {direction!r}",
            "direction": ["out", "in"],
        }
    depth = max(1, min(int(depth), 3))
    limit = max(1, min(int(limit), 200))
    sql = (_WALK_OUT if direction == "out" else _WALK_IN) + _WALK_SELECT
    cur = conn.execute(sql, [citable_key, depth, limit])
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    root = _catalog_row(conn, citable_key)
    if root is None and not rows:
        return {"status": STATUS_NOT_FOUND, "citable_key": citable_key}
    neighbors = [
        {
            "citable_key": r["neighbor"],
            "depth": r["depth"],
            "title": r["title"],
            "authors": r["authors"],
            "year": r["year"],
            "is_parsed": r["is_parsed"],
            "availability": availability_of(r["neighbor"], r["is_parsed"]),
            "citation_count": r["citation_count"],
        }
        for r in rows
    ]
    return {
        "status": STATUS_OK,
        "citable_key": citable_key,
        "root": _present_catalog(root) if root else None,
        "direction": direction,
        "depth": depth,
        "neighbors": neighbors,
        "truncated": len(rows) >= limit,
    }


# ── lookup_external: the open world around the closed corpus (OpenAlex) ─────────────────────────────


def lookup_external(doi: str, *, timeout: float = openalex.DEFAULT_TIMEOUT) -> dict:
    """Look up a work we do **not** hold — the destination ``availability == "identity"`` points at.

    ~90% of citation hops leave the corpus (only 785 of 8,277 ``chunk_cites`` land on a parsed paper),
    but 99.3% of catalog entities carry a DOI: identity is nearly always known, content almost never is.
    Rather than backfilling abstracts into the store, this fetches the work **live from OpenAlex** —
    title, authors, year, venue, the reconstructed abstract, ``cited_by_count``, a DOI URL and the
    open-access URL when there is one.

    Two invariants worth stating loudly:

    * **Provenance is not blurred.** The result carries ``source = "openalex"`` at the top level and
      inside ``work``. An external abstract is a *different epistemic object* from a passage in our
      index: not parsed by us, not page-locatable, not citable as a held passage. Downstream text that
      leans on it must say where it came from.
    * **Read-only.** Nothing is written to the store (ADR-0009 §3 keeps the serving DB read-only from
      the agent's side), and nothing is cached in v1 (``docs/issues/0019``).

    Returns ``{status, source, doi, work?, error?}`` where ``status`` is from
    :data:`~lit_rag.store.openalex.OPENALEX_STATUSES` — ``ok`` | ``no_abstract`` (found, identity
    returned, abstract absent upstream — common and expected, ~43%) | ``not_found`` | ``upstream_error``
    (a timeout or network failure, returned as **data**, never raised) | ``bad_request``.
    """
    return openalex.fetch_work(doi, timeout=timeout)


# ── get_figures: the per-figure notes (image + caption), read from the parsed tree ──────────────────


def get_figures(conn, citable_key: str) -> dict:
    """Return a paper's figures as per-figure notes: label, caption, page, and **handles** to the image
    and note files on disk. Read from ``tree.json`` (figures live in the parse, not the DB).

    The caption is the information-dense, readable part; ``image_path`` is a handle a vision-capable
    client or a human opens (inlining the pixels as a thumbnail is a later enhancement, reusing
    ``viz.figures``). A parsed paper with no figures returns an empty list; an unparsed reference or a
    missing artifact abstains.
    """
    row = _catalog_row(conn, citable_key)
    if row is None:
        return {"status": STATUS_NOT_FOUND, "citable_key": citable_key}
    if not row.get("tree_path"):
        status = STATUS_NO_BODY_UNPARSED if not row.get("is_parsed") else STATUS_ARTIFACT_MISSING
        return {"status": status, "citable_key": citable_key}
    tree_path = Path(row["tree_path"])
    if not tree_path.exists():
        return {
            "status": STATUS_ARTIFACT_MISSING,
            "citable_key": citable_key,
            "path": str(tree_path),
        }
    root = from_json(tree_path.read_text(encoding="utf-8"))
    base = tree_path.parent
    figures = []
    for node in root.walk():
        if node.type != "figure":
            continue
        a = node.attrs
        img = a.get("image_path")
        note = a.get("note_path")
        page = node.prov[0].page_no if node.prov else a.get("caption_page")
        figures.append(
            {
                "node_path": node.id,
                "label": a.get("label"),
                "caption": a.get("caption"),
                "page": page,
                "image_path": str(base / img) if img else None,
                "note_path": str(base / note) if note else None,
                # Addressing halves, kept separate from the absolute path above: `doc_id` is the
                # parsed directory's content hash and `image_rel` the file inside it. A serving
                # adapter composes a browser-facing URL from the pair (`store.artifacts`) without
                # having to re-derive either from a filesystem path it did not build.
                "doc_id": base.name,
                "image_rel": img,
                "note_rel": note,
                "image_missing": bool(a.get("image_missing", False)),
            }
        )
    return {"status": STATUS_OK, "citable_key": citable_key, "figures": figures}


# ── report_issue: append-only review queue (the agent proposes; a human gates) ──────────────────────


def _issue_queue_path(override: str | None = None) -> Path:
    return Path(override or os.environ.get("LITRAG_ISSUE_QUEUE") or _DEFAULT_ISSUE_QUEUE)


def report_issue(
    kind: str,
    note: str,
    *,
    citable_key: str | None = None,
    node_path: str | None = None,
    ref_key: str | None = None,
    marker: str | None = None,
    reporter: str | None = None,
    queue_path: str | None = None,
) -> dict:
    """Log an agent-reported issue (e.g. a broken/wrong reference, a garbled parse) to the review queue.

    Append-only: writes one JSON line to the durable on-disk queue and **never** mutates retrieval state
    — the agent *proposes*, a human triages into ``docs/issues/``. ``kind`` is a free-form category
    (e.g. ``broken_reference`` | ``wrong_reference`` | ``bad_parse`` | ``other``); the target fields
    pin what it's about. Returns the written record + the queue path.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "note": note,
        "citable_key": citable_key,
        "node_path": node_path,
        "ref_key": ref_key,
        "marker": marker,
        "reporter": reporter,
    }
    path = _issue_queue_path(queue_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    return {"status": STATUS_QUEUED, "path": str(path), "record": record}
