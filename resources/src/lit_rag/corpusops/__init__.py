"""Corpus operations — the tracked drivers that produce the real store (promoted from tmp/).

The four steps of the corpus production loop, each robust per-paper (one failure never kills the
batch), resumable, and reporting to a JSONL record file + summary:

    python -m lit_rag.corpusops parse        # PDFs -> output/parsed/<hash>/ vaults (Docling, GPU)
    python -m lit_rag.corpusops enrich       # Phase 1 (ADR-0005): GROBID structure, no network
    python -m lit_rag.corpusops consolidate  # Phase 2 (ADR-0005): CrossRef DOIs, resumable
    python -m lit_rag.corpusops ingest       # enriched trees -> the live Postgres store

These were the gitignored ``tmp/`` scripts that built the 226-paper corpus; they are tracked here so
the repo can reproduce its own store (architecture review 2026-07-06, finding F2). Shared helpers
live in this module; each step is its own submodule with a ``run(args)`` entrypoint.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

log = logging.getLogger("lit_rag.corpusops")


def setup_logging() -> None:
    """Timestamped INFO logging to stdout — the corpus runs are long; every line needs a clock."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")


def append_jsonl(path: Path, rec: dict) -> None:
    """Append one record — written per item as it completes, so a crash loses nothing."""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def fresh_report(report_dir: str | Path) -> tuple[Path, Path]:
    """Create the report dir and truncate its ``records.jsonl``; returns (records, summary) paths."""
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    records = report_dir / "records.jsonl"
    records.write_text("", encoding="utf-8")
    return records, report_dir / "summary.json"


def write_summary(path: Path, summary: dict) -> None:
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("DONE %s", json.dumps(summary))


def retry(fn, *args, attempts: int = 3, default=None, **kwargs):
    """Call ``fn`` with linear backoff; return ``default`` after the last failure (abstain, not crash)."""
    for attempt in range(attempts):
        try:
            return fn(*args, **kwargs)
        except Exception:
            if attempt == attempts - 1:
                return default
            time.sleep(2 * (attempt + 1))
    return default
