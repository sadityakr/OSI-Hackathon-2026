"""Unit tests for ramanlens.perception.fit (peak detection and Lorentzian fitting)."""

import numpy as np

from ramanlens.perception.fit import Peak, fit_peaks, lorentzian


def _three_peaks(seed, noise=15.0):
    rng = np.random.default_rng(seed)
    x = np.arange(100, 600, 0.8)
    true = [(250.0, 5.0, 800), (356.3, 4.0, 3000), (418.2, 6.0, 1500)]
    y = sum(lorentzian(x, *p) for p in true) + 50 + rng.normal(0, noise, x.size)
    return x, y, true


def test_recovery_is_stable_across_noise_seeds():
    for seed in range(10):
        x, y, true = _three_peaks(seed)
        peaks = fit_peaks(x, y)
        assert len(peaks) == 3, (seed, [round(p.position, 1) for p in peaks])
        for (x0, w, h), p in zip(true, peaks):
            assert abs(p.position - x0) < 0.5
            assert abs(p.fwhm - w) / w < 0.15
            assert abs(p.height - h) / h < 0.1


def test_pure_noise_gives_no_peaks():
    rng = np.random.default_rng(7)
    x = np.arange(100, 600, 1.0)
    for _ in range(5):
        assert fit_peaks(x, 100 + rng.normal(0, 10, x.size)) == []


def test_position_error_grows_with_noise():
    x, y_lo, _ = _three_peaks(3, noise=5.0)
    _, y_hi, _ = _three_peaks(3, noise=40.0)
    e_lo = fit_peaks(x, y_lo)[1].position_err
    e_hi = fit_peaks(x, y_hi)[1].position_err
    assert 0 < e_lo < e_hi < 1.0


def test_residual_pass_finds_unresolved_shoulder():
    # 30 % shoulder 4 cm-1 from a 6 cm-1 wide band: no separate maximum, so only the residual pass can find it.
    x = np.arange(300, 500, 0.5)
    y = lorentzian(x, 400, 6, 1000) + lorentzian(x, 404, 6, 300) + 10
    y = y + np.random.default_rng(0).normal(0, 3, x.size)
    peaks = [p for p in fit_peaks(x, y) if p.height > 100]
    assert len(peaks) == 2
    assert abs(peaks[0].position - 400) < 1.0 and abs(peaks[1].position - 404) < 1.0


def test_unsorted_input_and_area():
    x, y, _ = _three_peaks(0)
    rev = fit_peaks(x[::-1], y[::-1])
    fwd = fit_peaks(x, y)
    assert [round(p.position, 6) for p in rev] == [round(p.position, 6) for p in fwd]
    p = fwd[1]
    assert np.isclose(p.area, np.pi / 2 * p.height * p.fwhm)
    assert isinstance(p, Peak) and p.shape == "lorentzian" and p.is_substrate is False
    assert set(p.to_dict()) >= {"position", "fwhm", "height", "area", "position_err"}
