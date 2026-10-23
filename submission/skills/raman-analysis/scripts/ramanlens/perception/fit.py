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
from scipy.signal import find_peaks, peak_widths, savgol_coeffs, savgol_filter

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


def noise_sigma(signal, valid=None) -> float:
    """Robust noise level: MAD of the first differences divided by sqrt(2) (differences double the variance).

    valid: optional boolean mask; only differences between two valid neighbours are used (see clipped_mask).
    """
    d = np.diff(np.asarray(signal, dtype=float))
    if valid is not None:
        valid = np.asarray(valid, dtype=bool)
        pair = valid[1:] & valid[:-1]
        if pair.sum() >= 10:
            d = d[pair]
    return _robust_std(d) / np.sqrt(2.0)


def clipped_mask(y, min_fraction: float = 0.02) -> np.ndarray:
    """True where y sits exactly on its minimum value and that value repeats in at least min_fraction of points.

    A spectrum clipped at zero (or at a detector floor) has runs of identical values whose first differences are
    exactly zero; they pull the median absolute difference down and the noise estimate with it, so two-pixel noise
    excursions above the floor then pass as bands. Returns all False when no floor value repeats that often.
    """
    y = np.asarray(y, dtype=float)
    at_floor = y <= y.min()
    if at_floor.mean() < min_fraction:
        return np.zeros(y.shape, dtype=bool)
    return at_floor


# Smoothing windows (points) of the detector: the short one keeps narrow bands sharp, the long one averages a weak
# band that spans many pixels, which lifts it out of the noise (a matched-filter effect).
DETECT_WINDOWS = (5, 9)


def _noise_gain(window: int) -> float:
    """Factor by which a quadratic Savitzky-Golay filter of this length scales white noise: sqrt(sum of c_k^2)."""
    return float(np.sqrt(np.sum(savgol_coeffs(window, 2) ** 2)))


def _detect(x, signal, min_snr: float, sigma: float, dx: float):
    """Candidate peaks as (position, fwhm_estimate, height_estimate) from local maxima of the smoothed signal.

    The signal is smoothed at each window in DETECT_WINDOWS; a maximum is a candidate when its prominence exceeds
    min_snr times the noise of that smoothed curve (sigma, the raw per-point noise, times the filter's noise gain).
    Thresholding a smoothed curve against the raw noise would throw away the gain of the smoothing: weak bands at
    five to seven raw sigma that span several pixels were missed that way. Candidates found at the long window are
    kept only where no short-window candidate lies within half a linewidth.
    """
    n = signal.size
    span = x[-1] - x[0]
    found = []
    for win in DETECT_WINDOWS:
        if n < win + 2:
            continue
        smooth = savgol_filter(signal, win, 2)
        idx, _ = find_peaks(smooth, prominence=min_snr * sigma * _noise_gain(win))
        if idx.size == 0:
            continue
        widths_px = peak_widths(smooth, idx, rel_height=0.5)[0]
        for i, wp in zip(idx, widths_px):
            c = (float(x[i]), float(np.clip(wp * dx, 2 * dx, span / 3)), float(smooth[i]))
            if all(abs(c[0] - f[0]) > 0.5 * max(c[1], f[1]) for f in found):
                found.append(c)
    return sorted(found)


def _groups(candidates, merge_factor: float = 3.0):
    """Split position-sorted candidates into groups whose members lie within merge_factor linewidths of a neighbour."""
    groups = []
    for c in sorted(candidates):
        if groups and c[0] - groups[-1][-1][0] < merge_factor * max(c[1], groups[-1][-1][1]):
            groups[-1].append(c)
        else:
            groups.append([c])
    return groups


