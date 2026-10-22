"""Build held-out interpretation cases (int-*) for the RamanLens test set from open experimental datasets.

Interpretation cases test what a senior Raman researcher adds once the material is known: reading a series
(thickness, temperature, excitation energy) and stating caveats. This script cuts spectra out of the open
datasets in data/raw/spectra/ and writes input.json, spectrum_<label>.csv and rubric.json per case.

Input:
    The repository root (argument). Reads Zenodo 15048152 text files (CrSBr, Wdowik et al. 2025) and the
    Southampton xlsx files D0371 (WS2, McDonnell et al. 2018) and D1747 (MoSe2 and WSe2 monolayers).
Process:
    Selects columns (layer numbers, temperatures, excitation energies), drops missing points, sorts x ascending,
    maps answer-bearing columns to neutral labels, and writes rubrics whose items paraphrase what the source
    papers state, each with a locator.
Output:
    data/test_set/heldout/int-<material>-<topic>-<nn>/ folders. Existing folders are overwritten.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import openpyxl

HC = 1239.84198  # eV nm


def write_csv(path, x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    order = np.argsort(x)
    x, y = x[order], y[order]
    keep = np.concatenate([[True], np.diff(x) > 0])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("shift_cm1,intensity\n")
        for a, b in zip(x[keep], y[keep]):
            f.write(f"{a:.4f},{b:.6g}\n")
    return int(keep.sum())


def write_case(root, case_id, inp, rubric, spectra):
    d = root / "data" / "test_set" / "heldout" / case_id
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("spectrum_*.csv"):
        old.unlink()
    n = {}
    for fname, (x, y) in spectra.items():
        n[fname] = write_csv(d / fname, x, y)
    inp = {"case_id": case_id, "kind": "interpret", "task": "interpret", **inp}
    rubric = {"case_id": case_id, **rubric}
    (d / "input.json").write_text(json.dumps(inp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (d / "rubric.json").write_text(json.dumps(rubric, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(case_id, len(spectra), "spectra", min(n.values()), "to", max(n.values()), "points")


def load_tab(path):
    hdr = open(path, encoding="latin-1").readline().rstrip("\n").split("\t")
    d = np.genfromtxt(path, skip_header=1, delimiter="\t", missing_values="--", filling_values=np.nan)
    return [h.strip() for h in hdr], d


# ---------------------------------------------------------------- CrSBr (Wdowik et al. 2025)
CRSBR_PAPER = ("Wdowik, Varade, Vejpravova, Legut 2025, 'Magneto-Raman effect in van der Waals layered two-dimensional "
               "CrSBr antiferromagnet', arXiv:2503.15298 (v1)")
CRSBR_DATA = "https://doi.org/10.5281/zenodo.15048152"


def crsbr_cases(root):
    x_dir = root / "data" / "raw" / "spectra" / "CrSBr" / "zenodo15048152" / "x"

    # (a) thickness series, Figure3.txt
    hdr, d = load_tab(x_dir / "Figure3.txt")
    cols = {h.replace("Raman Int", "").strip(): j for j, h in enumerate(hdr) if j > 0}
    mapping = {"A": "3L", "B": "Bulk", "C": "1L", "D": "6L", "E": "2L", "F": "5L"}
    spectra, entries = {}, []
    for lab, layer in mapping.items():
        fn = f"spectrum_{lab}.csv"
        spectra[fn] = (d[:, 0], d[:, cols[layer]])
        entries.append({"file": fn, "label": f"flake {lab}",
                        "conditions": {"laser_nm": 532, "temperature_K": 295, "power_uW": 200}})
    order = sorted(mapping, key=lambda k: ["1L", "2L", "3L", "5L", "6L", "Bulk"].index(mapping[k]))
    inp = {
        "material": "CrSBr",
        "spectra": entries,
        "context": ("Six mechanically exfoliated CrSBr flakes from the same CVT-grown crystal, transferred onto a marked "
                    "substrate. Room temperature, ambient, backscattering, 532 nm, 200 uW, WITec spectrometer with an "
                    "1800 l/mm grating. Same settings for all six flakes. AFM has not been analysed yet."),
        "question": ("How do these six spectra differ and what can you say about the thickness of each flake? Rank them "
                     "if you can. Anything I should be careful about?"),
    }
    rubric = {
        "source": {"paper": CRSBR_PAPER, "dataset": CRSBR_DATA + " (Figure3.txt)",
                   "locator": "Fig. 3 and its discussion (p. 4); Table A3 'Present exp.' column; Fig. A1"},
        "items": [
            {"id": "f1", "kind": "finding", "weight": 1,
             "text": ("Identifies the three strong Ag modes (Ag1 near 104 to 114 cm-1, Ag2 near 238 to 245 cm-1, Ag3 near "
                      "341 to 343 cm-1) in the spectra, and notes Ag1 and Ag2 are much weaker than Ag3"),
             "locator": "p. 3 to 4 ('three strong Ag modes'; 'Ag1 and Ag2 phonons have much lower intensities than the "
                        "mode of Ag3', cf. Fig. 3); Table A3"},
            {"id": "f2", "kind": "finding", "weight": 2,
             "text": ("Ag1 and Ag2 blueshift (move to higher frequency) with increasing number of layers, so the flakes "
                      "with higher Ag1/Ag2 frequencies are thicker"),
             "locator": "p. 4: 'clearly show a blueshift of the peaks arising from the Ag1 and Ag2 phonons with an "
                        "increasing number of layers'; Fig. 9 discussion: redshift with decreasing layer number"},
            {"id": "c1", "kind": "caveat", "weight": 1,
             "text": "Ag3 barely shifts with thickness, so it is not a useful layer-number indicator",
             "locator": "p. 4: 'such a shift is hardly observed for the peak related to the Ag3 mode'"},
            {"id": "n1", "kind": "quantitative", "weight": 2,
             "text": ("Ranks the flakes from thinnest to thickest as " + " < ".join(f"flake {k}" for k in order)
                      + " (layer numbers 1L, 2L, 3L, 5L, 6L, bulk >70L); adjacent thick flakes (5L vs 6L) may be "
                        "ranked as indistinguishable without penalty"),
             "locator": "Fig. 3 trace labels; layer numbers from AFM (Fig. A1)"},
            {"id": "n2", "kind": "quantitative", "weight": 2,
             "text": (f"Identifies flake {order[0]} as a monolayer (Ag1 near 104, Ag2 near 238 cm-1) and flake "
                      f"{order[-1]} as bulk-like (near 114, 244, 343 cm-1)"),
             "locator": "Table A3, 'Present exp.' ML and bulk columns"},
            {"id": "c2", "kind": "caveat", "weight": 1,
             "text": ("CrSBr Raman intensities depend strongly on the crystal axis orientation relative to a linear laser "
                      "polarization, so absolute or relative peak intensities are not a reliable thickness measure "
                      "unless orientation is controlled"),
             "locator": "p. 4: 'A strong axial dependence of the intensities of Raman peaks measured in the linear "
                        "polarization mode [13]' (ref. 13 = Telford et al., Adv. Mater. 32, 2003240, 2020)"},
            {"id": "q1", "kind": "question", "weight": 1,
             "text": ("Asks for an independent thickness measurement (AFM step height; about 0.8 nm per layer) or the "
                      "laser polarization and flake orientation, to confirm the Raman-based ranking"),
             "locator": "Fig. A1 caption: layer number estimated from AFM with 1L about 0.8 nm"},
        ],
        "wrong_claims": [
            {"id": "w1", "penalty": 1, "text": "Uses the Ag3 position as the main thickness indicator"},
            {"id": "w2", "penalty": 1, "text": "States that Ag1/Ag2 soften (move to lower frequency) as the flakes get thicker"},
        ],
        "notes": ("Label map (answer key): " + ", ".join(f"flake {k} = {v}" for k, v in mapping.items())
                  + ". The paper states the trend qualitatively and gives positions only for ML and bulk (Table A3: Ag "
                    "104/238/341 cm-1 ML, 114/244/343 cm-1 bulk). Sampling is about 1.2 cm-1 per point. Linear "
                    "polarization state and substrate of Fig. 3 are not stated in the paper. A feature near 302 cm-1 in "
                    "thin flakes is not assigned by the paper and is not in the rubric."),
    }
    write_case(root, "int-CrSBr-thickness-01", inp, rubric, spectra)

    # (b) monolayer temperature series, Figure5-1L.txt
    hdr, d = load_tab(x_dir / "Figure5-1L.txt")
    spectra, entries = {}, []
    for j, h in enumerate(hdr):
        if j == 0:
            continue
        T = int(h.replace("Raman Int", "").replace("K", "").strip())
        fn = f"spectrum_{T}K.csv"
        spectra[fn] = (d[:, 0], d[:, j])
        entries.append({"file": fn, "label": f"{T} K",
                        "conditions": {"laser_nm": 532, "temperature_K": T,
                                       "polarization": "circular, crossed (sigma+ in / sigma- out)"}})
    inp = {
        "material": "CrSBr",
        "spectra": entries,
        "context": ("Monolayer CrSBr (thickness confirmed by AFM), exfoliated from a CVT crystal. Low-temperature confocal "
                    "Raman insert in a PPMS, backscattering, 532 nm, 100x objective (NA 0.82), circularly polarized "
                    "excitation with crossed circular detection. Spectra recorded on cooling from 300 K after the "
                    "temperature stabilized. Window starts at about 150 cm-1. A few points are missing in some traces."),
        "question": ("What changes in the spectrum as the monolayer is cooled, and what does it tell you about the "
                     "material? Anything I should be careful about?"),
    }
    rubric = {
        "source": {"paper": CRSBR_PAPER, "dataset": CRSBR_DATA + " (Figure5-1L.txt)",
                   "locator": "Fig. 5 and p. 5 discussion; Fig. 4(e)-(f)"},
        "items": [
            {"id": "f1", "kind": "finding", "weight": 2,
             "text": ("At low temperature additional features appear: a shoulder on the low-frequency side of Ag2 near "
                      "220 cm-1 (making Ag2 asymmetric) and a peak near 355 cm-1 on the high-frequency side of Ag3"),
             "locator": "p. 5: 'The shoulder of the Ag2 peak ... is located at about 220 cm-1. The second additional peak at "
                        "about 355 cm-1 which is adjacent to the Ag3 peak'; Fig. 5"},
            {"id": "f2", "kind": "finding", "weight": 2,
             "text": ("The extra features are present only below the Neel temperature (paper: TN about 116 K for these "
                      "samples, about 132 K in the literature): clear at 4 K, weak at 80 K, absent at 150 K and 300 K; they are "
                      "linked to the onset of magnetic order (spin-phonon coupling)"),
             "locator": "p. 5: 'these phonon modes emerge in the spectra only below the Neel temperature of CrSBr (TN about "
                        "116 K)'; abstract; intro (TN about 132 K, ref. 13)"},
            {"id": "f3", "kind": "finding", "weight": 1,
             "text": "Assigns the extra peak near 355 cm-1 to a B3g-symmetry mode (not seen at room temperature)",
             "locator": "p. 5: 'can be assigned to the mode of the B3g symmetry'"},
            {"id": "f4", "kind": "finding", "weight": 1,
             "text": ("From 300 K down to TN, Ag2 and Ag3 shift to higher frequency and narrow (equivalently: above TN "
                      "the Raman shifts decrease and the peaks broaden with increasing temperature, Ag2 broadening more "
                      "than Ag3)"),
             "locator": "p. 5: 'Above TN, a decrease in the Raman shifts of both modes is assisted by their significant "
                        "broadening ... FWHM of the Ag2 phonon exceeding that for the Ag3 one'; Fig. 4(e)-(f)"},
            {"id": "c1", "kind": "caveat", "weight": 1,
             "text": ("Temperature-driven shifts and broadening alone can come from anharmonicity and multiphonon "
                      "processes, so they are not by themselves evidence of magnetic order; the appearance of new modes "
                      "below TN is the magnetic signature"),
             "locator": "p. 5: broadening 'likely to be due to enhancement in multiphonon processes and phonon "
                        "anharmonicity'; 'shifts ... upon temperature due to other reasons, e.g., anharmonicity [50, 51]'"},
            {"id": "c2", "kind": "caveat", "weight": 1,
             "text": ("Peak intensities depend on the circular polarization configuration (parallel vs crossed, sigma+ "
                      "vs sigma-), so comparisons should be made in one fixed configuration"),
             "locator": "p. 4 to 5, Fig. 4: intensities 'remain sensitive to the right (+) and/or left (-) circular "
                        "polarizations'"},
            {"id": "q1", "kind": "question", "weight": 1,
             "text": ("Asks for finer temperature steps (around TN and below about 25 K) to locate the transition and a "
                      "possible low-temperature phase, or for a thicker/bulk reference measured the same way"),
             "locator": "p. 5: distinct regimes above TN, from about 25 K to TN, and a low-temperature phase near 25 K; "
                        "extra modes absent in bulk"},
        ],
        "wrong_claims": [
            {"id": "w1", "penalty": 1, "text": "Claims the extra peaks near 220 and 355 cm-1 are present at 150 K or 300 K"},
            {"id": "w2", "penalty": 1, "text": "Claims Ag2/Ag3 soften (shift to lower frequency) on cooling from 300 K"},
        ],
        "notes": ("Spectra from Fig. 5 (1L, crossed +/- circular). The 1L traces in the dataset appear background "
                  "subtracted (near-zero baseline) and are noisy; points stored as '--' in the source file were dropped. "
                  "The paper gives the Ag2 shoulder and B3g positions as approximate values; TN is stated as about 116 K "
                  "in the Fig. 5 discussion and about 132 K in the introduction (literature). The 25 K low-temperature "
                  "phase cannot be resolved from four temperatures and is only a question item."),
    }
    write_case(root, "int-CrSBr-temperature-01", inp, rubric, spectra)

    # (c) thick-flake control: 6L vs >70L at 4 K and 300 K
    spectra, entries = {}, []
    flake_map = {"A": "70L", "B": "6L"}
    for lab, layer in flake_map.items():
        hdr, d = load_tab(x_dir / f"Figure5-{layer}.txt")
        for j, h in enumerate(hdr):
            if j == 0:
                continue
            T = int(h.replace("Raman Int", "").replace("K", "").strip())
            if T not in (4, 300):
                continue
            fn = f"spectrum_{lab}_{T}K.csv"
            spectra[fn] = (d[:, 0], d[:, j])
            entries.append({"file": fn, "label": f"flake {lab}, {T} K",
                            "conditions": {"laser_nm": 532, "temperature_K": T,
                                           "polarization": "circular, crossed (sigma+ in / sigma- out)"}})
    inp = {
        "material": "CrSBr",
        "spectra": entries,
        "context": ("Two exfoliated CrSBr flakes of different thickness from the same crystal (AFM not yet analysed). "
                    "Both measured in a low-temperature confocal Raman insert in a PPMS, backscattering, 532 nm, circularly "
                    "polarized excitation with crossed circular detection, at 300 K and again at 4 K after cooling. "
                    "Window starts at about 150 cm-1. The two flakes' files were exported with different processing."),
        "question": ("Compare the two flakes at 4 K and 300 K. What differs between them, and what does it tell you about "
                     "each flake? Anything I should be careful about?"),
    }
    rubric = {
        "source": {"paper": CRSBR_PAPER, "dataset": CRSBR_DATA + " (Figure5-6L.txt, Figure5-70L.txt)",
                   "locator": "Fig. 5 and p. 5 discussion; Fig. 9 discussion (p. 6); Summary"},
        "items": [
            {"id": "f1", "kind": "finding", "weight": 2,
             "text": ("At 4 K flake B shows additional features absent at 300 K (an Ag2 low-frequency shoulder near "
                      "220 cm-1 and a peak near 355 cm-1 next to Ag3), while flake A shows no such extra peaks at 4 K"),
             "locator": "p. 5, Fig. 5: extra modes 'appear only in the 1L to 6L layers of CrSBr, and they are absent in "
                        "the bulk system'"},
            {"id": "f2", "kind": "finding", "weight": 2,
             "text": ("Concludes flake B is few-layer (paper: 1 to 6 layers) and flake A is thick / bulk-like, because "
                      "the magnetic-order-related extra modes below TN are reported only for few-layer CrSBr"),
             "locator": "p. 5; Summary: 'additional phonon peaks emerging below the Neel temperature ... only for 1-6 "
                        "layers of CrSBr, but they are absent in its bulk form'"},
            {"id": "f3", "kind": "finding", "weight": 1,
             "text": "Links the extra low-temperature features to magnetic ordering below TN (about 116 to 132 K) and spin-phonon coupling",
             "locator": "p. 5; abstract"},
            {"id": "n1", "kind": "quantitative", "weight": 1,
             "text": ("Notes that Ag2 (and Ag3) sit at slightly lower frequency in flake B than in flake A at 4 K, "
                      "consistent with the redshift with decreasing layer number"),
             "locator": "p. 6, Fig. 9 discussion: 'redshift of the Ag2 and Ag3 phonon frequencies with a decreasing number "
                        "of layers'; p. 4, Fig. 3"},
            {"id": "f4", "kind": "finding", "weight": 1,
             "text": "In both flakes Ag2 and Ag3 shift to higher frequency on cooling from 300 K to 4 K",
             "locator": "p. 5 and Summary: above TN the Raman shifts decrease with increasing temperature; Fig. 5"},
            {"id": "c1", "kind": "caveat", "weight": 1,
             "text": ("Absolute intensities and baselines are not comparable between the two flakes (different "
                      "thickness, optical interference, different export processing), so thickness should not be judged "
                      "from intensity"),
             "locator": "textbook: thin-film interference changes Raman intensity with thickness and substrate (Yoon et "
                        "al. 2009, Phys. Rev. B 80, 125422); dataset: 6L traces background subtracted, 70L traces raw counts"},
            {"id": "q1", "kind": "question", "weight": 1,
             "text": "Asks for an AFM thickness of both flakes, or for intermediate temperatures around TN, to confirm",
             "locator": "Fig. A1 (AFM thickness); Fig. 5 (temperature series)"},
        ],
        "wrong_claims": [
            {"id": "w1", "penalty": 1, "text": "Claims flake A (the thick flake) shows the low-temperature extra modes"},
            {"id": "w2", "penalty": 1, "text": "Concludes flake A is the thinner flake"},
        ],
        "notes": ("Label map (answer key): flake A = bulk (>70L, Figure5-70L.txt), flake B = 6L (Figure5-6L.txt), both "
                  "from the paper's Fig. 5 (crossed +/- circular). The 6L traces are background subtracted in the dataset, "
                  "the 70L traces are raw counts on a baseline near 2000; the context says only that processing differs. "
                  "The 80 K and 150 K columns are left out to keep the case a two-temperature contrast."),
    }
    write_case(root, "int-CrSBr-temperature-02", inp, rubric, spectra)


# ---------------------------------------------------------------- WS2 (McDonnell et al. 2018)
WS2_PAPER = ("McDonnell, Huang, Cui, Hewak, Smith 2018, 'Probing Excitons, Trions and Dark Excitons in Monolayer WS2 "
             "using Resonance Raman Spectroscopy', Nano Lett. 18, 1428, doi:10.1021/acs.nanolett.7b05184 (author "
             "manuscript in the dataset record)")
WS2_DATA = "https://doi.org/10.5258/SOTON/D0371 (RRS_Spectra.xlsx)"


def ws2_sheets(wb, T):
    names = {w.title.strip(): w.title for w in wb.worksheets}
    def arr(name):
        return np.array([[c if isinstance(c, (int, float)) else np.nan for c in r]
                         for r in wb[names[name]].iter_rows(values_only=True)], float)
    X, Y = arr(f"{T} Shift"), arr(f"{T} Intensity")
    W = [c for c in next(wb[names[f"{T} WL"]].iter_rows(values_only=True)) if c]
    return X, Y, W


def pick(W_nm, targets_eV):
    E = HC / np.asarray(W_nm, float)
    idx = []
    for t in targets_eV:
        i = int(np.argmin(np.abs(E - t)))
        if i not in idx:
            idx.append(i)
    return idx


def ws2_cases(root):
    wb = openpyxl.load_workbook(root / "data/raw/spectra/WS2/soton_D0371_eprint416765/RRS_Spectra.xlsx",
                                read_only=True, data_only=True)
    # (a) resonance series at 4 K
    X, Y, W = ws2_sheets(wb, "4K")
    targets = [2.142, 2.119, 2.096, 2.082, 2.070, 2.062, 2.048, 2.040, 2.028, 2.006, 1.978, 1.942]
    spectra, entries = {}, []
    for k, i in enumerate(sorted(pick(W, targets), key=lambda i: -W[i])):
        nm = float(W[i])
        fn = f"spectrum_{nm:.2f}nm.csv"
        spectra[fn] = (X[:, i], Y[:, i])
        entries.append({"file": fn, "label": f"{nm:.2f} nm excitation",
                        "conditions": {"laser_nm": round(nm, 2), "laser_eV": round(HC / nm, 4), "temperature_K": 4,
                                       "power_mW": 0.7}})
    inp = {
        "material": "WS2",
        "spectra": entries,
        "context": ("CVD-grown WS2 flake on 290 nm SiO2/Si, all spectra on the same spot, 4 K, tunable CW dye laser, "
                    "backscattering, 50x NA 0.55 objective, parallel linear polarization in and out, 0.7 mW. Intensities "
                    "corrected for spectrometer efficiency only. Same acquisition settings for every excitation wavelength."),
        "question": ("How does the spectrum change with excitation wavelength, and what does that tell you about this "
                     "flake and its electronic states? Anything I should be careful about?"),
    }
    rubric = {
        "source": {"paper": WS2_PAPER, "dataset": WS2_DATA + ", sheets '4K Shift/Intensity/WL'",
                   "locator": "Fig. 1a, Figs. 2, 4, 5, 6, Table 1, main text"},
        "items": [
            {"id": "f1", "kind": "finding", "weight": 1,
             "text": ("Assigns the main peaks: E' near 356 cm-1 and A1' near 417 cm-1 (single phonon), defect-activated LA "
                      "near 174 cm-1, 2ZA near 294 cm-1, 2LA near 349 cm-1 (overlapping E'), a broad unassigned feature "
                      "near 479 to 485 cm-1, and the Si substrate peak at 520 cm-1 on a luminescence background"),
             "locator": "Fig. 1a and text ('defect activated LA ... 174, 2ZA ... 294, 2LA ... 349, E' ... 356, A1' ... "
                        "417 ... new peak ... 479 cm-1')"},
            {"id": "n1", "kind": "quantitative", "weight": 1,
             "text": "Uses the A1'-E' separation (about 61 cm-1) to identify the flake as a monolayer",
             "locator": "Methods paragraph: 'difference in Raman shift of A1' and E' peaks of 61.1 cm-1' (with AFM 0.72 nm)"},
            {"id": "f2", "kind": "finding", "weight": 1,
             "text": "Peak positions and widths do not change with excitation energy; only the intensities change (resonance)",
             "locator": "text: 'the center energy and linewidth were independent of excitation energy'"},
            {"id": "f3", "kind": "finding", "weight": 2,
             "text": ("The A1' intensity is strongly resonant near 2.05 to 2.12 eV (about 585 to 605 nm) and the profile "
                      "has structure, with two maxima separated by roughly the phonon energy, explained as incoming and "
                      "outgoing resonance with the A exciton"),
             "locator": "Fig. 2 (4 K profile), Fig. 4a: 'two main peaks ... explained by incoming and outgoing resonances "
                        "with a single bright excitation'"},
            {"id": "f4", "kind": "finding", "weight": 2,
             "text": ("A low-energy tail of the resonance requires a second bright state: the trion, about 26 meV below "
                      "the exciton (exciton about 2.064 eV, trion about 2.038 eV at 4 K), with exciton-trion scattering"),
             "locator": "Fig. 4c, text: 'upper and lower energy resonances, at 2.064 and 2.038 eV, are the A exciton and "
                        "the A exciton based trion ... separation ... 26 meV'"},
            {"id": "f5", "kind": "finding", "weight": 1,
             "text": ("Different peaks have different resonance profiles (e.g. 2ZA has much less weight at lower "
                      "excitation energy than A1'), reflecting different exciton/trion channel weights; the two-phonon "
                      "and defect peaks involve large-wavevector dark states"),
             "locator": "Fig. 6, Table 1, text on two-phonon peaks"},
            {"id": "c1", "kind": "caveat", "weight": 1,
             "text": ("Comparing intensities across excitation wavelengths needs correction for thin-film interference "
                      "on SiO2/Si (paper uses micro-reflectivity) in addition to spectrometer response; these spectra are "
                      "not interference corrected"),
             "locator": "Methods: 'microreflectivity experiments ... substrate related optical interference effects ... "
                        "corrected'; dataset readme: 'corrections for REF not applied to this data'"},
            {"id": "c2", "kind": "caveat", "weight": 1,
             "text": ("Near resonance a broad photoluminescence background sits under the Raman peaks and must be "
                      "modelled (e.g. a polynomial background) when fitting"),
             "locator": "Fig. 1a caption ('superposed on luminescence'); fitting with 'a quadratic background, to account "
                        "for the luminescence'"},
            {"id": "q1", "kind": "question", "weight": 1,
             "text": ("Asks whether the power is in the linear regime and free of laser heating (e.g. power series, "
                      "Stokes/anti-Stokes ratio)"),
             "locator": "Methods: power dependence measured, 0.7 mW in the linear regime; heating checked with "
                        "Stokes/anti-Stokes ratio"},
        ],
        "wrong_claims": [
            {"id": "w1", "penalty": 1, "text": "Claims the A1' or E' frequency shifts (disperses) with excitation wavelength"},
            {"id": "w2", "penalty": 1, "text": "Assigns the broad feature near 479 to 485 cm-1 to a first-order single-phonon mode"},
            {"id": "w3", "penalty": 1, "text": "Attributes the intensity changes to thickness or sample changes between spectra"},
        ],
        "notes": ("Twelve 4 K excitation energies spanning about 1.94 to 2.14 eV. Energies quoted in the paper come from "
                  "fits to interference-corrected profiles; in these uncorrected data the A1' maxima still fall near the "
                  "incoming and outgoing A-exciton resonances. The paper's unassigned peak is quoted as 479 cm-1 in the "
                  "text and 485 cm-1 in the abstract."),
    }
    write_case(root, "int-WS2-resonance-01", inp, rubric, spectra)

    # (b) temperature: 4, 150, 295 K at four excitation energies each
    spectra, entries = {}, []
    for T, Tk in (("4K", 4), ("150K", 150), ("295K", 295)):
        X, Y, W = ws2_sheets(wb, T)
        for i in pick(W, [2.11, 2.07, 2.03, 1.99]):
            nm = float(W[i])
            fn = f"spectrum_{Tk}K_{nm:.1f}nm.csv"
            spectra[fn] = (X[:, i], Y[:, i])
            entries.append({"file": fn, "label": f"{Tk} K, {nm:.1f} nm",
                            "conditions": {"laser_nm": round(nm, 2), "laser_eV": round(HC / nm, 4), "temperature_K": Tk,
                                           "power_mW": 0.7}})
    inp = {
        "material": "WS2",
        "spectra": entries,
        "context": ("CVD-grown WS2 flake on 290 nm SiO2/Si, same spot throughout. Tunable CW dye laser, backscattering, "
                    "parallel linear polarization, 0.7 mW, at three temperatures with four excitation wavelengths each. "
                    "Intensities corrected for spectrometer efficiency only."),
        "question": ("How do the spectra change with temperature, and what does that tell you? Anything I should be "
                     "careful about when comparing temperatures?"),
    }
    rubric = {
        "source": {"paper": WS2_PAPER, "dataset": WS2_DATA + ", sheets 4K, 150K, 295K",
                   "locator": "Fig. 2, Fig. 5, main text"},
        "items": [
            {"id": "f1", "kind": "finding", "weight": 2,
             "text": ("The Raman intensity (A1' in particular) increases strongly on cooling, by roughly an order of "
                      "magnitude at 4 K relative to 295 K"),
             "locator": "text after Fig. 1: 'As the temperature decreases the Raman intensity increases significantly, by "
                        "approximately a factor of ten at 4K'"},
            {"id": "f2", "kind": "finding", "weight": 2,
             "text": ("The excitation energy of maximum enhancement moves to higher energy on cooling (room-temperature "
                      "resonance a single peak near 2.02 eV; at 4 K higher and structured), following the exciton energy "
                      "that decreases with increasing temperature"),
             "locator": "Fig. 2 text: 'at room temperature the resonance has the form of a single peak centered at 2.02eV ... "
                        "the central energy of the resonance increases'; Fig. 5b"},
            {"id": "f3", "kind": "finding", "weight": 1,
             "text": ("At low temperature the resonance develops structure (exciton plus trion channels, incoming and "
                      "outgoing resonances), whereas at room temperature it is one broad peak"),
             "locator": "Fig. 2; Figs. 4 to 5"},
            {"id": "f4", "kind": "finding", "weight": 1,
             "text": ("The trion contribution weakens much faster with temperature than the exciton one (trion-trion "
                      "amplitude down about 22 times from 4 K to 295 K, exciton-exciton about 40 percent)"),
             "locator": "Fig. 5a and text"},
            {"id": "c1", "kind": "caveat", "weight": 2,
             "text": ("Comparing temperatures at one fixed laser wavelength mixes the intensity change with the shift of "
                      "the resonance; a proper comparison needs the full excitation profile at each temperature"),
             "locator": "Fig. 2 (resonance center moves with temperature); follows from the resonance-profile method of the paper"},
            {"id": "c2", "kind": "caveat", "weight": 1,
             "text": ("Thin-film interference on SiO2/Si and its temperature dependence should be corrected (paper: "
                      "micro-reflectivity at each temperature); these spectra are not interference corrected"),
             "locator": "Methods; dataset readme ('corrections for REF not applied')"},
            {"id": "q1", "kind": "question", "weight": 1,
             "text": "Asks how the actual sample temperature / absence of laser heating was verified (e.g. Stokes/anti-Stokes ratio)",
             "locator": "Methods: 'absence of laser induced sample heating was further confirmed using measurements of the "
                        "Stokes/Anti-Stokes ratio'"},
        ],
        "wrong_claims": [
            {"id": "w1", "penalty": 1,
             "text": ("Attributes the order-of-magnitude intensity increase on cooling to the Bose-Einstein (n+1) "
                      "factor (which changes the Stokes intensity of a 417 cm-1 mode by only about 15 percent between 295 "
                      "K and 4 K)")},
            {"id": "w2", "penalty": 1, "text": "Claims the resonance moves to lower excitation energy on cooling"},
        ],
        "notes": ("Twelve spectra: 4, 150, 295 K, each at the dataset excitation energies closest to 2.11, 2.07, 2.03 and "
                  "1.99 eV. The factor of ten is the paper's value for interference-corrected profiles; in these uncorrected "
                  "data the peak A1' height is also about ten times larger at 4 K than at 295 K. The Bose factor in w1 is a "
                  "textbook Stokes population factor (Cardona, Light Scattering in Solids I, 1983)."),
    }
    write_case(root, "int-WS2-temperature-01", inp, rubric, spectra)


# ---------------------------------------------------------------- MoSe2 / WSe2 monolayers (McDonnell 2020, Viner 2021)
MCD2020 = ("McDonnell, Viner, Rivera, Xu, Smith 2020, 'Direct Observation of Intravalley Phonon Scattering of 2s Excitons "
           "in MoSe2 and WSe2 Monolayers', arXiv:2006.05912 (published 2D Mater. 2020)")
VINER = ("Viner, McDonnell, Ruiz-Tijerina, Rivera, Xu, Fal'ko, Smith 2021, 'Excited Rydberg States in TMD "
         "Heterostructures', 2D Mater. 8, 035047, arXiv:2103.09004")
D1747 = "https://doi.org/10.5258/SOTON/D1747"


def read_d1747(path, sheet):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb[sheet].iter_rows(values_only=True))
    out = []
    for c in range(0, len(rows[0]), 3):
        e = rows[0][c + 1] if c + 1 < len(rows[0]) else None
        if not isinstance(e, (int, float)):
            continue
        x, y = [], []
        for r in rows[2:]:
            if c + 1 < len(r) and isinstance(r[c], (int, float)) and isinstance(r[c + 1], (int, float)):
                x.append(r[c]); y.append(r[c + 1])
        out.append((float(e), np.array(x), np.array(y)))
    return out


def nearest(series, targets):
    picked = []
    for t in targets:
        s = min(series, key=lambda s: abs(s[0] - t))
        if s not in picked:
            picked.append(s)
    return picked


def tmd_entry(e, fn, extra=""):
    return {"file": fn, "label": f"{e:.4f} eV excitation{extra}",
            "conditions": {"laser_eV": round(e, 4), "laser_nm": round(HC / e, 2), "temperature_K": 4}}


def mose2_case(root):
    path = root / "data/raw/spectra/MoSe2/soton_449632/MoSe2_Data.xlsx"
    b2s = read_d1747(path, "Processed B2s Data")
    a1s = read_d1747(path, "Processed A1s Data")
    picked = nearest(b2s, [2.124, 2.096, 2.081, 2.069, 2.054, 2.042, 2.020, 2.000, 1.975]) + nearest(a1s, [1.679, 1.648])
    spectra, entries = {}, []
    for e, x, y in sorted(picked, key=lambda s: -s[0]):
        fn = f"spectrum_{e:.4f}eV.csv"
        spectra[fn] = (x, y)
        entries.append(tmd_entry(e, fn))
    inp = {
        "material": "MoSe2",
        "spectra": entries,
        "context": ("Exfoliated monolayer MoSe2 encapsulated in hBN on 290 nm SiO2/Si, 4 K, below 100 uW, tunable CW "
                    "lasers (Ti:sapphire and dye), triple spectrometer. Each spectrum is parallel minus crossed linear "
                    "polarization (to remove luminescence), corrected for thin-film interference and calibrated to "
                    "absolute scattering probability (x1e8) using the Si 520 cm-1 peak."),
        "question": ("Here is the monolayer at a set of excitation energies. What changes across the series, which "
                     "electronic states are being probed, and what do the peaks tell you? Anything I should be careful about?"),
    }
    rubric = {
        "source": {"paper": MCD2020 + "; " + VINER, "dataset": D1747 + " (MoSe2_Data.xlsx, sheets 'Processed B2s Data', "
                                                                       "'Processed A1s Data')",
                   "locator": "McDonnell 2020: Figs. 1 to 3, Table 1, p. 9 to 10; Viner 2021: p. 3, Table 1, SI S4"},
        "items": [
            {"id": "f1", "kind": "finding", "weight": 1,
             "text": "Identifies the A1'(Gamma) single-phonon peak near 241 cm-1 as the main first-order peak",
             "locator": "McDonnell 2020 p. 5: 'the 241.0 cm-1 peak in MoSe2 is also due to single A1'(Gamma) phonon scattering'"},
            {"id": "f2", "kind": "finding", "weight": 2,
             "text": ("Three peaks near 480, 531 and 583 cm-1 are the strongest features after the one-phonon peak in the "
                      "2.0 to 2.1 eV spectra but are not observed at the A1s resonance (near 1.65 eV, where other "
                      "multiphonon features at different positions occur); they are specific to the 2s (Rydberg) resonances"),
             "locator": "McDonnell 2020 p. 9: 'three Raman peaks at 480, 531 and 583 cm-1 ... observed at the A2s/B1s and "
                        "B2s resonances but not the A1s resonance'; Viner 2021 p. 3"},
            {"id": "f3", "kind": "finding", "weight": 2,
             "text": ("The higher-energy spectra are resonant with the B2s exciton (about 2.016 eV); the 2s-specific peaks "
                      "show incoming and outgoing resonances with it"),
             "locator": "McDonnell 2020 Table 1 (B2s 2016 meV); Viner 2021 Table 1, SI S4 and Table S2"},
            {"id": "f4", "kind": "finding", "weight": 1,
             "text": ("The 480/531/583 cm-1 peaks match combinations of Gamma-point phonons (2E', A1'+E', 2A1') and are "
                      "interpreted as intravalley scattering between Rydberg exciton states"),
             "locator": "McDonnell 2020 p. 9 to 10"},
            {"id": "n1", "kind": "quantitative", "weight": 1,
             "text": ("Places the low-energy spectra at the A1s exciton (about 1.648 eV) and notes the large drop in "
                      "absolute scattering at the 2s resonance relative to 1s (roughly two orders of magnitude)"),
             "locator": "McDonnell 2020 Table 1 (A1s 1648 meV); Viner 2021 p. 3: scattering at 1s resonances 'approximately "
                        "two orders of magnitude stronger than at the A2s and B2s'"},
            {"id": "c1", "kind": "caveat", "weight": 1,
             "text": ("The spectra are parallel minus crossed: depolarized features are removed and residual background or "
                      "negative values can remain where luminescence is strong"),
             "locator": "Viner 2021 SI S2 (subtraction, residual background when luminescence is strong); McDonnell 2020 Methods"},
            {"id": "c2", "kind": "caveat", "weight": 1,
             "text": ("Many weaker peaks are multi-phonon or defect-allowed with several possible assignments; only the "
                      "A1' peak has a firm single-phonon assignment"),
             "locator": "McDonnell 2020 p. 4 to 5 ('multiple possible assignments for most of these peaks')"},
            {"id": "q1", "kind": "question", "weight": 1,
             "text": ("Asks for (or recommends) finer excitation steps through the resonance, or reflectivity on the same "
                      "spot, to fit the resonance profile and pin the exciton energy"),
             "locator": "McDonnell 2020: resonance-profile fits and reflectivity at the same location (p. 3, Table 1)"},
        ],
        "wrong_claims": [
            {"id": "w1", "penalty": 1, "text": "Assigns the 480/531/583 cm-1 peaks to the substrate (Si or hBN)"},
            {"id": "w2", "penalty": 1, "text": "Claims the 480/531/583 cm-1 peaks are equally present at the A1s resonance"},
        ],
        "notes": ("Nine spectra from the B2s sheet (about 1.97 to 2.12 eV) and two from the A1s sheet (about 1.648 and "
                  "1.679 eV). Peak values: 480, 531, 583 cm-1 (McDonnell 2020) quoted as 480, 530, 580 cm-1 in Viner "
                  "2021. Both papers come from the same group and dataset family; both must be excluded from tool building."),
    }
    write_case(root, "int-MoSe2-resonance-01", inp, rubric, spectra)


def wse2_case(root):
    path = root / "data/raw/spectra/WSe2/soton_449632/WSe2_Data.xlsx"
    a2s = read_d1747(path, "Processed A2s Data")
    picked = nearest(a2s, [1.8432, 1.8703, 1.8847, 1.8999, 1.9115, 1.9258, 1.9325, 1.9409, 1.9564])
    spectra, entries = {}, []
    for e, x, y in sorted(picked, key=lambda s: -s[0]):
        fn = f"spectrum_{e:.4f}eV.csv"
        spectra[fn] = (x, y)
        entries.append(tmd_entry(e, fn))
    inp = {
        "material": "WSe2",
        "spectra": entries,
        "context": ("Exfoliated monolayer WSe2 encapsulated in hBN on 290 nm SiO2/Si, 4 K, below 100 uW, tunable CW dye "
                    "laser, triple spectrometer, excitation stepped in a few meV. Each spectrum is parallel minus crossed "
                    "linear polarization, interference corrected and calibrated to absolute scattering probability (x1e8) "
                    "using the Si 520 cm-1 peak. The A1s exciton of this sample is at about 1.740 eV."),
        "question": ("What happens across this excitation series, especially in the 480 to 510 cm-1 region, and what "
                     "does it tell you about the excitonic states? Anything I should be careful about?"),
    }
    rubric = {
        "source": {"paper": MCD2020 + "; " + VINER, "dataset": D1747 + " (WSe2_Data.xlsx, sheet 'Processed A2s Data')",
                   "locator": "McDonnell 2020: Fig. 4, p. 10 to 11, Table 1; Viner 2021: p. 3 to 4, SI S5, Table S3"},
        "items": [
            {"id": "f1", "kind": "finding", "weight": 1,
             "text": ("The A1'/E' peak near 249 to 250 cm-1 is resonantly enhanced twice in the series, at the incoming "
                      "(about 1.87 eV) and outgoing (about 1.90 eV) resonance with the A2s exciton"),
             "locator": "McDonnell 2020 p. 5 (249.3 cm-1 single-phonon peak), Fig. 2d; Viner 2021 SI S5 (both resonances "
                        "clearly visible with similar amplitude)"},
            {"id": "n1", "kind": "quantitative", "weight": 2,
             "text": ("Places the A2s exciton at about 1.871 eV, i.e. about 130 meV above the A1s (1.740 eV)"),
             "locator": "McDonnell 2020 Table 1 (A2s 1871 meV); Viner 2021 SI S5 (A1s-A2s 131 +/- 1 meV)"},
            {"id": "f2", "kind": "finding", "weight": 2,
             "text": ("A peak near 495 cm-1 appears only around the A2s resonance: a single peak at the incoming resonance, "
                      "vanishing just above it, then reappearing about 26 meV higher"),
             "locator": "McDonnell 2020 p. 10 to 11 ('single Raman peak at 495.1 cm-1 at the incident resonance ... at first "
                        "disappears ... returns ... threshold at about 26 meV'); Viner 2021 p. 3 to 4"},
            {"id": "f3", "kind": "finding", "weight": 2,
             "text": ("The 495 cm-1 feature is dispersive: its frequency moves down (by a few cm-1) with increasing "
                      "excitation energy, and near the outgoing resonance (about 1.93 eV) it grows strongly and splits "
                      "into three peaks (about 492.7, 495.9, 499.9 cm-1)"),
             "locator": "McDonnell 2020 Fig. 4 caption; Viner 2021 p. 4 ('disperses to lower shift by 2.5 cm-1 ... splits "
                        "into three closely spaced peaks')"},
            {"id": "f4", "kind": "finding", "weight": 1,
             "text": ("A dispersive peak cannot be a simple zone-centre phonon; it implies dark excitonic states with "
                      "features (minima or saddle points) in their dispersion near the A2s energy"),
             "locator": "McDonnell 2020 p. 11; Viner 2021 SI S5 (saddle point suggestion)"},
            {"id": "c1", "kind": "caveat", "weight": 1,
             "text": ("The spectra are parallel minus crossed; depolarized signals and luminescence are removed, so "
                      "residual background or negative values are processing artifacts, not features"),
             "locator": "Viner 2021 SI S2; McDonnell 2020 Methods"},
            {"id": "c2", "kind": "caveat", "weight": 1,
             "text": ("The peak assignment of the 495 cm-1 feature is open; the papers give no full explanation, so any "
                      "specific phonon assignment is speculative"),
             "locator": "McDonnell 2020 p. 11 ('no theoretical predictions ... available'); Viner 2021 SI S5"},
        ],
        "wrong_claims": [
            {"id": "w1", "penalty": 1, "text": "Treats the 490 to 500 cm-1 feature as a fixed-frequency second-order overtone (2A1') without noting its dispersion"},
            {"id": "w2", "penalty": 1, "text": "Attributes the 490 to 500 cm-1 feature to the Si substrate or hBN"},
        ],
        "notes": ("Nine spectra from the A2s sheet, about 1.843 to 1.956 eV. The A1s energy is given in the context because a "
                  "researcher would know it from PL or reflectivity on the same sample; it is not in these spectra."),
    }
    write_case(root, "int-WSe2-resonance-01", inp, rubric, spectra)


def main():
    ap = argparse.ArgumentParser(description="Build held-out interpretation cases from open datasets.")
    ap.add_argument("root", help="repository root")
    root = Path(ap.parse_args().root)
    crsbr_cases(root)
    ws2_cases(root)
    mose2_case(root)
    wse2_case(root)


if __name__ == "__main__":
    main()
