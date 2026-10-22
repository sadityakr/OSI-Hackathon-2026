"""Probe: pipeline on a noise-free single Lorentzian (throwaway). Prints the fitted peaks and baseline stats."""

import numpy as np

from ramanlens.perception.fit import fit_peaks
from ramanlens.perception.io import Spectrum
from ramanlens.perception.pipeline import analyze_spectrum
from ramanlens.perception.preprocess import baseline_als

x = np.arange(100, 800, 1.0)
y = 100 + 1000 * 4 / ((x - 520.7) ** 2 + 4)
res = analyze_spectrum(Spectrum(x=x, y=y, meta={"substrate": "Au"}))
print("pipeline:", [(round(p.position, 1), round(p.fwhm, 2), round(p.height, 2)) for p in res.peaks])
print("baseline min/max:", np.nanmin(res.baseline), np.nanmax(res.baseline))
b = baseline_als(y)
print("raw ALS min/max:", b.min(), b.max())
print("fit_peaks own baseline:", [(round(p.position, 1), round(p.fwhm, 2), round(p.height, 2)) for p in fit_peaks(x, y)])
