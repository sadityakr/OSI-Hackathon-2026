# OSI Hackathon 2026: RamanLens

Working repo for Aditya's entry in the 4th Open Scientific Intelligence Hackathon (Oct 21 to 22, 2026). Read this file first in every session, then `docs/architecture.md`, `docs/implementation.md`, and for build work `loop/TASKS.md` and `data/test_set/README.md`.

## The project in one sentence

An agent that reads a Raman spectrum the way an experienced 2D-materials researcher does and shows its work: every claim comes with the physics relation it used, the paper it came from, and the published reference spectrum retrieved and shown next to the measurement.

The headline result is a controlled comparison: the same model, prompt and Python sandbox, with and without the RamanLens tools, scored on held-out Raman cases (`eval/`).

Decision record: `ideas/ranking.md`. Design contract: `docs/architecture.md`. Build decisions: `docs/implementation.md`. Literature-layer evaluation: `docs/bond-evaluation.md`. Optional symmetry model research: `ideas/02-polarized-raman-symmetry-model-research.md`. Collaborator deck: Claude Slides artifact "RamanLens Plan".

## Hard constraints

- **Deadline: Fri Oct 23, 02:00 CEST** (Thu Oct 22, 7 pm CT).
- Deliverables: (1) public post with a video up to 4 min, no voice speed-up; (2) one-page write-up with a figure; (3) public code/data link; (4) submission form.
- Judging: potential for impact, innovativeness, relevance to physical sciences/math, novelty. Optimize for these, not polish.

## Status (updated Oct 22, 00:00 CEST)

Done:
- Planning: decision, architecture, implementation notes, Bond evaluation, five open-data catalogs, deck.
- `src/ramanlens/tracing.py` (LangSmith). `src/ramanlens/literature/` now only points to `iopic-bond`.
- `iopic-bond/`: standalone local MCP server over Valency Bond (find papers, ingest arXiv PDF, parse with Docling into a section/figure graph, list and view figures, offline caption search). Owned by the collaborator; do not edit from the build loop.
- Test set in `data/test_set/`: 13 dev cases (11 synthetic from the CRD, 2 experimental), 32 held-out cases (23 synthetic, 9 experimental: CrSBr x5, WS2 x2, MoSe2, WSe2), 1 rejected. Truth, sources and excluded papers in `data/test_set/README.md`.
- `eval/`: synthetic case generator (`eval/synth/`), agent runner with a `bare` and a `tools` arm (`run_agent.py`), report schema, scorer.
- `tests/`: contract tests the tools must pass (`tests/contract/`), scorer tests (`tests/eval/`), held-out leak guard.
- `loop/`: headless build loop, one fresh `claude -p` per task in `loop/TASKS.md` (T1 to T11), with deny rules in `loop/settings.json`.
- Data downloaded on the PC (`data/raw/`): CRD plus `crd_2d.pkl` cache, 11 arXiv PDFs, CrSBr (Zenodo 15048152, TUdatalib 4929), WS2, MoS2, MoSe2, WSe2 (Mendeley, Southampton), graphene (Zenodo 14883846, Dryad), RRUFF, Zenodo search dumps.

Next: run the build loop (T1 readers through T9 toolset), then the eval smoke run, then the held-out comparison, then write-up and video.

## Five-stage plan with stop points

| # | Stage | Done when | Maps to |
|---|---|---|---|
| 1 | Perception core | readers, preprocessing, fitting, pipeline, CRD matcher pass their contract tests | loop T1 to T5 |
| 2 | Relations and literature | polarization classifier, verified reference tables, six seed relations with self tests | loop T6 to T8 |
| 3 | Agent toolset and figures | toolset passes `test_toolset.py`; iopic-bond figure tools wired in | loop T9, T10 |
| 4 | Evaluation | `bare` vs `tools` on held-out; synthetic and experimental reported separately | `eval/` |
| 5 | Submit | one-pager, figure, video, form | `submission/` |

Each stage ends with a commit and one LangSmith trace. Cut lines in order: T10 figure tools, T11 hardening, extra reference tables, stage 4 synthetic tier.

## Repository layout

