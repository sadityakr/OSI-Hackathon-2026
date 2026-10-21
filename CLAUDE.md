# OSI Hackathon 2026: RamanLens

Working repo for Aditya's entry in the 4th Open Scientific Intelligence Hackathon (Oct 21 to 22, 2026). Read this file first in every session, then `docs/architecture.md` and `docs/implementation.md`.

## The project in one sentence

An agent that reads a Raman spectrum the way an experienced 2D-materials researcher does and shows its work: every claim comes with the physics relation it used, the paper it came from, and the published reference spectrum retrieved and shown next to the measurement.

Decision record: `ideas/ranking.md`. Design contract: `docs/architecture.md`. Build decisions as they are made: `docs/implementation.md`. Literature-layer evaluation and test plan: `docs/bond-evaluation.md`. Literature MCP server iopic-Bond (design, storage, tools): `docs/iopic-bond.md`. Background research on the optional symmetry model: `ideas/02-polarized-raman-symmetry-model-research.md`. Collaborator deck: Claude Slides artifact "RamanLens Plan" (six slides: pitch, what we build, architecture, traceability, five-stage plan, roles).

## Hard constraints

- **Deadline: Fri Oct 23, 02:00 CEST** (Thu Oct 22, 7 pm CT).
- Deliverables: (1) public post with a video up to 4 min, no voice speed-up; (2) one-page write-up with a figure; (3) public code/data link; (4) submission form.
- Judging: potential for impact, innovativeness, relevance to physical sciences/math, novelty. Optimize for these, not polish.
- Organizer mindset: speed over polish, learning over perfection. Scope ambitiously.

## Status (updated Oct 22, early morning CEST)

Done: brainstorm, decision, architecture, implementation notes, Bond evaluation, CRD downloaded and schema verified (`data/README.md`, loader in `scratch/crd/crd_loader.py`), LangSmith tracing module (`src/ramanlens/tracing.py`), package skeleton (`src/pyproject.toml`), five open-data catalogs (index in `data/README.md`), collaborator deck. Data downloaded on the PC into `data/raw/`: CRD (plus `crd_2d.pkl` cache), 11 arXiv PDFs, CrSBr (Zenodo 15048152, TUdatalib 4929), WS2, MoS2, MoSe2, WSe2 (Mendeley, Southampton), graphene (Zenodo 14883846, Dryad), RRUFF, Zenodo search dumps.

iopic-Bond (literature MCP server, `iopic-bond/`): built and installed in `.venv`. Verified: arXiv fetch, Docling parse, parse-once library, figure tools, 3 offline tests (`iopic-bond/tests/`); Lee 2010 (arXiv 1005.2509) ingested. Not yet verified: Bond calls (`VALENCY_BOND_TOKEN` not set), LangSmith spans, Claude Desktop. Not built: `show_figures` MCP Apps panel.

Evaluation scaffold (Oct 21 evening, commits `ca79151`, `c83f350` on local `master` after `846b3c3`): test set of 45 cases with ground truth (`data/test_set/`, 13 dev, 32 held out), harness comparing a bare agent with the tooled agent (`eval/`, runner `eval/run_agent.py`), 24 contract tests defining the tool API (`tests/contract/`, red by design), headless build loop with backlog T1 to T11 (`loop/`). Not yet run: the loop, and any API run of the comparison (needs `ANTHROPIC_API_KEY`; smoke-test cost first, `eval/README.md`).

Not started: perception tools, relation registry, reference tables, agent toolset. These are the loop's backlog: `powershell -ExecutionPolicy Bypass -File loop\run_loop.ps1`.

## The core claim and how it is measured

Same model, prompt and Python sandbox; one arm gets only Python (`bare`), the other also gets the RamanLens tools (`tools`). `eval/score.py` scores identification (top-1, top-3), verdicts on a stated material (some hints deliberately wrong), peak recall and precision, irrep and polarization-pattern accuracy, cosmic-ray rejection. Headline: the held-out score difference between the arms. Report synthetic (`syn-*`) and experimental (`exp-*`) cases separately, because synthetic cases come from the CRD that the tools arm's matcher also uses.

Git: the local repo (`master`, commit `846b3c3`, also on `backup/local-baseline`) and GitHub `origin/main` have unrelated histories. Sync plan: branch `sync/pc-oct21` from `origin/main`, add the local work in one commit, Aditya reviews and pushes. Do not push `master` as is.

## Five-stage plan with stop points

Each stage ends with a commit, one LangSmith trace of an end-to-end run, and a line in `LOG.md`. Stopping after any stage leaves something presentable.

| # | Stage | Done when | Built by |
|---|---|---|---|
| 1 | Perception core | readers, preprocessing, fitting, pipeline and CRD matcher pass their contract tests | loop T1 to T5 |
| 2 | Relations and literature | polarization classifier, verified reference tables, six seed relations with self tests | loop T6 to T8 |
| 3 | Toolset and figure grounding | `test_toolset.py` green; iopic-Bond figure tools wired into the toolset | loop T9, T10 |
| 4 | Evaluation | `bare` vs `tools` on the held-out split, synthetic and experimental reported separately | `eval/` |
| 5 | Submit | one-pager, figure, 4 min video, form (Oct 23, 02:00 CEST) | `submission/` |

