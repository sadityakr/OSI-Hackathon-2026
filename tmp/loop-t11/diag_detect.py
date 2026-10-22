"""Signal, noise and smoothed prominence at the truth positions of named dev cases (T11 diagnostics, throwaway).

Input: case folder names (dev or dev_hard) as arguments.
Process: same preprocessing as the pipeline (spike removal, ALS baseline), then noise estimates and the signal at
each truth position, raw and after Savitzky-Golay smoothing of several window lengths.
Output: text on stdout.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks, savgol_filter

from ramanlens.perception.fit import noise_sigma
from ramanlens.perception.io import read_spectrum
from ramanlens.perception.preprocess import baseline_als, remove_spikes

ROOT = Path(__file__).resolve().parents[2]
for name in sys.argv[1:]:
    case = next(p for s in ("dev", "dev_hard") if (p := ROOT / "data/test_set" / s / name).exists())
    truth = json.loads((case / "truth.json").read_text())
    sp = read_spectrum(case / "spectrum.csv")
    x, y = sp.x, sp.y
    yc, _ = remove_spikes(x, y)
    sig = yc - baseline_als(yc)
    dx = float(np.median(np.diff(x)))
    s0 = noise_sigma(sig)
    print(f"== {name} dx={dx:.3f} sigma={s0:.4g} max={sig.max():.4g}")
    for win in (5, 9, 15):
        sm = savgol_filter(sig, win, 2)
        ss = noise_sigma(sm)
        idx, pr = find_peaks(sm, prominence=0)
        line = []
        for t in truth["peaks"]:
            j = np.argmin(abs(x[idx] - t["position_cm1"])) if idx.size else None
            if j is None or abs(x[idx][j] - t["position_cm1"]) > 4:
                line.append(f"{t['position_cm1']}: no max")
            else:
                line.append(f"{t['position_cm1']}: h={sm[idx][j] / s0:.1f}s prom={pr['prominences'][j] / s0:.1f}s")
        print(f"  win {win:2d} smoothed sigma={ss / s0:.2f} s0 | " + "; ".join(line))
