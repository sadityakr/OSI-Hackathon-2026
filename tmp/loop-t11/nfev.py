"""Record curve_fit evaluation counts per group fit on dev cases (T11 diagnostics, throwaway).

Input: none (all single-spectrum dev and dev_hard cases).
Process: wraps fit.curve_fit to log (n_params, nfev, converged, max fitted height / noise) for every call.
Output: counts of converged fits by nfev, and the fits that hit the cap.
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit as _cf

from ramanlens.perception import fit
from ramanlens.perception.io import read_spectrum
from ramanlens.perception.pipeline import analyze_spectrum

ROOT = Path(__file__).resolve().parents[2]
LOG = []


def logged(f, xs, ys, p0, bounds, maxfev):
    try:
        popt, pcov, info, msg, ier = _cf(f, xs, ys, p0=p0, bounds=bounds, maxfev=maxfev, full_output=True)
        LOG.append((len(p0), info["nfev"], True, max(popt[5::3]) if len(popt) > 5 else 0))
        return popt, pcov
    except RuntimeError:
        LOG.append((len(p0), maxfev, False, max(p0[5::3])))
        raise


fit.curve_fit = logged
for split in ("dev", "dev_hard"):
    for case in sorted((ROOT / "data/test_set" / split).iterdir()):
        if json.loads((case / "input.json").read_text())["kind"] != "single":
            continue
        n0 = len(LOG)
        analyze_spectrum(read_spectrum(case / "spectrum.csv"))
        bad = [r for r in LOG[n0:] if not r[2]]
        ok = [r[1] for r in LOG[n0:] if r[2]]
        print(f"{case.name:20s} fits={len(LOG) - n0:3d} failed={len(bad)} max_nfev_ok={max(ok) if ok else None} "
              f"ok_nfev/param={max((r[1] / r[0] for r in LOG[n0:] if r[2]), default=0):.0f}", flush=True)
ok = np.array([r[1] / r[0] for r in LOG if r[2]])
print("converged nfev per parameter: percentiles 50/90/99/max", np.percentile(ok, [50, 90, 99, 100]))
