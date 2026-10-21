"""Unit tests for the agent toolset: JSON outputs, provenance, path confinement, error objects, angle series."""

import json
import shutil

import numpy as np
import pytest

from cases import dev_cases
from ramanlens.agent import toolset


def _call(name, inp, wd):
    return json.loads(toolset.call(name, inp, wd))


def test_every_tool_has_a_handler_and_valid_schema():
    assert {t["name"] for t in toolset.TOOLS} == set(toolset._HANDLERS)
    for t in toolset.TOOLS:
        schema = t["input_schema"]
        assert set(schema.get("required", [])) <= set(schema["properties"])


def test_paths_outside_the_work_folder_are_refused(tmp_path):
    (tmp_path / "work").mkdir()
    (tmp_path / "secret.csv").write_text("1,2\n3,4\n")
    with pytest.raises(PermissionError):
        toolset.call("load_spectrum", {"path": "../secret.csv"}, tmp_path / "work")
    with pytest.raises(FileNotFoundError):
        toolset.call("load_spectrum", {"path": "missing.csv"}, tmp_path / "work")


def test_fit_peaks_on_synthetic_spectrum_with_si_line(tmp_path):
    x = np.arange(100.0, 700.0, 0.5)
    rng = np.random.default_rng(0)
    y = (100 / (1 + ((x - 383) / 2) ** 2) + 120 / (1 + ((x - 408) / 2.5) ** 2) + 300 / (1 + ((x - 520.7) / 1.5) ** 2)
         + 10 + rng.normal(0, 1, x.size))
    np.savetxt(tmp_path / "s.csv", np.c_[x, y], delimiter=",", header="shift_cm1,intensity", comments="")
    out = _call("fit_peaks", {"path": "s.csv"}, tmp_path)
    pos = [p["position_cm1"] for p in out["peaks"]]
    assert any(abs(p - 383) < 1 for p in pos) and any(abs(p - 408) < 1 for p in pos)
    si = [p for p in out["peaks"] if p["is_substrate"]]
    assert len(si) == 1 and abs(si[0]["position_cm1"] - 520.7) < 1
    assert all(p["provenance"] == "measured" for p in out["peaks"]) and out["method"]
    off = _call("fit_peaks", {"path": "s.csv", "substrate": "sapphire"}, tmp_path)
    assert not any(p["is_substrate"] for p in off["peaks"])


def test_angle_series_tools(tmp_path):
    case = next(c for c in dev_cases(kind="angle_series"))
    shutil.copy(case["dir"] / "spectrum.csv", tmp_path / "spectrum.csv")
    info = _call("load_spectrum", {"path": "spectrum.csv"}, tmp_path)
    assert info["kind"] == "angle_series" and "parallel" in info["configs"] and len(info["angles_deg"]) >= 5
    pol = _call("classify_polarization", {"path": "spectrum.csv"}, tmp_path)
    assert pol["bands"] and all(b["pattern"] in pol["pattern_classes"] for b in pol["bands"])
    fit = _call("fit_peaks", {"path": "spectrum.csv"}, tmp_path)
    assert fit["peaks"] and "angle series" in fit["notes"][0]


def test_classify_polarization_refuses_single_spectrum(tmp_path):
    case = next(c for c in dev_cases(kind="single"))
    shutil.copy(case["dir"] / "spectrum.csv", tmp_path / "spectrum.csv")
    assert "error" in _call("classify_polarization", {"path": "spectrum.csv"}, tmp_path)


def test_match_library_attaches_literature_table(tmp_path):
    out = _call("match_library", {"positions_cm1": [383.0, 408.0], "x_range_cm1": [100, 700]}, tmp_path)
    top = out["candidates"][0]
    assert top["material"] == "MoS2" and top["literature_table"] == "2H-MoS2"
    assert top["source"] and top["matched"]


def test_lookup_unknown_material_returns_error_with_options(tmp_path):
    out = _call("lookup_reference_modes", {"material": "unobtainium"}, tmp_path)
    assert "error" in out and "2H-MoS2" in out["available"]
    g = _call("lookup_reference_modes", {"material": "graphene"}, tmp_path)
    assert all(m["source"]["doi"] or m["source"]["arxiv"] for m in g["modes"])


def test_relations_list_and_apply(tmp_path):
    rels = _call("list_relations", {"material": "MoS2"}, tmp_path)["relations"]
    assert any(r["name"] == "mos2_layer_number_from_separation" for r in rels)
    res = _call("apply_relation", {"name": "mos2_layer_number_from_separation",
                                   "inputs": {"delta_E2g_A1g_cm1": 19.1}}, tmp_path)
    assert res["applicable"] and res["values"]["layer_label"] == "1L" and res["source"]["citation"]
    closed = _call("apply_relation", {"name": "mos2_layer_number_from_separation",
                                      "inputs": {"delta_E2g_A1g_cm1": 40.0}}, tmp_path)
    assert closed["applicable"] is False and closed["reason"]
    assert "error" in _call("apply_relation", {"name": "nope", "inputs": {}}, tmp_path)


def test_unknown_tool_raises(tmp_path):
    with pytest.raises(KeyError):
        toolset.call("run_python", {}, tmp_path)
