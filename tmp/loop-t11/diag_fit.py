"""Fitted peaks of named dev cases with heights in raw-noise units and fit significance (T11 diagnostics, throwaway).

Input: case folder names (dev or dev_hard).
Process: analyze_spectrum; noise from the same preprocessing; truth positions for marking.
Output: text on stdout.
"""
import json
import sys
from pathlib import Path

import numpy as np

from ramanlens.perception.fit import noise_sigma
from ramanlens.perception.io import read_spectrum
from ramanlens.perception.pipeline import analyze_spectrum
from ramanlens.perception.preprocess import baseline_als, remove_spikes

ROOT = Path(__file__).resolve().parents[2]
for name in sys.argv[1:]:
    case = next(p for s in ("dev", "dev_hard") if (p := ROOT / "data/test_set" / s / name).exists())
    truth = json.loads((case / "truth.json").read_text())
    sp = read_spectrum(case / "spectrum.csv")
    yc, _ = remove_spikes(sp.x, sp.y)
    s0 = noise_sigma(yc - baseline_als(yc))
    res = analyze_spectrum(sp)
    tp = [t["position_cm1"] for t in truth["peaks"]]
    print(f"== {name} s0={s0:.4g}")
    for p in res.peaks:
        mark = "T" if any(abs(p.position - t) < 5 for t in tp) else "-"
        sig = p.height / p.height_err if p.height_err else float("nan")
        print(f"  {mark} {p.position:8.2f} fwhm {p.fwhm:6.2f} h/s0 {p.height / s0:6.1f} h/err {sig:6.1f} "
              f"area/err-ish {p.area / s0 / np.sqrt(max(p.fwhm, 1)):6.1f}")
    print("  truth", tp)
