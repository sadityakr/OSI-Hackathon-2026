"""Batch ingest: stream every enriched tree in output/parsed/ into the live store.

Loads the SciNCL model ONCE (looping the store CLI would reload it per doc). Per-doc try/except so
a single bad tree can't abort the corpus; ``lit_rag.store.ingest`` reconciles per paper, so
re-running after a re-parse converges the store to the trees (no orphans).
"""

from __future__ import annotations

import time
from pathlib import Path

from . import append_jsonl, fresh_report, log, write_summary


def add_args(ap) -> None:
    ap.add_argument("--parsed", default="output/parsed")
    ap.add_argument("--report", default="tmp/ingest_report")
    ap.add_argument("--device", default="cuda", choices=("cpu", "cuda"))


def run(args) -> int:
    from lit_rag.store import db
    from lit_rag.store.embed import SciNCLEmbedder
    from lit_rag.store.ingest import ingest_path

    root = Path(args.parsed)
    dirs = sorted(d for d in root.iterdir() if (d / "tree.json").exists())
    skipped = [d for d in root.iterdir() if d.is_dir() and not (d / "tree.json").exists()]
    log.info("[ingest] trees=%d | dirs without tree.json skipped=%d", len(dirs), len(skipped))

    records, summary_path = fresh_report(args.report)

    conn = db.connect()
    db.apply_schema(conn)
    embedder = SciNCLEmbedder(device=args.device)

    totals = {"docs": 0, "references": 0, "cites": 0, "chunks": 0, "errors": 0}
    t0 = time.time()
    for i, d in enumerate(dirs, 1):
        try:
            c = ingest_path(conn, d, embedder)
            totals["docs"] += 1
            for k in ("references", "cites", "chunks"):
                totals[k] += c.get(k, 0)
            append_jsonl(records, {"i": i, "hash": d.name, "status": "ok", **c})
            if i % 10 == 0 or i == len(dirs):
                dt = time.time() - t0
                log.info(
                    "[%d/%d] %s chunks=%s (%.0fs, %.1f docs/s)",
                    i,
                    len(dirs),
                    d.name,
                    c.get("chunks"),
                    dt,
                    i / dt,
                )
        except Exception as e:  # noqa: BLE001 — one bad tree must not abort the corpus
            totals["errors"] += 1
            append_jsonl(
                records,
                {"i": i, "hash": d.name, "status": "fail", "error": f"{type(e).__name__}: {e}"},
            )
            log.error("[%d/%d] ERROR %s: %s: %s", i, len(dirs), d.name, type(e).__name__, e)

    conn.close()
    write_summary(summary_path, {**totals, "wall_s": round(time.time() - t0)})
    return 1 if totals["errors"] else 0
