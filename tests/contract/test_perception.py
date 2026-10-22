"""Contract for the perception layer: reading, spike removal, baseline, peak fitting.

Exact-truth tests use Lorentzians generated here; dataset tests use the dev split. Imports sit inside each test so
every unmet requirement fails on its own line instead of aborting collection.
"""

import numpy as np
import pytest

from cases import dev_cases


def lorentz(x, x0, w, a):
    g = w / 2
    return a * g * g / ((x - x0) ** 2 + g * g)


def test_read_single_spectrum():
    from ramanlens.perception.io import read_spectrum
    case = next(c for c in dev_cases(kind="single"))
    s = read_spectrum(case["dir"] / "spectrum.csv")
    assert s.x.ndim == 1 and s.x.shape == s.y.shape and len(s.x) > 100
    assert np.all(np.diff(s.x) > 0), "shift axis must be returned ascending"


def test_read_angle_series():
    from ramanlens.perception.io import read_series
    case = next(c for c in dev_cases(kind="angle_series"))
    ser = read_series(case["dir"] / "spectrum.csv")
    # ser.spectra maps (config, angle_deg) -> 1D intensity array on the common axis ser.x
    assert set(c for c, _ in ser.spectra) == {"parallel", "crossed"}
    assert len({a for _, a in ser.spectra}) >= 8
    assert all(v.shape == ser.x.shape for v in ser.spectra.values())


def test_spike_removal_finds_injected_spike():
    from ramanlens.perception.preprocess import remove_spikes
    rng = np.random.default_rng(0)
    x = np.arange(100, 800, 1.0)
    y = lorentz(x, 400, 6, 1000) + 100 + rng.normal(0, 10, x.size)
    y[150] += 3000  # x = 250 cm-1, on the flat background (index 300 would be the top of the real band)
    y_clean, spikes = remove_spikes(x, y)
    assert any(abs(s - x[150]) < 2 for s in spikes)
    assert y_clean[150] < 300
    assert abs(y_clean[x == 400][0] - y[x == 400][0]) < 50, "a real peak must not be removed"


def test_baseline_als_removes_slope_keeps_peak():
    from ramanlens.perception.preprocess import baseline_als
    x = np.arange(100, 1100, 1.0)
    base = 200 + 0.3 * (x - 100) + 150 * np.exp(-((x - 700) / 300) ** 2)
    y = base + lorentz(x, 520, 4, 1000)
    b = baseline_als(y)
    assert np.median(np.abs((y - b)[(x < 450) | (x > 600)])) < 15
    assert (y - b)[x == 520][0] > 900


def test_fit_recovers_exact_lorentzians():
    from ramanlens.perception.fit import fit_peaks
    rng = np.random.default_rng(1)
    x = np.arange(100, 600, 0.8)
    true = [(250.0, 5.0, 800), (356.3, 4.0, 3000), (418.2, 6.0, 1500)]
    y = sum(lorentz(x, *p) for p in true) + 50 + rng.normal(0, 15, x.size)
    peaks = fit_peaks(x, y)
    # each peak object has .position, .fwhm, .height, .area, .position_err
    for x0, w, _ in true:
        p = min(peaks, key=lambda p: abs(p.position - x0))
        assert abs(p.position - x0) < 0.5
        assert abs(p.fwhm - w) / w < 0.15
        assert p.position_err is not None and p.position_err < 1.0
    assert len([p for p in peaks if p.height > 200]) == 3


def test_fit_resolves_close_doublet():
    from ramanlens.perception.fit import fit_peaks
    x = np.arange(200, 300, 0.5)
    y = lorentz(x, 248.0, 4.0, 1000) + lorentz(x, 253.0, 4.0, 700) + 20
    peaks = [p for p in fit_peaks(x, y) if p.height > 100]
    assert len(peaks) == 2
    assert sorted(round(p.position) for p in peaks) == [248, 253]


@pytest.mark.slow
def test_fit_recall_on_dev_single_cases():
    """Every truth peak of every dev single spectrum is found within its tolerance (>= 90 % overall)."""
    from ramanlens.perception.io import read_spectrum
    from ramanlens.perception.pipeline import analyze_spectrum
    found = total = 0
    for c in dev_cases(kind="single"):
        s = read_spectrum(c["dir"] / "spectrum.csv")
        res = analyze_spectrum(s)  # .peaks (fitted, spikes removed), .spikes (positions), .baseline
        for t in c["truth"]["peaks"]:
            total += 1
            found += any(abs(p.position - t["position_cm1"]) <= t["tolerance_cm1"] for p in res.peaks)
    assert total and found / total >= 0.9, f"recall {found}/{total}"


@pytest.mark.slow
def test_cosmic_rays_not_reported_as_peaks_on_dev():
    import json
    from ramanlens.perception.io import read_spectrum
    from ramanlens.perception.pipeline import analyze_spectrum
    checked = 0
    for c in dev_cases(kind="single"):
        spikes = [a["position_cm1"] for a in json.loads(c["truth"]["notes"] or "{}").get("artifacts", [])
                  if a.get("type") == "cosmic_ray"]
        if not spikes:
            continue
        res = analyze_spectrum(read_spectrum(c["dir"] / "spectrum.csv"))
        for s in spikes:
            checked += 1
            assert not any(abs(p.position - s) < 3 for p in res.peaks), (c["id"], s)
            assert any(abs(q - s) < 3 for q in res.spikes), (c["id"], s)
    assert checked > 0
