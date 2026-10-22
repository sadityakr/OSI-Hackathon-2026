# RamanLens

A Claude Code skill that reads Raman spectra of 2D and layered materials the way a senior researcher does and shows its work. The researcher usually knows the material; RamanLens interprets what changes across spectra (thickness, crystal quality, defects, strain, doping, temperature, magnetic order), flags artifacts and measurement pitfalls, asks about measurement conditions, and ties every claim to a fitted measurement, a physics relation with its validity range, or a paper with a figure or table locator. Identifying an unknown material is the first step it also handles.

Built for the [4th Open Scientific Intelligence Hackathon](https://llmhackathon.github.io/) (Oct 21 to 22, 2026) by Aditya Kumar (JGU Mainz). Private working repo shared with collaborators; it will be cleaned before anything is made public.

## The question we test

Does RamanLens beat the existing state of the art, and does it make an LLM a better Raman analyst? Six arms on the same held-out cases:

| Arm | What it is |
|---|---|
| `libsearch` | classical full-spectrum library search (cosine on preprocessed spectra), the standard non-LLM method |
| `pipeline` | the RamanLens tools as a fixed recipe, no LLM |
| `bare` (Haiku 5.5, Sonnet 5.5) | headless Claude Code with Python only |
| `skill` (Haiku 5.5, Sonnet 5.5) | the same plus the RamanLens skill and literature MCP servers |

Two kinds of cases: identification (`eval/score.py`: material, irreps, polarization patterns, layer number) and interpretation with the material known (`eval/judge.py`: a blind Opus judge grades each report against a rubric written from the source paper's own conclusions). Held-out cases come from papers never used to build the skill; their rubrics were written by an agent the skill builders never saw.

## What is in the repo

| Path | Contents |
|---|---|
| `skill/ramanlens/` | **the deliverable**: Claude Code plugin with the `raman-analysis` skill (`SKILL.md`, `scripts/` rl_qc, rl_fit, rl_series, rl, `reference/` notes on artifacts, relations, measurement questions and 10 materials with about 100 cited papers) |
| `src/ramanlens/` | the tested Python package the scripts call: perception (readers, despiking, baseline, fitting, CRD matcher, polarization), literature tables, relations, agent toolset, LangSmith tracing |
| `iopic-bond/` | local MCP server over [Valency Bond](https://docs.valency.io/): finds papers, downloads arXiv PDFs, parses figures, shows them to the model |
| `eval/` | runners (`run_claude_code.py` headless Claude Code arms, `run_agent.py` SDK arms, `baselines.py` non-LLM arms), `score.py`, `judge.py`, `make_figure.py`, `export_results.py`, case generators in `synth/` |
| `eval/runs/` | raw run output including full agent transcripts (large) |
| `results/` | the results of every run without transcripts: reports, judge grades, scores, cost per case; see `results/README.md` |
| `data/` | test set (`test_set/`, formats in its README and `INTERPRET.md`), provenance, data catalogs, download scripts, `raw/` downloaded data |
| `docs/` | architecture, research (`sota-research.md`), verified reference numbers with locators, handovers |
| `submission/` | one-page write-up, figure, video script |
| `tests/`, `loop/` | contract and unit tests (84 pass); the headless build loop that wrote `src/` |

## Quickstart (Windows PowerShell, from the repo root)

```powershell
python -m venv .venv
.venv\Scripts\pip install -e "src[trace,pdf]" -e "iopic-bond[parse]" pytest
copy .env.example .env                                      # optional keys; Claude Code login is enough for eval
powershell -ExecutionPolicy Bypass -File data\get_data.ps1  # the four files over 100 MB that git does not hold
.venv\Scripts\python.exe -m pytest tests -q -m "not slow"
```

Use the skill in your own Claude Code session: `claude --plugin-dir skill/ramanlens`, then ask about your spectra.

Run a comparison (uses your Claude Code subscription, about $0.05 to $0.20 per case):

```powershell
.venv\Scripts\python.exe eval\run_claude_code.py --arm bare  --split dev_interpret --run-name demo --model claude-haiku-5-5
.venv\Scripts\python.exe eval\run_claude_code.py --arm skill --split dev_interpret --run-name demo --model claude-haiku-5-5
.venv\Scripts\python.exe eval\judge.py eval\runs\demo          # interpretation cases
.venv\Scripts\python.exe eval\baselines.py --arm pipeline --split dev --run-name demo-id
.venv\Scripts\python.exe eval\score.py eval\runs\demo-id       # identification cases
```

## Data and licences

Code is MIT. The Computational Raman Database (Bagheri and Komsa, Sci. Data 2023) is CC BY 4.0. Experimental spectra keep their original licences, listed in `data/README.md` and `data/test_set/README.md`. `data/raw/` (paper PDFs, downloaded data) and `resources/src/` (private Lit-RAG reference code) are in this private repo for collaborators only and must be removed before any public release.

## Status (Oct 22, 13:30 CEST)

Skill, tools, test set, baselines and evaluation are built; the final held-out run is in progress. Progress log: `LOG.md`; current state and conventions: `CLAUDE.md`.
