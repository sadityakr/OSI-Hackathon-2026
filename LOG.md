# Progress log

## 2026-10-20

- Set up project folder; collected event info from Luma and Slack #general into `resources/`.
- Noted Miro pitch "Spectral Identifier" as a possible team; declined after brainstorming (see `ideas/ranking.md`).
- Brainstormed: Raman interpretation agent, polarized-Raman symmetry classifier, Bond plus figure retrieval, Raman meta-analysis, transport (tunnel junction) agent. Research agent produced `ideas/02-polarized-raman-symmetry-model-research.md` (data sources, physics, model options, two-day plan for the symmetry model).
- Decision: build RamanLens, the Raman interpretation agent with cited relations and figure-level literature grounding. Symmetry classifier and transport analysis are optional modules.
- Evaluated Valency MCP Bond for Raman literature retrieval (`docs/bond-evaluation.md`): concept queries return the canonical papers at rank 1 for CrSBr, MoS2 and graphene; numeric peak queries are useless; citation tools work; arXiv ids give PDF access from the PC.
- Wrote `docs/architecture.md` (layers, tool contract, report format, evaluation, tool-building loop) and rewrote `CLAUDE.md`.
- Open before day 1: download CRD zip on the PC; copy Lit-RAG parsing and figure code into `src/ramanlens/literature/pdf/`; configure Valency MCP in Claude Code; pick public spectra from Zenodo; create public repo.
- CRD downloaded by Aditya (MD5 verified). Schema inspected (`data/README.md`): irrep labels are per band via `IRbands`; loader in `scratch/crd/crd_loader.py` validated on 2H-WS2. Coverage check: CrSBr, graphene and 2H-MoS2 are absent from the CRD (only 3R-MoS2); WS2, WSe2, h-BN, CrBr3 present. Demo materials rely on literature mode tables.

## 2026-10-21

- Collaborator deck "RamanLens Plan" (6 slides: pitch, what we build, architecture, LangSmith traceability, five-stage plan with stop points, roles and decisions) published as a Claude Slides artifact.
- Added `src/ramanlens/tracing.py` (LangSmith `traced` decorator, `trace_run` root span with trace URL for the report, `anthropic_client()` wrapped with `wrap_anthropic`; no-op without `LANGSMITH_API_KEY`), `src/pyproject.toml`, `src/README.md`, `.env.example`. Smoke-tested both modes.
- Decision pending with collaborator: Python runner (Anthropic SDK plus tools) for eval and demo so model calls are traced; Claude Code for development. Same tool code.
- Two Sonnet agents cataloged open Raman data: `data/catalog-graphene-tmd.md` and `data/catalog-magnets-general.md`. Zenodo API is bot-blocked from the sandbox; both files contain PowerShell loops to re-run the Zenodo queries from the PC. Verified: WS2 sets on Mendeley and Southampton ePrints (CC BY), strained graphene on Dryad, VAMAS graphene interlab on Zenodo, Zenodo 15048152 CrSBr magneto-Raman zip (CC BY 4.0, contents unverified), RRUFF zips. No confirmed open polarization or temperature series for any 2D magnet; most CrSBr papers say "upon request"; TUdatalib handles 4928/4929 (Markina et al.) are the best lead and need a browser check.
- Aditya copied the Lit-RAG source into `resources/src/lit_rag/` (reference only, not shipped). Ported the minimal subset into `src/ramanlens/literature/pdf/` (schema, ids, docling_adapter, render, xref verbatim; trimmed `pipeline.py`: Docling with formula VLM off, no GROBID, citation or chemistry passes, cached by content hash). Added `literature/arxiv.py` (fetch_pdf with cache and %PDF check) and `literature/figures.py` (`extract_figures` -> Figure records with label, caption, page, image path, referencing paragraphs; `likely_spectrum_figures` caption pre-filter). Docling-free path tested in the sandbox; Docling path needs `scratch/smoke_figures.py` on the PC (`pip install -e src[pdf]`).
- Public repo live at github.com/sadityakr/osi-hackathon-2026 (everything committed incl. Lit-RAG reference copy; CRD zip pending LFS push from the PC).
- Valency Bond MCP configured project-wide in `.mcp.json` (HTTP, OAuth); auth once per machine via `/mcp` in Claude Code.
- No spectra or PDFs downloaded yet: every data host is blocked from the sandbox and the PC shell bridge is down. Added `data/get_data.ps1` (one-shot, idempotent): moves the CRD zip into `data/raw/crd/`, downloads CrSBr Zenodo 15048152, graphene Zenodo 14883846, WS2 Mendeley sets, RRUFF oriented, 11 key arXiv PDFs, and runs the Zenodo searches.
