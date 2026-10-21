"""Ingest — project a parsed tree into PostgreSQL, and query it back (M5, ADR-0004).

The orchestrator that ties the pure projections (:mod:`projection`, :mod:`chunker`) to the live store
(:mod:`db`, :mod:`embed`). It walks ``tree.json`` **into** the database — never the reverse — writing
the catalog row, the resolved reference stubs + ``cites`` edges, and the embedded ``chunks``.

Ingest **reconciles, not just upserts**: a paper's ``chunks`` and outgoing ``cites`` are
delete-then-reinserted inside the transaction, so after ingest the store's state for that paper
*exactly equals* what its current tree projects — a re-parse that renumbers ``node_path``s or drops
leaves leaves no orphaned chunks/edges behind (upserts alone can add and overwrite but never forget;
architecture review 2026-07-06, F3). Everything deleted is derived and rebuilt in the same call.
``catalog`` is the exception — rows are SHARED (a reference stub may be cited by many papers), so it
is upsert-only with the authority-aware merge below; orphaned stubs are a separate GC concern.

Dependency-injected on purpose: ``conn`` and ``embedder`` are passed in, so the row-building /
write-sequencing logic is unit-testable against a fake connection + fake embedder with no Postgres and
no model download — the heavy bits stay behind the seam.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..parsing.schema import BlockNode, from_json
from .chunker import iter_chunks
from .keywords import extract_keywords
from .projection import catalog_row, cites_edges, reference_rows
from .rank_fusion import rrf_fuse

# Columns every retrieval channel returns, so a hit is self-describing regardless of which channel (or
# fusion) produced it — same provenance shape for the caller/CLI.
_HIT_COLS = "citable_key, node_path, node_type, heading_path, text, page_start, page_end"

_CATALOG_COLS = (
    "citable_key",
    "doi",
    "title",
    "authors",
    "journal",
    "year",
    "published_date",
    "kind",
    "is_parsed",
    "pdf_path",
    "tree_path",
    "n_pages",
    "parse_status",
    "citation_count",
    "citation_count_as_of",
)

# Identity fields a *reference stub* must never overwrite on an already-parsed row. In a single-group
# corpus a parsed paper is usually also cited by its neighbours, so it gets re-upserted as a stub
# (is_parsed=False, kind='reference', sparser metadata). Plain COALESCE(EXCLUDED, catalog) only guards
# NULLs, so that stub would clobber the parsed identity (e.g. kind 'paper' -> 'reference'). These
# columns follow the parsed record instead: the stub fills gaps but never downgrades.
_IDENTITY_COLS = frozenset({"doi", "title", "authors", "journal", "year", "published_date", "kind"})


def _merge_clause(c: str) -> str:
    """The ``ON CONFLICT DO UPDATE SET`` expression for one column, by authority (see above)."""
    if c == "is_parsed":
        # Sticky-true: once a document is parsed, a later reference-stub upsert must never demote it.
        return "is_parsed = catalog.is_parsed OR EXCLUDED.is_parsed"
    if c in _IDENTITY_COLS:
        # Parsed record is authoritative for identity; a stub only fills what the parsed row lacks.
        return (
            f"{c} = CASE WHEN catalog.is_parsed AND NOT EXCLUDED.is_parsed "
            f"THEN COALESCE(catalog.{c}, EXCLUDED.{c}) "
            f"ELSE COALESCE(EXCLUDED.{c}, catalog.{c}) END"
        )
    # Additive fields (paths, page count, citation signals): the incoming non-null wins, never
    # clobbered back to null by a sparser write.
    return f"{c} = COALESCE(EXCLUDED.{c}, catalog.{c})"


def _clean_nul(v):
    """Strip NUL (0x00) bytes — PostgreSQL ``text`` columns reject them (occurs in some parses)."""
    return v.replace("\x00", "") if isinstance(v, str) else v


def _upsert_catalog(conn, row: dict) -> None:
    cols = [c for c in _CATALOG_COLS if c in row]
    vals = [
        _clean_nul(json.dumps(row[c]) if c == "authors" and row[c] is not None else row[c])
        for c in cols
    ]
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join(_merge_clause(c) for c in cols if c != "citable_key")
    sql = (
        f"INSERT INTO catalog ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT (citable_key) DO UPDATE SET {updates}"
    )
    conn.execute(sql, vals)


def _insert_cites(conn, edges: list[dict]) -> None:
    for e in edges:
        conn.execute(
            "INSERT INTO cites (from_key, to_key, marker) VALUES (%s, %s, %s) "
            "ON CONFLICT (from_key, to_key) DO UPDATE SET marker = COALESCE(EXCLUDED.marker, cites.marker)",
            [e["from_key"], e["to_key"], e.get("marker")],
        )


def _replace_chunk_cites(conn, citable_key: str, rows: list[dict]) -> None:
    """Rewrite a document's ``chunk_cites`` (ADR-0007) — clear this doc's rows, then insert fresh.
    Since ``ingest_tree`` now deletes the doc's chunks first (reconcile), the FK cascade already
    cleared these; the explicit DELETE stays as belt-and-braces (this fn is also callable alone).
    Must run after ``_upsert_chunks`` (the FK needs the chunk rows present)."""
    conn.execute("DELETE FROM chunk_cites WHERE citable_key = %s", [citable_key])
    for r in rows:
        conn.execute(
            "INSERT INTO chunk_cites (citable_key, node_path, ref_key, marker) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (citable_key, node_path, ref_key) DO UPDATE SET marker = EXCLUDED.marker",
            [r["citable_key"], r["node_path"], r["ref_key"], r["marker"]],
        )


def _upsert_chunks(conn, rows: list[dict]) -> None:
    for r in rows:
        conn.execute(
            "INSERT INTO chunks (citable_key, node_path, node_type, heading_path, text, "
            "page_start, page_end, embedding, parser_version) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (citable_key, node_path) DO UPDATE SET "
            "node_type = EXCLUDED.node_type, heading_path = EXCLUDED.heading_path, "
            "text = EXCLUDED.text, page_start = EXCLUDED.page_start, "
            "page_end = EXCLUDED.page_end, embedding = EXCLUDED.embedding, "
            "parser_version = EXCLUDED.parser_version",
            [
                r["citable_key"],
                r["node_path"],
                r["node_type"],
                r["heading_path"],
                r["text"],
                r["page_start"],
                r["page_end"],
                r["embedding"],
                r.get("parser_version", "unknown"),
            ],
        )


def build_chunk_rows(root: BlockNode, embedder) -> list[dict]:
    """Chunk the tree and attach an embedding per chunk — the rows ``_upsert_chunks`` writes."""
    chunks = list(iter_chunks(root))
    vectors = embedder.encode([c.text for c in chunks]) if chunks else []
    # derived-data provenance (review F4): every chunk records the parser code that produced its
    # tree, so "which chunks predate fix X?" is a WHERE clause, not a corpus re-derivation
    parser_version = (root.attrs.get("parse") or {}).get("parser_version", "unknown")
    return [
        {
            "citable_key": c.citable_key,
            "node_path": c.node_path,
            "node_type": c.node_type,
            "heading_path": c.heading_path,
            "text": c.text,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "embedding": v,
            "parser_version": parser_version,
        }
        for c, v in zip(chunks, vectors)
    ]


def chunk_cite_rows(root: BlockNode) -> list[dict]:
    """The chunk_cites rows for a tree (ADR-0007): one per (body chunk, cited DOI), flattening each
    chunk's resolved citations. The relational half of the chunk projection — the counterpart to
    :func:`build_chunk_rows`' vector half; pure, no embedder."""
    return [
        {"citable_key": c.citable_key, "node_path": c.node_path, "ref_key": ref, "marker": marker}
        for c in iter_chunks(root)
        for ref, marker in c.cites
    ]


