# Literature-in-the-Loop

**Scientific analysis grounded in published research.** A Claude Code meta skill that turns the literature on a
measurement technique into an analysis skill that checks the data like a senior researcher, compares it with the
published figures, cites every claim, records the whole analysis in a reproducible notebook, and keeps learning
from the analyses it runs. The worked example is Raman spectroscopy of 2D and layered materials.

Team **Analysis Paralysis**: Aditya Kumar<sup>1</sup>, Sourish Dey<sup>2</sup>, Pratyush Kumar Das<sup>3</sup>.
Built for the 4th Open Scientific Intelligence Hackathon, October 21 to 22, 2026.

<sup>1</sup> Institute of Physics, Johannes Gutenberg University Mainz, Germany<br>
<sup>2</sup> SumUp, Berlin, Germany<br>
<sup>3</sup> School of Mathematics and Physics, University of Queensland, Australia

**Read first:** the [video walkthrough](https://drive.google.com/file/d/1FBxnqSUh3ZgINgrnLJExAGhMsGK1QE8B/view?usp=drive_link)
(Google Drive), the [one-page write-up](submission/writeup.md) as submitted, the
[write-up figure](submission/figure_raman_skill.png), and the
[cross-domain supplement](submission/supplementary/OSI_Supplement.pdf).

## Why analysis needs the literature in the loop

A Raman peak can shift because of thickness, strain, defects, doping, temperature or a miscalibrated
spectrometer. Naming the material is the easy part. The hard part is the knowledge a senior colleague brings:
which features to distrust, which artifacts a setup produces, and what the papers on this material report for
the same variable. Analysis tools package none of this. Library search names a material and stops, and we found
no public machine-learning model for Raman of 2D materials ([docs/sota-research.md](docs/sota-research.md)).

## How a Raman analysis runs

![The researcher's spectra go through the raman-analysis skill: quality checks, fitting, identification, interpretation and comparison with a published figure found through Valency Bond and opened with litpick. The output is a Marimo notebook with tagged, cited claims.](docs/img/overview.svg)

1. **Conditions and quality.** `rl_qc.py` flags cosmic-ray spikes, saturation, background and the silicon
   calibration offset before anything is fitted.
2. **Fit.** `rl_fit.py` (one spectrum) and `rl_series.py` (several) fit every band with uncertainties and track
   each band across a series.
3. **Identify and assign.** A matcher over 385 layered crystals of the Computational Raman Database
   (Bagheri and Komsa, Sci. Data 2023) and curated literature tables ranks candidates and gives mode labels.
4. **Interpret.** Cited relations, each with its validity range, turn shifts into layer number, strain, doping
   or defect density. Notes on 10 materials, drawn from about 100 papers, say how each spectrum changes with
   each variable and what to ask about the measurement.
5. **Compare with the published figure.** Papers are found by concept through the
   [Valency Bond](https://docs.valency.io/) citation graph. **litpick**, our MCP server, opens the arXiv PDF,
   parses it once into a local library and serves the figure with its citation. The figure for the same
   variable is read off next to the fitted values.

The deliverable is a Marimo notebook: a plain Python file that reruns on the raw data. It
opens with a TL;DR, computes every quoted number from the data, tags each claim as measured, inferred,
literature or learned, and shows the published figure beside the user's spectra. See the two recorded demos in
[submission/demo/](submission/demo/): six CrSBr flakes of different thickness, and one CrSBr flake through three
defect doses (open the `raman_analysis.html` files).

## How the skill is built and keeps learning

![The literature-in-the-loop meta skill writes an analysis skill from published papers. Each run captures new items to an inbox; an item is promoted into the reference notes only when a paper confirms it or it recurs on two independent datasets. Instrument caveats go to a per-setup folder. Evaluation runs never learn.](docs/img/learning-loop.svg)

The meta skill [`literature-in-the-loop`](submission/skills/literature-in-the-loop/SKILL.md) writes a skill for
any measurement technique with the same layout: validated scripts, method rules and relations with validity
ranges, per-material notes in which every number carries a paper and a figure or table locator, machine-readable
`resources/`, and a notebook template. Learning is gated so the skill does not drift into folklore:

- every run appends new caveats, techniques and papers to `learned/inbox.md`, where they stay untrusted;
- an item is promoted into the notes only when a paper confirms it, or when it recurs on two independent
  datasets (then tagged `[learned]`); promotions only append, and each is logged in `learned/CHANGELOG.md`;
- caveats that belong to one instrument (a filter ghost line, a drifting Si offset) go to
  `setups/<instrument>/`, matched to the data by a file fingerprint;
- evaluation runs set `SKILL_LEARNING=off`, so held-out cases cannot leak into the skill.

The learning loop is specified in the skills and their templates; no real analysis has been run through capture
and promotion yet, and the evaluation below used a skill version without it.

## What the evaluation shows, including where the skill fell short

![Evaluation design and results: held-out identification top-1 0.52 for library search and 0.58 for the pipeline, polarization pattern 0.00 and 0.89; held-out interpretation with Haiku 5.5 rubric 0.50 bare and 0.41 with the skill, citation specificity 1.00 and 1.57; development cases top-1 0.46 to 1.00, irrep accuracy 0.47 to 0.84, caveats 0.61 to 0.88.](docs/img/evaluation.svg)

- **Held-out identification (37 cases):** our tools as a fixed pipeline beat classical library search on
  material top-1 (0.58 vs 0.52) and polarization pattern (0.89 vs 0.00). The LLM arms did not finish before the
  deadline.
- **Held-out interpretation (7 cases, Haiku 5.5):** the skill made citations more specific (1.00 to 1.57 on a
  0 to 2 scale), but the rubric score fell from 0.50 to 0.41. Better evidence retrieval did not yet give better
  scientific reasoning on these harder, paper-specific cases.
- **Development cases (Haiku 5.5):** large gains, e.g. material top-1 0.46 to 1.00. They did not carry over to
  the held-out interpretation cases.

Limits: few cases; the synthetic identification cases come from the same database the matcher uses; the judge is
an LLM. Every run, every report and every grade is in [results/](results/README.md).

## Beyond Raman: five cross-domain demonstrations

![Mean absolute-error reduction of physics-constrained estimators over simple baselines, 100 paired synthetic realisations per field: XRD 99.4 percent, NMR 98.8 percent, photoluminescence 84.7 percent, astronomy 42.0 percent, self-avoiding walks 99.5 percent.](docs/img/cross-domain.svg)

To test whether the approach transfers, Pratyush built paired synthetic benchmarks in five fields, comparing a
simple baseline estimator with one that uses the field's established physical constraints. These are
deliberately simplified, matched-model comparisons, not a validation of the full agent. Code, data and the
report with error distributions and bootstrap confidence intervals: [submission/supplementary/](submission/supplementary/).

## Repository map

| Path | What it is |
|---|---|
| [`submission/skills/raman-analysis/`](submission/skills/raman-analysis/) | **the Raman skill**: `SKILL.md`, `scripts/` (QC, fit, series, CLI, and the bundled `ramanlens` package), `reference/` (artifacts, relations, measurement questions, 10 material notes), `resources/` (reference tables, CRD library), `templates/` (notebook), `learned/`, `setups/` |
| [`submission/skills/literature-in-the-loop/`](submission/skills/literature-in-the-loop/) | **the meta skill** that builds such a skill for another technique, with `templates/` for the learning loop |
| [`skill/litpick/`](skill/litpick/) | **litpick**, the MCP server and Claude Code plugin that opens arXiv papers and serves their figures with citations |
| [`submission/demo/`](submission/demo/) | two recorded CrSBr demos: data, notebook, HTML report |
| [`submission/supplementary/`](submission/supplementary/) | cross-domain benchmarks (XRD, NMR, PL, astronomy, self-avoiding walks) |
| [`submission/writeup.md`](submission/writeup.md) | the submitted one-page write-up, with [figure](submission/figure_raman_skill.png) |
| [`src/ramanlens/`](src/ramanlens/) | development version of the processing package (readers, despiking, baseline, fitting, matcher, polarization, relations, agent toolset), used by the tests and the evaluation |
| [`eval/`](eval/README.md) | evaluation: `run_claude_code.py` (bare and skill arms), `baselines.py` (non-LLM arms), `score.py`, `judge.py`, case generators in `synth/` |
| [`data/test_set/`](data/test_set/README.md) | the test cases with spectra, answer keys and rubrics; dev and held-out splits |
| [`results/`](results/README.md) | every run's reports, grades, scores and cost, without transcripts |
| [`tests/`](tests/) | contract and unit tests |
| [`docs/`](docs/) | diagrams, verified reference numbers with locators, state-of-the-art survey |

## Try it

You need [Claude Code](https://claude.com/claude-code), Python 3.11 or newer, and
[uv](https://docs.astral.sh/uv/getting-started/installation/) (litpick provisions its own environment through it). From the repository root,
on Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\pip install -e submission\skills\raman-analysis\scripts
claude --plugin-dir submission --plugin-dir skill\litpick
```

Then ask about your own spectra, or about a demo set, for example: "Here are Raman spectra of six CrSBr flakes
in `submission/demo/crsbr-thickness/data/`, measured at 532 nm and room temperature. How thick is each flake?"
For finding papers, connect Valency Bond once: the project `.mcp.json` declares it; run `/mcp` in Claude Code
and sign in with a Valency account. Without it the skill falls back to its notes and web search.

## Reproduce the evaluation

```powershell
.venv\Scripts\pip install -e "src[trace]" pytest
.venv\Scripts\python -m pytest tests -q -m "not slow"

# non-LLM arms on the held-out identification cases
.venv\Scripts\python eval\baselines.py --arm libsearch --split heldout --kind identify --run-name my-id
.venv\Scripts\python eval\baselines.py --arm pipeline  --split heldout --kind identify --run-name my-id
.venv\Scripts\python eval\score.py eval\runs\my-id

# Claude Code arms on the held-out interpretation cases (uses your Claude Code login)
.venv\Scripts\python eval\run_claude_code.py --arm bare  --split heldout --kind interpret --run-name my-int --model claude-haiku-5-5
.venv\Scripts\python eval\run_claude_code.py --arm skill --split heldout --kind interpret --run-name my-int --model claude-haiku-5-5 --parallel 1
.venv\Scripts\python eval\judge.py eval\runs\my-int
```

The held-out results in `results/` were produced with an earlier skill version (v3) and iopic-Bond, the
predecessor of litpick; the runner now loads the current skill and litpick.

## Data and licences

Code is MIT ([LICENSE](LICENSE)). The Computational Raman Database (Bagheri and Komsa, Sci. Data 10, 80, 2023)
is CC BY 4.0; the repository ships the layered-crystal subset derived from it. Experimental spectra keep their
original licences, listed in [data/README.md](data/README.md) and [data/test_set/README.md](data/test_set/README.md).
The demo HTML reports embed a figure from Torres et al. 2022 (arXiv 2212.01754) for comparison.

## About this repository's history

This repository was cleaned for reading on October 23, 2026, after the submission deadline: development
material (build loop, planning notes, run transcripts, downloaded papers and raw data) was removed from the
current tree, and the final write-up and the skill files that were on disk at submission time were committed.
The commit history before that is unchanged.
