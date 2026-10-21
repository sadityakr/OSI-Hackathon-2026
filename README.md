# RamanLens

An agent that reads Raman spectra of 2D materials the way an experienced researcher does, and shows its work:
every peak assignment and material claim comes with the method, relation or paper it rests on.

Entry for the 4th Open Scientific Intelligence Hackathon (Oct 21 to 22, 2026). Author: Aditya Kumar, with a collaborator.

## The question we test

Does an AI agent read Raman spectra better when it has domain tools? We compare two arms with the same model
(Claude Opus 5.5), the same prompt and the same Python sandbox:

| Arm | What the agent has |
|---|---|
| `bare` | Python (numpy, scipy, lmfit) and its own knowledge |
| `tools` | the same, plus RamanLens tools: peak fitter with spike and baseline handling, a matcher against the Computational Raman Database and curated literature mode tables, a polarization classifier for angle series, physics relations with sources, and literature figure retrieval |

Both arms answer the same cases: identify the material, check a material the user names (sometimes deliberately
wrong), assign the peaks, classify polarization behaviour, and say what the data cannot tell. Answers are scored
against ground truth.

## Status (Oct 22, early morning)

| Part | State |
|---|---|
| Test set, 45 cases with ground truth (`data/test_set/`) | done |
| Scorer and two-arm runner (`eval/`) | done; scorer self-tests pass; no API run yet |
| Tool API contract tests (`tests/contract/`) | written, red by design |
| RamanLens tools (`src/ramanlens/`) | in progress, built by an agent loop (`loop/`) against the contract tests |
| Literature MCP server iopic-Bond (`iopic-bond/`) | built; Bond calls not yet verified |
| Results, write-up, video | not yet |

## Test set

- **34 synthetic cases** generated from the Computational Raman Database (Bagheri and Komsa 2023, Sci. Data 10, 80,
  CC BY 4.0): 22 layered materials. The single spectra include realistic frequency offsets, noise, fluorescence
  background, a Si substrate line and cosmic spikes. Eight are polarization angle series whose pattern classes are
  computed from the Raman tensors.
- **11 experimental cases** from open datasets (WS2, MoSe2, WSe2 from University of Southampton ePrints; CrSBr and
  graphene from Zenodo; MoS2 from Southampton), each scored against the interpretation published with the data.
- Split into `dev` (13, visible to the tool builder) and `heldout` (32, used only for the final comparison).
  Experimental cases are split by source paper, and papers behind held-out cases are excluded from building the tools.

Sources, licences and known biases: `data/test_set/README.md`.

## Repository layout

| Path | Contents |
|---|---|
| `src/ramanlens/` | the toolkit: perception (I/O, preprocessing, fitting, library matching, polarization), relations, literature tables, agent toolset, LangSmith tracing |
| `iopic-bond/` | local MCP server: Valency Bond literature search, arXiv PDF parsing, figure retrieval |
| `eval/` | two-arm runner, scorer, synthetic case generator |
| `tests/` | contract tests (tool API), scorer self-tests, unit tests |
| `data/` | data provenance, open-data catalogs, download script, test set |
| `loop/` | the headless agent loop that builds the tools task by task |
| `docs/` | architecture, implementation notes, literature-layer evaluation |

## Quickstart (Windows, Python 3.11+)

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e "src[trace,dev]"
.venv\Scripts\python.exe -m pip install -e "iopic-bond[parse]"   # literature server (Docling)
copy .env.example .env                                           # ANTHROPIC_API_KEY, VALENCY_BOND_TOKEN, LangSmith keys
powershell -ExecutionPolicy Bypass -File data\get_data.ps1     # CRD and open spectra into data\raw\
.venv\Scripts\python.exe -m pytest tests -q -m "not slow"       # contract tests show what is built so far
```

To run the comparison, put `ANTHROPIC_API_KEY` in `.env` (template `.env.example`) and follow `eval/README.md`.

## Licence

Code: MIT. Data in `data/test_set/` keeps the licence of its source (CC BY 4.0 for all experimental cases; see the
test-set README). Paper PDFs and figure crops are never committed.
