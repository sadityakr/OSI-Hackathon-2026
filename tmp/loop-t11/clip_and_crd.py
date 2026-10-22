"""Count clipped points per dev case and list CRD-visible GaSe modes (throwaway T11 diagnostic).

Input: dev and dev_hard spectra; the CRD layered subset through ramanlens.perception.library.
Process: fraction of points equal to the spectrum minimum; GaSe matcher candidate details.
Output: per-case clipped fraction and noise estimates; matched and missing GaSe modes.
"""
from pathlib import Path

import numpy as np

from ramanlens.perception.io import read_spectrum, read_series
from ramanlens.perception.fit import noise_sigma
from ramanlens.perception.library import match

ROOT = Path(__file__).resolve().parents[2] / "data/test_set"
for split in ("dev", "dev_hard"):
    for case in sorted((ROOT / split).iterdir()):
        p = case / "spectrum.csv"
        try:
            s = read_spectrum(p)
            y = s.y
        except Exception:
            y = np.concatenate(list(read_series(p).spectra.values()))
        frac = float(np.mean(y <= y.min()))
        keep = y > y.min()
        d = np.diff(y)
        both = keep[1:] & keep[:-1]
        print(f"{split}/{case.name:18s} clipped {frac:5.3f} sigma_all {noise_sigma(y):8.1f}"
              f" sigma_unclipped {np.median(np.abs(d[both] - np.median(d[both]))) * 1.4826 / np.sqrt(2):8.1f}")

for c in match([127.85, 204.65, 305.92], [9344, 281, 4614], top_k=3):
    print(c.material, c.score, c.matched, c.unmatched, c.missing)
