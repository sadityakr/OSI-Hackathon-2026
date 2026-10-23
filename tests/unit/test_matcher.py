"""Unit tests for the reference library and matcher (ramanlens.perception.library)."""

import numpy as np
import pytest

from ramanlens.perception import library as lib
from ramanlens.perception.library import RefEntry, RefMode, layer_normal_frame, match


def _entry(name, modes, kind="crd"):
    return RefEntry(material=name, modes=[RefMode(p, w, "A", f"m{p:.0f}") for p, w in modes], source="test",
                    kind=kind, entry_id=name)


def test_layer_frame_finds_van_der_waals_gap():
    # Hexagonal cell, c = 12 A, all atoms within a 3 A slab: the normal must be along c.
    a, c = 3.2, 12.0
    cell = np.array([[a, 0, 0], [-a / 2, a * np.sqrt(3) / 2, 0], [0, 0, c]])
    pos = np.array([[0, 0, 0.0], [a / 2, a / (2 * np.sqrt(3)), 1.5], [0, a / np.sqrt(3), 3.0]])
    Q = layer_normal_frame(cell, pos)
    assert abs(abs(Q[2] @ np.array([0, 0, 1.0])) - 1) < 1e-9
    assert np.allclose(Q @ Q.T, np.eye(3))


def test_scale_is_fitted_and_matches_are_labelled():
    ref = _entry("WS2", [(350.0, 1.0), (410.0, 0.6)])
    c = match([357.0, 418.2], [1.0, 0.6], library=[ref])[0]
    assert abs(c.scale - 1.02) < 0.002
    assert [m[2] for m in c.matched] == ["m350", "m410"] and not c.unmatched


def test_missing_strong_mode_is_penalized():
    good = _entry("AB", [(300.0, 1.0)])
    extra = _entry("CD", [(300.0, 1.0), (330.0, 1.0)])  # predicts a second strong line that was not measured
    cands = match([303.0], library=[extra, good])
    assert [c.material for c in cands] == ["AB", "CD"]
    assert cands[1].missing and cands[1].score < cands[0].score


def test_outside_modes_break_single_peak_ties_unless_window_given():
    lone = _entry("AB", [(200.0, 1.0)])
    busy = _entry("CD", [(200.0, 1.0), (600.0, 1.0)])
    assert match([202.0], library=[busy, lone])[0].material == "AB"
    # Measured window 150 to 300 cm-1: the 600 cm-1 mode could not have been seen, so the two tie.
    scores = {c.material: c.score for c in match([202.0], library=[busy, lone], x_range=(150, 300))}
    assert scores["AB"] == pytest.approx(scores["CD"])


def test_one_candidate_per_material_and_sorted():
    cands = match([300.0], library=[_entry("W2S4", [(270.0, 1.0)]), _entry("WS2", [(300.0, 1.0)]),
                                    _entry("XY", [(380.0, 1.0)])])
    ws2 = [c for c in cands if lib._formula_key(c.material) == lib._formula_key("WS2")]
    assert len(ws2) == 1 and ws2[0].entry_id == "WS2"  # the better-scoring polytype is kept
    assert all(cands[i].score >= cands[i + 1].score for i in range(len(cands) - 1))


def test_empty_input():
    assert match([]) == []


def test_crd_ws2_backscattering_visibility():
    """2H-WS2 (CRD row 90): E2g and A1g visible along c, E1g (xz, yz components only) invisible."""
    try:
        entries = lib.crd_library()
    except FileNotFoundError:
        pytest.skip("CRD not available")
    e = next(x for x in entries if x.entry_id == "crd:90")
    irreps = {m.irrep for m in e.modes if m.position_cm1 > 100}
    assert irreps == {"E2g", "A1g"}, [(m.position_cm1, m.irrep, m.rel_intensity) for m in e.modes]
