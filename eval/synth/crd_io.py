"""Minimal reader for the Computational Raman Database (CRD) used only by the synthetic test generator.

The evaluation code keeps its own loader on purpose: the generator that produces ground truth must not
share code with the RamanLens tools it is used to test, otherwise a bug in one would be invisible in the other.

Input:
    The CRD JSON dump (Bagheri and Komsa, Sci. Data 10, 80 (2023), CC BY 4.0), an ASE database export
    keyed by row id, or a pickle of a subset of its rows made by `cache_2d`.
Process:
    Parses frequencies, per-band irrep labels (mapped to modes through IRbands) and Raman tensors. Tensors
    are stored either as a list indexed by mode or as a dict keyed by the mode index as a string; both are handled.
    Finds the stacking direction of a layered cell as the lattice-plane family with the widest empty gap.
Output:
    Plain dicts and numpy arrays: one record per Gamma-point mode, plus a rotation matrix into the layer frame.
"""

import ast
import json
import pickle
import re

import numpy as np


def _nd(x):
    """Decode ASE's {"__ndarray__": [shape, dtype, flat]} encoding."""
    shape, dtype, data = x["__ndarray__"]
    return np.array(data, dtype=dtype).reshape(shape)


def load_rows(path):
    """Load the CRD rows from the full JSON dump or from a pickle subset."""
    if str(path).endswith(".pkl"):
        with open(path, "rb") as f:
            return pickle.load(f)
    with open(path) as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if isinstance(v, dict)}  # skip the 'ids' and 'nextid' bookkeeping keys


def cache_2d(json_path, pkl_path):
    """Write a pickle with only the layered ("2D") rows; the full JSON takes about 30 s to parse."""
    rows = load_rows(json_path)
    sub = {k: e for k, e in rows.items() if e["key_value_pairs"].get("dimensionality") == "2D"}
    with open(pkl_path, "wb") as f:
        pickle.dump(sub, f)
    return sub


def summary(entry):
    kv, dt = entry["key_value_pairs"], entry["data"]
    return dict(formula=dt["chemical_formula"], mpid=kv.get("mpid"), spacegroup=kv.get("spacegroup"),
                pointgroup=kv.get("pointgroup"), dimensionality=kv.get("dimensionality"),
                natom=dt["natom"], negative_freq_Gamma=kv.get("negative_freq_Gamma"))


def _tensor(tensors, i):
    if isinstance(tensors, dict):
        t = tensors.get(str(i))
    else:
        t = tensors[i] if i < len(tensors) else None
    return None if t is None else np.array(t, dtype=float)


def modes(entry):
    """One dict per Gamma mode: index, band, frequency in cm-1, irrep (per band), activity flags, Raman tensor."""
    kv, dt = entry["key_value_pairs"], entry["data"]
    freqs = np.array(re.findall(r"[-+]?\d+\.\d+(?:e[-+]?\d+)?", kv["frequencies_cm"]), dtype=float)
    labels = ast.literal_eval(kv["IRlabels"])
    bands = ast.literal_eval(kv["IRbands"])
    if labels is None or bands is None:  # a few rows have no symmetry analysis; treat them as unusable
        return []
    ra = _nd(dt["Ramanactive"])
    tensors = dt["raman_tensors"]
    out = []
    for b, (lab, idxs) in enumerate(zip(labels, bands)):
        for i in idxs:
            out.append(dict(mode=i, band=b, freq_cm=float(freqs[i]), irrep=lab,
                            raman_active=int(ra[i]), tensor=_tensor(tensors, i)))
    return out


def layer_frame(entry):
    """Rotation matrix Q whose rows are the layer-frame axes (x, y in plane, z = layer normal) in Cartesian coordinates.

    The layer normal is the lattice-plane family (h k l), searched over indices up to 2 so that rhombohedral
    primitive cells (layers along 111) are covered, whose atoms leave the widest empty slab: the van der Waals gap.
    x is the in-plane projection of the lattice vector most perpendicular to the normal, so angle 0 in a
    polarization series lies along a crystal axis. Rotate a tensor with Q @ R @ Q.T.
    """
    cell = entry["cell"]
    cell = _nd(cell["array"] if "array" in cell else cell)
    pos = _nd(entry["positions"])
    frac = np.linalg.solve(cell.T, pos.T).T
    recip = np.linalg.inv(cell).T  # rows b_i with a_i . b_j = delta_ij (no 2 pi)
    best_g, best_gap = None, -1.0
    for h in range(-2, 3):
        for k in range(-2, 3):
            for l in range(0, 3):
                hkl = np.array([h, k, l])
                if not hkl.any() or np.gcd.reduce(np.abs(hkl)) != 1:
                    continue
                g = hkl @ recip
                f = np.sort((frac @ hkl) % 1.0)  # atom position along the normal, in units of the plane spacing
                gaps = np.diff(np.concatenate([f, [f[0] + 1.0]]))
                gap_A = gaps.max() / np.linalg.norm(g)  # plane spacing d = 1/|g|
                if gap_A > best_gap + 1e-6:
                    best_g, best_gap = g, gap_A
    z = best_g / np.linalg.norm(best_g)
    j = int(np.argmin([abs(np.dot(a, z)) / np.linalg.norm(a) for a in cell]))
    x = cell[j] - np.dot(cell[j], z) * z
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.vstack([x, y, z]), best_gap
