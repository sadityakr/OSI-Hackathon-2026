"""Write-up figure: (a) CrSBr Raman spectra of six flakes with the analysed features,
(b) bare agent vs agent with the Raman skill, development results (skill v3).

Data: submission/demo/crsbr-thickness/data (Zenodo 15048152, Wdowik et al. 2025, CC BY 4.0).
Ag1 fit positions: dry run 4, submission/demo/README.md. Scores: results/README.md.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.gridspec import GridSpec

DATA = Path(sys.argv[1] if len(sys.argv) > 1 else "submission/demo/crsbr-thickness/data")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "submission/figure_raman_skill")

MAROON, GREY, SLATE, LIGHT = "#6E1A2A", "#9AA5AB", "#31515D", "#E7E6E6"
for f in font_manager.findSystemFonts():
    if "Carlito" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "Carlito" if any("Carlito" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans",
    "font.size": 9, "axes.edgecolor": SLATE, "axes.labelcolor": SLATE, "xtick.color": SLATE, "ytick.color": SLATE,
    "axes.linewidth": 1.2, "axes.spines.top": False, "axes.spines.right": False, "text.color": SLATE,
})

# AFM thickness order (answer key, never seen by the agent) and the skill's Ag1 fits (dry run 4)
order = [("C", "1L"), ("E", "2L"), ("A", "3L"), ("F", "5L"), ("D", "6L"), ("B", "bulk")]
ag1_fit = {"C": 103.1, "E": 103.3, "A": 108.6, "F": 111.9, "D": 113.3, "B": 114.0}
bands = [("Ag1", 98, 122), ("Ag2", 236, 252), ("Ag3", 333, 352)]

fig = plt.figure(figsize=(7.2, 3.4), dpi=300)
gs = GridSpec(1, 3, width_ratios=[1.3, 1.15, 0.5], wspace=0.62, figure=fig)

# (a) spectra
ax = fig.add_subplot(gs[0])
step = 1.0
for i, (key, lab) in enumerate(order):
    d = pd.read_csv(DATA / f"spectrum_{key}.csv")
    x, y = d.shift_cm1.to_numpy(), d.intensity.to_numpy().astype(float)
    y = (y - np.percentile(y, 5)) / (y.max() - np.percentile(y, 5))
    off = i * step
    col = MAROON if lab == "1L" else SLATE
    ax.plot(x, y + off, color=col, lw=1.1)
    ax.text(432, off + 0.22, f"{lab} ({key})", fontsize=7.5, color=col, va="bottom", ha="right")
    ax.plot([ag1_fit[key]], [np.interp(ag1_fit[key], x, y) + off], "o", ms=3.2,
            mfc="white", mec=MAROON, mew=1.2, zorder=5)
for name, lo, hi in bands:
    ax.axvspan(lo, hi, color=LIGHT, zorder=0, lw=0)
    ax.text((lo + hi) / 2 + (0 if name != "Ag1" else -2), len(order) * step + 0.05, name, ha="center", fontsize=8.5, fontweight="bold", color=MAROON)
ax.set_xlim(60, 435)
ax.set_ylim(-0.15, len(order) * step + 0.7)
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_xlabel("Raman shift (cm$^{-1}$)")
ax.set_title("a   CrSBr, six flakes, 532 nm", loc="left", fontsize=10, fontweight="bold", color=SLATE)
ax.plot([132], [len(order) * step + 0.45], "o", ms=3.2, mfc="white", mec=MAROON, mew=1.2)
ax.text(138, len(order) * step + 0.45, "Ag1 fit (skill)", fontsize=6.8, color=MAROON, va="center")

# (b) bare vs skill, 0 to 1 metrics
axb = fig.add_subplot(gs[1])
metrics = [
    ("Material top-1", 0.46, 1.00), ("Irrep accuracy", 0.47, 0.84), ("Polarization", 0.71, 0.88),
    ("Cosmic rays", 0.67, 1.00), ("Caveats", 0.61, 0.88), ("Rubric", 0.74, 0.79),
    ("Caveats, Sonnet", 0.75, 0.79), ("Rubric, Sonnet", 0.88, 0.89),
]
yy = np.arange(len(metrics))[::-1]
h = 0.38
axb.barh(yy + h / 2, [m[1] for m in metrics], h, color=GREY, label="bare")
axb.barh(yy - h / 2, [m[2] for m in metrics], h, color=MAROON, label="with skill")
for y0, (_, a, b) in zip(yy, metrics):
    axb.text(a + 0.015, y0 + h / 2, f"{a:.2f}", va="center", fontsize=6.8, color=SLATE)
    axb.text(b + 0.015, y0 - h / 2, f"{b:.2f}", va="center", fontsize=6.8, color=MAROON, fontweight="bold")
axb.set_yticks(yy, [m[0] for m in metrics], fontsize=7.8)
axb.set_xlim(0, 1.18)
axb.set_xticks([0, 0.5, 1.0])
axb.set_xlabel("score (0 to 1), Haiku 5.5 unless noted")
axb.set_title("b   Bare vs skill", loc="left", fontsize=10, fontweight="bold", color=SLATE)
fig.legend(*axb.get_legend_handles_labels(), frameon=False, fontsize=8, ncol=2, loc="upper right", bbox_to_anchor=(0.995, 1.0))

# (c) citation specificity, 0 to 2
axc = fig.add_subplot(gs[2])
xs = np.arange(2)
w = 0.36
axc.bar(xs - w / 2, [1.00, 1.57], w, color=GREY)
axc.bar(xs + w / 2, [1.86, 1.71], w, color=MAROON)
for x0, a, b in zip(xs, [1.00, 1.57], [1.86, 1.71]):
    axc.text(x0 - w / 2, a + 0.04, f"{a:.2f}", ha="center", fontsize=6.8, color=SLATE)
    axc.text(x0 + w / 2, b + 0.04, f"{b:.2f}", ha="center", fontsize=6.8, color=MAROON, fontweight="bold")
axc.set_xticks(xs, ["Haiku", "Sonnet"], fontsize=7.8)
axc.set_ylim(0, 2.2)
axc.set_yticks([0, 1, 2])
axc.set_title("c   Citations", loc="left", fontsize=10, fontweight="bold", color=SLATE)
axc.set_ylabel("specificity (0 to 2)")

fig.text(0.01, 0.005, "Spectra: Zenodo 15048152 (Wdowik et al. 2025, CC BY 4.0), labelled by AFM thickness. "
         "Scores: development cases, skill v3 (identification n = 15, interpretation n = 7).",
         fontsize=6.5, color=SLATE)
fig.subplots_adjust(left=0.03, right=0.99, top=0.86, bottom=0.17)
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT.with_suffix(".png"), dpi=300)
fig.savefig(OUT.with_suffix(".pdf"))
print("wrote", OUT.with_suffix(".png"), OUT.with_suffix(".pdf"))
