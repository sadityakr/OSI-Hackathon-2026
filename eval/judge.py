"""Grade interpretation reports against expert rubrics with a blind LLM judge, per case and per arm.

Interpretation cases (data/test_set/INTERPRET.md) have no single right label: the answer is a set of findings,
caveats and questions that the source paper supports. A judge model checks each rubric item against the report.
The judge never sees which arm wrote the report, and it has no tools, so it grades only what is written.

Input:
    A run directory from eval/run_claude_code.py (<run>/<arm>/<case_id>/report.json), and each case's input.json and
    rubric.json found under data/test_set/{dev_interpret,heldout}/<case_id>/.
Process:
    For each report, one headless `claude -p` call (default Opus, no tools, structured output) grades every rubric
    item as met (1), partly met (0.5) or not met (0), every wrong claim as made or not, and rates citation
    specificity (0 none, 1 papers named, 2 papers with figure/table locators). Case score = (sum of weight x met -
    sum of penalties of wrong claims made) / sum of weights, floored at 0. Results are cached per report.
Output:
    <run>/<arm>/<case_id>/judge.json, <run>/judge_scores.json, and a table per arm (overall and by item kind).
"""

import argparse
import hashlib
import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ("dev_interpret", "heldout")

JUDGE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["items", "wrong_claims", "citation_specificity"],
    "properties": {
        "items": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["id", "met", "why"],
            "properties": {"id": {"type": "string"}, "met": {"type": "number", "enum": [0, 0.5, 1]},
                           "why": {"type": "string"}}}},
        "wrong_claims": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["id", "made", "why"],
            "properties": {"id": {"type": "string"}, "made": {"type": "boolean"}, "why": {"type": "string"}}}},
        "citation_specificity": {"type": "integer", "enum": [0, 1, 2]},
    },
}

INSTRUCTIONS = """You grade a Raman spectroscopy analysis report against an expert rubric written from a published
paper. Grade only what the report states; do not reward knowledge you have that the report does not show.

For each rubric item: met = 1 if the report clearly makes the point (same physics, numbers within the stated
range if the item has numbers), 0.5 if it makes it partly or vaguely, 0 if absent or contradicted. A point counts
wherever it appears (summary, observations, caveats, questions, limits).
For each wrong claim: made = true only if the report asserts it (mentioning it in order to reject it is not made).
citation_specificity: 0 if literature claims carry no sources, 1 if papers are named, 2 if most literature claims
name a paper and a figure, table or equation.
Give a one-sentence reason for each grade, quoting the report where possible."""


def find_case(case_id):
    for s in SPLITS:
        d = ROOT / "data" / "test_set" / s / case_id
        if (d / "rubric.json").exists():
            return d
    return None


def judge_one(report_path, case_dir, model):
    out = report_path.parent / "judge.json"
    report = report_path.read_text(encoding="utf-8")
    rubric = json.loads((case_dir / "rubric.json").read_text(encoding="utf-8"))
    key = hashlib.sha256((report + json.dumps(rubric) + model).encode()).hexdigest()[:16]
    if out.exists():
        cached = json.loads(out.read_text(encoding="utf-8"))
        if cached.get("key") == key:
            return cached
    grading_rubric = {"items": [{k: i[k] for k in ("id", "kind", "text")} for i in rubric["items"]],
                      "wrong_claims": [{k: w[k] for k in ("id", "text")} for w in rubric.get("wrong_claims", [])]}
    prompt = (f"{INSTRUCTIONS}\n\n## Case given to the analyst\n{(case_dir / 'input.json').read_text()}\n\n"
              f"## Rubric\n{json.dumps(grading_rubric, indent=1)}\n\n## Report\n{report}")
    cmd = ["claude", "-p", "--model", model, "--json-schema", json.dumps(JUDGE_SCHEMA),
           "--setting-sources", "project", "--strict-mcp-config", "--permission-mode", "dontAsk",
           "--disallowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch", "Agent",
           "--output-format", "json", "--no-session-persistence"]
    with tempfile.TemporaryDirectory() as tmp:  # empty folder: the judge sees nothing but the prompt
        p = subprocess.run(cmd, input=prompt, cwd=tmp, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900)
    try:
        grades = json.loads(p.stdout)["structured_output"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return {"key": key, "error": (p.stdout or p.stderr)[-2000:]}

    weights = {i["id"]: i.get("weight", 1) for i in rubric["items"]}
    kinds = {i["id"]: i.get("kind", "finding") for i in rubric["items"]}
    penalties = {w["id"]: w.get("penalty", 1) for w in rubric.get("wrong_claims", [])}
    met = {g["id"]: g["met"] for g in grades["items"] if g["id"] in weights}
    total = sum(weights.values())
    gained = sum(weights[i] * met.get(i, 0) for i in weights)
    lost = sum(penalties[w["id"]] for w in grades["wrong_claims"] if w["made"] and w["id"] in penalties)
    by_kind = {}
    for i, w in weights.items():
        k = kinds[i]
        g, t = by_kind.get(k, (0.0, 0.0))
        by_kind[k] = (g + w * met.get(i, 0), t + w)
    result = {"key": key, "score": max(0.0, (gained - lost) / total) if total else None,
              "by_kind": {k: g / t for k, (g, t) in by_kind.items() if t},
              "wrong_claims_made": [w["id"] for w in grades["wrong_claims"] if w["made"]],
              "citation_specificity": grades["citation_specificity"], "grades": grades, "judge_model": model}
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def main():
    ap = argparse.ArgumentParser(description="Grade interpretation reports with a blind rubric judge.")
    ap.add_argument("run_dir", help="eval/runs/<run_name> with one folder per arm")
    ap.add_argument("--model", default="claude-opus-5-5", help="judge model (keep it fixed across runs)")
    ap.add_argument("--parallel", type=int, default=4, help="reports graded at the same time")
    args = ap.parse_args()
    run = Path(args.run_dir)

    jobs = []
    for arm in sorted(p for p in run.iterdir() if p.is_dir()):
        for case in sorted(p for p in arm.iterdir() if p.is_dir()):
            cd = find_case(case.name)
            if cd is not None:
                jobs.append((arm.name, case.name, case / "report.json", cd))

    def run_job(job):
        arm, case, rp, cd = job
        if not rp.exists():
            return arm, case, {"score": 0.0, "failed": True}
        return arm, case, judge_one(rp, cd, args.model)

    results = {}
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        for arm, case, res in pool.map(run_job, jobs):
            results.setdefault(arm, {})[case] = res
            print(f"{arm} {case}: score {res.get('score')} cites {res.get('citation_specificity')} "
                  f"{'ERROR' if 'error' in res else ''}", flush=True)

    summary = {}
    for arm, cases in results.items():
        kinds = sorted({k for r in cases.values() for k in r.get("by_kind", {})})
        summary[arm] = {"n": len(cases), "score": mean([r.get("score") for r in cases.values()]),
                        "citation_specificity": mean([r.get("citation_specificity") for r in cases.values()]),
                        "wrong_claims_made": sum(len(r.get("wrong_claims_made", [])) for r in cases.values()),
                        **{f"kind_{k}": mean([r.get("by_kind", {}).get(k) for r in cases.values()]) for k in kinds}}
    (run / "judge_scores.json").write_text(json.dumps({"summary": summary, "cases": results}, indent=1))
    keys = sorted({k for s in summary.values() for k in s})
    print("metric".ljust(26) + "".join(a.ljust(14) for a in summary))
    for k in keys:
        print(k.ljust(26) + "".join(str(summary[a].get(k)).ljust(14) for a in summary))


if __name__ == "__main__":
    main()