def ingest_tree(
    conn,
    root: BlockNode,
    *,
    embedder,
    pdf_path: str | None = None,
    tree_path: str | None = None,
) -> dict:
    """Project one parsed tree into the store (catalog + references + cites + chunks + chunk_cites).

    Reconciling per paper (see the module docstring): this paper's derived rows are cleared and
    rewritten in one transaction; shared ``catalog`` rows are merged, never cleared.
    """
    citable_key = root.attrs.get("citable_key") or root.id
    _upsert_catalog(conn, catalog_row(root, pdf_path=pdf_path, tree_path=tree_path))
    refs = reference_rows(root)
    for r in refs:
        _upsert_catalog(conn, r)
    # Reconcile: clear THIS paper's derived rows so stale node_paths / dropped leaves / retracted
    # edges from an earlier parse cannot survive. chunk_cites clears via its FK's ON DELETE CASCADE.
    conn.execute("DELETE FROM cites WHERE from_key = %s", [citable_key])
    conn.execute("DELETE FROM chunks WHERE citable_key = %s", [citable_key])
    edges = cites_edges(root)
    _insert_cites(conn, edges)
    chunk_rows = build_chunk_rows(root, embedder)
    _upsert_chunks(conn, chunk_rows)
    cite_rows = chunk_cite_rows(root)
    _replace_chunk_cites(conn, citable_key, cite_rows)
    conn.commit()
    return {
        "references": len(refs),
        "cites": len(edges),
        "chunks": len(chunk_rows),
        "chunk_cites": len(cite_rows),
    }


