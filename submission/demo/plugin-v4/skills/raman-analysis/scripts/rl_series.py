"""Compare a set of Raman spectra of one material: track each band across spectra with uncertainties.

Interpreting changes (thickness, dose, temperature, power, strain) needs every spectrum fitted the same way and the
bands matched across spectra, so that a 1 cm-1 shift is a measured difference with an error bar rather than an
impression from overlaid curves. A shared Si substrate line can serve as an internal calibration.

Input:
    Two or more spectrum files (two-column csv/txt), optional --labels in the same order, --substrate text,
    --si-correct to shift each spectrum so its Si line sits at 520.7 cm-1, --tol for band matching.
Process:
    Each spectrum: ramanlens.perception.pipeline.analyze_spectrum (despike, ALS baseline, Lorentzian fits with
    covariance errors, Si flag). Bands are matched across spectra by position (greedy, within --tol cm-1). For each
    band: position, FWHM, height and area per spectrum, shift relative to the first spectrum with propagated error,
    and height relative to the strongest sample band of the same spectrum. Pairwise separations of the two
    strongest bands are given because many relations use them (e.g. A1g - E2g in TMDs).
Output:
    JSON on stdout (bands x spectra table, Si offsets, separations, notes) and series.png (normalized overlay with
    an offset per spectrum, plus band positions vs spectrum).
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # file output only, no window
import matplotlib.pyplot as plt
import numpy as np

from ramanlens.perception.io import read_spectrum
from ramanlens.perception.pipeline import analyze_spectrum

SI_REF = 520.7  # cm-1, calibration convention (reported values 520 to 520.9: Lee 2010; Castellanos-Gomez 2014)


def err_or_zero(v):
    return float(v) if v is not None and np.isfinite(v) else 0.0


def main():
    ap = argparse.ArgumentParser(description="Fit and compare several spectra of one material band by band.")
    ap.add_argument("spectra", nargs="+", help="spectrum files, in the order to compare (first = reference)")
    ap.add_argument("--labels", nargs="*", default=None, help="labels in the same order (default: file names)")
    ap.add_argument("--substrate", default=None, help="substrate text, e.g. 'SiO2/Si' (flags the Si line)")
    ap.add_argument("--si-correct", action="store_true",
                    help="shift each spectrum so its Si line is at 520.7 cm-1 (only where a Si line is found)")
    ap.add_argument("--tol", type=float, default=6.0, help="max position difference (cm-1) to call bands the same")
    ap.add_argument("--min-snr", type=float, default=5.0, help="detection threshold in noise units")
    ap.add_argument("--out", default="series.png", help="plot path")
    args = ap.parse_args()
    labels = args.labels if args.labels and len(args.labels) == len(args.spectra) else \
        [Path(p).stem for p in args.spectra]

    fits, notes, si_offsets = [], [], {}
    for path, lab in zip(args.spectra, labels):
        s = read_spectrum(path)
        s.meta = {**(s.meta or {}), "substrate": args.substrate}
        res = analyze_spectrum(s, min_snr=args.min_snr)
        si = [p for p in res.peaks if p.is_substrate]
        shift = 0.0
        if si:
            si_offsets[lab] = round(si[0].position - SI_REF, 2)
            if args.si_correct:
                shift = SI_REF - si[0].position
        elif args.si_correct:
            notes.append(f"{lab}: no Si line found, not calibration-corrected")
        fits.append({"label": lab, "res": res, "shift": shift,
                     "peaks": [p for p in res.peaks if not p.is_substrate]})

    # Greedy band matching: start from the reference spectrum's bands, add unmatched bands of later spectra.
    bands = []
    for i, f in enumerate(fits):
        for p in sorted(f["peaks"], key=lambda q: -q.height):
            pos = p.position + f["shift"]
            best = None
            for b in bands:
                if i in b["members"]:
                    continue
                d = abs(b["center"] - pos)
                if d <= args.tol and (best is None or d < best[0]):
                    best = (d, b)
            if best is None:
                bands.append({"center": pos, "members": {i: p}})
            else:
                b = best[1]
                b["members"][i] = p
                b["center"] = float(np.mean([q.position + fits[j]["shift"] for j, q in b["members"].items()]))
    bands.sort(key=lambda b: b["center"])

    strongest = {i: max((p.height for p in f["peaks"]), default=np.nan) for i, f in enumerate(fits)}
    table = []
    for b in bands:
        ref = b["members"].get(0)
        row = {"band_cm1": round(b["center"], 1), "per_spectrum": []}
        for i, f in enumerate(fits):
            p = b["members"].get(i)
            if p is None:
                row["per_spectrum"].append({"label": f["label"], "present": False})
                continue
            pos = p.position + f["shift"]
            e = {"label": f["label"], "present": True, "position_cm1": round(pos, 2),
                 "position_err_cm1": round(err_or_zero(p.position_err), 3), "fwhm_cm1": round(p.fwhm, 2),
                 "fwhm_err_cm1": round(err_or_zero(p.fwhm_err), 3), "height": round(p.height, 3),
                 "area": round(p.area, 3), "height_rel_strongest": round(p.height / strongest[i], 3)}
            if ref is not None and i > 0:
                e["shift_vs_first_cm1"] = round(pos - (ref.position + fits[0]["shift"]), 2)
                e["shift_err_cm1"] = round(float(np.hypot(err_or_zero(p.position_err),
                                                          err_or_zero(ref.position_err))), 3)
            row["per_spectrum"].append(e)
        table.append(row)

    separations = []
    for i, f in enumerate(fits):
        top = sorted(f["peaks"], key=lambda q: -q.height)[:2]
        if len(top) == 2:
            a, b = sorted(top, key=lambda q: q.position)
            separations.append({"label": f["label"], "low_cm1": round(a.position + f["shift"], 2),
                                "high_cm1": round(b.position + f["shift"], 2),
                                "separation_cm1": round(b.position - a.position, 2),
                                "separation_err_cm1": round(float(np.hypot(err_or_zero(a.position_err),
                                                                           err_or_zero(b.position_err))), 3)})

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [3, 2]})
    for i, f in enumerate(fits):
        x = np.asarray(f["res"].x) + f["shift"]
        y = np.asarray(f["res"].y_clean) - np.nan_to_num(np.asarray(f["res"].baseline))
        ax.plot(x, y / (np.nanmax(y) or 1) + 1.1 * i, lw=0.8, label=f["label"])
    ax.set_xlabel("Raman shift (cm$^{-1}$)" + (" (Si-corrected)" if args.si_correct else ""))
    ax.set_ylabel("normalized intensity + offset")
    ax.legend(fontsize=7)
    for b in table:
        pts = [(k, e["position_cm1"], e["position_err_cm1"]) for k, e in enumerate(b["per_spectrum"]) if e["present"]]
        if len(pts) > 1:
            k, pos, er = zip(*pts)
            ax2.errorbar(k, np.array(pos) - pos[0], yerr=er, marker="o", ms=3, label=f"{b['band_cm1']:.0f}")
    ax2.set_xticks(range(len(fits)), [f["label"] for f in fits], rotation=30, fontsize=7)
    ax2.set_ylabel("shift vs first spectrum (cm$^{-1}$)")
    ax2.legend(fontsize=6, title="band")
    fig.tight_layout()
    fig.savefig(args.out, dpi=110)

    json.dump({"bands": table, "two_strongest_separation": separations, "si_offset_from_520.7_cm1": si_offsets,
               "si_corrected": bool(args.si_correct), "notes": notes, "plot": args.out,
               "method": "same pipeline per spectrum (ALS baseline, Lorentzian fits, covariance errors); bands "
                         f"matched within {args.tol} cm-1"}, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