- `src/ramanlens/` the toolkit: `tracing.py`, `perception/` (io, preprocess, fit, pipeline, library, polarization), `literature/` (reference tables, panels), `relations/`, `agent/toolset.py`. Built by the loop.
- `iopic-bond/` literature MCP server package (`pip install -e "iopic-bond[parse]"`, then `iopic-bond doctor`).
- `eval/` comparison harness; `eval/runs/` holds run outputs (gitignored on the PC).
- `tests/` `contract/` and `eval/` are fixed specifications; the loop adds its own tests under `tests/unit/`. Run with `.venv/Scripts/python.exe -m pytest tests -q -m "not slow"`.
- `loop/` `PROMPT.md`, `TASKS.md`, `settings.json`, `run_loop.ps1`.
- `data/` `README.md` (provenance and catalog index), five catalogs, `get_data.ps1` (+ `-All`), `scripts/`, `test_set/`, `build_set/`, `raw/`.
- `docs/`, `ideas/`, `resources/` (event info; `resources/src/lit_rag/` is the private Lit-RAG reference copy), `scratch/`, `notebooks/`, `submission/`.

## Data: what we have and what we do not

- **CRD** (Bagheri and Komsa 2023, CC BY 4.0) at `data/raw/crd/`: 5,099 crystals with per-mode frequencies, Raman tensors and irreps; irrep labels are per band, map through `IRbands`; `raman_tensors` can be a list or a dict. Not in it: CrSBr, graphene, 2H-MoS2 (only 3R). Frequencies run 0 to 3 % low.
- **Experimental cases** come from open deposits with the authors' published interpretation as truth; see `data/test_set/README.md`.
- **Papers excluded from tool building** (they hold held-out answers): McDonnell et al. 2018 (WS2), Viner et al. 2021 (MoSe2), McDonnell et al. 2020 (WSe2), Wdowik et al. 2025 (CrSBr). Never take reference-table or relation numbers from them.
- More open series data (CrSBr polarization and excitation on the Heyrovsky datarepo, NiPS3/CoPS3 temperature, 2M-WS2, pressure sets) in `data/catalog-series-quantum-magnetic.md`; several are CC BY-NC, keep derived data out of the MIT repo.

## External pieces

- **Valency Bond**, two routes. Claude Code (interactive): `.mcp.json` points at `https://mcp.valency.io/` with OAuth; authenticate once via `/mcp`. iopic-bond and scripts: Direct API token `VALENCY_BOND_TOKEN` in `.env` (from https://app.valency.io/settings). Rules: concept queries only, never frequencies; merge arXiv and PubMed duplicates on DOI; prefer arXiv ids.
- **LangSmith**: `@traced("span")`, `trace_run()`, `anthropic_client()` in `src/ramanlens/tracing.py`; no-op without `LANGSMITH_API_KEY`. The eval runner calls the Anthropic SDK directly, so both arms are fully traced.
- **Lit-RAG**: Aditya's private project; the needed parsing code lives in `iopic-bond/src/iopic_bond/pdf/`. Not named in the deliverable.

## Git

- Public repo: https://github.com/sadityakr/osi-hackathon-2026 (MIT).
- The PC working copy is on branch `master` with local commits (test set, eval, loop) not yet pushed; `origin/main` holds the cloud session's commits. Reconcile from the PC: `git fetch origin`, `git merge origin/main` (or rebase), then `git push origin master:main`.
- The PC `.gitignore` excludes `data/raw/`, `scratch/`, `resources/src/`, `eval/runs/`, `loop/logs/`. Large files (the CRD zip, 2.4 GB of graphene data) cannot go to GitHub without LFS.

## Logistics

- Aditya remote in Mainz (CEST), one collaborator. Claude Max credits; RTX 3060 12 GB.
- The cloud session cannot reach arXiv, Zenodo, Mendeley, Materials Cloud or LFS storage, and the PC shell bridge is often down; anything needing the network or the GPU runs on the PC.
- Project path on the PC: `C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon`. Secrets in `.env` (template `.env.example`), never committed.

## Working conventions

- Perception models are tools; the agent reasons. Physics lives in the relation registry: equation with all variables defined, validity range, source with locator, self tests from the paper.
- Every number in reference tables and relations is read from its source; if unverifiable, leave it out.
- Hypothesis before literature: never query Bond by peak positions.
- Never read `data/test_set/heldout/**/truth.json` while building tools; never put case ids or truth values in `src/`.
- Build set and evaluation set never overlap.
- Three provenance classes in every report: measured, inferred, literature. Say what the spectrum cannot tell.
- Every tool decorated with `@traced`; every report carries its trace URL.
- Module docstrings: summary, context, then Input, Process, Output. Comment decorators, dataclasses, generators and context managers for a physicist reader.
- No em dashes in any written output. Keep `LOG.md` current.

## Useful links

- Past submissions: https://llmhackathon.github.io/submissions
- Valency docs: https://docs.valency.io/
- CRD record: https://archive.materialscloud.org/records/0m9r0-g3486
- Event notes: `resources/event-info.md`
