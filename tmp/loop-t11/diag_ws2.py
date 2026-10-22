"""Step through detection and group fits of fit.py on one dev case (T11 diagnostics, throwaway).

Input: case folder name (dev or dev_hard).
Process: the pipeline's preprocessing, then fit._detect, fit._groups and fit._fit_group with band_snr per peak.
Output: text on stdout.
"""
import sys
from pathlib import Path

import numpy as np

from ramanlens.perception import fit
from ramanlens.perception.io import read_spectrum
from ramanlens.perception.preprocess import baseline_als, remove_spikes

ROOT = Path(__file__).resolve().parents[2]
case = next(p for s in ("dev", "dev_hard") if (p := ROOT / "data/test_set" / s / sys.argv[1]).exists())
sp = read_spectrum(case / "spectrum.csv")
yc, _ = remove_spikes(sp.x, sp.y)
x = sp.x
sig = yc - baseline_als(yc)
dx = float(np.median(np.diff(x)))
s0 = fit.noise_sigma(sig)
cands = fit._detect(x, sig, 5.0, s0, dx)
print("candidates", [(round(c[0], 1), round(c[1], 2), round(c[2] / s0, 1)) for c in cands])
for g in fit._groups(cands):
    peaks, rss, n, win = fit._fit_group(x, sig, g, dx)
    print("group", [round(c[0], 1) for c in g], "window", np.round(win, 1))
    for p in peaks:
        print(f"    {p.position:8.2f} w {p.fwhm:6.2f} h/s0 {p.height / s0:6.1f} snr {fit.band_snr(p, s0, dx):6.1f}")
