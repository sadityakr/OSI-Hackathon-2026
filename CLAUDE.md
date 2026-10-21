# OSI Hackathon 2026: RamanLens

Working repo for Aditya's entry in the 4th Open Scientific Intelligence Hackathon (Oct 21 to 22, 2026). Read this file first in every session, then `docs/architecture.md` and `docs/implementation.md`.

## The project in one sentence

An agent that reads a Raman spectrum the way an experienced 2D-materials researcher does and shows its work: every claim comes with the physics relation it used, the paper it came from, and the published reference spectrum retrieved and shown next to the measurement.

Decision record: `ideas/ranking.md`. Design contract: `docs/architecture.md`. Build decisions as they are made: `docs/implementation.md`. Literature-layer evaluation and test plan: `docs/bond-evaluation.md`. Background research on the optional symmetry model: `ideas/02-polarized-raman-symmetry-model-research.md`. Collaborator deck: Claude Slides artifact "RamanLens Plan" (six slides: pitch, what we build, architecture, traceability, five-stage plan, roles).

## Hard constraints

- **Deadline: Fri Oct 23, 02:00 CEST** (Thu Oct 22, 7 pm CT).
- Deliverables: (1) public post with a video up to 4 min, no voice speed-up; (2) one-page write-up with a figure; (3) public code/data link; (4) submission form.
- Judging: potential for impact, innovativeness, relevance to physical sciences/math, novelty. Optimize for these, not polish.
- Organizer mindset: speed over polish, learning over perfection. Scope ambitiously.

## Status (updated Oct 21, 18:00 CEST)

Done: brainstorm, decision, architecture, implementation notes, Bond evaluation, CRD downloaded and schema verified (`data/README.md`, loader in `scratch/crd/crd_loader.py`), LangSmith tracing module (`src/ramanlens/tracing.py`), package skeleton (`src/pyproject.toml`), open-data catalogs (`data/catalog-graphene-tmd.md`, `data/catalog-magnets-general.md`), collaborator deck.

Not started: perception tools, relation registry, Bond client, PDF and figure port, agent runner, evaluation set.

## Five-stage plan with stop points

Each stage ends with a commit, one LangSmith trace of an end-to-end run, and a line in `LOG.md`. Stopping after any stage leaves something presentable.

| # | Stage | Done when | Target |
|---|---|---|---|
| 1 | Perception core | a public WS2 spectrum fitted; CRD matcher ranks 2H-WS2 top 3; traced | Oct 21, 21:00 |
| 2 | Relations and literature | mode tables for graphene, 2H-MoS2, CrSBr with sources; Bond retrieval test 8 of 10; six seed relations pass self tests | Oct 22, 01:00 |
| 3 | Figure grounding | arXiv PDF to Raman panel on 10 papers, 8 found; panel shown beside measurement in the report | Oct 22, 12:00 |
| 4 | Evaluation | 20 held-out literature spectra scored on categorical fields; ablation without literature; matcher vs Claude vision comparison | Oct 22, 18:00 |
| 5 | Tool building and submit | agent writes two new relations from papers with passing tests; one-pager, figure, video, form | Oct 23, 01:00 |

Cut lines in order: digitizer (show the panel without overlay), retriever, third-party model scouting, stage 5 tool building.

## Folder layout

- `resources/` event info, announcements, judging criteria, Miro pitch. Reference only.
- `ideas/` candidate ideas, research report, `ranking.md` (the decision).
- `docs/` architecture, implementation notes, Bond evaluation, later the write-up sources.
- `src/ramanlens/` the package: `tracing.py` (done), `perception/`, `relations/`, `literature/`, `agent/`. Python 3.11+, `pip install -e src[trace]`. `src/README.md` has the quickstart.
- `data/` `README.md` (provenance of everything), two data catalogs, `raw/` downloads (gitignored: `crd/`, `spectra/<material>/`, `pdfs/`), `test_set/` held-out evaluation spectra with the paper's interpretation, `build_set/` papers used to generate relations (never overlaps the test set).
- `notebooks/` Marimo preferred (sponsor track).
- `submission/` one-pager, figure, video script, links.
- `scratch/` throwaway experiments (gitignored). Anything worth keeping is moved into `src/` or `docs/` deliberately.

## Data: what we have and what we do not

