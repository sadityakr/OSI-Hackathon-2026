"""Pick the interpretation case where the skill beat the bare agent most and write it up side by side.

The video needs one concrete case: what the bare agent said, what the skill said, which rubric items each met, and
which wrong claims each made. The case is chosen by the data, not by hand: largest judge-score gain of skill over
bare, ties broken by fewer wrong claims in the skill arm. Pass --case to inspect any other case, including cases
where the skill lost: report those too.

Input:
    eval/runs/<run>/judge_scores.json (from eval/judge.py), plus report.json per arm and case.
Process:
    Rank cases by score(skill) - score(bare); take the best (or --case); collect rubric item grades with the judge's
    reason, wrong claims asserted, and the report summaries.
Output:
    submission/case-study.md (or --out), plus the full ranking printed to the terminal.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def find_case(case_id):
    for split in ("heldout", "dev_interpret", "dev"):
        d = ROOT / "data" / "test_set" / split / case_id
        if (d / "rubric.json").exists():
            return d
    raise SystemExit(f"rubric for {case_id} not found")


def grades_by_id(judged):
    return {g["id"]: g for g in judged.get("grades", {}).get("items", [])}


def main():
    ap = argparse.ArgumentParser(description="Side-by-side case study from a judged interpretation run.")
    ap.add_argument("run", help="run name under eval/runs, e.g. final-int")
    ap.add_argument("--bare", default="bare")
    ap.add_argument("--skill", default="skill")
    ap.add_argument("--case", help="case id; default: the case with the largest skill gain")
    ap.add_argument("--out", default="submission/case-study.md")
    args = ap.parse_args()

    run = ROOT / "eval" / "runs" / args.run
    cases = json.loads((run / "judge_scores.json").read_text())["cases"]
    bare, skill = cases[args.bare], cases[args.skill]
    ranking = []
    for cid in sorted(set(bare) & set(skill)):
        b, s = bare[cid], skill[cid]
        if b.get("score") is None or s.get("score") is None:
            continue
        ranking.append((s["score"] - b["score"], -len(s.get("wrong_claims_made", [])), cid))
    ranking.sort(reverse=True)
    print("case".ljust(34), "skill - bare score")
    for gain, _, cid in ranking:
        print(cid.ljust(34), f"{gain:+.2f}")
    cid = args.case or ranking[0][2]

    rubric = json.loads((find_case(cid) / "rubric.json").read_text())
    b, s = bare[cid], skill[cid]
    gb, gs = grades_by_id(b), grades_by_id(s)
    wrong_text = {w["id"]: w["text"] for w in rubric.get("wrong_claims", [])}

    lines = [f"# Case study: {cid}", "",
             f"Selection: {'chosen with --case' if args.case else 'largest judge-score gain of skill over bare'}"
             f" in run `{args.run}`. Paper behind the case: {rubric['source']['paper']}.", "",
             f"Judge score: bare {b['score']:.2f}, skill {s['score']:.2f}. Citation specificity (0 to 2): bare "
             f"{b.get('citation_specificity')}, skill {s.get('citation_specificity')}.", "",
             "## Rubric items (judge grades: 1 met, 0.5 partly, 0 not met)", "",
             "| item | kind | what the paper says | bare | skill |", "|---|---|---|---|---|"]
    for it in rubric["items"]:
        i = it["id"]
        lines.append(f"| {i} | {it['kind']} | {it['text']} | {gb.get(i, {}).get('met', '-')} | "
                     f"{gs.get(i, {}).get('met', '-')} |")
    lines += ["", "## Wrong claims asserted", ""]
    for arm, res in (("bare", b), ("skill", s)):
        made = res.get("wrong_claims_made", [])
        lines.append(f"- {arm}: " + ("; ".join(f"{w} ({wrong_text.get(w, '')})" for w in made) if made else "none"))
    lines += ["", "## Where the two arms differ, with the judge's reason", ""]
    for it in rubric["items"]:
        i = it["id"]
        if gb.get(i, {}).get("met") != gs.get(i, {}).get("met"):
            lines += [f"**{i} ({it['kind']})**: {it['text']}",
                      f"- bare ({gb.get(i, {}).get('met')}): {gb.get(i, {}).get('why', '')}",
                      f"- skill ({gs.get(i, {}).get('met')}): {gs.get(i, {}).get('why', '')}", ""]
    for arm in (args.bare, args.skill):
        rep = json.loads((run / arm / cid / "report.json").read_text(encoding="utf-8"))
        lines += [f"## {arm} summary", "", rep.get("summary", ""), ""]
    out = ROOT / args.out
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
