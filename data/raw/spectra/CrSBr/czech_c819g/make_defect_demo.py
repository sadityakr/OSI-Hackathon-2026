"""Export the He+ irradiation series of 4L CrSBr (Sahu et al. dataset, Figure 2a/2b) as plain CSVs for a demo.

The demo agent gets spectra labelled only by treatment step and polarization, never by dose, so it has to find
the defect signatures itself. Source: Czech repository DOI 10.48700/72gk1-7mb53, CC BY 4.0.
Input: Figure_2.xlsx from the extracted dataset (argument 1) and an output folder (argument 2).
Process: sheet Figure_2a (E||a) and Figure_2b (E||b); row 1 headers, row 2 series label, data from row 3,
paired (shift, intensity) columns per series. Rows with empty cells are dropped; x sorted ascending.
Output: <out>/<step>_E-along-<axis>.csv with columns shift_cm1,intensity, plus provenance.json (kept outside the
demo folder by the caller, since it names the doses).
"""
import csv
import json
import sys
from pathlib import Path

import openpyxl

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
steps = {"Pristine": "step0_untreated", "3.9": "step1", "2.4": "step2", "1.2": "step3"}
prov = []
wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
for sheet, axis in (("Figure_2a", "a"), ("Figure_2b", "b")):
    rows = list(wb[sheet].iter_rows(values_only=True))
    labels = rows[1]
    for j in range(0, len(labels), 2):
        lab = str(labels[j] if labels[j] is not None else labels[j + 1])
        step = next(v for k, v in steps.items() if lab.strip().startswith(k))
        pts = sorted((r[j], r[j + 1]) for r in rows[2:]   # Origin writes "--" for missing points
                     if isinstance(r[j], (int, float)) and isinstance(r[j + 1], (int, float)))
        # the E||a sheet carries the figure's display factors (x5, x10, x20) and E||b is max-normalised,
        # so absolute intensities are not comparable between files: normalise every spectrum to its maximum
        top = max(p[1] for p in pts)
        pts = [(x, y / top) for x, y in pts]
        name = f"{step}_E-along-{axis}.csv"
        with open(out / name, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["shift_cm1", "intensity"])
            w.writerows(pts)
        prov.append({"file": name, "sheet": sheet, "label_in_source": lab, "n": len(pts),
                     "x_range": [pts[0][0], pts[-1][0]],
                     "y_range": [min(p[1] for p in pts), max(p[1] for p in pts)]})
print(json.dumps(prov, indent=1))
