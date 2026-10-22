"""Build exp-WS2-01 (4 K, 599 nm) and exp-WS2-02 (295 K, 614 nm) from the Southampton D0371 workbook; arg: xlsx path."""
import sys, json
sys.path.insert(0, "C:/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/scratch/curate_tmd")
import numpy as np, pandas as pd
from casekit import write_case, contrast
x = pd.ExcelFile(sys.argv[1])
def col(T, c):
    sh = x.parse(f"{T} Shift", header=None).astype(float)[c].values
    it = x.parse(f"{T} Intensity", header=None).astype(float)[c].values
    wl = x.parse(f"{T} WL", header=None).astype(float).iloc[0, c]
    return sh, it, wl
SRC = {"kind": "experimental", "dataset": "doi:10.5258/SOTON/D0371 (University of Southampton ePrints 416765, files RRS_Spectra.xlsx)",
       "paper": "McDonnell, Huang, Cui, Hewak, Smith 2018, Nano Letters 18(3), 1428-1434, doi:10.1021/acs.nanolett.7b05184 (read from the author accepted manuscript, Southampton ePrints 416941)",
       "licence": "CC BY 4.0 (dataset)"}
def peaks(extra_note):
    P = [(349, 3, "2LA(M)", "2LA"), (356, 3, "E'", "E'"), (417, 3, "A1'", "A1'"), (479, 5, "two-phonon E''(LO1)(M)+TA(M), tentative assignment in paper", "2ph")]
    return P
for T, c, cid in (("4K", 9, "exp-WS2-01"), ("295K", 15, "exp-WS2-02")):
    s, y, wl = col(T, c)
    ok = (s >= 100)
    for p in (174, 294, 356, 417, 479, 520):
        print(cid, p, contrast(s[ok], y[ok], p))
    Tn = 4 if T == "4K" else 295
    inp = {"case_id": cid, "kind": "single", "task": "identify", "material_hint": None, "laser_nm": round(float(wl), 2), "temperature_K": Tn,
           "substrate": "290 nm SiO2 on Si", "geometry": "backscattering, beam along c", "question": "Which material is this? Assign the peaks."}
    tr = {"case_id": cid, "material": "WS2", "formula": "WS2", "polytype": None, "spacegroup": None, "pointgroup": None, "hint_is_correct": None, "layers": 1,
          "peaks": [{"position_cm1": p, "tolerance_cm1": t, "irrep": None, "label": l, "pattern": None} for p, t, l, _ in peaks("")],
          "properties": {"layers": 1, "growth": "CVD", "layer_confirmation": "AFM thickness 0.72 nm plus Raman"},
          "source": dict(SRC, figure="Main text, Raman paragraph and Fig. 1a (4 K, 2.07 eV spectrum with six WS2 peaks plus Si 520); peak positions LA 174, 2ZA 294, 2LA 349, E' 356, A1' 417, 479 cm-1"),
          "notes": f"Resonance Raman spectrum, excitation {wl:.2f} nm ({1239.84/wl:.3f} eV), {Tn} K, efficiency-corrected, WS2 PL background present, raw intensities. Positions are those stated for the 4 K 2.07 eV spectrum of Fig. 1a; the paper says peak centres are independent of excitation energy. 2LA(M) (349) and E' (356) overlap and may appear as one band; relative intensities change strongly with excitation energy near resonance. The paper also reports defect-activated LA at 174, 2ZA at 294 and Si 520 (substrate) in the 4 K 2.07 eV spectrum; these are not clearly resolved above noise in this exported column and are deliberately left out of peaks. Paper states 'monolayer'; polytype/space group not stated in the paper so left null."}
    write_case(cid, s, y, inp, tr)
