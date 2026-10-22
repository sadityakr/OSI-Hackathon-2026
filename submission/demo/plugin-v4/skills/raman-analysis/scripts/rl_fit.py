"""Fit the Raman bands of a spectrum and write a peak table plus a plot the agent can look at.

This is the measurement step of the skill: positions, widths and heights with uncertainties come from here, so
that every "measured" number in a report has a reproducible origin. It wraps the ramanlens perception pipeline
and adds a plot, an optional fit window, and a compact table for reading.

Input:
    A spectrum file (two-column csv/txt, or the long angle-series csv, whose frames are summed). Optional
    --substrate text (e.g. "SiO2/Si") so the Si line is flagged as substrate, --window to refit a region, and
    --min-snr for the detection threshold.
Process:
    ramanlens.perception.pipeline.analyze_spectrum: cosmic-ray removal, asymmetric least squares baseline, peak
    detection by prominence over the noise, grouped multi-Lorentzian fit with covariance uncertainties, Si line
    flag. The plot shows data, baseline, total fit and each component, with residuals.
Output:
    peaks.json (next to the --out plot) and fit.png; the peak table as JSON on stdout.
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # file output only, no window
import matplotlib.pyplot as plt
import numpy as np

from ramanlens.perception.fit import lorentzian
from ramanlens.perception.io import Spectrum, read_series, read_spectrum
from ramanlens.perception.pipeline import analyze_spectrum


def load(path, substrate):
    with open(path, encoding="utf-8", errors="replace") as fh:
        header = fh.readline().lower()
    if "angle" in header:
        s = read_series(path)
        y = np.sum([np.asarray(v) for v in s.spectra.values()], axis=0)
        return Spectrum(x=np.asarray(s.x), y=y, meta={"substrate": substrate, "summed_angle_series": True})
    s = read_spectrum(path)
    s.meta = {**(s.meta or {}), "substrate": substrate}
    return s


def main():
    ap = argparse.ArgumentParser(description="Fit Raman bands; writes peaks.json and fit.png, prints the table.")
    ap.add_argument("spectrum", help="spectrum file (csv/txt; angle series are summed over frames)")
    ap.add_argument("--substrate", default=None, help="substrate text, e.g. 'SiO2/Si' (flags the Si line)")
    ap.add_argument("--window", nargs=2, type=float, metavar=("LO", "HI"), default=None,
                    help="only fit this shift range in cm-1 (use to resolve close bands)")
    ap.add_argument("--min-snr", type=float, default=5.0, help="detection threshold in noise units (lower finds "
                    "weaker bands, with more false ones)")
    ap.add_argument("--out", default="fit.png", help="plot path; peaks.json is written next to it")
    args = ap.parse_args()

    spec = load(args.spectrum, args.substrate)
    if args.window:
        m = (np.asarray(spec.x) >= args.window[0]) & (np.asarray(spec.x) <= args.window[1])
        spec = Spectrum(x=np.asarray(spec.x)[m], y=np.asarray(spec.y)[m], meta=spec.meta)
    res = analyze_spectrum(spec, min_snr=args.min_snr)

    x = np.asarray(res.x)
    fig, (ax, axr) = plt.subplots(2, 1, figsize=(9, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax.plot(x, res.y_clean, color="0.3", lw=0.8, label="data (spikes removed)")
    ax.plot(x, res.baseline, color="tab:orange", lw=0.8, label="baseline")
    base = np.nan_to_num(res.baseline)
    total = base.copy()
    for p in res.peaks:
        comp = lorentzian(x, p.position, p.fwhm, p.height)
        total += comp
        ax.plot(x, base + comp, lw=0.7, color="tab:red" if p.is_substrate else "tab:blue")
        ax.annotate(f"{p.position:.1f}" + (" Si" if p.is_substrate else ""), (p.position, base[np.argmin(
            abs(x - p.position))] + p.height), fontsize=7, ha="center", va="bottom")
    for s in res.spikes:
        ax.axvline(s, color="tab:purple", ls=":", lw=0.8)
    ax.plot(x, total, color="k", lw=0.6, ls="--", label="total fit")
    ax.set_ylabel("intensity")
    ax.legend(fontsize=7)
    axr.plot(x, res.y_clean - total, color="0.4", lw=0.6)
    axr.set_xlabel("Raman shift (cm$^{-1}$)")
    axr.set_ylabel("residual")
    fig.tight_layout()
    out = Path(args.out)
    fig.savefig(out, dpi=110)

    table = {"peaks": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.to_dict().items()}
                       for p in res.peaks],
             "spikes_cm1": [round(float(s), 1) for s in res.spikes], "notes": res.notes,
             "plot": str(out), "method": "ALS baseline + multi-Lorentzian least squares (ramanlens.perception)"}
    (out.parent / "peaks.json").write_text(json.dumps(table, indent=1))
    json.dump(table, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
