"""Peak detection and Lorentzian fitting of a single Raman spectrum.

Every downstream step (library matching, relations such as the MoS2 E2g-A1g separation, polarization analysis)
works from a peak table, not from the raw curve. This module turns a spike-free spectrum into that table, with a
fit uncertainty on every position so a relation can tell a real shift from noise.

Input: the Raman-shift axis x (cm-1) and the intensity y as 1D arrays (spikes already removed, see
preprocess.remove_spikes); optionally a baseline on the same axis, otherwise an ALS baseline is computed.
Process: candidate peaks are local maxima of the baseline-corrected, lightly smoothed signal whose prominence
exceeds a multiple of the noise. Candidates closer than a few linewidths are grouped and each group is fitted
with a sum of Lorentzians plus a linear background (scipy.optimize.curve_fit), so overlapping bands share their
tails correctly. One residual pass adds peaks the detector missed (shoulders) and refits.
Output: a list of Peak records sorted by position, each with position, FWHM, height, area and their 1-sigma
uncertainties from the fit covariance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, peak_widths, savgol_filter

from ramanlens.perception.preprocess import _robust_std, baseline_als


# @dataclass generates __init__, __repr__ and __eq__ from the field list, so a Peak is a plain typed record.
@dataclass
class Peak:
    """One fitted Raman band. Positions and widths in cm-1, height and area in the input intensity units."""

    position: float
    fwhm: float
    height: float
    area: float
    position_err: float | None = None
    fwhm_err: float | None = None
    height_err: float | None = None
    shape: str = "lorentzian"
    is_substrate: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def lorentzian(x, position, fwhm, height):
    """Lorentzian with peak value `height` at `position` and full width at half maximum `fwhm`."""
    g = fwhm / 2.0
    return height * g * g / ((x - position) ** 2 + g * g)


def _group_model(x, *params):
    """Sum of Lorentzians plus a linear background; params = (c0, c1, x_ref, p1, w1, h1, p2, w2, h2, ...)."""
    c0, c1, x_ref = params[0], params[1], params[2]
    y = c0 + c1 * (x - x_ref)
    for k in range(3, len(params), 3):
        y = y + lorentzian(x, params[k], params[k + 1], params[k + 2])
    return y


def noise_sigma(signal) -> float:
    """Robust noise level: MAD of the first differences divided by sqrt(2) (differences double the variance)."""
    return _robust_std(np.diff(np.asarray(signal, dtype=float))) / np.sqrt(2.0)


def _detect(x, signal, min_prominence: float, dx: float):
    """Candidate peaks as (position, fwhm_estimate, height_estimate) from local maxima of the smoothed signal."""
    n = signal.size
    smooth = savgol_filter(signal, 5, 2) if n >= 7 else signal
    idx, _ = find_peaks(smooth, prominence=min_prominence)
    if idx.size == 0:
        return []
    widths_px = peak_widths(smooth, idx, rel_height=0.5)[0]
    span = x[-1] - x[0]
    return [(float(x[i]), float(np.clip(wp * dx, 2 * dx, span / 3)), float(smooth[i]))
            for i, wp in zip(idx, widths_px)]


def _groups(candidates, merge_factor: float = 3.0):
    """Split position-sorted candidates into groups whose members lie within merge_factor linewidths of a neighbour."""
    groups = []
    for c in sorted(candidates):
        if groups and c[0] - groups[-1][-1][0] < merge_factor * max(c[1], groups[-1][-1][1]):
            groups[-1].append(c)
        else:
            groups.append([c])
    return groups


def _fit_group(x, signal, group, dx: float, window_factor: float = 6.0):
    """Fit one group of candidates; returns a list of Peak (initial estimates without errors if the fit fails)."""
    lo = min(p - window_factor * w for p, w, _ in group)
    hi = max(p + window_factor * w for p, w, _ in group)
    m = (x >= lo) & (x <= hi)
    xs, ys = x[m], signal[m]
    x_ref = 0.5 * (lo + hi)
    p0 = [float(np.min(ys)) if ys.size else 0.0, 0.0, x_ref]
    lower = [-np.inf, -np.inf, x_ref - 1e-9]
    upper = [np.inf, np.inf, x_ref + 1e-9]
    for p, w, h in group:
        shift = max(w, 3 * dx)
        p0 += [p, w, max(h, 1e-12)]
        lower += [p - shift, 0.5 * dx, 0.0]
        upper += [p + shift, 10 * w, np.inf]

    n_free = len(p0) - 1  # x_ref is pinned
    if xs.size <= n_free:
        return [Peak(p, w, h, np.pi / 2 * h * w) for p, w, h in group]
    try:
        popt, pcov = curve_fit(_group_model, xs, ys, p0=p0, bounds=(lower, upper), maxfev=20000)
        perr = np.sqrt(np.clip(np.diag(pcov), 0, None))
    except (RuntimeError, ValueError):
        return [Peak(p, w, h, np.pi / 2 * h * w) for p, w, h in group]

    peaks = []
    for k in range(3, len(popt), 3):
        pos, w, h = (float(v) for v in popt[k:k + 3])
        ep, ew, eh = (float(v) if np.isfinite(v) else None for v in perr[k:k + 3])
        peaks.append(Peak(position=pos, fwhm=w, height=h, area=np.pi / 2 * h * w,
                          position_err=ep, fwhm_err=ew, height_err=eh))
    return peaks


def _fit_all(x, signal, candidates, dx):
    peaks = []
    for g in _groups(candidates):
        peaks.extend(_fit_group(x, signal, g, dx))
    return peaks


def fit_peaks(x, y, baseline=None, min_snr: float = 5.0, residual_passes: int = 1) -> list[Peak]:
    """Detect and fit Raman bands; returns Peak records sorted by position.

    x, y: shift axis (cm-1) and intensity, spikes already removed. baseline: optional array on the same axis;
    when None an asymmetric least squares baseline is subtracted. min_snr: a band must stand out from its
    surroundings by at least min_snr times the noise to be reported. residual_passes: how many times to look
    for missed bands in the fit residual and refit.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    order = np.argsort(x)
    x, y = x[order], y[order]
    if x.size < 7:
        return []
    if baseline is None:
        baseline = baseline_als(y)
    else:
        baseline = np.asarray(baseline, dtype=float)[order]
    signal = y - baseline
    dx = float(np.median(np.diff(x)))
    sigma = noise_sigma(signal)

    candidates = _detect(x, signal, min_snr * sigma, dx)
    peaks = _fit_all(x, signal, candidates, dx)

    for _ in range(residual_passes):
        model = sum((lorentzian(x, p.position, p.fwhm, p.height) for p in peaks), np.zeros_like(x))
        # A residual feature counts only if it is clearly above the noise and above 5 % of the fitted model at
        # that position: real line shapes are not exact Lorentzians (and the baseline is imperfect), so a strong
        # band always leaves a residue of a few percent that must not be split into extra peaks.
        threshold = 1.5 * min_snr * sigma
        extra = [c for c in _detect(x, signal - model, threshold, dx)
                 if c[2] > max(threshold, 0.05 * float(np.interp(c[0], x, model)))
                 and all(abs(c[0] - p.position) > 0.5 * p.fwhm for p in peaks)]
        if not extra:
            break
        candidates = [(p.position, p.fwhm, p.height) for p in peaks] + extra
        peaks = _fit_all(x, signal, candidates, dx)

    keep = [p for p in peaks
            if x[0] <= p.position <= x[-1] and p.height >= 3 * sigma and p.fwhm > 0]
    return sorted(keep, key=lambda p: p.position)