def _fit_group(x, signal, group, dx: float, window_factor: float = 6.0, window=None, maxfev: int = 20000):
    """Fit one group of candidates; returns (peaks, rss, n_points, window).

    peaks are initial estimates without errors (and rss is inf) if the fit fails. window = (lo, hi) fixes the fit
    range, so two models of the same group can be compared on the same points.
    """
    if window is None:
        window = (min(p - window_factor * w for p, w, _ in group), max(p + window_factor * w for p, w, _ in group))
    lo, hi = window
    m = (x >= lo) & (x <= hi)
    xs, ys = x[m], signal[m]
    x_ref = 0.5 * (lo + hi)
    p0 = [float(np.min(ys)) if ys.size else 0.0, 0.0, x_ref]
    lower = [-np.inf, -np.inf, x_ref - 1e-9]
    upper = [np.inf, np.inf, x_ref + 1e-9]
    # A band narrower than about 1.5 pixels FWHM is not resolved by the detector (spikes are already removed), and
    # letting the width go below that lets the fit park a tall, sub-pixel "peak" between two noisy samples.
    min_fwhm = 1.5 * dx
    for p, w, h in group:
        shift = max(w, 3 * dx)
        p0 += [p, max(w, min_fwhm), max(h, 1e-12)]
        lower += [p - shift, min_fwhm, 0.0]
        upper += [p + shift, 10 * w, np.inf]

    n_free = len(p0) - 1  # x_ref is pinned
    unfitted = [Peak(p, w, h, np.pi / 2 * h * w) for p, w, h in group]
    if xs.size <= n_free:
        return unfitted, np.inf, xs.size, window
    try:
        popt, pcov = curve_fit(_group_model, xs, ys, p0=p0, bounds=(lower, upper), maxfev=maxfev)
        perr = np.sqrt(np.clip(np.diag(pcov), 0, None))
    except (RuntimeError, ValueError):
        return unfitted, np.inf, xs.size, window

    peaks = []
    for k in range(3, len(popt), 3):
        pos, w, h = (float(v) for v in popt[k:k + 3])
        ep, ew, eh = (float(v) if np.isfinite(v) else None for v in perr[k:k + 3])
        peaks.append(Peak(position=pos, fwhm=w, height=h, area=np.pi / 2 * h * w,
                          position_err=ep, fwhm_err=ew, height_err=eh))
    rss = float(np.sum((ys - _group_model(xs, *popt)) ** 2))
    return peaks, rss, xs.size, window


def _bic(rss: float, n: int, n_params: int) -> float:
    """Bayesian information criterion for a least-squares fit with Gaussian noise (Schwarz 1978, Ann. Stat. 6, 461)."""
    return n * np.log(max(rss, 1e-300) / n) + n_params * np.log(n)


def _merge_unresolved(x, signal, peaks, rss, n, window, dx):
    """Replace pairs of overlapping components by one band when the data do not support two.

    Noise on a single broad band can make the fit split it into two components closer than their linewidths
    (for example 412.9 and 415.4 cm-1 on one flat-topped band). For each adjacent pair closer than their mean
    FWHM, the group is refitted with the pair merged; the merged model is kept when its BIC is not worse.
    A genuinely resolved doublet (separation above the linewidth) is never a candidate.
    """
    while len(peaks) > 1 and np.isfinite(rss):
        peaks = sorted(peaks, key=lambda p: p.position)
        best = None
        for i in range(len(peaks) - 1):
            a, b = peaks[i], peaks[i + 1]
            if b.position - a.position >= 0.5 * (a.fwhm + b.fwhm):
                continue
            hsum = max(a.height + b.height, 1e-12)
            merged = ((a.position * a.height + b.position * b.height) / hsum,
                      max(a.fwhm, b.fwhm) + (b.position - a.position), max(a.height, b.height))
            group = [(p.position, p.fwhm, p.height) for j, p in enumerate(peaks) if j not in (i, i + 1)]
            # A trial merge that does not converge quickly is not a better description of the data: cap the
            # evaluations so it fails (rss = inf, merge rejected) instead of iterating for a minute.
            new_peaks, new_rss, _, _ = _fit_group(x, signal, group + [merged], dx, window=window, maxfev=2000)
            k = 2 + 3 * len(peaks)  # linear background plus three per peak
            if _bic(new_rss, n, k - 3) <= _bic(rss, n, k) and (best is None or new_rss < best[1]):
                best = (new_peaks, new_rss)
        if best is None:
            break
        peaks, rss = best
    return peaks


