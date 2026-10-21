"""Ingest papers into the library and read their figures back.

The parse-once rule lives here: ``ingest`` returns the stored parse when the paper is already in the
library with the current parser version, and only otherwise downloads and parses it.

Input: an arXiv id, optionally the paper's Bond record (title, DOI, licence) for ``meta.json``.
Process: store lookup -> ``arxiv.fetch_pdf`` -> ``pdf.parse_pdf`` (Docling) -> figure records ->
``Store.record_parse``. Synchronous and slow on a cold parse; the server runs it in a worker thread.
Output: dicts with an explicit ``status`` (``ok``, ``cached``, ``fetch_failed``, ``parse_failed``,
``not_found``) so the agent reasons about a gap instead of catching an exception.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from . import config
from .arxiv import bare_id, fetch_pdf
from .figures import figures_from_tree
from .pdf.schema import from_json
from .store import Store


def _parser_version() -> str:
    # imported lazily: the pipeline module pulls in the Docling adapter
    from .pdf.pipeline import PARSER_VERSION

    return PARSER_VERSION


def figure_dicts(tree_path: Path) -> list[dict]:
    """Figure records from a stored ``tree.json``, with paths relative to its folder."""
    doc_dir = tree_path.parent
    root = from_json(tree_path.read_text(encoding="utf-8"))
    out = []
    for f in figures_from_tree(root, doc_dir):
        rel = f.image_path.relative_to(doc_dir).as_posix() if f.image_path else None
        out.append({
            "label": f.label or (f"Figure {_stem_number(rel)}" if rel else None),
            "caption": f.caption,
            "page": f.page,
            "image_rel": rel,
            "image_path": str(f.image_path) if f.image_path else None,
            "mentions": f.mentions,
            "node_id": f.node_id,
        })
    return out


def _stem_number(rel: Optional[str]) -> Optional[str]:
    m = re.search(r"fig(?:ure)?[._-]?(\d+)", rel or "", re.I)
    return m.group(1) if m else None


def _figure_number(text: Optional[str]) -> Optional[str]:
    """"Figure 2", "FIG. 2", "Fig 2b", "2" -> "2"."""
    m = re.search(r"(\d+)", text or "")
    return m.group(1) if m else None


def find_figure(figures: list[dict], which: str) -> Optional[dict]:
    """Match a figure by its printed number ("2", "Fig. 2", "Figure 2") or node id."""
    for f in figures:
        if which == f.get("node_id"):
            return f
    want = _figure_number(which)
    if want is None:
        return None
    for f in figures:
        if _figure_number(f.get("label")) == want:
            return f
    return None


def meta_from_bond(p: dict) -> dict:
    """The fields of a Bond paper record worth keeping in ``meta.json``."""
    first = (p.get("dates") or {}).get("first_available") or {}
    year = (first.get("value") or p.get("first_submitted") or "")[:4]
    return {
        "doi": p.get("doi") or None,
        "title": p.get("title"),
        "authors": p.get("authors") or [],
        "year": int(year) if year.isdigit() else None,
        "license": p.get("license"),
        "url": p.get("url"),
        "journal_ref": p.get("journal_ref"),
        "citation_count": p.get("citation_count"),
    }


def ingest(store: Store, arxiv_id: str, *, meta: Optional[dict] = None, force: bool = False) -> dict:
    """Return the paper's parse from the library, parsing it first if needed."""
    base_id = bare_id(arxiv_id)
    row = store.lookup(base_id=base_id)
    if row and not force and row["status"] == "parsed" and row["parser_version"] == _parser_version():
        tree = store.tree_path(row)
        if tree:
            return {"status": "cached", "paper": row, "tree_path": str(tree)}

    meta = meta or {}
    pdf = fetch_pdf(base_id, store.paper_dir(base_id) / "paper.pdf")
    if pdf is None:
        store.record_failure(base_id, "fetch_failed", meta)
        return {"status": "fetch_failed", "base_id": base_id,
                "detail": f"could not download https://arxiv.org/pdf/{base_id}"}

    from .pdf import parse_pdf

    try:
        root = parse_pdf(pdf, store.parsed_dir(base_id), device=config.parse_device(), force=force)
    except ImportError:
        return {"status": "parse_failed", "base_id": base_id,
                "detail": "Docling is not installed: pip install iopic-bond[parse]"}
    except Exception as exc:  # Docling failures are varied; record and report, never crash the server
        store.record_failure(base_id, "parse_failed", meta)
        return {"status": "parse_failed", "base_id": base_id, "detail": f"{type(exc).__name__}: {exc}"}

    tree = store.parsed_dir(base_id) / root.id / "tree.json"
    row = store.record_parse(base_id, meta, root.id, _parser_version(), figure_dicts(tree))
    return {"status": "ok", "paper": row, "tree_path": str(tree)}


def outline(tree_path: Path, max_sections: int = 40) -> list[str]:
    """Section headings of a parsed paper, in reading order."""
    root = from_json(Path(tree_path).read_text(encoding="utf-8"))
    heads = []
    for n in root.walk():
        if n.type in ("section", "subsection", "chapter") and n.text:
            heads.append(n.text.strip()[:120])
    return heads[:max_sections]
