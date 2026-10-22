"""Build CrSBr test-set candidate cases from Zenodo 15048152 (Wdowik et al. 2025).

Reads the authors' Figure3.txt and Figure5-*.txt exports and writes spectrum.csv, input.json and truth.json
per the data/test_set README schema. Usage: make_crsbr_cases.py <extracted_dir> <candidates_dir>.
"""
import sys, json, os, pandas as pd

src, out = sys.argv[1], sys.argv[2]
PAPER = ("Wdowik, Varade, Vejpravova, Legut 2025, Magneto-Raman effect in van der Waals layered two-dimensional "
         "CrSBr antiferromagnet, arXiv:2503.15298 (preprint v1; journal version not verified)")
DATASET = "https://doi.org/10.5281/zenodo.15048152"
def rd(f):
    d = pd.read_csv(os.path.join(src, f), sep="\t", na_values=["--"], skipinitialspace=True)
    return d.apply(pd.to_numeric, errors="coerce")

def peak(pos, tol, irrep, label):
    return {"position_cm1": pos, "tolerance_cm1": tol, "irrep": irrep, "label": label}

base = dict(material="CrSBr", formula="CrSBr", polytype=None, spacegroup="Pmmn (59)", pointgroup="mmm (D2h)", hint_is_correct=None)
cases = []
f3 = rd("Figure3.txt")
cases.append(dict(n=1, df=f3[[f3.columns[0], f3.columns[1]]], T=300, layers=1, fig="Fig. 3 (1L trace); Table A3 'Present exp.' column (ML: 104, 238, 341)",
    peaks=[peak(104, 6, "Ag", "Ag1"), peak(238, 5, "Ag", "Ag2"), peak(341, 5, "Ag", "Ag3")],
    props={"layers": 1, "magnetic_order": "A-type antiferromagnet below T_N"},
    notes="Room-temperature layer-dependent spectrum, WITec, 532 nm, 200 uW, backscattering; the paper does not state the linear polarization of Fig. 3. Substrate not stated beyond 'marked substrate fabricated using photolithography'. Peak near 302 cm-1 is visible but not assigned in the paper's experimental table, so it is not in the answer key. Temperature stated only as room temperature (300 K used, as in Fig. 4/5 labels).",
    raw="Figure3.txt", cfg=None, pol=None))
cases.append(dict(n=2, df=f3[[f3.columns[0], f3.columns[6]]], T=300, layers=None, fig="Fig. 3 (Bulk trace); Table A3 'Present exp.' column (bulk: 114, 244, 343)",
    peaks=[peak(114, 5, "Ag", "Ag1"), peak(244, 5, "Ag", "Ag2"), peak(343, 5, "Ag", "Ag3")],
    props={"layers": "bulk (>70 layers)", "magnetic_order": "A-type antiferromagnet below T_N"},
    notes="Bulk crystal (>70 layers, AFM thickness), room temperature, WITec, 532 nm. Linear polarization not stated for Fig. 3. Paper states A1g and A2g blueshift with increasing layer number while A3g barely moves.",
    raw="Figure3.txt", cfg=None, pol=None))
for n, f, col, lay, T, kind in [(3, "Figure5-6L.txt", 4, 6, 300, "hi"), (4, "Figure5-6L.txt", 1, 6, 4, "lo"), (5, "Figure5-70L.txt", 1, None, 4, "bulk4")]:
    d = rd(f); d = d[[d.columns[0], d.columns[col]]].dropna()
    peaks = [peak(244 if lay is None else 244, 8, "Ag", "Ag2"), peak(343, 6, "Ag", "Ag3")]
    props = {"layers": lay if lay else "bulk (>70 layers)", "T_N_K_stated": "132 (ref. 13 in paper) and ~116 (this work)"}
    if kind == "lo":
        peaks += [peak(355, 10, "Bg3", "Bg3 (new peak near Ag3)"), peak(220, 10, None, "shoulder of Ag2 (new peak)")]
        props["new_peaks_below_TN"] = True
        note = "Same 6L flake as case 03 but at 4 K, below T_N. Circularly polarized, crossed +/- configuration, 532 nm, attoRAMAN in PPMS. Paper states two additional peaks appear below T_N next to Ag2 (~220 cm-1 shoulder) and Ag3 (~355 cm-1, assigned Bg3), only in 1L-6L and absent in bulk. Spectrum range starts at 151 cm-1 so Ag1 is not covered. Exported trace is baseline-subtracted by the authors (negative values present). Ag2 hardens at low T (peak ~247 cm-1 here)."
    elif kind == "hi":
        props["new_peaks_below_TN"] = False
        note = "Same 6L flake as case 04 but at 300 K, above T_N: no extra peaks near Ag2/Ag3. Circularly polarized, crossed +/-, 532 nm. Range starts at 151 cm-1 (Ag1 not covered). Authors' export is baseline-subtracted (negative values present)."
    else:
        props["new_peaks_below_TN"] = False
        note = "Bulk (>70L) at 4 K, below T_N: the paper states the extra peaks near Ag2 and Ag3 are absent in bulk. Circularly polarized, crossed +/-, 532 nm. Range starts at 151 cm-1. Raw counts with an offset of ~2000 (not baseline-subtracted); two points near 329-331 cm-1 are missing in the export and are dropped."
    cases.append(dict(n=n, df=d, T=T, layers=lay, fig=f"Fig. 5 ({'6L' if lay else '>70L bulk'}, {T} K, crossed +/-); peak description in Sec. III text and Table A3",
        peaks=peaks, props=props, notes=note, raw=f, cfg="crossed circular +/-", pol=None))

for c in cases:
    cid = f"exp-CrSBr-{c['n']:02d}"
    d = os.path.join(out, cid); os.makedirs(d, exist_ok=True)
    df = c["df"].copy(); df.columns = ["shift_cm1", "intensity"]; df = df.dropna()
    df.to_csv(os.path.join(d, "spectrum.csv"), index=False)
    geom = "backscattering, beam along c" + (f"; {c['cfg']}" if c["cfg"] else "")
    json.dump(dict(case_id=cid, kind="single", task="identify", material_hint=None, laser_nm=532, temperature_K=c["T"],
                   substrate=None, geometry=geom, question="Which material is this? Assign the peaks."),
              open(os.path.join(d, "input.json"), "w"), indent=2)
    t = dict(case_id=cid, **base, layers=c["layers"], peaks=c["peaks"], properties=c["props"],
             source=dict(kind="experimental", dataset=DATASET + " (file " + c["raw"] + ")", paper=PAPER, figure=c["fig"], licence="CC BY 4.0"),
             notes=c["notes"])
    json.dump(t, open(os.path.join(d, "truth.json"), "w"), indent=2)
    print(cid, len(df))