- **CRD** (Bagheri and Komsa 2023, CC BY 4.0) is at `data/raw/crd/` (move the zip there if it is still in `data/`). 5,099 crystals with per-mode frequencies, Raman tensors and irreps; irrep labels are per band, map through `IRbands`. **Not in it: CrSBr, graphene, 2H-MoS2** (only 3R). In it: 2H-WS2 (row 90), 2H-WSe2, h-BN, CrBr3, InSe, GaSe. Consequence: literature mode tables for the three demo materials are mandatory; WS2 is the first end-to-end test material.
- **Open experimental spectra** (see the two catalogs): WS2 on Mendeley Data (jsmbyfmck2, bjkct6pwx5) and Southampton ePrints (D0371, xlsx), strained graphene on Dryad (5qfttdzm9), VAMAS graphene interlab on Zenodo (10008276, 609 MB), MoS2/MoSe2/WSe2 xlsx sets on Southampton ePrints, CrSBr magneto-Raman zip on Zenodo (15048152, CC BY 4.0, contents unverified). RRUFF zips for minerals. No open raw data found for CrI3, CrPS4, MPS3, Fe3GeTe2, black phosphorus, ReS2, h-BN.
- **No confirmed open polarization or temperature series for any 2D magnet.** Most CrSBr Raman papers say "upon request". Best lead: TUdatalib handles 4928 and 4929 (Markina et al.), blocked by a bot wall from the sandbox; check in a browser, else email the authors. Group CrSBr data may be used privately for sanity checks; the public demo and repo use literature-only CrSBr unless Aditya decides otherwise.
- Zenodo's API is bot-blocked from the sandbox; both catalogs contain PowerShell loops to re-run the queries from the PC.
- The evaluation set will be mostly digitized from papers; the catalogs list the target papers.

## External pieces and where they come from

- **Valency MCP Bond**: literature discovery and citation graph. Configured project-wide in `.mcp.json` (streamable HTTP, `https://mcp.valency.io/`, OAuth 2.0, no secret in the repo). First use on a machine: start Claude Code in the repo folder, approve the project server, then run `/mcp` and authenticate `valency` in the browser with the Valency account (not the Claude account). Check with a `list_sources` call. Rules in `docs/bond-evaluation.md`: concept queries only, never frequencies; merge arXiv and PubMed duplicates on DOI; prefer arXiv ids for PDF access.
- **PDF parsing and figure extraction**: ported from Aditya's private Lit-RAG project (GitLab). Copy the parsing, section graph and figure-extraction code into `src/ramanlens/literature/pdf/` and adapt it. Lit-RAG is not a dependency and is not named in the deliverable; its MCP server is not needed. TODO: Aditya copies the modules in.
- **LangSmith**: `src/ramanlens/tracing.py` gives `@traced("span")`, `trace_run()` (root span, trace URL into the report) and `anthropic_client()` wrapped with `wrap_anthropic`. No-op without `LANGSMITH_API_KEY`. Span names are listed in the module docstring; keep them stable, the evaluation notebook filters on them. Claude Code's own model calls are not visible to LangSmith: develop in Claude Code, run evaluation and demo through the Python runner in `src/ramanlens/agent/` (Anthropic SDK plus the same tools) so the full tree is captured. Pending agreement with the collaborator.
- **Third-party Raman models**: none chosen. Scout for public weights with 2D-materials training data for at most one hour; likely none exist, record that as a finding. The identification comparison (CRD matcher vs CRD-trained retriever vs Claude vision on the plotted spectrum) is an evaluation item in stage 4.

## Logistics

- Aditya participates remotely (Mainz, CEST = UTC+2), with one collaborator (role split proposed in the deck: Aditya on physics, relations, test set and narration; collaborator on LangSmith wiring, runner, PDF port, cache, repo hygiene; Claude agents on fitter, Bond client, self tests, one-pager draft).
- Compute and model access: Claude Max subscription API credits; RTX 3060 with 12 GB VRAM on the PC.
- The agent under test runs on the PC; the cloud session is used for planning, docs, and code that does not need arXiv, Zenodo or Materials Cloud access (all three are blocked from the sandbox).
- Project path on the PC: `C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon`. Secrets go in `.env` (template `.env.example`), never in the repo.
- Public repo: https://github.com/sadityakr/osi-hackathon-2026 (MIT). The CRD zip must be pushed from the PC via Git LFS (`.gitattributes` tracks `*.zip`); the sandbox cannot reach LFS storage.

## Working conventions

- Perception models are tools; the agent reasons. The physics lives in the relation registry, each relation with equation (all variables defined), validity range, source paper, and a self-test from that paper.
- Hypothesis before literature: never query Bond by peak positions.
- Build set and evaluation set never overlap.
- Three provenance classes in every report: measured, inferred, literature. Say what the spectrum cannot tell.
- Every tool is decorated with `@traced`; every report carries its trace URL.
- Every claim in the write-up reproducible from `src/`.
- No em dashes in any written output.
- Keep `LOG.md` current: dated bullets of decisions and progress.

## Useful links

- Past submissions: https://llmhackathon.github.io/submissions
- Datasets: https://github.com/blaiszik/awesome-matchem-datasets
- Valency docs: https://docs.valency.io/
- CRD record: https://archive.materialscloud.org/records/0m9r0-g3486
- Miro teaming board: https://miro.com/app/board/uXjVEeJogfE=/?share_link_id=927837268598
- Full event notes: `resources/event-info.md`
