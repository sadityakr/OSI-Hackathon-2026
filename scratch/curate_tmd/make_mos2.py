"""Build exp-MoS2-01 from Southampton D2829 workbook tab 'Fig 2' spot 1 (MoS2 ALD film on black Si); arg: xlsx."""
import sys
sys.path.insert(0, "C:/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/scratch/curate_tmd")
import pandas as pd
from casekit import write_case
f = pd.read_excel(sys.argv[1], sheet_name="Fig 2", header=None)
s = pd.to_numeric(f.iloc[3:, 0], errors="coerce").values; y = pd.to_numeric(f.iloc[3:, 1], errors="coerce").values
cid = "exp-MoS2-01"
inp = {"case_id": cid, "kind": "single", "task": "identify", "material_hint": None, "laser_nm": None, "temperature_K": None,
       "substrate": "black silicon (Si nanowires), ALD-grown MoS2 film", "geometry": "backscattering", "question": "Which material is this? Assign the peaks."}
tr = {"case_id": cid, "material": "MoS2", "formula": "MoS2", "polytype": None, "spacegroup": None, "pointgroup": None, "hint_is_correct": None, "layers": None,
      "peaks": [{"position_cm1": 383.4, "tolerance_cm1": 5, "irrep": "E2g", "label": "E2g (in-plane)", "pattern": None},
                {"position_cm1": 407.3, "tolerance_cm1": 5, "irrep": "A1g", "label": "A1g (out-of-plane)", "pattern": None}],
      "properties": {"synthesis": "ALD, 15 cycles, on Si nanowire (black Si), no alumina (sample S4)", "A1g_minus_E2g_cm1": 23.9},
      "source": {"kind": "experimental", "dataset": "doi:10.5258/SOTON/D2829 (University of Southampton ePrints 488525, Dataset_MORGAN_SiNW.xlsx)",
                 "paper": "Zeimpekis, Rahman, Leung, Ebert, De Leon Albarran, Morgan 2024, ACS Applied Energy Materials, doi:10.1021/acsaem.3c03055 (paper text NOT read, paywalled; interpretation taken from the dataset's own tabs)",
                 "figure": "Dataset tab 'Fig 2' (typical Raman spectra, spot 1 of sample S4, 15 ALD cycles SiNW/MoS2) and tab 'Fig 3' (fitted E2g 383.42 +/- 0.61 and A1g 407.32 +/- 0.45 cm-1 for 15 MoS2/SiNW)",
                 "licence": "CC BY 4.0"},
      "notes": "UNVERIFIED context: laser wavelength, layer number and temperature not stated in the dataset files (paper not read). Spectrum is only ~351-451 cm-1 (the dataset's plotted window), normalised, with the first point forced to 0; no baseline correction applied by us. Peak positions are the Gaussian-fit means over several spots reported in tab Fig 3, so spot 1 may differ by about 1 cm-1. A1g-E2g splitting 23.9 cm-1 is consistent with few-layer MoS2 but the paper's layer count was not verified."}
write_case(cid, s, y, inp, tr, lo=0, hi=1000)
