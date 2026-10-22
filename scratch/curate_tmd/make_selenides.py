"""Build exp-MoSe2-01 and exp-WSe2-01 from Southampton 449632 processed resonance Raman workbooks; args: MoSe2.xlsx WSe2.xlsx."""
import sys
sys.path.insert(0, "C:/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/scratch/curate_tmd")
import pandas as pd
from casekit import write_case
def block(path, sheet, k):
    df = pd.read_excel(path, sheet_name=sheet, header=None); j = 3 * k
    return float(df.iloc[0, j + 1]), pd.to_numeric(df.iloc[2:, j], errors="coerce").values, pd.to_numeric(df.iloc[2:, j + 1], errors="coerce").values
DS = "doi:10.5258/SOTON/D1747 (University of Southampton ePrints 449632, files MoSe2_Data.xlsx / WSe2_Data.xlsx, sheet 'Processed A1s Data')"
NOTE = ("Processed spectrum as deposited (parallel minus crossed polarisation subtraction to remove PL, thin-film-interference corrected, absolute scattering probability x1e8; NOT raw counts). "
        "hBN-encapsulated monolayer, 4 K, resonance Raman near the A1s exciton at {e:.4f} eV ({nm:.1f} nm). Excitation-dependent relative intensities: other weaker peaks exist but only the single-phonon peak whose position the paper states is listed. "
        "Si 520 cm-1 substrate peak may appear. ")
for mat, path, sheet, k, pos, lab, fig, paper, extra in (
    ("MoSe2", sys.argv[1], "Processed A1s Data", 18, 240.0, "A1'", "text and Supplementary Section S3 / Fig. S2 of the dataset paper (240 cm-1 A1' peak of monolayer MoSe2); excitation range 1.24-2.25 eV, all spectra at 4 K",
     "Viner, McDonnell, Ruiz-Tijerina, Rivera, Xu, Fal'ko, Smith 2021, 2D Materials 8, 035047 'Excited Rydberg States in MoSe2/WSe2 Heterostructures', arXiv:2103.09004 (doi not independently verified here)",
     "Position 240 cm-1 is from the dataset's own paper; the companion paper (McDonnell et al. 2020, arXiv:2006.05912) gives 241.0 cm-1 for the same peak."),
    ("WSe2", sys.argv[2], "Processed A1s Data", 10, 249.3, "A1'/E' (single-phonon, near-degenerate in monolayer)", "Main text of the companion paper arXiv:2006.05912 (249.3 cm-1 peak assigned to single-phonon A1'/E' scattering in hBN-encapsulated monolayer WSe2); Fig. 1 colour plots",
     "McDonnell, Viner, Rivera, Xu, Smith 2020, 2D Materials 'Observation of intravalley phonon scattering of 2s excitons in MoSe2 and WSe2 monolayers' (arXiv:2006.05912; journal volume/DOI not verified here)",
     "UNVERIFIED transfer: peak position 249.3 cm-1 comes from the companion paper (dataset DOI 10.5258/SOTON/D1315, whose xlsx files are empty on the server), not from the paper that describes this 449632 dataset; the 449632 spectrum peaks at ~250 cm-1.")):
    e, s, y = block(path, sheet, k); nm = 1239.84 / e; cid = f"exp-{mat}-01"
    inp = {"case_id": cid, "kind": "single", "task": "identify", "material_hint": None, "laser_nm": round(nm, 1), "temperature_K": 4,
           "substrate": "hBN-encapsulated on SiO2/Si", "geometry": "backscattering, beam along c", "question": "Which material is this? Assign the peaks."}
    tr = {"case_id": cid, "material": mat, "formula": mat, "polytype": None, "spacegroup": None, "pointgroup": None, "hint_is_correct": None, "layers": 1,
          "peaks": [{"position_cm1": pos, "tolerance_cm1": 3, "irrep": None, "label": lab, "pattern": None}],
          "properties": {"layers": 1, "encapsulation": "hBN"},
          "source": {"kind": "experimental", "dataset": DS, "paper": paper, "figure": fig, "licence": "CC BY 4.0 (record page)"},
          "notes": NOTE.format(e=e, nm=nm) + extra}
    write_case(cid, s, y, inp, tr, lo=100, hi=1000)
