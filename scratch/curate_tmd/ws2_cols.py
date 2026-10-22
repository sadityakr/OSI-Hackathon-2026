"""Show smoothed local maxima of selected D0371 columns. args: xlsx T col [col...]"""
import sys, numpy as np, pandas as pd
from scipy.signal import find_peaks
x = pd.ExcelFile(sys.argv[1]); T = sys.argv[2]
sh = x.parse(f"{T} Shift", header=None).astype(float); it = x.parse(f"{T} Intensity", header=None).astype(float); wl = x.parse(f"{T} WL", header=None).astype(float).iloc[0]
for c in map(int, sys.argv[3:]):
    s = sh[c].values; y = it[c].values; o = np.argsort(s); s, y = s[o], y[o]
    ys = np.convolve(y, np.ones(5)/5, "same")
    p, pr = find_peaks(ys, prominence=0.08*(np.nanmax(ys)-np.nanmin(ys)))
    print(T, c, wl[c], "nan:", np.isnan(s).sum(), [(round(s[i]), round(ys[i])) for i in p])
