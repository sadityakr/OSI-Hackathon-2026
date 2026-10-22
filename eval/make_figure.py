"""Make the write-up figure and results table: every arm on identification and interpretation metrics.

The headline of the project is a comparison of six arms on the same held-out cases: classical library search and
the RamanLens pipeline (no LLM), and two Claude models each without and with the RamanLens skill. This script turns
the scorer and judge outputs into one two-panel figure and a markdown table for the one-page write-up.

Input:
    --id label=<run>/<arm> ...   identification arms (eval/runs/<run>/scores.json from eval/score.py)
    --int label=<run>/<arm> ...  interpretation arms (eval/runs/<run>/judge_scores.json from eval/judge.py)
Process:
    Identification metrics are averaged per arm over synthetic (syn-*) and experimental (exp-*) cases separately,
    because synthetic cases come from the database the matchers use. Interpretation: mean rubric score, caveat
    items, and citation specificity (0 to 2, shown divided by 2). Arms are colored by family (library search,
    pipeline, Haiku, Sonnet); bare LLM arms are hatched, skill arms solid.
Output:
    --out PNG (300 dpi) and the same path with .md: a table of every number in the figure plus case counts.
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # file output only, no window
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
# Okabe-Ito hues, validated as a categorical palette (dataviz validator, light surface); fixed order by family.
FAMILY_COLOR = {"library": "#CC79A7", "pipeline": "#E69F00", "haiku": "#0072B2", "sonnet": "#D55E00",
                "opus": "#009E73"}
ID_METRICS = [("id_top1", "syn", "identify\n(synthetic)"), ("id_top1", "exp", "identify\n(experimental)"),
              ("irrep_acc", "syn", "irrep\n(synthetic)"), ("pattern_acc", "syn", "polarization\n(synthetic)"),
              ("property_acc", "exp", "layers\n(experimental)")]
INT_METRICS = [("score", "rubric score"), ("kind_caveat", "caveats"), ("citation_specificity", "citations")]


def parse(specs):
    out = []
    for s in specs or []:
        label, path = s.split("=", 1)
        run, arm = path.rsplit("/", 1)
        out.append((label, run, arm))
    return out


def family(label):
    low = label.lower()
    return next((f for f in ("haiku", "sonnet", "opus", "pipeline") if f in low), "library")


def id_values(run, arm):
    rows = json.loads((ROOT / "eval" / "runs" / run / "scores.json").read_text())[arm]["cases"]
    vals = {}
    for metric, tier, _ in ID_METRICS:
        xs = [float(r[metric]) for r in rows if r["case_id"].startswith(tier + "-") and r.get(metric) is not None]
        vals[(metric, tier)] = (np.mean(xs) if xs else np.nan, len(xs))
    return vals


def int_values(run, arm):
    s = json.loads((ROOT / "eval" / "runs" / run / "judge_scores.json").read_text())["summary"][arm]
    out = {}
    for k, _ in INT_METRICS:
        v = s.get(k)
        v = np.nan if v is None else float(v) / (2.0 if k == "citation_specificity" else 1.0)
        out[k] = (v, s.get("n"))
    return out


def bars(ax, groups, arms, values):
    width = 0.8 / len(arms)
    for j, (label, *_rest) in enumerate(arms):
        fam = family(label)
        bare = "bare" in label.lower()
        xs = np.arange(len(groups)) + (j - (len(arms) - 1) / 2) * width
        ys = [values[j][g][0] for g in groups]
        ax.bar(xs, np.nan_to_num(ys), width * 0.92, color="white" if bare else FAMILY_COLOR[fam],
               edgecolor=FAMILY_COLOR[fam], hatch="////" if bare else None, linewidth=1.0, label=label)
        for x, y in zip(xs, ys):
            ax.text(x, (y if np.isfinite(y) else 0) + 0.015, f"{y:.2f}" if np.isfinite(y) else "n/a",
                    ha="center", va="bottom", fontsize=5.5, color="0.25", rotation=90)
    ax.set_ylim(0, 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, color="0.9", lw=0.6)
    ax.set_axisbelow(True)


def main():
    ap = argparse.ArgumentParser(description="Two-panel comparison figure and markdown table for the write-up.")
    ap.add_argument("--id", nargs="*", help="identification arms as label=run/arm")
    ap.add_argument("--int", dest="interp", nargs="*", help="interpretation arms as label=run/arm")
    ap.add_argument("--out", default="submission/figure.png", help="output PNG; a .md table is written next to it")
    args = ap.parse_args()
    ida, inta = parse(args.id), parse(args.interp)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [5, 3]})
    idv = [id_values(r, a) for _, r, a in ida]
    for (label, _, _), v in zip(ida, idv):
        if family(label) == "library":  # a library search has no polarization analysis: not applicable, not 0
            v[("pattern_acc", "syn")] = (np.nan, 0)
    keys = [(m, t) for m, t, _ in ID_METRICS]
    bars(a1, keys, ida, idv)
    a1.set_xticks(range(len(keys)), [lab for _, _, lab in ID_METRICS], fontsize=8)
    a1.set_ylabel("fraction correct (held-out)")
    intv = [int_values(r, a) for _, r, a in inta]
    ikeys = [k for k, _ in INT_METRICS]
    bars(a2, ikeys, inta, intv)
    a2.set_xticks(range(len(ikeys)), [lab for _, lab in INT_METRICS], fontsize=8)
    a2.set_ylabel("judge score (citations / 2)")
    handles, labels = a1.get_legend_handles_labels()
    h2, l2 = a2.get_legend_handles_labels()
    for h, l in zip(h2, l2):
        if l not in labels:
            handles.append(h)
            labels.append(l)
    fig.legend(handles, labels, loc="lower center", ncol=len(labels), fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300)

    lines = ["| arm | " + " | ".join(lab.replace("\n", " ") for _, _, lab in ID_METRICS) + " |",
             "|---|" + "---|" * len(ID_METRICS)]
    for (label, _, _), v in zip(ida, idv):
        lines.append(f"| {label} | " + " | ".join(f"{v[k][0]:.2f} (n={v[k][1]})" for k in keys) + " |")
    lines += ["", "| arm | " + " | ".join(lab for _, lab in INT_METRICS) + " (0-2) |", "|---|---|---|---|"]
    for (label, _, _), v in zip(inta, intv):
        lines.append(f"| {label} | {v['score'][0]:.2f} (n={v['score'][1]}) | {v['kind_caveat'][0]:.2f} | "
                     f"{2 * v['citation_specificity'][0]:.2f} |")
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
