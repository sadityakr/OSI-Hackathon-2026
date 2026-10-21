"""Generate synthetic Raman test cases with exact ground truth from the Computational Raman Database.

Experimental 2D-material Raman data with published interpretations is scarce, and no open polarization-resolved
series with ground truth exists for 2D magnets. Synthetic cases fill that gap: they exercise peak fitting,
identification, hint verification and polarization analysis against answers known exactly.

Input:
    The CRD JSON dump or the 2D-row pickle (`--crd`), and the case plan in `PLAN` below
    (CRD row, common name, polytype, split, case kinds).
Process:
    For each mode band the DFT Raman tensor is rotated into the layer frame (beam along the layer normal).
    Single spectra use the in-plane, polarization-averaged intensity times the Bose factor (n+1)/omega, then add
    realism: global frequency scale (DFT runs a few percent off experiment), per-peak jitter, Lorentzian widths,
    fluorescence baseline, noise, optional Si substrate line and cosmic spikes. Angle series compute
    parallel and crossed intensities per band with a random sample rotation; each peak's pattern class is computed
    from the curves, not hand-assigned.
Output:
    data/test_set/<split>/syn-<name>-<nn>/ with spectrum.csv, input.json, truth.json (schema in data/test_set/README.md).
    Deterministic for a given --seed.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from crd_io import layer_frame, load_rows, modes, summary

HC_OVER_K = 1.4388  # cm K, second radiation constant, converts wavenumber to temperature
SI_LINE = 520.7  # cm-1, Si optical phonon, the usual calibration line

# (CRD row, common name, polytype or None, split, list of case kinds)
# kinds: "identify", "verify_true", "verify_false:<wrong hint>", "angle"
PLAN = [
    ("90", "WS2", "2H", "dev", ["identify", "verify_true", "angle"]),
    ("98", "MoS2", "3R", "dev", ["identify", "verify_false:WSe2"]),
    ("1252", "hBN", "2H", "dev", ["identify"]),
    ("83", "GaSe", None, "dev", ["identify"]),
    ("1495", "GeS", None, "dev", ["identify", "angle"]),
    ("2666", "Bi2Se3", None, "dev", ["identify"]),
    ("2677", "BiOBr", None, "dev", ["angle"]),
    ("3285", "WSe2", "2H", "heldout", ["identify", "verify_false:MoS2"]),
    ("2750", "MoSe2", "3R", "heldout", ["identify", "verify_true"]),
    ("4000", "CrBr3", None, "heldout", ["identify", "angle", "verify_false:CrI3"]),
    ("2562", "HfS2", "1T", "heldout", ["identify", "angle"]),
    ("4574", "ZrS2", "1T", "heldout", ["identify"]),
    ("2772", "SnSe2", "1T", "heldout", ["identify", "verify_true"]),
    ("951", "PbI2", None, "heldout", ["identify"]),
    ("2884", "GaS", None, "heldout", ["identify"]),
    ("3488", "InSe", None, "heldout", ["identify"]),
    ("1105", "Bi2Te2Se", None, "heldout", ["identify"]),
    ("1012", "GeSe", None, "heldout", ["identify", "angle"]),
    ("33", "ZrS3", None, "heldout", ["identify", "angle"]),
    ("3497", "MoTe2", "2H", "heldout", ["identify"]),
    ("3597", "CdI2", None, "heldout", ["identify"]),
    ("2046", "BiOI", None, "heldout", ["angle"]),
]

ANGLES = np.arange(0, 180, 10)  # degrees, incident polarization angle in the lab frame


def bose_weight(freq_cm, T=295.0):
    """Stokes intensity factor (n + 1) / omega."""
    n = 1.0 / np.expm1(HC_OVER_K * freq_cm / T)
    return (n + 1.0) / freq_cm


def band_curves(tensors, theta_deg):
    """Parallel and crossed intensity of one band (degenerate tensors summed) vs incident angle, in-plane fields."""
    th = np.radians(theta_deg)
    e_i = np.stack([np.cos(th), np.sin(th), np.zeros_like(th)], axis=1)
    e_x = np.stack([-np.sin(th), np.cos(th), np.zeros_like(th)], axis=1)
    par = sum(np.einsum("ni,ij,nj->n", e_i, R, e_i) ** 2 for R in tensors)
    crs = sum(np.einsum("ni,ij,nj->n", e_x, R, e_i) ** 2 for R in tensors)
    return par, crs


def classify(par, crs, global_max):
    """Pattern class of one band from its curves over a full turn (see the README table)."""
    m = max(par.max(), crs.max())
    if m < 0.02 * global_max:
        return "silent"
    p_var = (par.max() - par.min()) / par.max() if par.max() > 0 else 1.0
    if p_var < 0.05:
        if crs.max() < 0.05 * par.max():
            return "isotropic_par_only"
        c_var = (crs.max() - crs.min()) / crs.max()
        if c_var < 0.05 and abs(crs.mean() - par.mean()) < 0.1 * par.mean():
            return "isotropic_both"
        return "other"
    spec = np.abs(np.fft.rfft(par)) / len(par)  # par sampled over 360 deg in 1 deg steps
    a0, a2, a4 = spec[0], spec[2], spec[4]
    if a2 > 0.1 * a0:
        return "twofold"
    if a4 > 0.1 * a0 and par.min() < 0.05 * par.max():
        return "fourfold"
    return "other"


def bands_of(entry):
    """Raman-active bands in the layer frame: frequency, irrep, rotated tensors."""
    Q, _ = layer_frame(entry)
    by_band = {}
    for m in modes(entry):
        if m["raman_active"] != 1 or m["tensor"] is None or m["freq_cm"] < 10:
            continue
        b = by_band.setdefault(m["band"], dict(freq=[], irrep=m["irrep"], tensors=[]))
        b["freq"].append(m["freq_cm"])
        b["tensors"].append(Q @ m["tensor"] @ Q.T)
    out = []
    for b in by_band.values():
        out.append(dict(freq=float(np.mean(b["freq"])), irrep=b["irrep"], tensors=b["tensors"]))
    return sorted(out, key=lambda b: b["freq"])


def lorentz(x, x0, fwhm):
    g = fwhm / 2.0
    return g * g / ((x - x0) ** 2 + g * g)


def realistic_positions(bands, rng):
    # CRD vs experiment: WS2 1.006-1.01, WSe2 ~1.02, 3R-MoS2 ~1.00, HfS2 1.00-1.03 (data/README.md), so DFT runs 0-3 % low
    scale = rng.uniform(1.0, 1.025)
    for b in bands:
        b["pos"] = b["freq"] * scale + rng.normal(0, 1.5)
        b["fwhm"] = rng.uniform(3.0, 9.0)
    return scale


LOW_CUTOFF = 60.0  # cm-1, typical edge-filter limit; lower modes are outside the recorded window


def in_window(bands):
    """Keep bands that land inside the recorded window (above the edge-filter cutoff)."""
    return [b for b in bands if b["pos"] > LOW_CUTOFF + 10.0]


def make_single(entry, rng, substrate):
    bands = bands_of(entry)
    theta = np.arange(0, 360, 1.0)
    scale = realistic_positions(bands, rng)
    bands = in_window(bands)
    for b in bands:
        par, crs = band_curves(b["tensors"], theta)
        b["w"] = (par.mean() + crs.mean()) * bose_weight(b["freq"])
    wmax = max(b["w"] for b in bands)
    lo = LOW_CUTOFF
    hi = max(1100.0, max(b["pos"] for b in bands if b["w"] > 0.03 * wmax) + 200.0)
    x = np.arange(lo, hi, rng.uniform(0.8, 1.3)) + rng.uniform(0, 0.5)
    amp = rng.uniform(2000, 20000)
    y = np.zeros_like(x)
    peaks = []
    for b in bands:
        rel = b["w"] / wmax
        if rel < 0.03:
            continue
        y += amp * rel * lorentz(x, b["pos"], b["fwhm"])
        if rel >= 0.08:
            peaks.append(dict(position_cm1=round(b["pos"], 1), tolerance_cm1=4.0, irrep=b["irrep"],
                              label=b["irrep"], relative_intensity=round(rel, 3)))
    if substrate:
        y += amp * rng.uniform(0.3, 1.5) * lorentz(x, SI_LINE + rng.normal(0, 0.3), 3.5)
        peaks.append(dict(position_cm1=SI_LINE, tolerance_cm1=2.0, irrep="F2g", label="Si substrate",
                          substrate=True))
    # fluorescence background, noise and cosmic spikes
    y += amp * (rng.uniform(0, 0.3) + rng.uniform(-0.1, 0.2) * (x - lo) / (hi - lo)
                + rng.uniform(0, 0.4) * np.exp(-(((x - rng.uniform(lo, hi)) / rng.uniform(300, 900)) ** 2)))
    y += rng.normal(0, amp / rng.uniform(30, 150), size=x.size)
    artifacts = []
    if rng.random() < 0.4:
        i = rng.integers(10, x.size - 10)
        y[i] += amp * rng.uniform(0.5, 2.0)
        artifacts.append(dict(type="cosmic_ray", position_cm1=round(float(x[i]), 1)))
    y = np.round(np.clip(y, 0, None), 1)
    rows = "shift_cm1,intensity\n" + "\n".join(f"{a:.2f},{b}" for a, b in zip(x, y))
    peaks.sort(key=lambda p: p["position_cm1"])
    return rows, peaks, dict(frequency_scale=round(scale, 4), artifacts=artifacts)


def make_angle(entry, rng):
    bands = bands_of(entry)
    scale = realistic_positions(bands, rng)
    bands = in_window(bands)
    offset = rng.uniform(0, 180)  # unknown sample rotation: crystal axis sits at this lab angle
    full = np.arange(0, 360, 1.0)
    for b in bands:
        par, crs = band_curves(b["tensors"], full - offset)
        b["full"] = (par, crs)
        b["peak"] = max(par.max(), crs.max()) * bose_weight(b["freq"])
    gmax = max(max(b["full"][0].max(), b["full"][1].max()) for b in bands)
    wmax = max(b["peak"] for b in bands)
    lo, hi = LOW_CUTOFF, max(b["pos"] for b in bands) + 100.0
    x = np.arange(lo, hi, 1.0)
    amp = rng.uniform(2000, 20000)
    noise = amp / rng.uniform(40, 120)
    lines, peaks, silent = [], [], []
    for b in bands:
        b["pattern"] = classify(*b["full"], gmax)
    for config, k in (("parallel", 0), ("crossed", 1)):
        for ang in ANGLES:
            y = np.zeros_like(x)
            for b in bands:
                w = b["full"][k][int(ang)] * bose_weight(b["freq"]) / wmax
                y += amp * w * lorentz(x, b["pos"], b["fwhm"])
            y += amp * 0.05 + rng.normal(0, noise, size=x.size)
            y = np.clip(y, 0, None)
            lines += [f"{a:.2f},{v:.1f},{ang},{config}" for a, v in zip(x, y)]
    for b in bands:
        rel = b["peak"] / wmax
        if b["pattern"] == "silent" or rel < 0.08:
            if b["pattern"] == "silent":
                silent.append(dict(position_cm1=round(b["pos"], 1), irrep=b["irrep"]))
            continue
        p = dict(position_cm1=round(b["pos"], 1), tolerance_cm1=4.0, irrep=b["irrep"], label=b["irrep"],
                 pattern=b["pattern"], relative_intensity=round(rel, 3))
        if b["pattern"] == "twofold":
            p["max_parallel_angle_deg"] = int(np.argmax(b["full"][0][:180]))
        peaks.append(p)
    rows = "shift_cm1,intensity,angle_deg,config\n" + "\n".join(lines)
    return rows, peaks, dict(frequency_scale=round(scale, 4), crystal_axis_lab_angle_deg=round(offset, 1),
                             silent_modes=silent)


def write_case(root, split, case_id, inp, truth, rows):
    d = root / split / case_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "spectrum.csv").write_text(rows + "\n")
    (d / "input.json").write_text(json.dumps(inp, indent=2) + "\n")
    (d / "truth.json").write_text(json.dumps(truth, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Generate synthetic CRD-based Raman test cases with exact truth.")
    ap.add_argument("--crd", required=True, help="crd.json or the 2D-row pickle made by crd_io.cache_2d")
    ap.add_argument("--out", default="data/test_set", help="test-set root (dev/ and heldout/ are created below it)")
    ap.add_argument("--seed", type=int, default=20261021, help="random seed; output is deterministic for a seed")
    args = ap.parse_args()

    rows_db = load_rows(args.crd)
    rng = np.random.default_rng(args.seed)
    root = Path(args.out)
    counter = {}
    for row, name, polytype, split, kinds in PLAN:
        entry = rows_db[row]
        s = summary(entry)
        for kind in kinds:
            n = counter[name] = counter.get(name, 0) + 1
            case_id = f"syn-{name}-{n:02d}"
            source = dict(kind="synthetic",
                          dataset="Computational Raman Database v1.0.1, doi:10.24435/materialscloud:pg-h3",
                          paper="Bagheri and Komsa 2023, Sci. Data 10, 80, doi:10.1038/s41597-023-01988-5",
                          figure=f"CRD row {row}, {s['mpid']}", licence="CC BY 4.0")
            truth = dict(case_id=case_id, material=name, formula=name, polytype=polytype,
                         spacegroup=s["spacegroup"], pointgroup=s["pointgroup"], hint_is_correct=None,
                         layers="bulk", peaks=[], properties={}, source=source, notes="")
            inp = dict(case_id=case_id, kind="single", task="identify", material_hint=None, laser_nm=532,
                       temperature_K=295, substrate=None, geometry="backscattering, beam along the layer normal",
                       question="Which material is this? Assign the Raman peaks.")
            if kind == "angle":
                csv, peaks, extra = make_angle(entry, rng)
                inp.update(kind="angle_series", substrate="none (suspended)",
                           question="Which material is this? Assign the peaks and classify each peak's "
                                    "polarization dependence (parallel and crossed configurations).")
            else:
                substrate = bool(rng.random() < 0.5)
                csv, peaks, extra = make_single(entry, rng, substrate)
                inp["substrate"] = "SiO2/Si" if substrate else None
                if kind.startswith("verify"):
                    hint = name if kind == "verify_true" else kind.split(":", 1)[1]
                    inp.update(task="verify", material_hint=hint,
                               question=f"The user says this sample is {hint}. Is the spectrum consistent "
                                        f"with that? Justify from reference data or literature.")
                    truth["hint_is_correct"] = kind == "verify_true"
            truth["peaks"] = peaks
            truth["notes"] = json.dumps(extra)
            write_case(root, split, case_id, inp, truth, csv)
            print(split, case_id, kind, len(peaks), "peaks")


if __name__ == "__main__":
    main()
