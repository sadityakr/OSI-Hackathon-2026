"""Unit tests for ramanlens.perception.polarization beyond the contract: edge cases and dev-case details."""

import json
from pathlib import Path

import numpy as np
import pytest

from ramanlens.perception.polarization import analyze_series, classify_curves

DEV = Path(__file__).resolve().parents[2] / "data" / "test_set" / "dev"


def _curves(R, theta_deg):
    th = np.radians(theta_deg)
    ei = np.stack([np.cos(th), np.sin(th), 0 * th], 1)
    ex = np.stack([-np.sin(th), np.cos(th), 0 * th], 1)
    par = np.einsum("ni,ij,nj->n", ei, R, ei) ** 2
    crs = np.einsum("ni,ij,nj->n", ex, R, ei) ** 2
    return par, crs


def test_twofold_axis_found_for_opposite_sign_diagonal():
    theta = np.arange(0, 180, 10.0)
    par, crs = _curves(np.diag([1.0, -0.5, 0.0]), theta - 35.0)
    got = classify_curves(theta, par, crs)
    assert got["pattern"] == "twofold"
    assert abs((got["max_parallel_angle_deg"] - 35.0 + 90) % 180 - 90) < 3


def test_flat_parallel_without_crossed_is_undetermined():
    theta = np.arange(0, 180, 10.0)
    got = classify_curves(theta, np.ones(theta.size), None)
    assert got["pattern"] == "undetermined"


def test_too_few_angles_is_undetermined():
    got = classify_curves([0, 45, 90], [1, 2, 1], [0, 0, 0])
    assert got["pattern"] == "undetermined"


def test_pure_noise_is_not_twofold():
    rng = np.random.default_rng(0)
    theta = np.arange(0, 180, 10.0)
    par = 1.0 + rng.normal(0, 0.05, theta.size)
    got = classify_curves(theta, par, 1.0 + rng.normal(0, 0.05, theta.size))
    assert got["pattern"] == "isotropic_both"


@pytest.mark.slow
def test_dev_series_twofold_axis_and_patterns():
    from ramanlens.perception.io import read_series
    for case in ("syn-GeS-02", "syn-BiOBr-01", "syn-WS2-03"):
        truth = json.loads((DEV / case / "truth.json").read_text())
        res = analyze_series(read_series(DEV / case / "spectrum.csv"))
        for t in truth["peaks"]:
            near = [r for r in res if abs(r["position_cm1"] - t["position_cm1"]) <= t["tolerance_cm1"]]
            assert near and near[0]["pattern"] == t["pattern"], (case, t, near[:1])
            if t["pattern"] == "twofold":
                d = abs((near[0]["max_parallel_angle_deg"] - t["max_parallel_angle_deg"] + 90) % 180 - 90)
                assert d < 10, (case, t, near[0]["max_parallel_angle_deg"])
