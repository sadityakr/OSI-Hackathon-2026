"""Probe: dev single spectra, axis ranges, fitted peaks vs truth (throwaway, not shipped).

Used by loop T4 to see where the raw fitter disagrees with the dev truth before writing the pipeline.
Input: the dev split of data/test_set. Process: reads each single spectrum, removes spikes, fits peaks, or runs
the pipeline if importable. Output: printed table per case.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from cases import dev_cases  # noqa: E402

from ramanlens.perception.io import read_spectrum  # noqa: E402
from ramanlens.perception.preprocess import remove_spikes  # noqa: E402
from ramanlens.perception.fit import fit_peaks  # noqa: E402

use_pipeline = "--pipeline" in sys.argv
if use_pipeline:
    from ramanlens.perception.pipeline import analyze_spectrum  # noqa: E402

for c in dev_cases(kind="single"):
    s = read_spectrum(c["dir"] / "spectrum.csv")
    if use_pipeline:
        res = analyze_spectrum(s)
        peaks, spikes = res.peaks, res.spikes
    else:
        yc, spikes = remove_spikes(s.x, s.y)
        peaks = fit_peaks(s.x, yc)
    truth = [t["position_cm1"] for t in c["truth"]["peaks"]]
    notes = json.loads(c["truth"]["notes"] or "{}") if (c["truth"]["notes"] or "").startswith("{") else {}
    cr = [a["position_cm1"] for a in notes.get("artifacts", []) if a.get("type") == "cosmic_ray"]
    print(f"{c['id']}: x {s.x[0]:.1f}..{s.x[-1]:.1f} dx {s.x[1]-s.x[0]:.2f} task {c['input']['task']} "
          f"formula {c['truth']['formula']} substrate {c['input'].get('substrate')}")
    print("  truth:", truth, " cosmic:", cr, " spikes:", [round(v, 1) for v in spikes])
    print("  fit:  ", [(round(p.position, 1), round(p.fwhm, 1), round(p.height, 1),
                       "S" if p.is_substrate else "") for p in peaks])
