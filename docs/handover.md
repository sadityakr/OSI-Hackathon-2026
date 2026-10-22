# Handover prompt (Oct 22, 00:10 CEST)

Paste the block below into a fresh Claude Code session started in the repo folder on the PC
(`C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon`).

---

You are taking over RamanLens, Aditya Kumar's entry for the 4th Open Scientific Intelligence Hackathon. Submission deadline: **Fri Oct 23, 02:00 CEST** (Thu Oct 22, 7 pm CT). Today is Oct 22. Work fast; speed over polish.

**Goal.** RamanLens is a toolkit that lets an AI agent read Raman spectra the way an experienced 2D-materials researcher does, with every claim tied to a measurement, a cited physics relation, or a paper. The headline result is a controlled comparison: the same model, prompt and Python sandbox, with (`tools` arm) and without (`bare` arm) the RamanLens tools, scored on held-out cases.

**Read first, in this order:** `CLAUDE.md`, `data/test_set/README.md`, `eval/README.md`, `loop/TASKS.md`, `loop/PROMPT.md`, the last 30 lines of `LOG.md`. Then `docs/architecture.md` sections 2A and 2B if you need the design.

**State right now.**
- Built: test set (45 cases: 13 dev, 32 held-out, synthetic from the Computational Raman Database plus experimental CrSBr, WS2, MoSe2, WSe2, graphene, MoS2), scorer and two-arm runner in `eval/`, 24 contract tests in `tests/contract/` (red by design), headless build loop in `loop/` with backlog T1 to T11, LangSmith tracing in `src/ramanlens/tracing.py`, and `iopic-bond/` (local MCP server over Valency Bond: paper search, arXiv download, Docling parse into a figure graph, figure viewing).
- Not built: everything in `src/ramanlens/perception/`, `relations/`, `literature/reference_tables.py`, `agent/toolset.py`. That is the loop's backlog.
- Not run yet: the loop, any API run of `eval/run_agent.py`, Bond calls from iopic-bond (needs `VALENCY_BOND_TOKEN`).
- Data on disk in `data/raw/` (about 3.5 GB, not in git): CRD (`crd.json`, `crd_2d.pkl`), 11 arXiv PDFs, CrSBr (Zenodo 15048152 unzipped twice under `CrSBrPaper1/` and `zenodo15048152/x/`), WS2, MoS2, MoSe2, WSe2, graphene (2.4 GB), RRUFF oriented minerals. `data/get_data.ps1 -All` has not been run; the extra series sets in `data/catalog-series-quantum-magnetic.md` are optional.

**Git.** Local `master` and GitHub `main` were merged on Oct 22 (`902177d`) and are one history; push with `git push origin master:main`, pull first, stage files by name (never `git add -A`). The tracked `.gitignore` keeps `.env`, `.venv/`, `data/raw/`, `scratch/`, `resources/src/`, `eval/runs/`, `loop/logs/` out of git.

**Do next, in order.**
1. Check `.env` has `ANTHROPIC_API_KEY` (and ideally `VALENCY_BOND_TOKEN`, LangSmith keys). Run the fast tests: `.venv\Scripts\python.exe -m pytest tests -q -m "not slow"` and note the baseline.
2. Start the build loop: `powershell -ExecutionPolicy Bypass -File loop\run_loop.ps1 -MaxIterations 12`. While it runs, do not edit `src/`, `tests/unit/`, `loop/TASKS.md`, `LOG.md` or `docs/tool-status.md` in this session; use a separate git worktree for anything else. Check `loop/logs/status.txt` and `LOG.md` between iterations; if a task is `[blocked]`, read why and decide whether to fix by hand.
3. In parallel (outside the loop's paths): cost-check the eval with the smoke run in `eval/README.md` (two dev cases per arm) and read the token usage in each `transcript.json`.
4. Once T1 to T9 are green: run both arms on `--split heldout --run-name final`, then `eval\score.py eval\runs\final`. Report synthetic (`syn-*`) and experimental (`exp-*`) cases separately.
5. Submission (by Oct 22 evening): one-page write-up with one figure (score difference per metric, plus one example report with the retrieved literature figure beside the measured spectrum), a video of at most 4 minutes posted publicly without a login wall, code link, and the form. Draft in `submission/`.

**Rules that matter.**
- Never read `data/test_set/heldout/**/truth.json` while building tools; never put case ids or truth values in `src/`.
- Never take numbers for reference tables or relations from the excluded papers (McDonnell 2018, Viner 2021, McDonnell 2020, Wdowik 2025); every number must be read from its source, never from memory.
- Never query Bond by peak positions; form a material hypothesis first.
- Do not edit `tests/contract/`, `tests/eval/`, `eval/`, `data/test_set/` to make tools pass. Fix the tool.
- No em dashes in anything written. Keep `LOG.md` current with dated bullets.
- Aditya is a physicist: explain code choices plainly, cite physics sources in comments.

**Known limits.** The cloud session that wrote the planning docs cannot reach arXiv, Zenodo or Mendeley, and its link to the PC shell is unreliable; all network and GPU work happens on the PC. GPU: RTX 3060, 12 GB. Model: Claude Max credits.

When you start, summarize the state you find in five lines and say which step you are on.

---
