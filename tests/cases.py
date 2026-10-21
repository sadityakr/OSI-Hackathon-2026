"""Helpers that load test-set cases for the test suite.

Only the dev split is loaded here. Held-out truth is for the final comparison and must never be read by tests or
tools; see data/test_set/README.md.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "data" / "test_set" / "dev"


def dev_cases(kind=None, tier=None, task=None):
    """List of dicts with keys id, dir, input, truth for dev cases, optionally filtered."""
    out = []
    for d in sorted(DEV.iterdir()) if DEV.exists() else []:
        if not (d / "truth.json").exists():
            continue
        inp = json.loads((d / "input.json").read_text())
        if kind and inp["kind"] != kind:
            continue
        if task and inp["task"] != task:
            continue
        if tier and not d.name.startswith(tier + "-"):
            continue
        out.append({"id": d.name, "dir": d, "input": inp, "truth": json.loads((d / "truth.json").read_text())})
    return out


def load_csv(case):
    return pd.read_csv(case["dir"] / "spectrum.csv")
