"""Minimal loader for the Computational Raman Database (Bagheri & Komsa 2023) JSON dump.
Scratch version; move to src/ramanlens/perception/library.py once the architecture is approved.
"""
import json, re, ast
import numpy as np

def _nd(x):
    shape, dtype, data = x["__ndarray__"]
    return np.array(data, dtype=dtype).reshape(shape)

def load_crd(path):
    raw = json.load(open(path))
    return {k: v for k, v in raw.items() if isinstance(v, dict)}  # drop 'ids', 'nextid'

def modes(entry):
    """Return list of dicts, one per phonon mode at Gamma, with band-level irrep label and Raman tensor."""
    kv, dt = entry["key_value_pairs"], entry["data"]
    freqs = np.array(re.findall(r"[-+]?\d+\.\d+(?:e[-+]?\d+)?", kv["frequencies_cm"]), dtype=float)
    labels = ast.literal_eval(kv["IRlabels"])
    bands = ast.literal_eval(kv["IRbands"])
    ra = _nd(dt["Ramanactive"]); ir = _nd(dt["IRactive"])
    tensors = dt["raman_tensors"]
    out = []
    for b, (lab, idxs) in enumerate(zip(labels, bands)):
        for i in idxs:
            T = tensors[i] if i < len(tensors) and tensors[i] is not None else None
            out.append(dict(mode=i, band=b, freq_cm=float(freqs[i]), irrep=lab,
                            raman_active=int(ra[i]), ir_active=int(ir[i]),
                            tensor=np.array(T) if T is not None else None))
    return out

def summary(entry):
    kv, dt = entry["key_value_pairs"], entry["data"]
    return dict(formula=dt["chemical_formula"], mpid=kv.get("mpid"), spacegroup=kv.get("spacegroup"),
                pointgroup=kv.get("pointgroup"), dimensionality=kv.get("dimensionality"),
                bandgap=kv.get("bandgap"), natom=dt["natom"],
                negative_freq_Gamma=kv.get("negative_freq_Gamma"), negative_freq_path=kv.get("negative_freq_path"))

if __name__ == "__main__":
    import sys
    db = load_crd(sys.argv[1])
    e = db["90"]  # 2H-WS2 mp-224
    print(summary(e))
    for m in modes(e):
        if m["raman_active"] == 1:
            print(f"{m['freq_cm']:7.1f} cm-1  {m['irrep']:5s} diag={np.round(np.diag(m['tensor']),3)}")
