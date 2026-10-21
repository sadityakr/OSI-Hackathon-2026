"""Regression test: spike removal plus fit_peaks alone find the dev truth peaks (no pipeline, no substrate logic).

Kept separate from the contract recall test so a recall drop can be traced to the fitter rather than the pipeline.
Reads dev truth only (allowed for debugging); never the held-out split.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "contract"))


@pytest.mark.slow
def test_fitter_recall_on_dev_single_cases():
    from cases import dev_cases
    from ramanlens.perception.fit import fit_peaks
    from ramanlens.perception.io import read_spectrum
    from ramanlens.perception.preprocess import remove_spikes
    found = total = 0
    for c in dev_cases(kind="single"):
        s = read_spectrum(c["dir"] / "spectrum.csv")
        y_clean, _ = remove_spikes(s.x, s.y)
        peaks = fit_peaks(s.x, y_clean)
        for t in c["truth"]["peaks"]:
            total += 1
            found += any(abs(p.position - t["position_cm1"]) <= t["tolerance_cm1"] for p in peaks)
    assert total and found / total >= 0.9, f"recall {found}/{total}"
