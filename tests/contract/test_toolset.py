"""Contract for the agent toolset that eval/run_agent.py exposes to the tooled arm."""

import json
import shutil

from cases import dev_cases

REQUIRED = {"load_spectrum", "fit_peaks", "match_library", "classify_polarization", "lookup_reference_modes",
            "list_relations", "apply_relation"}


def test_tool_definitions_are_valid():
    from ramanlens.agent import toolset
    names = [t["name"] for t in toolset.TOOLS]
    assert len(names) == len(set(names))
    assert REQUIRED <= set(names), REQUIRED - set(names)
    assert not {"run_python", "submit_report"} & set(names), "reserved for the harness"
    for t in toolset.TOOLS:
        assert t["description"] and len(t["description"]) > 40
        assert t["input_schema"]["type"] == "object"


def test_tools_run_on_a_dev_case(tmp_path):
    from ramanlens.agent import toolset
    case = next(c for c in dev_cases(kind="single"))
    shutil.copy(case["dir"] / "spectrum.csv", tmp_path / "spectrum.csv")
    out = json.loads(toolset.call("load_spectrum", {"path": "spectrum.csv"}, tmp_path))
    assert out["n_points"] > 100
    fit = json.loads(toolset.call("fit_peaks", {"path": "spectrum.csv"}, tmp_path))
    assert fit["peaks"] and all("position_cm1" in p for p in fit["peaks"])
    m = json.loads(toolset.call("match_library", {"positions_cm1": [356.0, 418.0]}, tmp_path))
    assert m["candidates"] and all("source" in c for c in m["candidates"])


def test_tool_outputs_are_json_with_provenance(tmp_path):
    from ramanlens.agent import toolset
    out = json.loads(toolset.call("lookup_reference_modes", {"material": "2H-MoS2"}, tmp_path))
    assert out["modes"] and all(m.get("source") for m in out["modes"])
