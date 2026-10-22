import sys
sys.path.insert(0, sys.argv[1])
import numpy as np
from crd_io import cache_2d, modes, summary, layer_frame
from crd_io import load_rows; rows = load_rows(sys.argv[3])
for k, e in sorted(rows.items(), key=lambda kv: kv[1]["data"]["natom"]):
    s = summary(e)
    if s["negative_freq_Gamma"]: continue
    Q, gap = layer_frame(e)
    vis = []
    for m in modes(e):
        if m["raman_active"] == 1 and m["tensor"] is not None:
            R = Q @ m["tensor"] @ Q.T
            w = R[0,0]**2 + R[1,1]**2 + 2*R[0,1]**2
            vis.append((round(m["freq_cm"]), m["irrep"], w))
    if not vis: continue
    wmax = max(v[2] for v in vis)
    strong = sorted({(f, ir) for f, ir, w in vis if w > 0.05*wmax and f > 60})
    print(k, s["formula"], s["spacegroup"], s["pointgroup"], s["natom"], f"gap={gap:.2f}", strong, sep=" | ")
