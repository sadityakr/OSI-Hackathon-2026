You are packaging Aditya's OSI Hackathon entry into a clean public repository. Deadline: Fri Oct 23, 02:00 CEST
(submission needs a public code link, a one-page write-up with a figure, and a video of at most 4 min).
Working repo (private, source of everything): C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon

## Read first, in this order
1. `submission/packaging-plan.md`: the source of truth for the pitch, naming, features, serving and the public
   repo layout (section 5). Where this prompt and the plan disagree, ask.
2. `CLAUDE.md` (conventions, data licences), `results/README.md` (which runs count), `submission/writeup.md`,
   `submission/skill-v4/` (the skill version to publish), `skill/literature-in-the-loop/` (the meta skill),
   `data/test_set/README.md` (licences of every dataset), `docs/handover-skill-v4-demo.md` (another session's
   tasks; read it for context, do not do them).

## The vision in five lines (use this wording in README and write-up)
- Name: **Literature-in-the-Loop**. Tagline: "Literature in the loop: from raw data to grounded insight."
- We sell the method and the meta skill: connect the literature to every analysis step, so one measurement
  yields everything it can and the next experiment is planned from evidence. The meta skill builds, for any
  technique, a skill that runs on raw data and returns a traced, literature-grounded analysis.
- The Raman skill (2D materials) is the first visible implementation. "RamanLens" must not appear anywhere a
  reader sees it; the Python module `ramanlens` stays as an internal import name tonight.
- Core features: Valency Bond (fast access to 44.5M papers, citation walking), iopic-Bond (our MCP server that
  pulls the exact figure from a paper and shows it to the model), the Marimo notebook as the report (analysis
  and literature in one place, every cutoff and window traceable, exports to PDF), method grounding and system
  grounding.
- Positioning: Anthropic's Model Hardware Standard (MHS) connects agents to instruments, MCP connects them to
  tools; Literature-in-the-Loop connects measured results to grounded insight. Instrument connection is vision,
  never claimed as built.

## Parallel work: do not collide
- The held-out Sonnet evaluation may still be running, and another Claude Code session is working through
  `docs/handover-skill-v4-demo.md` (guard, Marimo install, skill v4 swap, demo prep).
- In the working repo, do NOT edit anything, do not run the evaluation, do not install into `.venv`, do not
  commit or push. Read and copy only.
- Build the public repo in a NEW folder: `C:\Users\sadit\Desktop\P_Projects\Hackathons\literature-in-the-loop`,
  `git init` there with no history from the working repo.

## Build the public repo (layout from plan section 5)
```
README.md
LICENSE                          MIT (copy), plus a DATA section in README for dataset licences
.claude-plugin/marketplace.json  lists both plugins
plugins/literature-in-the-loop/  from skill/literature-in-the-loop/
plugins/raman-skill/             from skill/ramanlens/, with SKILL.md, reference/notebook.md and templates/ taken
                                 from submission/skill-v4/; plugin.json name "raman-skill"; a plugin .mcp.json
                                 that starts iopic-bond (`iopic-bond serve`, expected on PATH after install)
iopic-bond/                      MCP server, src and tests, no library data
src/                             the ramanlens package the Raman scripts import
demo/crsbr-thickness/            the six spectra from data/test_set/heldout/int-CrSBr-thickness-01/spectrum_*.csv
                                 (CC BY 4.0, Zenodo 15048152; never rubric.json); notebook, HTML and PDF are added
                                 after Aditya records the demo
eval/                            runner, judge, scorer, compare, baselines, synth generators, README
data/test_set/                   cases, truth and rubrics, README with licences, withheld_papers.txt
results/                         the exported results (no transcripts)
docs/                            chain diagram (SVG), architecture notes worth keeping, how to build a skill for
                                 another technique
```
Leave out: `data/raw/`, `eval/runs/` (transcripts), `resources/`, `loop/logs/`, `scratch/`, `tmp/`, `ideas/`,
`.env`, `.venv/`, caches, egg-info, any PDF of a paper, `skill/literature-to-skill/` (old name).

Rules while copying:
- Material notes cite "corpus p." locators and name the group's private Lit-RAG corpus in their header lines.
  In the public copy, replace the header explanation with "p. = page of the published journal PDF" and change
  "corpus p." to "journal p."; no mention of Lit-RAG, laufey or the group corpus anywhere.
- Plugin `.mcp.json` must not contain machine paths. Document the install instead.
- Default iopic-bond behaviour stays unfiltered; document `IOPIC_BOND_EXCLUDE_FILE` for fair tests.

## README (pitch first, in this order)
1. Name, tagline, three sentences of the vision.
2. The chain diagram: instrument -> raw data + metadata -> traced analysis (Marimo) -> existing knowledge
   (Bond + figures) -> grounded interpretation -> report an agent or researcher reads to plan the next experiment.
   Draw it as a simple SVG in `docs/`, no em dashes in labels.
3. Screenshot slot for the CrSBr notebook (placeholder until the demo exists).
4. Results: three numbers with n and the held-out caveat; use [TBD] where `results/README.md` has no final
   value yet, never invent numbers. State the fair-test rule (the agent never sees the paper the test data come
   from; iopic-Bond withholds it).
5. Install and try: add the marketplace in Claude Code or the Claude desktop app, install `raman-skill` and
   `literature-in-the-loop`, install the Python packages (`pip install -e src -e iopic-bond[parse]`,
   `VALENCY_BOND_TOKEN` in `.env`), run on `demo/crsbr-thickness/`, open with `marimo edit`, export with
   `marimo export pdf`.
6. Build a skill for another technique with the meta skill.
7. How it was evaluated (arms, held-out split, blind rubric judge, withheld papers).
8. iopic-Bond: own section (Valency prize: best use of MCP Bond).
9. Limits, licences, credits.

## Write-up
Draft `WRITEUP.md` in the new repo: one page with one figure, same pitch and numbers ([TBD] where pending),
built from `submission/writeup.md` but reframed around Literature-in-the-Loop.

## Checks before you stop
- Grep the new repo, case-insensitive, for: RamanLens (outside import lines and the `ramanlens` package
  folder), Lit-RAG, lit_rag, litrag, laufey, corpus p., C:\Users, sadit, .env content, tokens, "private".
  Report each remaining hit.
- No file over 50 MB; total size reported.
- `marketplace.json` and both `plugin.json` parse as JSON; run `claude plugin validate` on each if the command
  exists.
- Every link in README resolves to a file in the new repo.
- No em dashes anywhere you wrote.

## Stop point
Commit locally in the new repo. Do NOT create the GitHub repository and do NOT push: making it public is
Aditya's call. Report back: the file tree (two levels), total size, the grep results, what you left out and
why, open [TBD]s, and the exact commands to create the public repo `sadityakr/literature-in-the-loop` and push.
