"""Helpers to write a test-set candidate case (spectrum.csv, input.json, truth.json) per data/test_set/README.md."""
import json, os
import numpy as np

ROOT = "C:/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/data/test_set/candidates"

def contrast(s, y, pos, w=6, side=25):
    """Smoothed intensity at pos minus median of flanking windows (pos+-side), to check a peak is really there."""
    s = np.asarray(s); y = np.asarray(y, float)
    c = y[(abs(s - pos) <= w)].max()
    fl = y[((abs(s - pos) > side - 5) & (abs(s - pos) <= side + 5))]
    return float(c - np.median(fl)), float(np.std(fl))

def write_case(case_id, shift, inten, inp, truth, lo=100, hi=1000):
    s = np.asarray(shift, float); y = np.asarray(inten, float)
    ok = ~np.isnan(s) & ~np.isnan(y) & (s >= lo) & (s <= hi)
    s, y = s[ok], y[ok]; o = np.argsort(s); s, y = s[o], y[o]
    d = os.path.join(ROOT, case_id); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "spectrum.csv"), "w", newline="") as f:
        f.write("shift_cm1,intensity\n")
        for a, b in zip(s, y): f.write(f"{a:.3f},{b:.6g}\n")
    json.dump(inp, open(os.path.join(d, "input.json"), "w"), indent=2)
    json.dump(truth, open(os.path.join(d, "truth.json"), "w"), indent=2, ensure_ascii=False)
    print(case_id, len(s), "points", s.min(), s.max())