def apply_catalog_signals(conn, signals: list[dict]) -> int:
    """Upsert catalog-only signals (citation_count + as-of) onto existing catalog rows.

    The M6 ``catalog_signals.json`` sidecar route: the drifting citation count reaches the catalog
    here, never via ``tree.json`` (design §3.7). Only touches rows that already exist (an enrichment,
    not an insert), and the DB CHECK still guarantees a count never lands without its as-of date.
    """
    n = 0
    for s in signals:
        if s.get("citation_count") is None:
            continue
        conn.execute(
            "UPDATE catalog SET citation_count = %s, citation_count_as_of = %s WHERE citable_key = %s",
            [s["citation_count"], s.get("citation_count_as_of"), s["citable_key"]],
        )
        n += 1
    conn.commit()
    return n


def ingest_path(conn, doc_dir, embedder) -> dict:
    """Ingest a parsed ``<hash>/`` directory (its ``tree.json`` + optional ``catalog_signals.json``)."""
    doc_dir = Path(doc_dir)
    tree_path = doc_dir / "tree.json"
    root = from_json(tree_path.read_text(encoding="utf-8"))
    counts = ingest_tree(conn, root, embedder=embedder, tree_path=str(tree_path))
    signals_path = doc_dir / "catalog_signals.json"
    if signals_path.exists():
        signals = json.loads(signals_path.read_text(encoding="utf-8"))
        counts["catalog_signals"] = apply_catalog_signals(conn, signals)
    return counts


def _attach_citations(conn, hits: list[dict]) -> None:
    """Hydrate each hit with the references it cites (ADR-0007) — a serve-time join over *only* the
    returned chunks (O(k), not O(corpus)). Sets ``hit['citations']`` to a list of resolved refs
    (marker, ref_key/DOI, title, authors, year, **availability**) looked up from the catalog by id —
    never embedded, never fuzzy-matched. Unresolved refs simply have null metadata (LEFT JOIN).

    ``availability`` (the closed vocabulary in :mod:`~lit_rag.store.tools`) is the *membership* fact:
    can this cited work be opened here (``full_text``), only identified (``identity``, → external
    lookup), or not even that (``unresolved``)? It rides along for free — ``is_parsed`` is one more
    column on the SAME single join, so the O(1)-round-trip / O(k)-row cost ADR-0007 designed for is
    unchanged; there is no per-hit lookup and no N+1.

    (The ``tools`` import is function-local *only* to break the import cycle: ``tools`` imports the
    query functions from this module, so the membership vocabulary — which belongs with the rest of the
    agent-facing contract — cannot be imported here at module level.)"""
    from .tools import availability_of

    cks = [h["citable_key"] for h in hits]
    nps = [h["node_path"] for h in hits]
    cur = conn.execute(
        "SELECT cc.citable_key, cc.node_path, cc.marker, cc.ref_key, c.title, c.authors, c.year, "
        "COALESCE(c.is_parsed, FALSE) AS is_parsed "
        "FROM chunk_cites cc "
        "JOIN unnest(%s::text[], %s::text[]) AS q(citable_key, node_path) "
        "  ON cc.citable_key = q.citable_key AND cc.node_path = q.node_path "
        "LEFT JOIN catalog c ON c.citable_key = cc.ref_key "
        "ORDER BY cc.marker",
        [cks, nps],
    )
    cols = [d[0] for d in cur.description]
    by_chunk: dict[tuple[str, str], list[dict]] = {}
    for row in cur.fetchall():
        r = dict(zip(cols, row))
        by_chunk.setdefault((r["citable_key"], r["node_path"]), []).append(
            {
                "marker": r["marker"],
                "ref_key": r["ref_key"],
                "title": r["title"],
                "authors": r["authors"],
                "year": r["year"],
                "availability": availability_of(r["ref_key"], r["is_parsed"]),
            }
        )
    for h in hits:
        h["citations"] = by_chunk.get((h["citable_key"], h["node_path"]), [])


def _chunk_id(hit: dict) -> tuple[str, str]:
    """A chunk's stable identity across channels — the (document, node) key RRF merges on."""
    return (hit["citable_key"], hit["node_path"])


