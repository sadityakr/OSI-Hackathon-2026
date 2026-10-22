"""Time analyze_spectrum per dev case and count detector candidates (T11 diagnostics, throwaway).

Input: none (all single-spectrum dev and dev_hard cases).
Process: analyze_spectrum with a wall clock; fit._detect candidate count on the same preprocessing.
Output: text on stdout.
"""
import json
import time
from pathlib import Path

import numpy as np

from ramanlens.perception import fit
from ramanlens.perception.io import read_spectrum
from ramanlens.perception.pipeline import analyze_spectrum
from ramanlens.perception.preprocess import baseline_als, remove_spikes

ROOT = Path(__file__).resolve().parents[2]
for split in ("dev", "dev_hard"):
    for case in sorted((ROOT / "data/test_set" / split).iterdir()):
        if json.loads((case / "input.json").read_text())["kind"] != "single":
            continue
        sp = read_spectrum(case / "spectrum.csv")
        yc, _ = remove_spikes(sp.x, sp.y)
        sig = yc - baseline_als(yc)
        dx = float(np.median(np.diff(sp.x)))
        n = len(fit._detect(sp.x, sig, 5.0, fit.noise_sigma(sig), dx))
        t = time.perf_counter()
        res = analyze_spectrum(sp)
        print(f"{case.name:20s} n={sp.x.size:5d} cands={n:3d} peaks={len(res.peaks):3d} t={time.perf_counter() - t:6.1f}s",
              flush=True)
