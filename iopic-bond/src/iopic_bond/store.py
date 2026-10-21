"""The local library: one folder per paper, indexed by a SQLite file.

Every parsed paper is kept, so the library grows with use and the same paper is never parsed twice.
The folders are the source of truth; ``index.sqlite`` is derived from them and ``reindex()`` rebuilds
it, so deleting the index loses nothing.

Input: the library root (``config.home()``) and records from the ingest step.
Process: ``lookup`` by DOI or arXiv base id; ``record_parse`` writes ``meta.json`` and the index rows;
``search`` runs SQLite FTS5 full-text search over figure captions, the paragraphs that mention each
figure, and paper titles.
Output: dict rows; the folder layout below.

    <root>/
      index.sqlite
      papers/<base_id>/paper.pdf
      papers/<base_id>/meta.json
      papers/<base_id>/parsed/<content_hash>/tree.json, figures/...

All storage access goes through this module, so a remote store could replace it later.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    base_id        TEXT PRIMARY KEY,   -- arXiv id without version
    doi            TEXT,
    title          TEXT,
    authors        TEXT,               -- JSON list
    year           INTEGER,
    license        TEXT,
    url            TEXT,
    content_hash   TEXT,               -- names parsed/<hash>/
    parser_version TEXT,
    status         TEXT,               -- parsed | fetch_failed | parse_failed
    n_figures      INTEGER,
    updated_at     TEXT
);
CREATE INDEX IF NOT EXISTS papers_doi ON papers(doi);
-- FTS5 is SQLite's built-in full-text search; base_id and label are stored but not tokenised
CREATE VIRTUAL TABLE IF NOT EXISTS figures_fts USING fts5(
    base_id UNINDEXED, label UNINDEXED, image_rel UNINDEXED, title, caption, mentions
);
"""


def folder_name(base_id: str) -> str:
    """Old-style ids contain a slash (``cond-mat/0501234``), which cannot be a folder name."""
    return base_id.replace("/", "_")


class Store:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else config.home()
        self.papers_dir = self.root / "papers"
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "index.sqlite", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(_SCHEMA)

    # -- paths ---------------------------------------------------------------------------------

    def paper_dir(self, base_id: str) -> Path:
        return self.papers_dir / folder_name(base_id)

    def parsed_dir(self, base_id: str) -> Path:
        return self.paper_dir(base_id) / "parsed"

    def tree_path(self, row: dict) -> Optional[Path]:
        if not row.get("content_hash"):
            return None
        p = self.parsed_dir(row["base_id"]) / row["content_hash"] / "tree.json"
        return p if p.exists() else None

    # -- lookup --------------------------------------------------------------------------------

    def lookup(self, *, base_id: Optional[str] = None, doi: Optional[str] = None) -> Optional[dict]:
        """Find a paper by DOI first (shared by the arXiv and journal records), then by arXiv id."""
        if doi:
            r = self.db.execute("SELECT * FROM papers WHERE lower(doi) = lower(?)", (doi.strip(),)).fetchone()
            if r:
                return dict(r)
        if base_id:
            r = self.db.execute("SELECT * FROM papers WHERE base_id = ?", (base_id,)).fetchone()
            if r:
                return dict(r)
        return None

    def known_ids(self, papers: list[dict]) -> set[str]:
        """Base ids among ``papers`` (Bond records) that are already parsed in the library."""
        out = set()
        for p in papers:
            row = self.lookup(base_id=p.get("base_id"), doi=p.get("doi") or None)
            if row and row["status"] == "parsed":
                out.add(p.get("base_id"))
        return out

    # -- write ---------------------------------------------------------------------------------

    def record_failure(self, base_id: str, status: str, meta: dict) -> None:
        self._upsert(base_id, {**meta, "status": status, "content_hash": None, "n_figures": 0})

    def record_parse(self, base_id: str, meta: dict, content_hash: str, parser_version: str,
                     figures: list[dict]) -> dict:
        """Store a finished parse: ``meta.json`` in the folder, then the index rows."""
        meta = {**meta, "base_id": base_id, "content_hash": content_hash,
                "parser_version": parser_version, "status": "parsed", "n_figures": len(figures)}
        self.paper_dir(base_id).mkdir(parents=True, exist_ok=True)
        (self.paper_dir(base_id) / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        self._upsert(base_id, meta)
        self._index_figures(base_id, meta.get("title") or "", figures)
        return self.lookup(base_id=base_id)

    def _upsert(self, base_id: str, m: dict) -> None:
        self.db.execute(
            """INSERT INTO papers (base_id, doi, title, authors, year, license, url, content_hash,
                                   parser_version, status, n_figures, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(base_id) DO UPDATE SET
                 doi=excluded.doi, title=excluded.title, authors=excluded.authors, year=excluded.year,
                 license=excluded.license, url=excluded.url, content_hash=excluded.content_hash,
                 parser_version=excluded.parser_version, status=excluded.status,
                 n_figures=excluded.n_figures, updated_at=excluded.updated_at""",
            (base_id, m.get("doi") or None, m.get("title"), json.dumps(m.get("authors") or []),
             m.get("year"), m.get("license"), m.get("url"), m.get("content_hash"),
             m.get("parser_version"), m.get("status"), m.get("n_figures"),
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        self.db.commit()

    def _index_figures(self, base_id: str, title: str, figures: list[dict]) -> None:
        self.db.execute("DELETE FROM figures_fts WHERE base_id = ?", (base_id,))
        self.db.executemany(
            "INSERT INTO figures_fts (base_id, label, image_rel, title, caption, mentions) VALUES (?,?,?,?,?,?)",
            [(base_id, f.get("label"), f.get("image_rel"), title, f.get("caption") or "",
              " ".join(f.get("mentions") or [])) for f in figures],
        )
        self.db.commit()

    # -- read ----------------------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Full-text search over figure captions, mentioning paragraphs and titles.

        Words are quoted so FTS5 syntax characters in the query cannot break it. All words must
        match; if nothing does, any word may match.
        """
        words = [w for w in re.findall(r"[\w\-]+", query) if len(w) > 1]
        if not words:
            return []
        rows = []
        for joiner in (" ", " OR "):
            fts_query = joiner.join(f'"{w}"' for w in words)
            rows = self.db.execute(
                """SELECT base_id, label, image_rel, title, caption,
                          snippet(figures_fts, 5, '[', ']', ' ... ', 12) AS mention_snippet
                   FROM figures_fts WHERE figures_fts MATCH ? ORDER BY rank LIMIT ?""",
                (fts_query, limit),
            ).fetchall()
            if rows:
                break
        return [dict(r) for r in rows]

    def list_papers(self) -> list[dict]:
        return [dict(r) for r in self.db.execute(
            "SELECT base_id, doi, title, year, n_figures, status FROM papers ORDER BY updated_at DESC")]

    # -- maintenance ---------------------------------------------------------------------------

    def reindex(self, figures_of) -> int:
        """Rebuild the index from the folders. ``figures_of(tree_path)`` returns figure dicts."""
        self.db.executescript("DELETE FROM papers; DELETE FROM figures_fts;")
        n = 0
        for meta_path in self.papers_dir.glob("*/meta.json"):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            base_id = meta["base_id"]
            tree = self.parsed_dir(base_id) / str(meta.get("content_hash")) / "tree.json"
            if meta.get("status") != "parsed" or not tree.exists():
                self._upsert(base_id, meta)
                continue
            self._upsert(base_id, meta)
            self._index_figures(base_id, meta.get("title") or "", figures_of(tree))
            n += 1
        return n
