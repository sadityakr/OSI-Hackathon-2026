"""Load a paper corpus from a directory of Markdown documents.

A document's id is its filename stem (e.g. `crsbr-bandgap.md` -> `crsbr-bandgap`). This is a
stand-in for the real ingestion pipeline (PDF -> typed block tree with provenance handles), kept
deliberately trivial so the evaluation harness has something to retrieve over from day one.
"""

from __future__ import annotations

from pathlib import Path


def load_corpus(directory: str | Path) -> dict[str, str]:
    """Return {doc_id: text} for every `*.md` file in `directory`."""
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"corpus directory not found: {root}")
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.md"))}
