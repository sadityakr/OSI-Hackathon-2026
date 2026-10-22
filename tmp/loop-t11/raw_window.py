"""Print raw spectrum points in a shift window, with the robust noise level (throwaway T11 diagnostic).

Input: case path relative to data/test_set, window centre and half width in cm-1.
Process: reads the spectrum, removes spikes, estimates sigma from first differences.
Output: x, y, y_clean rows inside the window and sigma.
"""
import sys
from pathlib import Path

import numpy as np

from ramanlens.perception.io import read_spectrum
from ramanlens.perception.preprocess import remove_spikes
from ramanlens.perception.fit import noise_sigma

ROOT = Path(__file__).resolve().parents[2] / "data/test_set"
s = read_spectrum(ROOT / sys.argv[1] / "spectrum.csv")
c, hw = float(sys.argv[2]), float(sys.argv[3])
yc, spikes = remove_spikes(s.x, s.y)
print("spikes", spikes, "sigma(raw diff)", round(noise_sigma(s.y), 1), "dx", np.median(np.diff(s.x)))
m = (s.x > c - hw) & (s.x < c + hw)
for xi, yi, ci in zip(s.x[m], s.y[m], yc[m]):
    print(f"{xi:8.2f} {yi:10.1f} {ci:10.1f}")
