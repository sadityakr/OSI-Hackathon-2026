"""Quality and measurement-condition checks on a Raman spectrum, before any interpretation.

An experienced reader first asks whether the data can be trusted: spikes, a saturated detector, a large
fluorescence background, a shifted calibration, a cut-off low-wavenumber window, or a resolution too coarse for
the claim at hand. This script turns those checks into flags with plain explanations for the agent.

Input:
    A spectrum file readable by ramanlens.perception.io (two-column csv/txt, or the long angle-series csv; for a
    series the frames are summed).
Process:
    Cosmic-ray spikes with ramanlens.perception.preprocess.remove_spikes (modified z-score on first differences,
    Whitaker and Hayes 2018); saturation as a run of identical maximum values; fluorescence as the asymmetric least
    squares baseline relative to the strongest band; Si calibration offset from a Lorentzian fit near 520.7 cm-1
    when a narrow line is there; the recorded window and point spacing; signal to noise of the strongest band.
Output:
    JSON on stdout: {"flags": [{"flag", "severity", "detail"}], "window_cm1", "point_spacing_cm1",
    "spikes_cm1", "si_line": {...} or null, "snr_strongest"}.
"""

import argparse
import json
import sys

import numpy as np
from scipy.optimize import curve_fit

from ramanlens.perception.io import read_series, read_spectrum
from ramanlens.perception.preprocess import baseline_als, remove_spikes

SI_REF = 520.7  # cm-1, common calibration convention; reported values range 520 to 520.9 (Lee 2010; Castellanos-Gomez 2014)


def load_xy(path):
    """x, y of a single spectrum, or of the sum of all frames of an angle series."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        header = fh.readline().lower()
    if "angle" in header:
        s = read_series(path)
        return np.asarray(s.x), np.sum([np.asarray(v) for v in s.spectra.values()], axis=0), True
    s = read_spectrum(path)
    return np.asarray(s.x), np.asarray(s.y), False


def lorentz(x, x0, w, a, c):
    return a * (w / 2) ** 2 / ((x - x0) ** 2 + (w / 2) ** 2) + c


def si_line(x, y):
    """Fit a Lorentzian to a narrow line within 515 to 526 cm-1; None if there is no clear line."""
    m = (x > 505) & (x < 536)
    if m.sum() < 8:
        return None
    xs, ys = x[m], y[m]
    i = int(np.argmax(ys))
    if not 515 < xs[i] < 526:
        return None
    try:
        p, cov = curve_fit(lorentz, xs, ys, p0=[xs[i], 4.0, ys[i] - np.median(ys), np.median(ys)], maxfev=5000)
    except (RuntimeError, ValueError):
        return None
    if not (1.0 < abs(p[1]) < 12 and p[2] > 5 * np.std(ys - lorentz(xs, *p))):
        return None
    err = float(np.sqrt(np.diag(cov))[0]) if np.all(np.isfinite(cov)) else None
    return {"position_cm1": round(float(p[0]), 2), "fwhm_cm1": round(abs(float(p[1])), 2),
            "position_err_cm1": None if err is None else round(err, 3),
            "offset_from_520.7_cm1": round(float(p[0]) - SI_REF, 2)}


def main():
    ap = argparse.ArgumentParser(description="Quality and measurement-condition flags for a Raman spectrum.")
    ap.add_argument("spectrum", help="spectrum file (csv/txt; angle series are summed)")
    args = ap.parse_args()

    x, y, is_series = load_xy(args.spectrum)
    flags = []
    dx = float(np.median(np.diff(x)))
    y_clean, spikes = remove_spikes(x, y)
    if len(spikes):
        flags.append({"flag": "cosmic_ray_spikes", "severity": "info",
                      "detail": f"{len(spikes)} spike(s) removed at {[round(float(s), 1) for s in spikes]} cm-1; "
                                "report them under artifacts, never as peaks."})

    top = np.max(y)
    run = int(np.sum(np.isclose(y, top, rtol=0, atol=1e-9 * max(abs(top), 1))))
    if run >= 3:
        flags.append({"flag": "possible_saturation", "severity": "warning",
                      "detail": f"{run} points sit exactly at the maximum; the strongest band may be clipped."})

    base = baseline_als(y_clean)
    signal = y_clean - base
    peak = float(np.max(signal))
    noise = float(np.median(np.abs(np.diff(signal))) / 0.6745 / np.sqrt(2))
    if peak > 0 and float(np.max(base) - np.min(base)) > 2 * peak:
        flags.append({"flag": "strong_background", "severity": "warning",
                      "detail": "baseline variation exceeds twice the strongest band: fluorescence or "
                                "photoluminescence; weak bands and intensity ratios are less reliable."})

    si = si_line(x, y_clean)
    if si:
        off = si["offset_from_520.7_cm1"]
        sev = "warning" if abs(off) > 1.0 else "info"
        flags.append({"flag": "si_substrate_line", "severity": sev,
                      "detail": f"Si line at {si['position_cm1']} cm-1 (offset {off:+.2f} from 520.7). "
                                + ("Calibration may be off: correct shifts before 1 to 3 cm-1 interpretations. "
                                   if abs(off) > 1.0 else "")
                                + "Assign as 'Si substrate'; Si second-order features near 950 and 980 cm-1 "
                                  "(and a computed 2TA band near 300) are also substrate."})

    if x[0] > 100:
        flags.append({"flag": "low_wavenumber_cutoff", "severity": "info",
                      "detail": f"data start at {x[0]:.0f} cm-1: shear and breathing modes and low-frequency "
                                "modes are not observable; their absence is not evidence."})
    if dx > 1.5:
        flags.append({"flag": "coarse_sampling", "severity": "warning",
                      "detail": f"point spacing {dx:.2f} cm-1: splittings and shifts below about {2 * dx:.1f} "
                                "cm-1 are not resolvable (e.g. 2LA(M) vs E2g in WS2, layer shifts)."})
    snr = peak / noise if noise > 0 else None
    if snr is not None and snr < 20:
        flags.append({"flag": "low_snr", "severity": "warning",
                      "detail": f"strongest band only {snr:.0f} x noise: weak modes may be missed."})

    json.dump({"flags": flags, "window_cm1": [round(float(x[0]), 1), round(float(x[-1]), 1)],
               "point_spacing_cm1": round(dx, 3), "spikes_cm1": [round(float(s), 1) for s in spikes],
               "si_line": si, "snr_strongest": None if snr is None else round(snr, 1),
               "angle_series_summed": is_series}, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
