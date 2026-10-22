"""Withheld papers: keep the papers behind an evaluation case out of the agent's reach.

Input: ``IOPIC_BOND_EXCLUDE`` (entries separated by commas, semicolons or newlines) and/or
``IOPIC_BOND_EXCLUDE_FILE`` (a text file, one entry per line, ``#`` starts a comment). Each entry is an
arXiv id (``2503.15298``), a DOI (anything with a ``/``, ``https://doi.org/`` prefix allowed) or a
title fragment (any other text, matched case-insensitively as a substring of the title).
Process: every tool that returns or opens papers asks ``is_excluded`` before it does.
Output: withheld papers never appear in search results and cannot be ingested, listed or viewed.

Why: when the data under test come from a paper, that paper (and its companions) holds the answer.
The agent may use everything else the literature reports, but not the source of the test data.
"""
from __future__ import annotations

import os
import re
from typing import Optional

from .arxiv import bare_id, looks_like_arxiv_id

WITHHELD = {"status": "withheld",
            "detail": "This paper is withheld in this session (it is the source of the data under test)."}


def _raw_entries() -> list[str]:
    out = [x for x in re.split(r"[,;\n]", os.environ.get("IOPIC_BOND_EXCLUDE", ""))]
    path = os.environ.get("IOPIC_BOND_EXCLUDE_FILE", "").strip()
    if path:
        with open(path, encoding="utf-8") as fh:  # a missing file is an error: the guard must not fail open
            out += [line.split("#", 1)[0] for line in fh]
    return out


def _entries() -> tuple[set[str], set[str], list[str]]:
    ids, dois, titles = set(), set(), []
    for e in (x.strip() for x in _raw_entries()):
        if not e:
            continue
        if looks_like_arxiv_id(e):
            ids.add(bare_id(e).lower())
        elif "/" in e:
            dois.add(_doi(e))
        else:
            titles.append(e.lower())
    return ids, dois, titles


def _doi(s: str) -> str:
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", s.strip().lower())


def active() -> bool:
    return bool(os.environ.get("IOPIC_BOND_EXCLUDE", "").strip()
                or os.environ.get("IOPIC_BOND_EXCLUDE_FILE", "").strip())


def is_excluded(paper_id: Optional[str] = None, doi: Optional[str] = None, title: Optional[str] = None) -> bool:
    """True when the paper matches a withheld arXiv id, DOI or title fragment."""
    if not active():
        return False
    ids, dois, titles = _entries()
    if paper_id and bare_id(str(paper_id)).lower() in ids:
        return True
    if doi and _doi(str(doi)) in dois:
        return True
    t = (title or "").lower()
    return bool(t) and any(frag in t for frag in titles)


def record_excluded(p: dict) -> bool:
    """``is_excluded`` for a paper record from Bond or the store (any of base_id, id, doi, title)."""
    return (is_excluded(p.get("base_id"), p.get("doi"), p.get("title"))
            or is_excluded(p.get("id") or p.get("paper_id") or p.get("arxiv_id")))
