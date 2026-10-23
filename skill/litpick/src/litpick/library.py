"""The library: one SQLite file plus one folder per paper.

    <home>/litpick.db
    <home>/papers/<key>/paper.pdf
    <home>/papers/<key>/fig-<label>.png      (rendered on first view, then reused)

Tables
    papers    one row per paper (arXiv version or local PDF), with the parser version used
    figures   one row per figure: page, region, caption, how the region was found
    mentions  paragraphs that cite a figure
    fig_fts   full-text index over captions, mentions and titles (SQLite FTS5)

SQLite runs in WAL mode so the MCP server and the command-line tool can use the library at the
same time. Each paper is written in one transaction: a crash never leaves half a paper.
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .paths import db_path, papers_dir, safe_name

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    key            TEXT PRIMARY KEY,   -- '2407.13230v2' or 'local-<sha12>'
    source         TEXT NOT NULL,      -- 'arxiv' | 'local'
    base_id        TEXT,               -- '2407.13230' for arXiv papers
    version        TEXT,               -- 'v2'
    title          TEXT,
    authors        TEXT,               -- JSON list
    year           INTEGER,
    sha256         TEXT,
    pages          INTEGER,
    parser_version TEXT,
    origin         TEXT,               -- where the PDF came from (URL or original path)
    ingested_at    REAL
);
CREATE INDEX IF NOT EXISTS papers_base ON papers(base_id);
CREATE INDEX IF NOT EXISTS papers_sha ON papers(sha256);
CREATE TABLE IF NOT EXISTS figures (
    paper_key TEXT NOT NULL REFERENCES papers(key) ON DELETE CASCADE,
    label     TEXT NOT NULL,
    page      INTEGER,
    bbox      TEXT,
    caption   TEXT,
    method    TEXT,
    PRIMARY KEY (paper_key, label)
);
CREATE TABLE IF NOT EXISTS mentions (
    paper_key TEXT NOT NULL REFERENCES papers(key) ON DELETE CASCADE,
    label     TEXT NOT NULL,
    text      TEXT
);
"""
FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS fig_fts USING fts5(
    title, caption, mentions, paper_key UNINDEXED, label UNINDEXED, tokenize='porter unicode61'
);
"""


class _Con(sqlite3.Connection):
    """A connection that remembers whether this Python's SQLite has FTS5."""
    fts: bool = False


@contextmanager
def connect():
    con = sqlite3.connect(db_path(), timeout=30, factory=_Con)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    try:
        con.executescript(FTS)
        con.fts = True
    except sqlite3.OperationalError:  # a Python build without FTS5: fall back to LIKE search
        con.fts = False
    try:
        yield con
        con.commit()
    finally:
        con.close()


def paper_dir(key: str) -> Path:
    d = papers_dir() / safe_name(key)
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_paper(con, key: str) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM papers WHERE key = ?", (key,)).fetchone()


def latest_for_base(con, base_id: str) -> sqlite3.Row | None:
    rows = con.execute("SELECT * FROM papers WHERE base_id = ?", (base_id,)).fetchall()
    if not rows:
        return None
    return max(rows, key=lambda r: int((r["version"] or "v0")[1:] or 0))


def by_sha(con, sha: str) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM papers WHERE sha256 = ?", (sha,)).fetchone()


def resolve_key(con, ref: str) -> str | None:
    """'2407.13230' -> newest stored version; '2407.13230v1' -> that version; keys as given."""
    if get_paper(con, ref):
        return ref
    from .arxiv import parse_id
    aid = parse_id(ref)
    if aid and aid.version and get_paper(con, aid.full):
        return aid.full
    if aid:
        row = latest_for_base(con, aid.base)
        return row["key"] if row else None
    return None


def save_paper(con, *, key, source, base_id, version, title, authors, year, sha256, pages,
               parser_version, origin, figures) -> None:
    con.execute("DELETE FROM papers WHERE key = ?", (key,))  # cascades to figures and mentions
    if con.fts:
        con.execute("DELETE FROM fig_fts WHERE paper_key = ?", (key,))
    con.execute(
        "INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (key, source, base_id, version, title, json.dumps(authors), year, sha256, pages,
         parser_version, origin, time.time()),
    )
    for f in figures:
        con.execute("INSERT INTO figures VALUES (?,?,?,?,?,?)",
                    (key, f.label, f.page, json.dumps(f.bbox), f.caption, f.method))
        con.executemany("INSERT INTO mentions VALUES (?,?,?)", [(key, f.label, t) for t in f.mentions])
        if con.fts:
            con.execute("INSERT INTO fig_fts VALUES (?,?,?,?,?)",
                        (title, f.caption, "\n".join(f.mentions), key, f.label))
    # old renders may show a different region now; drop them so they are drawn again
    for png in paper_dir(key).glob("fig-*.png"):
        png.unlink(missing_ok=True)


def figures_of(con, key: str) -> list[dict]:
    rows = con.execute("SELECT * FROM figures WHERE paper_key = ?", (key,)).fetchall()
    out = []
    for r in rows:
        ments = [m["text"] for m in con.execute(
            "SELECT text FROM mentions WHERE paper_key = ? AND label = ?", (key, r["label"]))]
        out.append({"label": r["label"], "page": r["page"], "bbox": json.loads(r["bbox"]),
                    "caption": r["caption"], "method": r["method"], "mentions": ments})
    return out


def search(con, query: str, limit: int = 10) -> list[dict]:
    if con.fts:
        terms = [t for t in re.findall(r"\w+", query) if t]
        if not terms:
            return []
        fts_q = " OR ".join(f'"{t}"' for t in terms)
        rows = con.execute(
            "SELECT paper_key, label, caption, bm25(fig_fts, 2.0, 5.0, 1.0) AS score "
            "FROM fig_fts WHERE fig_fts MATCH ? ORDER BY score LIMIT ?", (fts_q, limit)).fetchall()
    else:
        like = f"%{query}%"
        rows = con.execute(
            "SELECT paper_key, label, caption, 0 AS score FROM figures WHERE caption LIKE ? LIMIT ?",
            (like, limit)).fetchall()
    out = []
    for r in rows:
        p = get_paper(con, r["paper_key"])
        out.append({"paper": r["paper_key"], "figure": r["label"],
                    "title": p["title"] if p else "", "caption": r["caption"][:400]})
    return out


def all_papers(con) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM papers ORDER BY ingested_at DESC").fetchall()


def delete_paper(con, key: str) -> bool:
    if not get_paper(con, key):
        return False
    con.execute("DELETE FROM papers WHERE key = ?", (key,))
    if con.fts:
        con.execute("DELETE FROM fig_fts WHERE paper_key = ?", (key,))
    d = papers_dir() / safe_name(key)
    for f in d.glob("*"):
        f.unlink(missing_ok=True)
    try:
        d.rmdir()
    except OSError:
        pass
    return True
