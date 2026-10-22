"""Probe: print raw data and truth notes around a shift window for one dev case (throwaway, not shipped).

Input: case id, lo, hi on the command line. Process: reads the dev spectrum. Output: printed x, y rows and notes.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
from ramanlens.perception.io import read_spectrum  # noqa: E402

case, lo, hi = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
d = ROOT / "data" / "test_set" / "dev" / case
s = read_spectrum(d / "spectrum.csv")
t = json.loads((d / "truth.json").read_text())
print("peaks:", t["peaks"])
print("notes:", t["notes"])
m = (s.x >= lo) & (s.x <= hi)
for xi, yi in zip(s.x[m], s.y[m]):
    print(f"{xi:8.2f} {yi:10.1f}")
