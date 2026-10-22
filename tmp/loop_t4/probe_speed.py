"""Probe: profile the pipeline on a noise-free two-band spectrum (throwaway)."""

import cProfile
import pstats

import numpy as np

from ramanlens.perception.io import Spectrum
from ramanlens.perception.pipeline import analyze_spectrum


def lorentz(x, x0, w, a):
    g = w / 2
    return a * g * g / ((x - x0) ** 2 + g * g)


x = np.arange(60, 600, 1.0)
y = 20 + lorentz(x, 72, 4, 900) + lorentz(x, 300, 5, 500)
pr = cProfile.Profile()
pr.enable()
res = analyze_spectrum(Spectrum(x=x, y=y))
pr.disable()
print([(round(p.position, 1), round(p.fwhm, 1), round(p.height, 1)) for p in res.peaks], res.notes)
pstats.Stats(pr).sort_stats("cumulative").print_stats(14)
