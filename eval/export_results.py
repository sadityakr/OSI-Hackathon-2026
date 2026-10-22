"""Copy the results of evaluation runs into the tracked results/ folder, without the bulky transcripts.

eval/runs/ holds everything an arm produced, including full agent transcripts with embedded plot images (about
100 MB), and is not committed. Collaborators and judges need the outcome of every arm, with and without the skill:
each report, each judge grade, the aggregate scores, and what each run cost. This script copies exactly those.

Input:
    eval/runs/<run>/ for every run except smoke tests and probes (or the runs named with --runs).
Process:
    Per case: report.json and judge.json copied; transcript.json reduced to its usage block (tokens, cost in USD as
    reported by Claude Code, turns, seconds) and model. Per run: scores.json and judge_scores.json copied.
Output:
    results/<run>/<arm>/<case>/{report.json, judge.json, usage.json} and results/<run>/{scores,judge_scores}.json.
"""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PREFIXES = ("smoke", "probe")


def main():
    ap = argparse.ArgumentParser(description="Export evaluation results (no transcripts) into results/.")
    ap.add_argument("--runs", nargs="*", default=None, help="run names to export (default: all except smoke/probe)")
    args = ap.parse_args()
    src_root, dst_root = ROOT / "eval" / "runs", ROOT / "results"
    runs = args.runs or sorted(p.name for p in src_root.iterdir() if p.is_dir() and not p.name.startswith(SKIP_PREFIXES))
    for run in runs:
        src = src_root / run
        dst = dst_root / run
        if dst.exists():
            shutil.rmtree(dst)
        for f in ("scores.json", "judge_scores.json"):
            if (src / f).exists():
                dst.mkdir(parents=True, exist_ok=True)
                shutil.copy(src / f, dst / f)
        n = 0
        for case in sorted(src.glob("*/*/")):
            out = dst / case.parent.name / case.name
            for f in ("report.json", "judge.json"):
                if (case / f).exists():
                    out.mkdir(parents=True, exist_ok=True)
                    shutil.copy(case / f, out / f)
            tr = case / "transcript.json"
            if tr.exists() and out.exists():
                t = json.loads(tr.read_text(encoding="utf-8"))
                (out / "usage.json").write_text(json.dumps({k: t.get(k) for k in ("arm", "model", "effort", "usage")},
                                                           indent=1), encoding="utf-8")
            n += out.exists()
        print(f"{run}: {n} cases")


if __name__ == "__main__":
    main()
