"""Summarise the D0371 WS2 resonance Raman workbook: per temperature, WL range, shift range, strongest peak per column."""
import sys, numpy as np, pandas as pd
x = pd.ExcelFile(sys.argv[1])
for T in sys.argv[2:]:
    sh = x.parse(f"{T} Shift", header=None).astype(float); it = x.parse(f"{T} Intensity", header=None).astype(float); wl = x.parse(f"{T} WL", header=None).astype(float).iloc[0]
    print(T, "ncols", sh.shape[1], "WL", wl.min(), wl.max())
    for j in range(sh.shape[1]):
        s = sh.iloc[:, j].values; y = it.iloc[:, j].values
        ok = ~np.isnan(s) & ~np.isnan(y)
        i = np.argmax(np.where(ok & (s>300) & (s<450), y, -1e9))
        print(f"  col{j} wl={wl[j]} shift {np.nanmin(s):.0f}-{np.nanmax(s):.0f} max in 300-450 at {s[i]:.1f} I={y[i]:.0f} median={np.nanmedian(y):.0f}")
