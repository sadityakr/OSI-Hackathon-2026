"""Score agent reports against test-set truth, per case and aggregated per arm.

This is the yardstick for the headline comparison (bare agent vs agent with RamanLens tools) and for the build
loop's dev-set progress. It must stay independent of the RamanLens package so that it cannot be bent by the code
it measures; the build loop is denied write access to this file.

Input:
    A run directory produced by eval/run_agent.py: <run>/<arm>/<case_id>/report.json and transcript.json.
    Truth from data/test_set/<split>/<case_id>/truth.json.
Process:
    Material match by normalized element counts (so '2H-WS2' == 'WS2' == 'S2W'); hint verdicts; peak recall and
    precision within each truth peak's tolerance; irrep and polarization-pattern accuracy on matched peaks;
    cosmic-ray handling; a leak flag if the transcript mentions truth files.
Output:
    Prints a per-arm summary table and writes <run>/scores.json (per case and aggregate).
"""

import argparse
import json
import math
import re
from pathlib import Path

ALIASES = {"graphene": "C", "graphite": "C", "hbn": "BN", "boronnitride": "BN", "hexagonalboronnitride": "BN"}
POLYTYPE = re.compile(r"^(\d[hrt]\d?|h|t|1t'|td)[-_ ]", re.IGNORECASE)


