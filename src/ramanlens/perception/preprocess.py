"""Preprocessing of a single Raman spectrum: cosmic-ray spike removal and baseline estimation.

Peak fitting and library matching assume a spectrum without detector spikes and without the broad fluorescence
background. This module removes both before any peak is fitted, and is used by the perception pipeline and by the
polarization analysis.

Input: the Raman-shift axis x (cm-1, ascending) and the intensity y as 1D arrays of equal length.
Process: spikes are points that stand out from their immediate neighbours by far more than any real band can,
because a real band is sampled by several detector pixels while a cosmic ray hits one or two; they are replaced by
linear interpolation between the neighbours. The baseline is an asymmetric least squares smoother (Eilers and
Boelens 2005) that follows the background and ignores points that lie above it.
Output: remove_spikes returns the cleaned intensity and the spike positions in cm-1; baseline_als returns the
baseline as an array on the same axis.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.ndimage import median_filter
from scipy.sparse.linalg import spsolve


def _robust_std(v: np.ndarray) -> float:
    """Standard deviation estimated from the median absolute deviation, insensitive to spikes and peaks."""
    mad = np.median(np.abs(v - np.median(v)))
    return 1.4826 * mad if mad > 0 else float(np.std(v)) or 1e-12


def remove_spikes(x, y, threshold: float = 8.0, max_width: int = 2, sharpness: float = 2.0,
                  background_window: int = 31):
    """Find and remove cosmic-ray spikes; return (y_clean, spike_positions_cm1).

    For every run of w = 1..max_width adjacent pixels, the excess e is how far the run's lowest point lies above
    the straight line joining the pixels just outside it. A run is a spike when
      1. e > threshold * sigma, with sigma the robust noise of the same excess measured over the whole spectrum, and
      2. e > sharpness * (height of the outer neighbours above the local background).
    Condition 2 is what keeps real bands: for a Lorentzian of FWHM G pixels the excess of its top pixel over its
    neighbours divided by the neighbours' height is 4 / G**2, so with sharpness = 2 only features narrower than
    about 1.4 pixels FWHM count as spikes. A spike sitting on top of a real band is still found, and its pixels
    are replaced by the interpolation between the outer neighbours, which restores the band underneath.
    The input array is not modified.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    y_clean = y.copy()
    n = y.size
    if n < 2 * max_width + 3:
        return y_clean, []

    # Noise scale of the single-pixel excess y[i] - (y[i-1] + y[i+1]) / 2, from the whole spectrum.
    sigma = _robust_std(y[1:-1] - 0.5 * (y[:-2] + y[2:]))
    # Local background: a wide running median sits under bands and ignores spikes.
    background = median_filter(y, size=min(background_window, n | 1), mode="nearest")

    spikes = []
    for _ in range(3):  # repeat: a removed spike can uncover a neighbouring one
        found = False
        for w in range(1, max_width + 1):
            for i in range(1, n - w):
                left, right = i - 1, i + w
                run = y_clean[i:i + w]
                line = y_clean[left] + (y_clean[right] - y_clean[left]) * (np.arange(1, w + 1) / (w + 1))
                excess = float(np.min(run - line))
                if excess <= threshold * sigma:
                    continue
                neighbour_height = max(y_clean[left] - background[left], y_clean[right] - background[right], 0.0)
                if excess <= sharpness * neighbour_height:
                    continue
                spikes.append(float(x[i + int(np.argmax(run))]))
                y_clean[i:i + w] = line
                found = True
        if not found:
            break
    return y_clean, sorted(set(spikes))


def baseline_als(y, lam: float = 1e5, p: float = 0.01, n_iter: int = 10) -> np.ndarray:
    """Asymmetric least squares baseline (Eilers and Boelens 2005, Leiden University Medical Centre report).

    Minimizes sum_i w_i (y_i - z_i)^2 + lam * sum_i (z_{i+1} - 2 z_i + z_{i-1})^2 over the baseline z. The
    second-difference penalty (weight lam) makes z smooth but leaves straight slopes unpenalized; the weights are
    w_i = p where y_i > z_i (points on a band) and 1 - p elsewhere, so with small p the baseline hugs the
    background from below. Larger lam gives a stiffer baseline; p between 0.001 and 0.05 is typical.
    """
    y = np.asarray(y, dtype=float)
    n = y.size
    if n < 3:
        return y.copy()
    d = sparse.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n))
    penalty = lam * (d.T @ d)
    w = np.ones(n)
    z = y
    for _ in range(n_iter):
        W = sparse.diags(w)
        z = spsolve((W + penalty).tocsc(), w * y)
        w_new = np.where(y > z, p, 1.0 - p)
        if np.array_equal(w_new, w):
            break
        w = w_new
    return np.asarray(z)
