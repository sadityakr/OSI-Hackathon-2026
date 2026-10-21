"""Unit tests for ramanlens.perception.preprocess (spike removal and ALS baseline)."""

import numpy as np

from ramanlens.perception.preprocess import baseline_als, remove_spikes


def lorentz(x, x0, w, a):
    g = w / 2
    return a * g * g / ((x - x0) ** 2 + g * g)


def _spectrum(seed=0):
    rng = np.random.default_rng(seed)
    x = np.arange(100, 800, 1.0)
    y = lorentz(x, 400, 6, 1000) + lorentz(x, 600, 4, 500) + 100 + rng.normal(0, 10, x.size)
    return x, y


def test_spike_off_peak_is_removed_and_peaks_kept():
    x, y = _spectrum()
    y_spiky = y.copy()
    y_spiky[150] += 3000  # x = 250, flat region
    y_clean, spikes = remove_spikes(x, y_spiky)
    assert spikes == [250.0]
    assert abs(y_clean[150] - y[150]) < 50
    for x0 in (400, 600):
        i = int(np.where(x == x0)[0][0])
        assert y_clean[i] == y[i], "a real peak must be untouched"
    assert y_spiky[150] > 3000, "input array must not be modified"


def test_spike_on_top_of_a_peak_restores_the_peak():
    x, y = _spectrum()
    y_spiky = y.copy()
    y_spiky[300] += 3000  # x = 400, top of the 1000-count band
    y_clean, spikes = remove_spikes(x, y_spiky)
    assert any(abs(s - 400) < 2 for s in spikes)
    assert abs(y_clean[300] - y[300]) < 150, "the band under the spike is interpolated back"


def test_two_pixel_spike_is_removed():
    x, y = _spectrum(1)
    y_spiky = y.copy()
    y_spiky[550:552] += [2500, 1800]  # x = 650, 651, flat region
    y_clean, spikes = remove_spikes(x, y_spiky)
    assert any(abs(s - x[550]) < 2 for s in spikes)
    assert np.all(np.abs(y_clean[550:552] - y[550:552]) < 60)


def test_no_spikes_in_clean_noisy_spectrum():
    for seed in range(5):
        x, y = _spectrum(seed)
        _, spikes = remove_spikes(x, y)
        assert spikes == []


def test_narrow_but_resolved_band_is_not_a_spike():
    x = np.arange(400, 650, 1.0)
    y = lorentz(x, 520.7, 3.0, 2000) + 50 + np.random.default_rng(3).normal(0, 5, x.size)
    _, spikes = remove_spikes(x, y)
    assert spikes == []


def test_baseline_als_on_flat_and_curved_background():
    x = np.arange(0, 1000, 1.0)
    background = 300 + 200 * np.exp(-((x - 300) / 250) ** 2)
    y = background + lorentz(x, 600, 8, 800)
    b = baseline_als(y)
    assert np.median(np.abs((y - b)[np.abs(x - 600) > 60])) < 10
    assert (y - b)[600] > 700