def element_counts(name):
    """Reduced element-count dict for a material string, or None if it is not parseable."""
    s = re.sub(r"\(.*?\)", "", str(name)).strip()
    s = POLYTYPE.sub("", s)
    key = re.sub(r"[\s\-_']", "", s).lower()
    if key in ALIASES:
        s = ALIASES[key]
    s = re.sub(r"[\s\-_]", "", s)
    parts = re.findall(r"([A-Z][a-z]?)(\d*\.?\d*)", s)
    if not parts or "".join(e + n for e, n in parts) != s:
        return None
    counts = {}
    for el, n in parts:
        counts[el] = counts.get(el, 0) + (float(n) if n else 1.0)
    g = 0
    for v in counts.values():
        if v != int(v):
            return {k: round(v, 3) for k, v in counts.items()}
        g = math.gcd(g, int(v))
    return {k: int(v) // g for k, v in counts.items()}


PHASE_PREFIX = re.compile(r"^([a-z]|[α-ω]|\d[hrt]\d?|1t'|td)-", re.IGNORECASE)


def material_counts(name):
    """element_counts of a candidate name, tolerating descriptive words ('monolayer graphene', 'm-GaTe (thin)',
    'β-TiNCl'): try the whole string, then each word with a phase prefix stripped."""
    c = element_counts(name)
    if c is not None:
        return c
    for word in re.sub(r"\(.*?\)", " ", str(name)).replace("/", " ").split():
        c = element_counts(PHASE_PREFIX.sub("", word))
        if c is not None:
            return c
    return None


def same_material(a, b):
    ca, cb = material_counts(a), material_counts(b)
    return ca is not None and ca == cb


def norm_irrep(s):
    """Canonical Mulliken label: superscript mode index and trailing mode number dropped ('E^1_2g' -> 'e2g',
    'Ag2' -> 'ag', "A1'" -> 'a1p')."""
    s = re.sub(r"\^\{?\d+\}?", "", str(s or ""))
    s = re.sub(r"[\s_{}()]", "", s).replace("'", "p")
    s = re.sub(r"(?<=[gu])\d+$", "", s)
    return s.lower()


def irrep_matches(truth, reported):
    """True if the truth irrep equals the reported one, or one of several in a combined label like 'A1g+E2g'."""
    t = norm_irrep(truth)
    if not t:
        return None
    # Alternatives in parentheses count too: "E2g (E' in the monolayer)" contains "E2g" and "E'".
    parts = re.split(r"[+,/()]| and | in | or ", str(reported or ""))
    return any(norm_irrep(part.split()[0]) == t for part in parts if part.strip())


PROPERTY_SYNONYMS = {
    "layers": ["layers", "layer", "layernumber", "numberoflayers", "nlayers", "thickness"],
    "defect_level": ["defectlevel", "defects", "defect", "disorder", "defectdensity"],
    "L_D_nm": ["ldnm", "ld", "interdefectdistance", "defectdistance"],
    "strain_sign": ["strainsign", "strain"],
    "doping_type": ["dopingtype", "doping"],
    "phase": ["phase", "polytype"],
}


def _norm_name(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def property_matches(key, want, reported):
    """Compare one truth property with the report's properties list.

    Truth value forms: an int (exact, e.g. layers), [lo, hi] (the first number in the reported value must lie in the
    range), or a string (the reported value must contain it, case-insensitive, e.g. 'tensile', 'high').
    Returns None if the report has no property with a matching name, which scores as wrong.
    """
    names = PROPERTY_SYNONYMS.get(key, [_norm_name(key)])
    hits = [p for p in reported if _norm_name(p.get("name", "")) in names
            or any(n in _norm_name(p.get("name", "")) for n in names if len(n) > 4)]
    if not hits:
        return None
    value = str(hits[0].get("value", ""))
    for word, n in (("monolayer", "1"), ("single layer", "1"), ("bilayer", "2"), ("trilayer", "3")):
        value = re.sub(word, n, value, flags=re.IGNORECASE)
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", value)]
    if isinstance(want, bool) or isinstance(want, str):
        return str(want).lower() in value.lower()
    if isinstance(want, (int, float)):
        return bool(nums) and nums[0] == want
    if isinstance(want, list) and len(want) == 2:
        return bool(nums) and want[0] <= nums[0] <= want[1]
    return None


def score_case(report, truth, inp, transcript_text=""):
    res = {"case_id": truth["case_id"], "task": inp["task"], "kind": inp["kind"]}
    cands = [c["material"] for c in report.get("candidates", [])]
    if inp["task"] == "identify":
        res["id_top1"] = bool(cands) and same_material(cands[0], truth["formula"])
        res["id_top3"] = any(same_material(c, truth["formula"]) for c in cands[:3])
    else:
        want = "consistent" if truth["hint_is_correct"] else "inconsistent"
        res["hint_correct"] = report.get("hint_verdict") == want

    rep = [p for p in report.get("peaks", []) if isinstance(p.get("position_cm1"), (int, float))]
    tpk = truth["peaks"]
    used, matched = set(), []
    for t in tpk:
        best = None
        for j, p in enumerate(rep):
            d = abs(p["position_cm1"] - t["position_cm1"])
            if j not in used and d <= t["tolerance_cm1"] and (best is None or d < best[0]):
                best = (d, j)
        if best:
            used.add(best[1])
            matched.append((t, rep[best[1]]))
    res["peak_recall"] = len(matched) / len(tpk) if tpk else None
    res["peak_precision"] = len(used) / len(rep) if rep else (None if not tpk else 0.0)
    res["position_mae_cm1"] = (sum(abs(t["position_cm1"] - p["position_cm1"]) for t, p in matched) / len(matched)
                               if matched else None)
    irr = [irrep_matches(t["irrep"], p.get("irrep") or p.get("assignment")) for t, p in matched
           if not t.get("substrate") and t.get("irrep")]
    irr = [x for x in irr if x is not None]
    res["irrep_acc"] = sum(irr) / len(irr) if irr else None
    if inp["kind"] == "angle_series":
        pat = [(t["pattern"] == p.get("pattern")) for t, p in matched if t.get("pattern")]
        res["pattern_acc"] = sum(pat) / len(pat) if pat else None

    # Only standard keys are scored; free-text properties in older truth files (e.g. 'D_cause_stated') stay notes.
    want_props = {k: v for k, v in (truth.get("properties") or {}).items() if k in PROPERTY_SYNONYMS}
    if want_props:
        got = [bool(property_matches(k, v, report.get("properties", []))) for k, v in want_props.items()]
        res["property_acc"] = sum(got) / len(got)

    notes = truth.get("notes")
    try:
        extra = json.loads(notes) if notes else {}
    except (TypeError, ValueError):
        extra = {}
    spikes = [a["position_cm1"] for a in extra.get("artifacts", []) if a.get("type") == "cosmic_ray"]
    if spikes:
        as_peak = any(abs(p["position_cm1"] - s) < 3 for p in rep for s in spikes)
        res["cosmic_ray_rejected"] = not as_peak

    res["leak_suspect"] = bool(re.search(r"truth\.json|test_set[/\\](dev|heldout)", transcript_text))
    return res


def aggregate(rows):
    keys = ["id_top1", "id_top3", "hint_correct", "peak_recall", "peak_precision", "irrep_acc", "pattern_acc",
            "property_acc", "cosmic_ray_rejected", "position_mae_cm1"]
    out = {"n_cases": len(rows)}
    for k in keys:
        vals = [float(r[k]) for r in rows if r.get(k) is not None]
        out[k] = round(sum(vals) / len(vals), 3) if vals else None
        out[k + "_n"] = len(vals)
    out["leak_suspects"] = [r["case_id"] for r in rows if r.get("leak_suspect")]
    out["failed_runs"] = [r["case_id"] for r in rows if r.get("failed")]
    return out


def main():
    ap = argparse.ArgumentParser(description="Score a run directory of agent reports against test-set truth.")
    ap.add_argument("run_dir", help="eval/runs/<run_name>, containing one folder per arm")
    ap.add_argument("--test-set", default="data/test_set", help="test-set root with dev/ and heldout/")
    args = ap.parse_args()
    run = Path(args.run_dir)
    ts = Path(args.test_set)
    result = {}
    for arm_dir in sorted(p for p in run.iterdir() if p.is_dir()):
        rows = []
        for case_dir in sorted(p for p in arm_dir.iterdir() if p.is_dir()):
            # Only identification cases have truth.json; interpretation cases (int-*, rubric.json) go to judge.py.
            case = next((ts / s / case_dir.name for s in ("dev", "dev_hard", "heldout")
                         if (ts / s / case_dir.name / "truth.json").exists()), None)
            if case is None:
                continue
            truth = json.loads((case / "truth.json").read_text())
            inp = json.loads((case / "input.json").read_text())
            rp = case_dir / "report.json"
            if not rp.exists():
                rows.append({"case_id": case_dir.name, "failed": True})
                continue
            tr = case_dir / "transcript.json"
            rows.append(score_case(json.loads(rp.read_text()), truth, inp, tr.read_text() if tr.exists() else ""))
        result[arm_dir.name] = {"aggregate": aggregate(rows), "cases": rows}
    (run / "scores.json").write_text(json.dumps(result, indent=2))
    keys = ["n_cases", "id_top1", "id_top3", "hint_correct", "peak_recall", "peak_precision", "irrep_acc",
            "pattern_acc", "property_acc", "cosmic_ray_rejected", "position_mae_cm1"]
    print("metric".ljust(22) + "".join(a.ljust(14) for a in result))
    for k in keys:
        print(k.ljust(22) + "".join(str(result[a]["aggregate"].get(k)).ljust(14) for a in result))
    for a in result:
        if result[a]["aggregate"]["leak_suspects"] or result[a]["aggregate"]["failed_runs"]:
            print(a, "leak suspects:", result[a]["aggregate"]["leak_suspects"],
                  "failed:", result[a]["aggregate"]["failed_runs"])


if __name__ == "__main__":
    main()
