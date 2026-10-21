"""Polarization analysis of Raman angle series: pattern class of each band from its parallel and crossed curves.

In backscattering along the layer normal with in-plane linear polarizations, how a band's intensity changes with
the polarization angle depends only on the in-plane part of its Raman tensor, so the angle dependence tells the
symmetry class of the mode (A1g, E, Ag, B) without knowing the sample orientation. The agent uses this to assign
irreps, and the test set scores it.

Input: classify_curves takes the incident polarization angles (degrees) and the intensity of one band in parallel
and crossed configuration at those angles. analyze_series takes an AngleSeries (perception.io.read_series).
Process: each curve is fitted with a Fourier series in 2 theta and 4 theta. For an in-plane tensor [[a, d], [d, b]]
the parallel intensity is (m + r cos(2 theta - phi))**2 and the crossed one r**2 sin**2(2 theta - phi), with
m = (a + b) / 2 and r the anisotropic part (Loudon 1964, Adv. Phys. 13, 423, for the tensor forms). So a 2 theta
term in the parallel curve means m != 0 and r != 0 (twofold), a parallel curve that is pure 4 theta and drops to
zero means m = 0 (fourfold, B modes), and flat curves mean r = 0 (A1g, no crossed signal) or a degenerate E pair
(crossed equal to parallel). Fourier amplitudes are rotation invariant, so the unknown sample rotation drops out.
analyze_series finds the bands on the sum of all spectra (perception.pipeline), then fits the height of each band
in every spectrum with positions and widths held fixed, and classifies each band's curves.
Output: classify_curves returns {"pattern", "max_parallel_angle_deg", "fourier"}; analyze_series returns one dict
per band with position, width, pattern, angle of maximum parallel intensity (twofold only) and the curves.
"""

from __future__ import annotations

import numpy as np

from ramanlens.perception.fit import lorentzian
from ramanlens.perception.io import AngleSeries, Spectrum
from ramanlens.perception.pipeline import analyze_spectrum
from ramanlens.perception.preprocess import baseline_als, remove_spikes

PATTERNS = ("isotropic_par_only", "isotropic_both", "twofold", "fourfold", "other", "undetermined")

# Thresholds on Fourier amplitudes, relative to the mean parallel intensity P0. They follow the class definitions
# the synthetic test cases are labelled with (data/test_set/README.md; eval/synth/make_synthetic.py uses
# |rfft|/N > 0.1 a0 on the parallel curve, which is a cosine amplitude > 0.2 P0). Design choices, not literature.
TWOFOLD_MIN_A2 = 0.2       # 2 theta amplitude of the parallel curve above this -> twofold
FOURFOLD_MIN_A4 = 0.5      # 4 theta amplitude of the parallel curve above this (pure B mode: A4 = P0) -> fourfold
ISOTROPIC_MAX_MOD = 0.2    # total 2 theta + 4 theta modulation of a curve below this -> flat
PAR_ONLY_MAX_CROSSED = 0.15  # mean crossed / mean parallel below this -> no crossed signal (A1g)
BOTH_MAX_DIFF = 0.25       # |mean crossed - mean parallel| / mean parallel below this -> E pair
SIGNIFICANCE = 3.0         # an amplitude counts only when it exceeds this many standard errors


def _fourier(theta_deg: np.ndarray, y: np.ndarray) -> dict:
    """Least-squares fit y = c0 + A2 cos(2 theta - phi2) + A4 cos(4 theta - phi4); amplitudes with standard errors."""
    th = np.radians(theta_deg)
    basis = np.stack([np.ones_like(th), np.cos(2 * th), np.sin(2 * th), np.cos(4 * th), np.sin(4 * th)], axis=1)
    coef, *_ = np.linalg.lstsq(basis, y, rcond=None)
    resid = y - basis @ coef
    dof = max(y.size - basis.shape[1], 1)
    sigma = float(np.sqrt(np.sum(resid ** 2) / dof))
    # For roughly uniform angle sampling the cos and sin coefficients have variance 2 sigma**2 / N.
    amp_err = sigma * np.sqrt(2.0 / y.size)
    return {"c0": float(coef[0]), "a2": float(np.hypot(coef[1], coef[2])), "a4": float(np.hypot(coef[3], coef[4])),
            "phi2_deg": float(np.degrees(np.arctan2(coef[2], coef[1]))),
            "phi4_deg": float(np.degrees(np.arctan2(coef[4], coef[3]))),
            "amp_err": float(amp_err), "coef": coef}


