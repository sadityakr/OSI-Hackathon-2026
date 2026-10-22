# Literature-in-the-Loop: packaging and pitch plan (updated Oct 22, 19:35 CEST)

Deadline Fri Oct 23, 02:00 CEST. Supersedes the 18:35 version.

## 1. What we sell

**The idea: connect the literature to every analysis step, so one measurement yields everything it can, and the
next experiment is planned from evidence.** A meta skill builds, for any measurement technique, a skill that runs
on raw data and returns a traced analysis grounded in what the literature already knows about that technique and
that material system. Raman spectroscopy of 2D materials is the first visible implementation, the "Raman skill".

The chain we close:

```
instrument -> raw data + metadata -> traced analysis (Marimo notebook) -> existing knowledge (Bond + figures)
           -> grounded interpretation -> report that an agent or researcher reads to plan the next experiment
```

Positioning for the video: Anthropic's Model Hardware Standard (MHS, research preview since Aug 2026) connects
agents to instruments, so data can flow from the machine with its settings attached; MCP connects agents to
tools and data. We build the next layer: from the measured result to grounded insight, with the literature
joined at the analysis step itself. MHS gets the data out of the instrument; we make sense of it against what
is already known.

Name: **Literature-in-the-Loop** (the method and the meta skill, `literature-in-the-loop`). Tagline: "Literature in the loop: from raw data to grounded insight." "RamanLens" disappears from everything a judge sees (README, write-up, video, plugin name). The Raman
implementation is the "Raman skill" (`raman-analysis`). The Python module `ramanlens` stays internal tonight:
renaming it breaks 84 tests and the eval runner hours before the deadline; rename it in the public repo later.

## 2. The features that make the chain work (what to show for each)

| Feature | What it does | What exists | What to show |
|---|---|---|---|
| **Valency Bond** | Fast concept search over 44.5M papers; walk citations to the original paper where a property was measured | Bond via MCP; forward citations through Bond (`expand`), backward through the parsed reference list of an ingested paper | Agent finds a review, walks to the original measurement paper |
| **iopic-Bond** (our MCP server) | Pulls the exact figure the agent needs from the paper (open arXiv PDFs), shows it to the model, hands the image to the notebook | Built: `find_papers`, `expand`, `ingest_paper`, `list_figures`, `view_figure`, `search_library`; withheld-paper guard for fair tests | `view_figure` in the Claude desktop app: the published Raman figure appears in the conversation |
| **Marimo notebook as the report** | One place for the analysis and the literature it rests on, with citations. The complete record: every baseline, cutoff, window and threshold is a cell, so a reader sees and can change what a polished figure hides. Exports to PDF (`marimo export pdf`, tested) for sharing | Template with six FILL cells, computed cells for all numbers, figure beside the data, tagged and cited claims | Scroll the CrSBr notebook; change a fit window live and watch the band table update |
| **Method and system grounding** | Literature on how to analyze the technique (method) and on what was reported for the material (system) | Notes for 10 materials, ~100 papers with locators; relations with validity ranges | The interpretation cites the Torres figure with a locator next to the measured trend |
| **Meta skill** | Builds such a skill for any technique: notes, relations, scripts, notebook template | `skill/literature-in-the-loop/` | Show its SKILL.md and name the next techniques (PL, XRD, magnetotransport) |
| **Instrument connection** (vision) | Metadata straight from the instrument into the notebook, e.g. through an MHS driver | Not built; metadata comes from files and the user | One sentence and one diagram box in the video, labelled as next |

Why the notebook and not a figure: a published figure is the end of a chain of choices (baseline, cutoffs,
smoothing, which spectra to show) that the reader cannot see or redo. The notebook keeps that chain, so the
analysis can be checked, rerun on the next dataset, and read by an agent that plans the next experiment.

## 3. Mapping to the criteria

| Criterion | Line | Evidence |
|---|---|---|
| Impact | Any lab gets the most out of each measurement and plans the next one from evidence, not memory | CrSBr notebook; time and cost per case |
| Innovativeness | Literature joins the analysis at the step where it is needed, including the figures, not as a chat search afterwards | chain diagram; `view_figure` call mid-analysis |
| Novelty | A meta skill that compiles a technique's literature into an executable skill plus a traced notebook template; figure-level access to Bond papers | meta SKILL.md; iopic-Bond |
| Relevance | Layer number, defects, strain, doping, magnetic order in 2D materials | CrSBr ranking against AFM; held-out results |

