"""Print truth peaks, truth notes and fitted peaks for named dev cases (throwaway T11 diagnostic).

Input: case paths relative to data/test_set (dev or dev_hard only).
Process: reads truth.json and runs the fit_peaks tool on spectrum.csv.
Output: truth positions with relative intensities, the start of the notes, fitted (position, fwhm, height).
"""
import json
import sys
from pathlib import Path

from ramanlens.agent import toolset as T

ROOT = Path(__file__).resolve().parents[2] / "data/test_set"
for c in sys.argv[1:]:
    d = ROOT / c
    t = json.loads((d / "truth.json").read_text())
    print("==", c)
    print("truth", [(p["position_cm1"], p.get("relative_intensity")) for p in t["peaks"]])
    print("notes", str(t.get("notes"))[:700])
    f = json.loads(T.call("fit_peaks", {"path": "spectrum.csv"}, str(d)))
    print("fit", [(p["position_cm1"], p["fwhm_cm1"], p["height"]) for p in f["peaks"]], f["notes"])