def _eval_fourier(coef: np.ndarray, theta_deg: np.ndarray) -> np.ndarray:
    th = np.radians(theta_deg)
    return (coef[0] + coef[1] * np.cos(2 * th) + coef[2] * np.sin(2 * th)
            + coef[3] * np.cos(4 * th) + coef[4] * np.sin(4 * th))


def _public(f: dict) -> dict:
    return {k: round(v, 6) for k, v in f.items() if k != "coef"}


def classify_curves(theta_deg, par, crossed=None) -> dict:
    """Pattern class of one band from its parallel and crossed intensities versus incident polarization angle.

    theta_deg: incident polarization angles in degrees (any range; at least 5 distinct angles mod 180).
    par, crossed: intensities at those angles; crossed may be None when only parallel spectra were measured.
    Returns {"pattern": one of PATTERNS, "max_parallel_angle_deg": float in [0, 180) for twofold else None,
    "fourier": amplitudes of both curves, "reason": short text}.
    """
    theta = np.asarray(theta_deg, dtype=float)
    par = np.asarray(par, dtype=float)
    out = {"pattern": "undetermined", "max_parallel_angle_deg": None, "fourier": {}, "reason": ""}
    if theta.size != par.size or np.unique(np.round(theta % 180, 3)).size < 5:
        out["reason"] = "fewer than 5 distinct angles (mod 180), a 4 theta Fourier series cannot be fitted"
        return out
    fp = _fourier(theta, par)
    out["fourier"]["parallel"] = _public(fp)
    p0 = fp["c0"]
    if p0 <= 0:
        out["reason"] = "mean parallel intensity is not positive"
        return out

    def significant(a, f):
        return a > SIGNIFICANCE * f["amp_err"]

    if fp["a2"] > TWOFOLD_MIN_A2 * p0 and significant(fp["a2"], fp):
        grid = np.arange(0.0, 180.0, 0.5)
        out["pattern"] = "twofold"
        out["max_parallel_angle_deg"] = float(grid[np.argmax(_eval_fourier(fp["coef"], grid))])
        out["reason"] = f"parallel curve has a 2 theta term (A2/P0 = {fp['a2'] / p0:.2f})"
        return out
    if fp["a4"] > FOURFOLD_MIN_A4 * p0 and significant(fp["a4"], fp):
        out["pattern"] = "fourfold"
        out["reason"] = f"parallel curve is 4 theta modulated (A4/P0 = {fp['a4'] / p0:.2f}) without a 2 theta term"
        return out
    par_flat = (fp["a2"] + fp["a4"]) < ISOTROPIC_MAX_MOD * p0
    if not par_flat:
        out["pattern"] = "other"
        out["reason"] = "parallel curve modulated but neither twofold nor fourfold"
        return out
    if crossed is None:
        out["pattern"] = "undetermined"
        out["reason"] = "parallel curve flat; without crossed spectra A1g and E cannot be told apart"
        return out
    crossed = np.asarray(crossed, dtype=float)
    fc = _fourier(theta, crossed)
    out["fourier"]["crossed"] = _public(fc)
    c0 = fc["c0"]
    if c0 < PAR_ONLY_MAX_CROSSED * p0:
        out["pattern"] = "isotropic_par_only"
        out["reason"] = f"parallel flat, crossed near zero (C0/P0 = {c0 / p0:.2f})"
    elif abs(c0 - p0) < BOTH_MAX_DIFF * p0 and (fc["a2"] + fc["a4"]) < ISOTROPIC_MAX_MOD * max(c0, 1e-12):
        out["pattern"] = "isotropic_both"
        out["reason"] = f"parallel and crossed flat and equal (C0/P0 = {c0 / p0:.2f})"
    else:
        out["pattern"] = "other"
        out["reason"] = f"parallel flat but crossed neither zero nor equal to parallel (C0/P0 = {c0 / p0:.2f})"
    return out


