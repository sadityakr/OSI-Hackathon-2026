"""Unit tests for ramanlens.perception.pipeline and the fitter changes made with it (width floor, merge step).

Synthetic Lorentzians generated here, so every expected value is exact.
"""

import json

import numpy as np
import pytest

from ramanlens.perception.fit import fit_peaks
from ramanlens.perception.io import Spectrum
from ramanlens.perception.pipeline import analyze_spectrum, substrate_may_be_silicon


def lorentz(x, x0, w, a):
    g = w / 2
    return a * g * g / ((x - x0) ** 2 + g * g)


def test_laser_line_region_is_excluded():
    x = np.arange(-100, 1000, 2.0)
    y = 50 + lorentz(x, 0, 8, 5000) + lorentz(x, 30, 60, 800) + lorentz(x, 400, 6, 600)
    res = analyze_spectrum(Spectrum(x=x, y=y))
    assert res.min_shift_cm1 == 50
    assert all(p.position >= 50 for p in res.peaks)
    assert any(abs(p.position - 400) < 1 for p in res.peaks)
    assert res.baseline.shape == x.shape and np.isnan(res.baseline[x < 50]).all()


def test_no_cut_when_axis_starts_above_laser_line():
    x = np.arange(60, 600, 1.0)
    y = 20 + lorentz(x, 72, 4, 900) + lorentz(x, 300, 5, 500)
    res = analyze_spectrum(Spectrum(x=x, y=y))
    assert res.min_shift_cm1 is None
    assert any(abs(p.position - 72) < 1 for p in res.peaks)


def test_si_not_flagged_on_named_non_silicon_substrate():
    x = np.arange(100, 800, 1.0)
    y = 100 + lorentz(x, 520.7, 4, 1000)
    res = analyze_spectrum(Spectrum(x=x, y=y, meta={"substrate": "Au"}))
    assert len(res.peaks) == 1 and not res.peaks[0].is_substrate


def test_broad_band_at_520_is_not_the_substrate():
    x = np.arange(100, 800, 1.0)
    y = 100 + lorentz(x, 520.0, 20, 1000)
    res = analyze_spectrum(Spectrum(x=x, y=y))
    assert res.peaks and not any(p.is_substrate for p in res.peaks)


def test_substrate_text_parsing():
    assert substrate_may_be_silicon(None)
    assert substrate_may_be_silicon("SiO2/Si")
    assert substrate_may_be_silicon("black silicon (Si nanowires)")
    assert not substrate_may_be_silicon("Au")
    assert not substrate_may_be_silicon("SiO2")
    assert not substrate_may_be_silicon("sapphire")


def test_spike_is_reported_not_fitted():
    rng = np.random.default_rng(3)
    x = np.arange(100, 800, 1.0)
    y = 100 + lorentz(x, 400, 6, 1000) + rng.normal(0, 5, x.size)
    y[250] += 4000  # x = 350
    res = analyze_spectrum(Spectrum(x=x, y=y))
    assert any(abs(s - 350) < 1 for s in res.spikes)
    assert not any(abs(p.position - 350) < 3 for p in res.peaks)


def test_noisy_single_band_is_not_split():
    """One noisy band must come out as one peak (the merge step removes unresolved pairs)."""
    hits = 0
    for seed in range(5):
        rng = np.random.default_rng(seed)
        x = np.arange(300, 500, 1.0)
        y = 200 + lorentz(x, 413.6, 6, 3000) + rng.normal(0, 120, x.size)
        peaks = [p for p in fit_peaks(x, y) if abs(p.position - 413.6) < 8]
        hits += len(peaks) == 1
    assert hits == 5


@pytest.mark.slow
def test_dev_cosmic_rays_found_and_not_fitted():
    """Same check as the contract test of that name, but skipping cases whose truth notes are free text, not JSON."""
    from cases import dev_cases
    from ramanlens.perception.io import read_spectrum
    checked = 0
    for c in dev_cases(kind="single"):
        try:
            notes = json.loads(c["truth"]["notes"] or "{}")
        except json.JSONDecodeError:
            continue
        spikes = [a["position_cm1"] for a in notes.get("artifacts", []) if a.get("type") == "cosmic_ray"]
        if not spikes:
            continue
        res = analyze_spectrum(read_spectrum(c["dir"] / "spectrum.csv"))
        for s in spikes:
            checked += 1
            assert not any(abs(p.position - s) < 3 for p in res.peaks), (c["id"], s)
            assert any(abs(q - s) < 3 for q in res.spikes), (c["id"], s)
    assert checked > 0


def test_fitted_width_never_below_detector_resolution():
    rng = np.random.default_rng(4)
    x = np.arange(300, 500, 1.0)
    y = 200 + lorentz(x, 414.8, 7, 600) + rng.normal(0, 150, x.size)
    assert all(p.fwhm >= 1.5 - 1e-9 for p in fit_peaks(x, y))