Cut lines in order: T10 figure tools, T11 hardening, extra reference tables, the synthetic tier of stage 4.

## Folder layout

- `resources/` event info, announcements, judging criteria, Miro pitch. Reference only.
- `ideas/` candidate ideas, research report, `ranking.md` (the decision).
- `docs/` architecture, implementation notes, Bond evaluation, later the write-up sources.
- `src/ramanlens/` the package: `tracing.py` (done), `perception/`, `relations/`, `literature/` (Raman-specific steps only: panel selection, digitizer), `agent/`. Python 3.11+, `pip install -e src[trace]`. `src/README.md` has the quickstart.
- `iopic-bond/` separate MIT package and local MCP server: Bond search, arXiv fetch, PDF parse into a graph (`pdf/`, ported from Lit-RAG), figure tools, SQLite-indexed library. RamanLens imports it; it never imports RamanLens. `iopic-bond/README.md` has install and client config.
- `data/` `README.md` (provenance of everything), data catalogs, `raw/` downloads (`crd/`, `spectra/<material>/`, `iopic-bond/` the paper library), `test_set/` evaluation cases (`dev/`, `heldout/`, `rejected/`; schema, sources and excluded papers in its README), `build_set/` papers used to generate relations (never overlaps the test set).
- `eval/` comparison harness: `run_agent.py`, `score.py`, `report_schema.py`, `synth/` (deterministic synthetic case generator with its own CRD loader). Run output in `eval/runs/` (never commit). Commands in `eval/README.md`.
- `tests/` `contract/` (tool API spec, read-only for the loop), `eval/` (scorer self-tests), `unit/` (the loop's own tests). `pytest.ini` at the root; fast run: `.venv\Scripts\python.exe -m pytest tests -q -m "not slow"`.
- `loop/` build loop: `PROMPT.md` (per-iteration instructions), `TASKS.md` (backlog), `settings.json` (allow and deny rules), `run_loop.ps1` (runner), `logs/` (never commit). Create `loop/STOP` to end a run.
- `notebooks/` Marimo preferred (sponsor track).
- `submission/` one-pager, figure, video script, links.
- `scratch/` throwaway experiments (tracked on GitHub). Anything worth keeping is moved into `src/`, `iopic-bond/` or `docs/` deliberately.
- The repo has no `.gitignore` (Aditya's decision). Never `git add -A` or `git add .`: stage files by name, and never commit `.env`, `.venv/` or `data/raw/` (secrets, and paper PDFs and figure crops that may not be redistributed).

## Data: what we have and what we do not

- **CRD** (Bagheri and Komsa 2023, CC BY 4.0) is at `data/raw/crd/` (move the zip there if it is still in `data/`). 5,099 crystals with per-mode frequencies, Raman tensors and irreps; irrep labels are per band, map through `IRbands`. **Not in it: CrSBr, graphene, 2H-MoS2** (only 3R). In it: 2H-WS2 (row 90), 2H-WSe2, h-BN, CrBr3, InSe, GaSe. Consequence: literature mode tables for the three demo materials are mandatory; WS2 is the first end-to-end test material.
- **Open experimental spectra** (see the two catalogs): WS2 on Mendeley Data (jsmbyfmck2, bjkct6pwx5) and Southampton ePrints (D0371, xlsx), strained graphene on Dryad (5qfttdzm9), VAMAS graphene interlab on Zenodo (10008276, 609 MB), MoS2/MoSe2/WSe2 xlsx sets on Southampton ePrints, CrSBr magneto-Raman zip on Zenodo (15048152, CC BY 4.0, contents unverified). RRUFF zips for minerals. No open raw data found for CrI3, CrPS4, MPS3, Fe3GeTe2, black phosphorus, ReS2, h-BN.
- **Open CrSBr polarization and excitation series exist** on the Heyrovsky Institute data repository (Sahu et al., DOIs 10.48700/datst.e94rx-q2q41 and 10.48700/c819g-kjx76, CC BY; manual download). Other open series: NiPS3/CoPS3 10 to 300 K (Zenodo 23300631, 20449397), 2M-WS2 temperature and polarization (Dataverse 10.7910/DVN/I9UNL7, CC0). TUdatalib 4928/4929 (Markina et al.) still needs a browser check. Five data catalogs in `data/` (index in `data/README.md`); `data/get_data.ps1 -All` fetches all scripted picks. Group CrSBr data may be used privately for sanity checks; the public demo and repo use literature-only CrSBr unless Aditya decides otherwise.
- Zenodo's API is bot-blocked from the sandbox; both catalogs contain PowerShell loops to re-run the queries from the PC.
- **Test set as built** (`data/test_set/README.md`): 34 synthetic cases from the CRD (22 layered materials, single spectra and 8 polarization angle series with pattern classes computed from the Raman tensors) and 11 experimental cases (WS2, MoSe2, WSe2, CrSBr held out; graphene, MoS2 in dev), split by source paper. The Heyrovsky CrSBr polarization sets are not in it yet; they are the best candidate for a real polarized held-out case. Papers behind held-out cases must not be used to build tables or relations (list in the test-set README).

## External pieces and where they come from

- **Valency MCP Bond**: literature discovery and citation graph. Configured project-wide in `.mcp.json` (streamable HTTP, `https://mcp.valency.io/`, OAuth 2.0, no secret in the repo). First use on a machine: start Claude Code in the repo folder, approve the project server, then run `/mcp` and authenticate `valency` in the browser with the Valency account (not the Claude account). Check with a `list_sources` call. Rules in `docs/bond-evaluation.md`: concept queries only, never frequencies; merge arXiv and PubMed duplicates on DOI; prefer arXiv ids for PDF access.
- **iopic-Bond** (`iopic-bond/`, design in `docs/iopic-bond.md`): our MCP server that wraps Bond. It runs on each user's machine and calls Bond with the Valency Direct API bearer token (`VALENCY_BOND_TOKEN` in `.env`; get it from the Settings page in the Valency app, documented at https://docs.valency.io/guides/api/). OAuth is only for chat clients such as Claude Code; the token is the documented route for programs. Library at `IOPIC_BOND_HOME` (here `data/raw/iopic-bond/`): one folder per arXiv paper plus `index.sqlite`; a paper is parsed once per parser version. Check with `.venv\Scripts\iopic-bond.exe doctor`.
- **PDF parsing and figure extraction**: ported from Aditya's private Lit-RAG project (reference copy in `resources/src/lit_rag/`) into `iopic-bond/src/iopic_bond/pdf/`. Needs Docling (`pip install -e iopic-bond[parse]`); a cold parse of a short paper took about 3 min on CPU including the first model download. Lit-RAG is not a dependency and is not named in the deliverable.
- **LangSmith**: `src/ramanlens/tracing.py` gives `@traced("span")`, `trace_run()` (root span, trace URL into the report) and `anthropic_client()` wrapped with `wrap_anthropic`. No-op without `LANGSMITH_API_KEY`. Span names are listed in the module docstring; keep them stable, the evaluation notebook filters on them. Claude Code's own model calls are not visible to LangSmith: develop in Claude Code, run evaluation and demo through the Python runner `eval/run_agent.py` (Anthropic SDK manual tool loop over `ramanlens.agent.toolset`) so the full tree is captured.
- **Third-party Raman models**: none chosen. Scout for public weights with 2D-materials training data for at most one hour; likely none exist, record that as a finding. The identification comparison (CRD matcher vs CRD-trained retriever vs Claude vision on the plotted spectrum) is an evaluation item in stage 4.

## Logistics

- Aditya participates remotely (Mainz, CEST = UTC+2), with one collaborator (role split proposed in the deck: Aditya on physics, relations, test set and narration; collaborator on LangSmith wiring, runner, PDF port, cache, repo hygiene; Claude agents on fitter, Bond client, self tests, one-pager draft).
- Compute and model access: Claude Max subscription API credits; RTX 3060 with 12 GB VRAM on the PC.
- The agent under test runs on the PC; the cloud session is used for planning, docs, and code that does not need arXiv, Zenodo or Materials Cloud access (all three are blocked from the sandbox).
- Project path on the PC: `C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon`. Secrets go in `.env` (template `.env.example`), never in the repo.
- Public repo: https://github.com/sadityakr/osi-hackathon-2026 (MIT). Raw data (`data/raw/`, including the CRD zip and 2.4 GB of graphene data) stays out of git and is fetched by `data/get_data.ps1`. Sync plan for the diverged histories: see Status.

## Working conventions

- Perception models are tools; the agent reasons. The physics lives in the relation registry, each relation with equation (all variables defined), validity range, source paper, and a self-test from that paper.
- Hypothesis before literature: never query Bond by peak positions.
- Build set and evaluation set never overlap.
- Held-out truth (`data/test_set/heldout/**/truth.json`) is read only by `eval/score.py`; tools never contain case ids or truth paths (`tests/contract/test_no_heldout_leak.py`). Fix the tool, never the contract test or the scorer.
- The build loop stages only `src/`, `tests/unit/`, `loop/TASKS.md`, `LOG.md` and `docs/tool-status.md` by name; while it runs, other sessions avoid those paths or work in a separate git worktree.
- Three provenance classes in every report: measured, inferred, literature. Say what the spectrum cannot tell.
- Every tool is decorated with `@traced`; every report carries its trace URL.
- Every claim in the write-up reproducible from `src/`.
- No em dashes in any written output.
- Keep `LOG.md` current: dated bullets of decisions and progress.

## Useful links

- Past submissions: https://llmhackathon.github.io/submissions
- Datasets: https://github.com/blaiszik/awesome-matchem-datasets
- Valency docs: https://docs.valency.io/ (bearer token: https://docs.valency.io/guides/api/)
- CRD record: https://archive.materialscloud.org/records/0m9r0-g3486
- Miro teaming board: https://miro.com/app/board/uXjVEeJogfE=/?share_link_id=927837268598
- Full event notes: `resources/event-info.md`
