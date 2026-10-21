"""Self-tests of the evaluation scorer: an oracle report scores perfectly, a wrong one does not."""

import json

from cases import dev_cases
from score import aggregate, element_counts, irrep_matches, same_material, score_case


def oracle_report(case):
    t, inp = case["truth"], case["input"]
    peaks = [dict(position_cm1=p["position_cm1"], fwhm_cm1=None, assignment=p["label"], irrep=p["irrep"],
                  pattern=p.get("pattern"), provenance="literature", source="oracle") for p in t["peaks"]]
    verdict = "not_applicable"
    if inp["task"] == "verify":
        verdict = "consistent" if t["hint_is_correct"] else "inconsistent"
    return dict(candidates=[dict(material=t["formula"], confidence=1.0, evidence="")], hint_verdict=verdict,
                hint_reasoning="", peaks=peaks, properties=[], artifacts=[], citations=[], limits=[])


def test_material_normalization():
    assert same_material("2H-WS2", "WS2")
    assert same_material("S2W", "WS2")
    assert same_material("hBN", "BN")
    assert same_material("graphene", "C")
    assert same_material("MoS2 (molybdenite)", "MoS2")
    assert not same_material("MoS2", "WS2")
    assert not same_material("MoSe2", "MoS2")
    assert element_counts("Bi2Te2Se") == {"Bi": 2, "Te": 2, "Se": 1}


def test_irrep_matching():
    assert irrep_matches("E2g", "E2g")
    assert irrep_matches("E2g", "E^1_2g")
    assert irrep_matches("A1g", "A1g")
    assert irrep_matches("Ag", "Ag2")
    assert not irrep_matches("A1g", "E2g")


def test_oracle_scores_perfect_on_every_dev_case():
    cases = dev_cases()
    assert cases, "no dev cases found; run eval/synth/make_synthetic.py"
    rows = [score_case(oracle_report(c), c["truth"], c["input"]) for c in cases]
    agg = aggregate(rows)
    for k in ("id_top1", "hint_correct", "peak_recall", "peak_precision", "irrep_acc", "pattern_acc"):
        assert agg[k] in (None, 1.0), (k, agg[k])


def test_wrong_report_scores_zero():
    c = next(c for c in dev_cases() if c["input"]["task"] == "identify")
    rep = oracle_report(c)
    rep["candidates"] = [dict(material="Bi2Se3" if c["truth"]["formula"] != "Bi2Se3" else "WS2",
                              confidence=1.0, evidence="")]
    for p in rep["peaks"]:
        p["position_cm1"] += 50
    r = score_case(rep, c["truth"], c["input"])
    assert r["id_top1"] is False and r["peak_recall"] == 0.0


def test_leak_flag():
    c = dev_cases()[0]
    r = score_case(oracle_report(c), c["truth"], c["input"], transcript_text=json.dumps("open('../truth.json')"))
    assert r["leak_suspect"]
