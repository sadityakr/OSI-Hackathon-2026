"""Inspect CrSBr Zenodo 15048152 text spectra: range, and strongest peaks per column."""
import sys, pandas as pd, numpy as np
from scipy.signal import find_peaks, savgol_filter
for f in sys.argv[1:]:
    d = pd.read_csv(f, sep="\t")
    print("==", f, d.shape, list(d.columns))
    x = d.iloc[:,0].values
    print(" x range", x.min(), x.max(), "dx", np.median(np.diff(x)))
    for c in d.columns[1:]:
        y = d[c].values.astype(float)
        ys = savgol_filter(y, 7, 2)
        p,_ = find_peaks(ys, prominence=(ys.max()-np.median(ys))*0.1)
        print(" ", c.strip(), "min/max", y.min(), y.max(), "peaks", [(round(x[i],1), round(ys[i])) for i in p])
