"""``python -m lit_rag.store.cli`` — initialise the DB, ingest parsed trees, and query (M5).

A thin operator front-end over :mod:`ingest`. Needs the live store (the compose Postgres) and, for
``ingest``/``query``, the SciNCL model — so it is *not* part of ``make check`` (that stays offline).
Run the DB first (``make db-up``), then ``init`` / ``ingest`` / ``query``.
"""

from __future__ import annotations

import argparse
import sys


def _score(hit: dict) -> str:
    """A compact score tag for a hit, whichever channel(s) produced it."""
    if (
        "rrf_score" in hit
    ):  # hybrid: show the fused score + which channels voted (s=semantic, l=lexical)
        voted = "".join(c for i, c in ((0, "s"), (1, "l")) if i in hit.get("channel_ranks", {}))
        return f"rrf={hit['rrf_score']:.4f}[{voted}]"
    if "distance" in hit:
        return f"dist={hit['distance']:.3f}"
    return f"lex={hit['lexical_score']:.3f}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="lit_rag.store.cli", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="apply schema.sql to the database (idempotent)")

    pi = sub.add_parser("ingest", help="ingest a parsed <hash>/ directory (or its tree.json)")
    pi.add_argument("doc_dir", help="output/parsed/<hash>/ directory")
    pi.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="SciNCL device")

    pq = sub.add_parser("query", help="search over ingested chunks (hybrid by default)")
    pq.add_argument("text", help="the query string")
    pq.add_argument("-k", type=int, default=5, help="number of results")
    pq.add_argument(
        "--mode",
        default="hybrid",
        choices=["hybrid", "semantic", "lexical"],
        help="hybrid = RRF(semantic, lexical); semantic = ANN only; lexical = full-text only",
    )
    pq.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    pq.add_argument(
        "--cite",
        action="store_true",
        help="hydrate each hit with the references it cites (ADR-0007; off by default)",
    )

    args = p.parse_args(argv)

    from . import db

    conn = db.connect()
    try:
        if args.cmd == "init":
            db.apply_schema(conn)
            print("schema applied")
            return 0

        db.apply_schema(conn)  # ensure tables exist before ingest/query

        if args.cmd == "ingest":
            from .embed import SciNCLEmbedder
            from .ingest import ingest_path

            counts = ingest_path(conn, args.doc_dir, SciNCLEmbedder(device=args.device))
            print(f"ingested {args.doc_dir}: {counts}")
            return 0
        if args.cmd == "query":
            from .ingest import hybrid_query, lexical_query, semantic_query

            if args.mode == "lexical":  # no embedder needed for the full-text channel
                hits = lexical_query(conn, args.text, args.k, hydrate_citations=args.cite)
            else:
                from .embed import SciNCLEmbedder

                embedder = SciNCLEmbedder(device=args.device)
                fn = hybrid_query if args.mode == "hybrid" else semantic_query
                hits = fn(conn, embedder, args.text, args.k, hydrate_citations=args.cite)
            for i, hit in enumerate(hits, 1):
                pages = f"p.{hit['page_start']}" + (
                    f"-{hit['page_end']}" if hit["page_end"] != hit["page_start"] else ""
                )
                head = hit["heading_path"] or hit["node_type"]
                print(f"\n[{i}] {_score(hit)}  {hit['citable_key']}  {pages}  {head}")
                print(f"    {hit['text'][:200]}")
                for c in hit.get("citations", []):
                    who = (
                        (c["authors"][0] + " et al.") if c.get("authors") else (c["ref_key"] or "?")
                    )
                    yr = f", {c['year']}" if c.get("year") else ""
                    print(
                        f"      ↳ {c.get('marker') or '[?]'} {who}: {c.get('title') or c['ref_key']}{yr}"
                    )
            return 0
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
