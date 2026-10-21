"""Contract for polarization analysis of angle series (backscattering, in-plane linear polarizations).

Pattern classes are defined in data/test_set/README.md. Exact tests build curves from textbook Raman tensors;
dataset tests use the dev angle-series cases.
"""

import numpy as np
import pytest

from cases import dev_cases


def curves(tensors, theta_deg):
    th = np.radians(theta_deg)
    ei = np.stack([np.cos(th), np.sin(th), 0 * th], 1)
    ex = np.stack([-np.sin(th), np.cos(th), 0 * th], 1)
    par = sum(np.einsum("ni,ij,nj->n", ei, R, ei) ** 2 for R in tensors)
    crs = sum(np.einsum("ni,ij,nj->n", ex, R, ei) ** 2 for R in tensors)
    return par, crs


TEXTBOOK = {
    "isotropic_par_only": [np.diag([1.0, 1.0, 0.5])],                                  # A1g, hexagonal
    "isotropic_both": [np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, 0]]),                 # E2g pair
                       np.array([[0, -1.0, 0], [-1.0, 0, 0], [0, 0, 0]])],
    "twofold": [np.diag([1.0, 0.3, 0.2])],                                               # Ag, orthorhombic
    "fourfold": [np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, 0]])],                     # B1g, tetragonal
}


@pytest.mark.parametrize("pattern", list(TEXTBOOK))
def test_classify_curves_textbook(pattern):
    from ramanlens.perception.polarization import classify_curves
    theta = np.arange(0, 180, 10.0)
    rng = np.random.default_rng(3)
    for offset in (0.0, 27.0, 61.0):  # unknown sample rotation
        par, crs = curves(TEXTBOOK[pattern], theta - offset)
        par = par + rng.normal(0, 0.02, par.size)
        crs = crs + rng.normal(0, 0.02, crs.size)
        got = classify_curves(theta, np.clip(par, 0, None), np.clip(crs, 0, None))
        # returns dict with "pattern" and, for twofold, "max_parallel_angle_deg"
        assert got["pattern"] == pattern, (pattern, offset, got)
        if pattern == "twofold":
            d = abs((got["max_parallel_angle_deg"] - offset + 90) % 180 - 90)
            assert d < 10


@pytest.mark.slow
def test_angle_series_dev_cases():
    from ramanlens.perception.io import read_series
    from ramanlens.perception.polarization import analyze_series
    right = total = 0
    for c in dev_cases(kind="angle_series"):
        res = analyze_series(read_series(c["dir"] / "spectrum.csv"))  # list of dicts: position_cm1, pattern, ...
        for t in c["truth"]["peaks"]:
            total += 1
            near = [r for r in res if abs(r["position_cm1"] - t["position_cm1"]) <= t["tolerance_cm1"]]
            right += bool(near) and near[0]["pattern"] == t["pattern"]
    assert total and right / total >= 0.9, f"{right}/{total}"
