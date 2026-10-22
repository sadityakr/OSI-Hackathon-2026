"""Probe the RamanLens toolset on the dev and dev_hard cases and print per-case weak spots.

Throwaway diagnostic for loop task T11 (hardening). It reads only dev and dev_hard truth, never held-out truth.

Input: data/test_set/dev*/<case>/ (input.json, spectrum.csv, truth.json).
Process: runs load_spectrum, fit_peaks, match_library and classify_polarization through ramanlens.agent.toolset,
then matches fitted peaks to truth peaks within tolerance.
Output: one block per case on stdout plus totals (peak recall, precision, top-1 and top-3 identification, pattern acc).
"""
import json
import sys
from pathlib import Path

from ramanlens.agent import toolset

ROOT = Path(__file__).resolve().parents[2]
splits = sys.argv[1:] or ["dev", "dev_hard"]
tot = dict(tp=0, truth=0, fit=0, top1=0, top3=0, n=0, pat_ok=0, pat_n=0)
for split in splits:
    for case in sorted((ROOT / "data/test_set" / split).iterdir()):
        inp = json.loads((case / "input.json").read_text())
        truth = json.loads((case / "truth.json").read_text())
        wd = str(case)
        sub = inp.get("substrate")
        fit = json.loads(toolset.call("fit_peaks", {"path": "spectrum.csv", **({"substrate": sub} if sub else {})}, wd))
        if "error" in fit:
            print(case.name, "FIT ERROR", fit)
            continue
        peaks = fit["peaks"]
        tpeaks = [p for p in truth["peaks"] if not p.get("substrate")]
        found, missed = [], []
        for t in tpeaks:
            near = [p for p in peaks if abs(p["position_cm1"] - t["position_cm1"]) <= t["tolerance_cm1"]]
            (found if near else missed).append(t["position_cm1"])
        nonsub = [p for p in peaks if not p.get("is_substrate")]
        extra = [round(p["position_cm1"], 1) for p in nonsub
                 if not any(abs(p["position_cm1"] - t["position_cm1"]) <= t["tolerance_cm1"] for t in tpeaks)]
        tot["tp"] += len(found); tot["truth"] += len(tpeaks); tot["fit"] += len(nonsub)
        pos = [p["position_cm1"] for p in nonsub]
        ints = [p["height"] for p in nonsub]
        lo, hi = fit["analysed_range_cm1"]
        args = {"positions_cm1": pos, "intensities": ints, "top_k": 5}
        if lo is not None:
            args["x_range_cm1"] = [lo, hi]
        m = json.loads(toolset.call("match_library", args, wd))
        names = [c.get("formula") or c.get("material") for c in m.get("candidates", [])]
        f = truth.get("formula")
        rank = next((i + 1 for i, nm in enumerate(names) if nm and f and nm.replace("-", "").lower().endswith(f.lower())), None)
        if inp.get("task") == "identify" or True:
            tot["n"] += 1; tot["top1"] += rank == 1; tot["top3"] += bool(rank and rank <= 3)
        line = f"{split}/{case.name}: found {len(found)}/{len(tpeaks)} missed {missed} extra {extra} rank {rank} top {names[:3]}"
        if inp.get("kind") == "angle_series":
            pol = json.loads(toolset.call("classify_polarization", {"path": "spectrum.csv"}, wd))
            bands = pol.get("peaks") or pol.get("bands") or []
            for t in tpeaks:
                if "pattern" not in t:
                    continue
                tot["pat_n"] += 1
                b = min(bands, key=lambda b: abs(b["position_cm1"] - t["position_cm1"]), default=None)
                if b and abs(b["position_cm1"] - t["position_cm1"]) <= t["tolerance_cm1"] and b.get("pattern") == t["pattern"]:
                    tot["pat_ok"] += 1
                else:
                    line += f"\n    pattern miss at {t['position_cm1']}: truth {t['pattern']} got {b and (round(b['position_cm1'],1), b.get('pattern'))}"
        print(line)
print(tot)