def _semantic_channel(conn, embedder, query: str, limit: int) -> list[dict]:
    """The ANN channel: the ``limit`` nearest chunks by SciNCL cosine distance, best-first."""
    qvec = embedder.encode([query])[0]
    # ``encode`` returns a plain ``list[float]``, which psycopg sends as ``double precision[]``.
    # The ``<=>`` cosine operator is only defined on ``vector``, and operators (unlike INSERT) do
    # not apply the array→vector assignment cast — so cast the parameter explicitly.
    cur = conn.execute(
        f"SELECT {_HIT_COLS}, (embedding <=> %s::vector) AS distance "
        "FROM chunks WHERE embedding IS NOT NULL "
        "ORDER BY embedding <=> %s::vector LIMIT %s",
        [qvec, qvec, limit],
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _lexical_channel(conn, query: str, limit: int) -> list[dict]:
    """The full-text channel: the ``limit`` best chunks by ``ts_rank_cd`` over the query's SALIENT
    KEYWORDS, best-first.

    ADR-0015 (Issue 0014): the query is first reduced to its discriminating terms
    (:func:`~lit_rag.store.keywords.extract_keywords`), and those are **OR-combined**. Plain
    ``websearch_to_tsquery`` AND-s every term — which a long natural-language question never satisfies,
    so the channel would go silent — so each keyword contributes its own tsquery joined by the ``||``
    tsquery-OR operator (still injection-safe: every term is parsed by ``websearch_to_tsquery``, never
    interpolated). ``ts_rank_cd`` (cover density) then rewards chunks matching MORE of the keywords, so
    precision survives the AND→OR switch. No salient keywords ⇒ no lexical contribution (empty list).
    """
    terms = extract_keywords(query)
    if not terms:
        return []
    ors = " || ".join(["websearch_to_tsquery('english', %s)"] * len(terms))
    cur = conn.execute(
        f"WITH q AS (SELECT ({ors}) AS tsq) "
        f"SELECT {_HIT_COLS}, ts_rank_cd(tsv, q.tsq) AS lexical_score "
        "FROM chunks, q WHERE tsv @@ q.tsq "
        "ORDER BY lexical_score DESC LIMIT %s",
        [*terms, limit],
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def semantic_query(
    conn, embedder, query: str, k: int = 5, *, hydrate_citations: bool = False
) -> list[dict]:
    """ANN-only search: embed ``query`` and return the ``k`` nearest chunks with their provenance.

    With ``hydrate_citations`` (ADR-0007), each hit also carries ``citations`` — the resolved works
    it cites, joined from the catalog at serve time. Off by default so the caller controls token cost.
    """
    hits = _semantic_channel(conn, embedder, query, k)
    if hydrate_citations and hits:
        _attach_citations(conn, hits)
    return hits


def lexical_query(conn, query: str, k: int = 5, *, hydrate_citations: bool = False) -> list[dict]:
    """Full-text-only search — the ``k`` best chunks by ``ts_rank_cd`` (no embedder needed)."""
    hits = _lexical_channel(conn, query, k)
    if hydrate_citations and hits:
        _attach_citations(conn, hits)
    return hits


def hybrid_query(
    conn,
    embedder,
    query: str,
    k: int = 5,
    *,
    pool: int = 50,
    hydrate_citations: bool = False,
) -> list[dict]:
    """Hybrid retrieval (design §5.2): fuse the semantic and lexical channels by Reciprocal Rank Fusion.

    The semantic channel (SciNCL/ANN) finds meaning-similar chunks; the lexical channel (Postgres FTS)
    matches the exact discriminating tokens the embedding model collapses (CrSBr vs CrCl3). Each
    contributes its top ``pool`` candidates (default 50); :func:`rrf_fuse` merges them by rank — a
    chunk strong in *both* channels beats one strong in only one — and the fused top ``k`` are returned.
    RRF is score-scale-free, so no semantic/lexical weight has to be tuned (that weight is a named open
    problem the fusion sidesteps). Fused hits carry ``rrf_score`` + ``channel_ranks``; ``distance`` /
    ``lexical_score`` are present when the hit came from that channel.
    """
    sem = _semantic_channel(conn, embedder, query, pool)
    lex = _lexical_channel(conn, query, pool)
    fused = rrf_fuse([sem, lex], k=k, id_of=_chunk_id)
    if hydrate_citations and fused:
        _attach_citations(conn, fused)
    return fused
