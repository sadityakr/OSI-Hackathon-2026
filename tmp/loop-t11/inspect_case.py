"""Print fit output, matcher labels and truth peaks for named dev cases (T11 diagnostics, throwaway).

Input: case folder names as arguments (dev or dev_hard).
Process: toolset fit_peaks and match_library; truth read from the dev folders only.
Output: text on stdout.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
from ramanlens.agent import toolset  # noqa: E402

for name in sys.argv[1:]:
    case = next(p for s in ("dev", "dev_hard") if (p := ROOT / "data/test_set" / s / name).exists())
    truth = json.loads((case / "truth.json").read_text())
    inp = json.loads((case / "input.json").read_text())
    fit = json.loads(toolset.call("fit_peaks", {"path": "spectrum.csv", "substrate": inp.get("substrate")}, case))
    print(f"== {name} range={fit['analysed_range_cm1']} notes={fit['notes']}")
    for p in fit["peaks"]:
        print(f"   fit {p['position_cm1']:8.2f} fwhm {p['fwhm_cm1']:6.2f} h {p['height']:10.4g} sub={p['is_substrate']}")
    for t in truth["peaks"]:
        print(f"   truth {t['position_cm1']:8.2f} {t.get('irrep')} {t.get('label')} tol {t['tolerance_cm1']}")
    print("   truth notes:", str(truth.get("notes"))[:400])
    peaks = [p for p in fit["peaks"] if not p["is_substrate"]]
    m = json.loads(toolset.call("match_library", {"positions_cm1": [p["position_cm1"] for p in peaks],
                                                  "intensities": [p["height"] for p in peaks],
                                                  "x_range_cm1": fit["analysed_range_cm1"]}, case))
    for c in m["candidates"][:3]:
        print(f"   cand {c['material']} {c['score']} {c['kind']} scale={c['frequency_scale']} matched={c['matched']} "
              f"missing={c['missing_strong_modes']}")