def _group_windows(groups, window_factor: float = 6.0, guard: float = 3.0, core: float = 2.0):
    """Fit range of each group: +-window_factor linewidths, but not into a neighbouring group's band.

    A window that reaches a strong band outside the group makes the fit treat that band's flank as the group's
    signal (a weak A1g next to a strong E2g collapsed into a noise spike that way). The window therefore stops
    `guard` linewidths before the nearest member of the neighbouring group, where a Lorentzian has fallen below
    3 % of its height and the linear background absorbs the rest, but always keeps `core` linewidths around the
    group's own members.
    """
    windows = []
    for i, g in enumerate(groups):
        lo = min(p - window_factor * w for p, w, _ in g)
        hi = max(p + window_factor * w for p, w, _ in g)
        if i > 0:
            p, w, _ = groups[i - 1][-1]
            lo = max(lo, p + guard * w)
        if i + 1 < len(groups):
            p, w, _ = groups[i + 1][0]
            hi = min(hi, p - guard * w)
        lo = min(lo, min(p - core * w for p, w, _ in g))
        hi = max(hi, max(p + core * w for p, w, _ in g))
        windows.append((lo, hi))
    return windows


def _fit_all(x, signal, candidates, dx):
    peaks = []
    groups = _groups(candidates)
    for g, win in zip(groups, _group_windows(groups)):
        group_peaks, rss, n, window = _fit_group(x, signal, g, dx, window=win)
        peaks.extend(_merge_unresolved(x, signal, group_peaks, rss, n, window, dx))
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
    sigma = noise_sigma(signal, valid=~clipped_mask(y))

    candidates = _detect(x, signal, min_snr, sigma, dx)
    peaks = _fit_all(x, signal, candidates, dx)

    for _ in range(residual_passes):
        model = sum((lorentzian(x, p.position, p.fwhm, p.height) for p in peaks), np.zeros_like(x))
        # A residual feature counts only if it is clearly above the noise (1.5 times the detection threshold) and
        # above 5 % of the fitted model at that position: real line shapes are not exact Lorentzians (and the
        # baseline is imperfect), so a strong band always leaves a residue of a few percent that must not be split
        # into extra peaks.
        extra = [c for c in _detect(x, signal - model, 1.5 * min_snr, sigma, dx)
                 if c[2] > 0.05 * float(np.interp(c[0], x, model))
                 and all(abs(c[0] - p.position) > 0.5 * p.fwhm for p in peaks)]
        if not extra:
            break
        candidates = [(p.position, p.fwhm, p.height) for p in peaks] + extra
        peaks = _fit_all(x, signal, candidates, dx)

    keep = [p for p in peaks
            if x[0] <= p.position <= x[-1] and p.height >= 3 * sigma and p.fwhm > 0
            and band_snr(p, sigma, dx) >= min_snr]
    return sorted(keep, key=lambda p: p.position)


def band_snr(peak: Peak, sigma: float, dx: float) -> float:
    """Signal-to-noise ratio of a whole Lorentzian band for white noise sigma per point and point spacing dx.

    This is the SNR of the matched filter: sqrt(sum over points of L(x)^2) / sigma. For a Lorentzian of height h
    and FWHM w the sum is h^2 * pi * w / (4 dx), so SNR = (h / sigma) * sqrt(pi * w / (4 dx)). A broad band at a few
    sigma per point is significant; a noise blip at the width floor (1.5 points) with the same height is not.
    """
    if sigma <= 0:
        return np.inf
    return float(peak.height / sigma * np.sqrt(np.pi * peak.fwhm / (4.0 * dx)))
