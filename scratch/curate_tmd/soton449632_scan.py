"""List excitation energy and top peaks for each spectrum block (shift, intensity, blank column triplets) in a sheet. args: xlsx sheet"""
import sys, numpy as np, pandas as pd
from scipy.signal import find_peaks
df = pd.read_excel(sys.argv[1], sheet_name=sys.argv[2], header=None)
for j in range(0, df.shape[1], 3):
    if j+1 >= df.shape[1]: break
    e = df.iloc[0, j+1]; s = pd.to_numeric(df.iloc[2:, j], errors="coerce").values; y = pd.to_numeric(df.iloc[2:, j+1], errors="coerce").values
    ok = ~np.isnan(s) & ~np.isnan(y); s, y = s[ok], y[ok]
    if len(s) < 20: continue
    ys = np.convolve(y, np.ones(3)/3, "same")
    p, _ = find_peaks(ys, prominence=0.05*(ys.max()-ys.min()))
    top = sorted(p, key=lambda i: -ys[i])[:6]
    print(j//3, e, f"{s.min():.0f}-{s.max():.0f}", [(round(s[i]), float(f"{ys[i]:.3g}")) for i in sorted(top)])
