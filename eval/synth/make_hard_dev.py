"""Generate hard synthetic development cases from uncommon layered materials in the Computational Raman Database.

A bare Claude agent scores near 100 % on the original dev cases because they are common materials it knows from
memory (WS2, MoS2, hBN, ...). These cases use layered crystals that rarely appear in the Raman literature and
degrade the spectra further, so that the dev split is about as hard as the held-out split and tool improvements
can be measured while developing. They go to a separate folder (dev_hard/) so the build loop's contract tests,
which iterate over dev/, are not affected.

Input:
    The CRD 2D-row pickle or full JSON dump (`--crd`) and the case plan in `PLAN` below. None of the PLAN rows or
    formulas appear in make_synthetic.PLAN (neither dev nor held-out), so there is no overlap with existing cases.
Process:
    Reuses the spectrum physics of make_synthetic.py unchanged (make_single, make_angle: DFT Raman tensors in the
    layer frame, Bose factor, frequency scale, jitter, baseline, noise). Each spectrum is then hardened: extra
    Gaussian noise at a drawn signal-to-noise ratio relative to the strongest Raman band, a forced cosmic spike on
    selected cases, and a forced Si substrate line on others. Truth peaks that sink below three noise standard
    deviations are removed from the answer key, because a competent reader could not find them.
Output:
    <out>/dev_hard/syn-<name>-<nn>/ with spectrum.csv, input.json and truth.json (schema in
    data/test_set/README.md). Deterministic for a given --seed.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # make_synthetic and crd_io live next to this file

from crd_io import load_rows, summary  # noqa: E402
from make_synthetic import make_angle, make_single, write_case  # noqa: E402

SPLIT = "dev_hard"

# (CRD row, common name, reduced formula, polytype or None, crystal family, case kind, options)
# kinds: "identify", "verify_false:<wrong hint>", "angle"
# options: snr = strongest band height / added noise sigma; spike = force a cosmic ray; si = force Si substrate line
PLAN = [
    ("179", "HfSe2", "HfSe2", "1T", "trigonal", "identify", dict(snr=30, spike=False, si=True)),
    ("2968", "GaTe", "GaTe", None, "hexagonal", "identify", dict(snr=20, spike=False, si=False)),
    ("1571", "AsI3", "AsI3", None, "trigonal", "identify", dict(snr=15, spike=True, si=False)),
    ("4232", "InSiTe3", "InSiTe3", None, "trigonal", "identify", dict(snr=40, spike=True, si=False)),
    ("1132", "TiNCl", "TiNCl", None, "orthorhombic", "identify", dict(snr=15, spike=False, si=True)),
    ("2296", "InOCl", "InOCl", None, "orthorhombic", "identify", dict(snr=25, spike=True, si=False)),
    ("2296", "InOCl", "InOCl", None, "orthorhombic", "angle", dict(snr=25, spike=True)),
    ("4496", "SnS", "SnS", None, "orthorhombic", "angle", dict(snr=25, spike=False)),
    ("4496", "SnS", "SnS", None, "orthorhombic", "verify_false:SnSe", dict(snr=15, spike=True, si=False)),
    ("4140", "CdPS3", "CdPS3", None, "monoclinic", "verify_false:FePS3", dict(snr=18, spike=False, si=True)),
]

NOTES_EXTRA = {
    "GaTe": "CRD row 2968 is the hexagonal P6_3/mmc polymorph of GaTe; the common bulk form is monoclinic C2/m, "
            "whose spectrum differs. Formula identification is what is scored.",
    "InSiTe3": "CRD formula In2Si2Te6.",
    "CdPS3": "CRD formula Cd2P2S6. Hint FePS3 is deliberately wrong (same MPX3 family, different metal).",
    "SnS": "Hint SnSe (verify case) is deliberately wrong (same Pnma structure, heavier chalcogen).",
}


def _smooth_max(y):
    """Height of the strongest feature, robust to single-point cosmic spikes (5-point running median)."""
    pad = np.pad(y, 2, mode="edge")
    med = np.median(np.lib.stride_tricks.sliding_window_view(pad, 5), axis=1)
    return med.max() - np.median(y)


def _spike_index(x, peaks, rng):
    """Index for a cosmic spike at least 15 cm-1 from every truth peak, so it does not hide a real band."""
    for _ in range(200):
        i = int(rng.integers(10, x.size - 10))
        if all(abs(x[i] - p["position_cm1"]) > 15 for p in peaks):
            return i
    return int(rng.integers(10, x.size - 10))


def harden_single(csv, peaks, extra, rng, snr, spike):
    """Add noise at the given SNR, optionally a cosmic spike; drop truth peaks below 3 sigma."""
    data = np.array([[float(v) for v in line.split(",")] for line in csv.splitlines()[1:]])
    x, y = data[:, 0], data[:, 1]
    height = _smooth_max(y)
    sigma = height / snr
    y = y + rng.normal(0, sigma, size=y.size)
    if spike:
        i = _spike_index(x, peaks, rng)
        y[i] += height * rng.uniform(0.8, 1.6)
        extra["artifacts"].append(dict(type="cosmic_ray", position_cm1=round(float(x[i]), 1)))
    y = np.round(np.clip(y, 0, None), 1)
    kept = [p for p in peaks if p.get("substrate") or p["relative_intensity"] >= 3.0 / snr]
    extra.update(added_noise_snr=snr, dropped_below_3sigma=[p["position_cm1"] for p in peaks if p not in kept])
    rows = "shift_cm1,intensity\n" + "\n".join(f"{a:.2f},{b}" for a, b in zip(x, y))
    return rows, kept, extra


def harden_angle(csv, peaks, extra, rng, snr, spike):
    """Same as harden_single for a long-format polarization series; the spike lands in one spectrum only."""
    lines = csv.splitlines()[1:]
    x = np.array([float(line.split(",")[0]) for line in lines])
    y = np.array([float(line.split(",")[1]) for line in lines])
    meta = [line.split(",", 2)[2] for line in lines]  # "angle,config"
    height = y.max() - np.median(y)
    sigma = height / snr
    y = y + rng.normal(0, sigma, size=y.size)
    artifacts = []
    if spike:
        key = meta[int(rng.integers(0, len(meta)))]
        idx = np.array([i for i, m in enumerate(meta) if m == key])
        j = _spike_index(x[idx], peaks, rng)
        y[idx[j]] += height * rng.uniform(0.8, 1.6)
        ang, cfg = key.split(",")
        artifacts.append(dict(type="cosmic_ray", position_cm1=round(float(x[idx[j]]), 1), angle_deg=int(ang),
                              config=cfg))
    y = np.clip(y, 0, None)
    kept = [p for p in peaks if p["relative_intensity"] >= 3.0 / snr]
    extra.update(added_noise_snr=snr, artifacts=artifacts,
                 dropped_below_3sigma=[p["position_cm1"] for p in peaks if p not in kept])
    rows = "shift_cm1,intensity,angle_deg,config\n" + "\n".join(
        f"{a:.2f},{v:.1f},{m}" for a, v, m in zip(x, y, meta))
    return rows, kept, extra


def main():
    ap = argparse.ArgumentParser(description="Generate hard synthetic dev cases (uncommon layered materials, "
                                             "lower SNR, spikes, Si line) into <out>/dev_hard/.")
    ap.add_argument("--crd", default="data/raw/crd/crd_2d.pkl",
                    help="crd.json or the 2D-row pickle made by crd_io.cache_2d")
    ap.add_argument("--out", default="data/test_set", help="test-set root; cases go to <out>/dev_hard/")
    ap.add_argument("--seed", type=int, default=20261022, help="random seed; output is deterministic for a seed")
    args = ap.parse_args()

    rows_db = load_rows(args.crd)
    rng = np.random.default_rng(args.seed)
    root = Path(args.out)
    counter = {}
    for row, name, formula, polytype, family, kind, opt in PLAN:
        entry = rows_db[row]
        s = summary(entry)
        n = counter[name] = counter.get(name, 0) + 1
        case_id = f"syn-{name}-{n:02d}"
        source = dict(kind="synthetic",
                      dataset="Computational Raman Database v1.0.1, doi:10.24435/materialscloud:pg-h3",
                      paper="Bagheri and Komsa 2023, Sci. Data 10, 80, doi:10.1038/s41597-023-01988-5",
                      figure=f"CRD row {row}, {s['mpid']}", licence="CC BY 4.0")
        truth = dict(case_id=case_id, material=name, formula=formula, polytype=polytype,
                     spacegroup=s["spacegroup"], pointgroup=s["pointgroup"], hint_is_correct=None,
                     layers="bulk", peaks=[], properties={}, source=source, notes="")
        inp = dict(case_id=case_id, kind="single", task="identify", material_hint=None, laser_nm=532,
                   temperature_K=295, substrate=None, geometry="backscattering, beam along the layer normal",
                   question="Which material is this? Assign the Raman peaks.")
        if kind == "angle":
            csv, peaks, extra = make_angle(entry, rng)
            csv, peaks, extra = harden_angle(csv, peaks, extra, rng, opt["snr"], opt["spike"])
            inp.update(kind="angle_series", substrate="none (suspended)",
                       question="Which material is this? Assign the peaks and classify each peak's "
                                "polarization dependence (parallel and crossed configurations).")
        else:
            csv, peaks, extra = make_single(entry, rng, opt["si"])
            csv, peaks, extra = harden_single(csv, peaks, extra, rng, opt["snr"], opt["spike"])
            inp["substrate"] = "SiO2/Si" if opt["si"] else None
            if kind.startswith("verify"):
                hint = kind.split(":", 1)[1]
                inp.update(task="verify", material_hint=hint,
                           question=f"The user says this sample is {hint}. Is the spectrum consistent "
                                    f"with that? Justify from reference data or literature.")
                truth["hint_is_correct"] = False
        extra.update(crystal_family=family, crd_formula=s["formula"], hard_dev=True)
        truth["peaks"] = peaks
        truth["notes"] = json.dumps(extra) + (" " + NOTES_EXTRA[name] if name in NOTES_EXTRA else "")
        write_case(root, SPLIT, case_id, inp, truth, csv)
        print(SPLIT, case_id, kind, len(peaks), "peaks")


if __name__ == "__main__":
    main()