def _band_heights(x: np.ndarray, y: np.ndarray, positions: np.ndarray, fwhms: np.ndarray) -> np.ndarray:
    """Heights of Lorentzians with fixed positions and widths in one spectrum (linear least squares).

    Spikes are removed and an asymmetric least squares baseline subtracted first; a constant column absorbs any
    residual offset. Overlapping bands are fitted jointly, so their intensities are separated.
    """
    y_clean, _ = remove_spikes(x, y)
    signal = y_clean - baseline_als(y_clean)
    cols = [lorentzian(x, p, w, 1.0) for p, w in zip(positions, fwhms)]
    design = np.stack(cols + [np.ones_like(x)], axis=1)
    coef, *_ = np.linalg.lstsq(design, signal, rcond=None)
    return coef[:-1]


def analyze_series(series: AngleSeries, min_snr: float = 5.0) -> list[dict]:
    """Find the bands of an angle series and classify the polarization pattern of each.

    Bands are fitted on the sum of all spectra; then each band's height is extracted from every (config, angle)
    spectrum with position and width fixed, and classify_curves is applied to the resulting curves. Angles
    measured in only one configuration are dropped from the crossed comparison.
    Returns a list of dicts sorted by position: position_cm1, position_err_cm1, fwhm_cm1, is_substrate, pattern,
    max_parallel_angle_deg, reason, angles_deg, parallel, crossed (heights, None when not measured), method.
    """
    x = np.asarray(series.x, dtype=float)
    total = np.sum([np.asarray(v, dtype=float) for v in series.spectra.values()], axis=0)
    summary = analyze_spectrum(Spectrum(x, total, dict(series.meta or {})), min_snr=min_snr)
    peaks = summary.peaks
    if not peaks:
        return []
    keep = x >= summary.min_shift_cm1 if summary.min_shift_cm1 is not None else np.ones(x.size, dtype=bool)
    xs = x[keep]
    positions = np.array([p.position for p in peaks])
    fwhms = np.array([p.fwhm for p in peaks])

    par_angles = sorted(a for c, a in series.spectra if c == "parallel")
    crs_angles = sorted(a for c, a in series.spectra if c == "crossed")
    heights = {k: _band_heights(xs, np.asarray(v, dtype=float)[keep], positions, fwhms)
               for k, v in series.spectra.items() if k[0] in ("parallel", "crossed")}
    both = sorted(set(par_angles) & set(crs_angles))
    angles = both if len(both) >= 5 else par_angles

    results = []
    for i, p in enumerate(peaks):
        par = np.clip([heights[("parallel", a)][i] for a in angles], 0, None)
        crs = np.clip([heights[("crossed", a)][i] for a in angles], 0, None) if angles == both and both else None
        cls = classify_curves(angles, par, crs)
        results.append({
            "position_cm1": round(float(p.position), 2),
            "position_err_cm1": None if p.position_err is None else round(float(p.position_err), 3),
            "fwhm_cm1": round(float(p.fwhm), 2),
            "is_substrate": bool(p.is_substrate),
            "pattern": cls["pattern"],
            "max_parallel_angle_deg": cls["max_parallel_angle_deg"],
            "reason": cls["reason"],
            "angles_deg": [float(a) for a in angles],
            "parallel": [round(float(v), 4) for v in par],
            "crossed": None if crs is None else [round(float(v), 4) for v in crs],
            "method": "bands fitted on the summed series (Lorentzian), heights per spectrum with fixed position and "
                      "width, Fourier series in 2 theta and 4 theta per curve",
        })
    return sorted(results, key=lambda r: r["position_cm1"])
