"""Deterministic tool-only probe over the dev and dev_hard cases (build loop T11 diagnostics, throwaway).

Runs the RamanLens toolset the way a minimal agent would (fit_peaks, drop substrate lines, match_library with the
analysed range, classify_polarization for angle series), turns the result into a report, and scores it with
eval/score.py. Reads dev truth only; never touches heldout.

Input:
    data/test_set/dev and data/test_set/dev_hard case folders.
Process:
    For each case: toolset calls, a report with candidates, peaks (irrep from the top candidate's matched label) and
    patterns, then eval.score.score_case. Prints per-case lines with misses and extras.
Output:
    Text table on stdout.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval.score import score_case  # noqa: E402
from ramanlens.agent import toolset  # noqa: E402


def run_case(case: Path):
    inp = json.loads((case / "input.json").read_text())
    truth = json.loads((case / "truth.json").read_text())
    fit = json.loads(toolset.call("fit_peaks", {"path": "spectrum.csv", "substrate": inp.get("substrate")}, case))
    peaks = [p for p in fit["peaks"] if not p["is_substrate"]]
    rep_peaks = [{"position_cm1": p["position_cm1"]} for p in fit["peaks"]]
    m = json.loads(toolset.call("match_library", {"positions_cm1": [p["position_cm1"] for p in peaks],
                                                  "intensities": [p["height"] for p in peaks],
                                                  "x_range_cm1": fit["analysed_range_cm1"]}, case))
    cands = m["candidates"]
    if cands:
        lab = {round(mm["measured_cm1"], 2): mm["label"] for mm in cands[0]["matched"]}
        for rp in rep_peaks:
            rp["irrep"] = lab.get(round(rp["position_cm1"], 2))
    if inp["kind"] == "angle_series":
        pol = json.loads(toolset.call("classify_polarization", {"path": "spectrum.csv"}, case))
        for rp in rep_peaks:
            near = [b for b in pol["bands"] if abs(b["position_cm1"] - rp["position_cm1"]) < 3]
            if near:
                rp["pattern"] = near[0]["pattern"]
    report = {"candidates": [{"material": c["material"]} for c in cands], "peaks": rep_peaks, "properties": []}
    if inp["task"] == "verify":
        report["hint_verdict"] = "consistent"
    s = score_case(report, truth, inp)
    tpos = [t["position_cm1"] for t in truth["peaks"]]
    rpos = [p["position_cm1"] for p in rep_peaks]
    miss = [t for t in truth["peaks"] if not any(abs(r - t["position_cm1"]) <= t["tolerance_cm1"] for r in rpos)]
    extra = [r for r in rpos if not any(abs(r - t) <= 5 for t in tpos)]
    return s, truth, cands, miss, extra, fit


def main():
    splits = sys.argv[1:] or ["dev", "dev_hard"]
    for split in splits:
        print(f"== {split}")
        for case in sorted((ROOT / "data/test_set" / split).iterdir()):
            if not (case / "input.json").exists():
                continue
            s, truth, cands, miss, extra, fit = run_case(case)
            top = [f"{c['material']}({c['score']:.2f},{c['kind'][:3]})" for c in cands[:3]]
            print(f"{case.name:20s} truth={truth['formula']:8s} top1={s.get('id_top1')} top3={s.get('id_top3')} "
                  f"hint={s.get('hint_correct')} rec={s['peak_recall']} prec={s['peak_precision']} "
                  f"irr={s['irrep_acc']} pat={s.get('pattern_acc')} cos={s.get('cosmic_ray_rejected')}")
            print(f"    cands={top}")
            if miss:
                print(f"    missed={[(t['position_cm1'], t.get('irrep'), t.get('tolerance_cm1')) for t in miss]}")
            if extra:
                print(f"    extra={extra} spikes={fit['spikes_cm1']}")


if __name__ == "__main__":
    main()
