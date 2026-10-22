# Handover: install Marimo, switch to skill v4, record the CrSBr demo

For Claude Code on Aditya's PC, repo root `C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon`.
Read `CLAUDE.md` and `submission/packaging-plan.md` first. Deadline Fri Oct 23, 02:00 CEST. No em dashes in any
written output.

## Context in five lines

- Skill v4 is staged in `submission/skill-v4/` (SKILL.md, `reference/notebook.md`, `templates/raman_notebook.py`).
  It makes the agent open one published figure for the material system and deliver a Marimo notebook built from
  the template.
- The project is now called Literature-in-the-Loop. The meta skill is at `skill/literature-in-the-loop/` (separate
  plugin, not loaded by the eval). Delete the old copy `skill/literature-to-skill/` (renamed; the cloud session
  cannot delete files on the PC).
- `src/pyproject.toml` now lists marimo as a core dependency; the `.venv` does not have it yet.
- The held-out runs use skill v3. Do not change `skill/ramanlens/` until the Sonnet held-out runs have finished,
  or the two models are scored on different skills.
- In the cloud the template, filled by hand for int-CrSBr-thickness-01 with Torres 2022 Fig. 1h values, ranked the
  six flakes in the AFM order (Ag1: C 102.9, E 103.3, A 108.6, F 111.9, D 113.3, B 114.0 cm-1). The demo shows
  whether the agent gets there on its own.

## Testing rule: the agent never reads the paper the data come from

Every test dataset comes from a paper (int-CrSBr-* from Wdowik et al. 2025, arXiv 2503.15298). That paper holds
the answer, so the agent must not read it. It may use everything else the literature reports: that is the point
of system grounding, and it is what a researcher with new flakes would do. Torres et al. 2022 (arXiv
2212.01754) is an earlier, independent paper on CrSBr layer dependence, so it is allowed.

Two guards, both already in place:
- Build time: the skill notes exclude the source papers (`reference/materials/CrSBr.md`, line 5).
- Run time (new, committed by the cloud session): iopic-bond hides and refuses withheld papers when
  `IOPIC_BOND_EXCLUDE_FILE` points at `data/test_set/withheld_papers.txt` (Wdowik 2025, Sahu 2025, McDonnell
  2018 and 2020, Viner 2021). Code in `iopic-bond/src/iopic_bond/exclude.py`, tests in
  `iopic-bond/tests/test_exclude.py`. Without the variable nothing changes, so the running eval is unaffected.
- The direct Valency MCP cannot be filtered, so test runs do not get it. Literature search goes through
  iopic-bond `find_papers`, which calls Bond with `VALENCY_BOND_TOKEN` and applies the filter. Bond is still
  the search engine (Valency prize unaffected).

## Task 0: check the guard (now, safe while the eval runs)

