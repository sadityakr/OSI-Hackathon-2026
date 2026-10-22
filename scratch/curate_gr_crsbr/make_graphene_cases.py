"""Build graphene test-set candidate cases from Zenodo 14883846 (Bukvisova et al., Fig. S1D Raman exports).

Reads the two WITec text exports (graphene grown on Au and Cu), keeps the x/y columns as spectrum.csv and writes
input.json and truth.json per the data/test_set README schema. Usage: make_graphene_cases.py <S1_dir> <candidates_dir>.
"""
import sys, os, json

src, out = sys.argv[1], sys.argv[2]
PAPER = ("Bukvisova, Kalousek, Patocka, Zlamal, Planer, Mahel, Citterberg, Novak, Sikola, Kolibal 2025, Casimir-like effect "
         "driven self-assembly of graphene on molten metals, arXiv:2503.04327 (preprint; journal version not verified)")
def load(f):
    rows = []
    for l in open(os.path.join(src, f)):
        p = l.split()
        try: rows.append((float(p[0]), float(p[1])))
        except (ValueError, IndexError): pass
    return rows
specs = [
 (1, "FigS1D Au exported_Raman.txt", "Au", 1348, 1578, 2681,
  {"substrate_metal": "Au", "D_peak_relative": "higher than on Cu", "D_cause_stated": "likely strain from rapid solidification (50 K/s cooling)"}),
 (2, "FigS1D Cu exported_Raman.txt", "Cu", 1350, 1580, 2696,
  {"substrate_metal": "Cu", "D_peak_relative": "lower than on Au"}),
]
for n, f, metal, d, g, td, props in specs:
    cid = f"exp-graphene-{n:02d}"
    od = os.path.join(out, cid); os.makedirs(od, exist_ok=True)
    rows = load(f)
    with open(os.path.join(od, "spectrum.csv"), "w") as fh:
        fh.write("shift_cm1,intensity\n")
        for x, y in rows: fh.write(f"{x:.4f},{y:.1f}\n")
    json.dump(dict(case_id=cid, kind="single", task="identify", material_hint=None, laser_nm=None, temperature_K=295,
                   substrate=f"{metal} (solidified droplet/wire after CVD growth)", geometry="backscattering (WITec confocal, assumed; not stated)",
                   question="Which material is this? Assign the peaks."), open(os.path.join(od, "input.json"), "w"), indent=2)
    json.dump(dict(case_id=cid, material="graphene", formula="C", polytype=None, spacegroup=None, pointgroup=None,
        hint_is_correct=None, layers=None,
        peaks=[dict(position_cm1=d, tolerance_cm1=8, irrep=None, label="D"),
               dict(position_cm1=g, tolerance_cm1=6, irrep="E2g", label="G"),
               dict(position_cm1=td, tolerance_cm1=12, irrep=None, label="2D")],
        properties=props,
        source=dict(kind="experimental", dataset="https://doi.org/10.5281/zenodo.14883846 (005_Data.zip, S1/" + f + ")",
                    paper=PAPER, figure="Fig. S1D (Supporting Information: Raman spectra of graphene grown on Au and Cu, after rapid cooling to room temperature)",
                    licence="CC BY 4.0"),
        notes=("WEAK CASE. The paper only states that the layers are graphene (confirmed by Raman), that the D peak is higher on Au than on Cu, "
               "laser power 0.2 mW and grating 2400 g/mm. Layer number, laser wavelength and peak positions are NOT stated in the paper: peak positions in this key "
               "were read from the data by the curator (D, G, 2D local maxima) and are not the authors' values. Laser wavelength is unknown (the 2D position suggests 532 nm, unverified). "
               "Spectrum is raw CCD counts including a broad background; x axis runs from about -105 to 3650 cm-1.")),
        open(os.path.join(od, "truth.json"), "w"), indent=2)
    print(cid, len(rows))