## 4. Evidence

1. Held-out numbers (v3 skill): identification on experimental cases (library search, Haiku bare, Haiku with
   skill); caveats and citation specificity; cost per case. Report synthetic separately.
2. The demo case: CrSBr thickness, six flakes. Bare and skill v3 got the order wrong; the notebook's windowed
   fits give C 102.9, E 103.3, A 108.6, F 111.9, D 113.3, B 114.0 cm-1, which matches the AFM order, with the
   end members matching Torres 2022 Fig. 1h. Shown as a demonstration (v4 was written after v3 failed this
   held-out case), with the source paper withheld from the agent.
3. Fair-test rule, stated once in the video: the agent never sees the paper the data come from; iopic-Bond
   withholds it, and the skill notes were built without it.

## 5. How we serve it

| Who | How | Tonight |
|---|---|---|
| Judges, anyone curious (no install) | A public page with the CrSBr notebook (static Marimo HTML export; a browser-run WASM export would need the Python package installable in the browser, so skip it tonight), the chain diagram and the results | yes |
| Claude Code and Claude desktop app users | The public repo is a plugin marketplace: add it, install `raman-skill` and `literature-in-the-loop`; the Raman plugin starts iopic-Bond itself | yes: `.claude-plugin/marketplace.json`, plugin `.mcp.json` |
| Researchers building a skill for their own technique | Run the meta skill in Claude Code with Bond and iopic-Bond | yes (documented), not demonstrated beyond Raman |
| claude.ai users without a terminal | iopic-Bond as a hosted remote connector (lab MCP hosting plan) | roadmap |

Public repo: a fresh repo with only the deliverables. The working repo's history contains paper PDFs, the
private Lit-RAG code and transcripts; deleting them in a last commit does not remove them from history. The
working repo stays private with the full evaluation record; the public repo links the results it reports.

Public repo layout:

```
README.md                       pitch, chain diagram, notebook screenshot, numbers, install
.claude-plugin/marketplace.json
plugins/literature-in-the-loop/    the meta skill
plugins/raman-skill/            skill, scripts, reference notes, notebook template, .mcp.json (iopic-bond)
iopic-bond/                     MCP server (MIT)
src/                            Python package the Raman scripts import
demo/crsbr-thickness/           the six spectra, the agent's notebook, its HTML export
eval/                           runner, judge, scorer, rubric-format docs; results summary table
```

## 6. Demo in the Claude desktop app (Aditya records)

Use the app's Code mode on the PC, not the chat mode: the chat mode runs code in a cloud sandbox that has
neither the Python package nor your local spectra, while Code mode runs the scripts locally and still shows each
MCP call, including the figure returned by `view_figure`. Rehearse once and check that the figure is visible in
the tool result; if it shows only as a placeholder, open the saved `image_path` beside it during the recording.

Setup in the demo folder `C:\Users\sadit\raman-demo\crsbr-thickness` (outside the repo, six CSV files only):

- `.mcp.json` in the demo folder: iopic-bond only, with `IOPIC_BOND_HOME`, `IOPIC_BOND_EXCLUDE_FILE`
  (repo `data\test_set\withheld_papers.txt`) and `IOPIC_BOND_ENV_FILE` (repo `.env`, for `VALENCY_BOND_TOKEN`).
  No direct Valency server in the test, because its results cannot be filtered.
- `.claude\settings.json` in the demo folder: deny reads of the repo's `data/test_set`, `eval`, `results`,
  `submission`.
- The skill: skill v4 copied into the plugin after the Sonnet runs finish, loaded from the repo (marketplace or
  plugin folder).
- Pre-ingest Torres 2022 (`iopic-bond ingest 2212.01754`) so the recording does not wait for a parse.

## 7. Time plan to 02:00

| Time | Task |
|---|---|
| now | Claude Code on the PC: handover Tasks 0 to 2 (guard, Marimo, skill v4 after the Sonnet runs) |
| after the runs | judge, figure, [TBD] numbers |
| 1 h | demo rehearsal and recording in the desktop app |
| 1 h | fresh public repo with marketplace, rename to Raman skill in visible text, README pitch-first |
| 45 min | public notebook page, write-up final |
| 1 h | video edit and post |
| rest | buffer, submission form |

Cut order if late: meta-skill walkthrough in the video (keep one slide), cost numbers.