1. `.venv\Scripts\python.exe -m pytest iopic-bond\tests -q`: all pass.
2. `VALENCY_BOND_TOKEN` must be in `.env` (Valency app, Settings; https://docs.valency.io/guides/api/). The v3
   dev transcripts show `find_papers` failing with "VALENCY_BOND_TOKEN is not set". Check with
   `.venv\Scripts\iopic-bond.exe doctor`. If Aditya has no token, stop and tell him: without it the test runs
   have no search, only the pre-ingested papers.
3. Audit the existing v3 skill-arm transcripts for leaks: search every `eval\runs\final-*\skill\*\transcript.jsonl`
   for the ids, DOIs and title fragments in `withheld_papers.txt` inside tool calls and tool results (not in the
   prompt). Report each hit with run, case and tool. In the transcripts checked so far the skill arm made no
   literature calls in interpretation, so none are expected; identification cases need checking.

## Task 1: install Marimo (now, safe while the eval runs)

```powershell
.venv\Scripts\pip install "marimo>=0.9" nbformat "nbconvert[webpdf]"
.venv\Scripts\python.exe -m playwright install chromium   # for marimo export pdf (WebPDF)
.venv\Scripts\marimo --version
```
Done when the version prints. Do not reinstall `src` while an eval case is running.

## Task 2: wait for the Sonnet held-out runs, then switch to v4

1. Check whether the runs are finished: `eval\runs\final-int-sonnet\skill\` and `eval\runs\final-id-sonnet\skill\`
   must each hold a `report.json` for every case (7 interpretation, 37 identification), and no `claude` or
   `run_claude_code.py` process may still be running (`Get-Process python, claude -ErrorAction SilentlyContinue`).
   If they are still running, do Task 3 preparation (steps 1 to 3 below) and come back.
2. Copy the staged files into the skill (adds two files, replaces SKILL.md; leaves the other reference notes):
   ```powershell
   $dst = "skill\ramanlens\skills\raman-analysis"
   Copy-Item submission\skill-v4\SKILL.md $dst\SKILL.md -Force
   Copy-Item submission\skill-v4\reference\notebook.md $dst\reference\notebook.md -Force
   New-Item -ItemType Directory -Force $dst\templates | Out-Null
   Copy-Item submission\skill-v4\templates\raman_notebook.py $dst\templates\raman_notebook.py -Force
   ```
3. Run the fast tests: `.venv\Scripts\python.exe -m pytest tests -q -m "not slow"`. All must stay green.
4. Commit: "skill v4: system figure step required, Marimo notebook template" and a dated line in `LOG.md`.
5. For any eval run from now on (not the finished v3 runs): in `eval/run_claude_code.py` `mcp_config`, drop the
   direct `valency` server for the skill arm and add `IOPIC_BOND_EXCLUDE_FILE` (repo
   `data/test_set/withheld_papers.txt`) and `IOPIC_BOND_ENV_FILE` (repo `.env`) to the iopic-bond `env`; drop
   `mcp__valency__*` from `SKILL_TOOLS`. Note in `results/README.md` that v3 runs had direct Valency without the
   guard and what the Task 0 audit found.

## Task 3: prepare and record the CrSBr demo

Preparation (can run before Task 2 finishes):

1. **Demo folder outside the repo, without answers.** The held-out folder holds `rubric.json` with the AFM
   truth, and results and transcripts in the repo discuss it. The demo agent must see neither, so the demo runs
   outside the repo with read-deny rules as a second guard.
   ```powershell
   $repo = "C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon"
   $demo = "C:\Users\sadit\raman-demo\crsbr-thickness"
   New-Item -ItemType Directory -Force $demo | Out-Null
   Copy-Item "$repo\data\test_set\heldout\int-CrSBr-thickness-01\spectrum_*.csv" $demo
   ```
   Copy only the six CSV files: never `rubric.json` or `input.json`.
2. **Pre-ingest the Torres paper** so the recording does not wait about 3 min for a cold Docling parse:
   ```powershell
   $env:IOPIC_BOND_HOME = "$repo\data\raw\iopic-bond"
   & "$repo\.venv\Scripts\iopic-bond.exe" ingest 2212.01754
   ```
   Confirm that the figure showing the layer dependence (Fig. 1, panel h in the notes) was extracted: look in
   `data\raw\iopic-bond\papers\2212.01754\` and open the image. If the parse failed, report it; the demo still
   runs on the notes, but the figure step is the point.
3. **Demo config files** in `submission\demo\` (commit them):
   - `demo-mcp.json` (iopic-bond only, with the guard; no direct Valency):
     ```json
     {"mcpServers": {
       "iopic-bond": {
         "command": "C:\\Users\\sadit\\Desktop\\P_Projects\\Hackathons\\OSI Hackathon\\.venv\\Scripts\\iopic-bond.exe",
         "args": ["serve"],
         "env": {
           "IOPIC_BOND_HOME": "C:\\Users\\sadit\\Desktop\\P_Projects\\Hackathons\\OSI Hackathon\\data\\raw\\iopic-bond",
           "IOPIC_BOND_EXCLUDE_FILE": "C:\\Users\\sadit\\Desktop\\P_Projects\\Hackathons\\OSI Hackathon\\data\\test_set\\withheld_papers.txt",
           "IOPIC_BOND_ENV_FILE": "C:\\Users\\sadit\\Desktop\\P_Projects\\Hackathons\\OSI Hackathon\\.env"
         }
       }}}
     ```
     `IOPIC_BOND_ENV_FILE` is needed because the demo folder is outside the repo, so `.env` (with the Bond token)
     is not found from the working directory.
   - `demo-settings.json`: deny reads of the answers, as `eval/run_claude_code.py` does (`deny_test_set`), using
     the same path form the runner builds from `ROOT.as_posix()`:
     `{"permissions": {"deny": ["Read(/<repo posix path>/data/test_set/**)", "Read(/<repo posix path>/eval/**)",
     "Read(/<repo posix path>/results/**)", "Read(/<repo posix path>/submission/**)"]}}`
4. **Dry run, headless, not recorded** (after Task 2), from `$demo`, with the runner's flags minus the report
   schema:
   ```powershell
   cd $demo
   claude -p "<demo prompt below>" --model claude-sonnet-5-5 `
     --plugin-dir "$repo\skill\ramanlens" `
     --strict-mcp-config --mcp-config "$repo\submission\demo\demo-mcp.json" `
     --settings "$repo\submission\demo\demo-settings.json" `
     --permission-mode dontAsk `
     --allowedTools Bash Read Write Edit Glob Grep Skill "mcp__iopic-bond__*" `
     --disallowedTools WebSearch WebFetch Agent Task `
     --output-format stream-json --verbose > dryrun.jsonl
   ```
   The scripts and the notebook import `ramanlens`, so the `.venv` Python must be the one on PATH in that shell
   (`& "$repo\.venv\Scripts\Activate.ps1"` first). Check, and report each line as pass or fail:
   - a `view_figure` call on arXiv 2212.01754 (or another CrSBr layer-dependence figure) appears in
     `dryrun.jsonl`;
   - no tool result contains a withheld paper (ids, DOIs, titles in `withheld_papers.txt`); a `withheld` status
     is fine (the guard worked; note it), any other appearance is a leak and the run does not count;
   - no read of anything under the repo's `data/test_set`, `eval`, `results` or `submission`;
   - no `mcp__valency__` call (the server is not configured; if one appears, the config was not applied);
   - `raman_analysis.py` and `raman_analysis.html` exist and `marimo check raman_analysis.py` passes;
   - the band table puts Ag1 of C and E lowest and of B and D highest; the interpretation cites the figure with
     a locator and asks for AFM.
   If the figure step does not fire, tighten step 8 of `SKILL.md` (for example, name Torres 2022 Fig. 1 as the
   default thickness figure for CrSBr in `reference/literature.md`), rerun the dry run, and commit the change.
   Move the dry-run outputs to `submission\demo\crsbr-thickness-dryrun\` before the recording, so the demo
   folder holds only the six CSV files again.

Recording (Aditya does this; Claude Code prepares everything above):

- In `$demo`, with the `.venv` activated, start
  `claude --model claude-sonnet-5-5 --plugin-dir "$repo\skill\ramanlens" --mcp-config "$repo\submission\demo\demo-mcp.json" --settings "$repo\submission\demo\demo-settings.json"`
  and paste the demo prompt. Record the screen. Then `marimo edit raman_analysis.py` and scroll: band table,
  Ag1 trend, Torres figure beside it, interpretation, references.
- Afterwards Claude Code copies the notebook, its HTML export and the session transcript into
  `submission\demo\crsbr-thickness\` and commits them. The AFM order (C 1L < E 2L < A 3L < F 5L < D 6L < B bulk)
  is shown in the video as the check, never given to the agent.

## Demo prompt

> These are Raman spectra of six mechanically exfoliated CrSBr flakes from the same CVT-grown crystal, on a
> marked substrate. Room temperature, ambient, backscattering, 532 nm, 200 uW, WITec with an 1800 l/mm grating,
> same settings for all six. AFM has not been analysed yet. How do these six spectra differ, and what can you say
> about the thickness of each flake? Rank them if you can. Anything I should be careful about? Use the
> raman-analysis skill and give me the notebook.

(Same context and question as the held-out case input, plus the last sentence.)

## Honesty notes for the write-up

- int-CrSBr-thickness-01 is a held-out case and v4 was written after v3 failed it. Present the v4 run as a
  demonstration; the held-out scores in the write-up stay the v3 numbers.
- If time allows, run v4 on one more case (int-CrSBr-temperature-01 or int-WS2-temperature-01, again from a clean
  folder without `rubric.json`) and report whether the figure step fired and whether the reading matched.

## Report back

One short message: guard tests and Bond token status, the leak audit result, Marimo version, whether the Sonnet runs were complete when v4 went in, test result, the
dry-run checklist, any SKILL.md change made, and the commit hashes.
