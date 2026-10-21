# RamanLens

An AI agent that reads a Raman spectrum the way an experienced materials researcher does and shows its work. Every claim in its report comes with the measurement it rests on, the physics relation it used, and the paper it came from, with the published reference figure retrieved for comparison.

Built for the [4th Open Scientific Intelligence Hackathon](https://llmhackathon.github.io/) (Oct 21 to 22, 2026) by Aditya Kumar (JGU Mainz).

## The question we test

Does a frontier model analyse Raman data better with domain tools than with Python alone? `eval/` runs the same model, prompt and sandbox in two arms:

| Arm | What the agent has |
|---|---|
| `bare` | a Python sandbox (numpy, scipy, lmfit, pandas, matplotlib) |
| `tools` | the same, plus RamanLens: peak fitting, spike and baseline handling, a matcher against 5,099 computed Raman spectra, a polarization classifier, verified literature reference tables, cited physics relations, and literature figure retrieval |

Both are scored on held-out cases: synthetic spectra generated from the Computational Raman Database with exact truth, and experimental spectra from open deposits (CrSBr, WS2, MoSe2, WSe2) whose truth is the authors' published interpretation.

## What is in the repo

| Path | Contents |
|---|---|
| `src/ramanlens/` | the toolkit: perception, literature tables, relations, agent toolset, LangSmith tracing |
| `iopic-bond/` | a local MCP server over [Valency Bond](https://docs.valency.io/): finds papers, downloads arXiv PDFs, parses them into a section and figure graph, shows figures to the model |
| `eval/` | synthetic case generator, two-arm agent runner, report schema, scorer |
| `tests/` | contract tests every tool must pass, scorer tests, held-out leak guard |
| `loop/` | headless build loop: one fresh Claude Code session per backlog task |
| `data/` | test set, provenance, five catalogs of open Raman data, download scripts |
| `docs/`, `ideas/` | architecture, implementation notes, decision record, research |

## Quickstart (Windows PowerShell, from the repo root)

```powershell
python -m venv .venv
.venv\Scripts\pip install -e "src[trace,pdf]" -e "iopic-bond[parse]" pytest
copy .env.example .env          # add ANTHROPIC_API_KEY, VALENCY_BOND_TOKEN, optional LangSmith keys
powershell -ExecutionPolicy Bypass -File data\get_data.ps1        # CRD, spectra, PDFs (add -All for more)
.venv\Scripts\python.exe -m pytest tests -q -m "not slow"         # contract tests
```

Run the comparison:

```powershell
.venv\Scripts\python.exe eval\run_agent.py --arm bare  --split dev --run-name smoke
.venv\Scripts\python.exe eval\run_agent.py --arm tools --split dev --run-name smoke
.venv\Scripts\python.exe eval\score.py eval\runs\smoke
```

Build the tools with the loop: `powershell -ExecutionPolicy Bypass -File loop\run_loop.ps1 -MaxIterations 12`.

## Data and licences

Code is MIT. The Computational Raman Database (Bagheri and Komsa, Sci. Data 2023) is CC BY 4.0. Experimental spectra keep their original licences, listed per source in `data/README.md` and `data/test_set/README.md`; some catalogued series are CC BY-NC and are not redistributed here. Large raw files are fetched by `data/get_data.ps1` rather than stored in git.

## Status

Planning, test set, evaluation harness and literature server are in place; the perception and relation tools are being built by the loop. Progress log: `LOG.md`.
