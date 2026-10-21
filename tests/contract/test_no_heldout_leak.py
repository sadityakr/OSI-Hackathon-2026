"""Guard: tool code must not contain held-out or dev case answers.

The builder agent may read dev truth to debug, but the package must solve cases from the spectrum, not from a
lookup of case ids. Held-out truth must never be referenced at all.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source_text():
    files = [p for p in (ROOT / "src" / "ramanlens").rglob("*") if p.suffix in {".py", ".json", ".yaml", ".csv"}]
    return {p: p.read_text(encoding="utf-8", errors="replace") for p in files}


def test_no_case_ids_or_truth_paths_in_package():
    ids = [d.name for split in ("dev", "heldout") for d in (ROOT / "data" / "test_set" / split).glob("*")]
    pattern = re.compile("|".join([r"truth\.json", r"test_set[/\\\\]heldout"] + [re.escape(i) for i in ids]))
    hits = [(str(p.relative_to(ROOT)), m.group(0)) for p, t in _source_text().items() for m in [pattern.search(t)]
            if m]
    assert hits == []
