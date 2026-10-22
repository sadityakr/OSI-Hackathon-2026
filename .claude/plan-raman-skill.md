# Plan: RamanLens as a Claude Code skill, built test-first against a bare agent (2026-10-22, 00:40 CEST)

Research behind this plan: `docs/sota-research.md`. Status: proposal, waiting for Aditya's decisions (end of file).

## What gets built: one skill, thin scripts over the ramanlens package, curated knowledge

```
skill/ramanlens/                      a Claude Code plugin dir, loaded with --plugin-dir
  .claude-plugin/plugin.json
  skills/raman-analysis/
    SKILL.md                          short expert workflow (under 150 lines), loads references on demand
    scripts/                          one-shot CLIs, JSON to stdout, PNG plots the agent can look at
      rl_fit.py        despike (Whitaker-Hayes) -> baseline (pybaselines arPLS) -> find_peaks -> lmfit
                       (Lorentzian / Voigt / BWF by BIC) -> peaks with errors, Si offset, plot
      rl_qc.py         artifact and condition flags: spikes, saturation, fluorescence slope, Si calibration,
                       notch cutoff, plasma-line suspects, heating risk, resolution vs claimed splitting
      rl_match.py      CRD + literature-table matcher with fitted frequency scale and missing-mode penalty
      rl_polar.py      angle-series classifier (Fourier 2 theta / 4 theta)
      rl_relation.py   list / apply relations with validity check (the ten in docs/sota-research.md)
    reference/
      relations.md         equation, variables, validity, source per relation
      materials/<m>.md     mode table with sources, known defects and their signatures, typical pitfalls
      artifacts.md         universal red flags and what each looks like
      measurement-questions.md   what to ask the user and why
      literature.md        how to use Valency + iopic-bond: concept query, ingest arXiv paper, view the figure,
                           compare with the measured spectrum
```

Why a skill plus scripts: the agent reasons, the scripts measure. Research says the gains come from extracted peak
tables and retrieval (IR-Agent, SpectraLLM), and no public ML model covers 2D materials, so no neural model is in the
toolset. Physics relations carry layer number, strain, doping and defects. Scripts call `src/ramanlens/` so the same
code serves the skill, the SDK toolset (T9) and the contract tests.

## How "better" is measured: headless Claude Code, two arms, same everything else

- New runner `eval/run_claude_code.py` (new file; `run_agent.py`, `score.py` untouched): per case, copy
  `input.json` + `spectrum.csv` into a fresh folder outside the repo, run `claude -p` with
  `--json-schema` (REPORT_SCHEMA), `--setting-sources` limited so the user's global CLAUDE.md and skills do not
  leak in, `--strict-mcp-config`, fixed `--model` and `--effort`. Arm `bare`: Bash/Python only. Arm `skill`: plus
  `--plugin-dir skill/ramanlens` and the Valency + iopic-bond MCP servers. Writes the same
  `eval/runs/<run>/<arm>/<case>/report.json` that `score.py` already reads. Runs on Max credits; no API key needed.
- Gap: `score.py` ignores `properties` (layers, defects, strain), which is half of what this skill is for. Needs a
  small scorer extension plus truth for new cases (decision 3).

## Order: each step adds one capability, then re-runs the dev split; keep it only if dev scores improve

| Step | Adds | Dev check | Est. |
|---|---|---|---|
| 0 | eval runner; bare baseline on 13 dev cases; smoke cost per case | baseline numbers, tokens per case | 1.5 h |
| 1 | perception core (T1 to T4: readers, despike, baseline, fit, Si flag) + `rl_fit.py`, `rl_qc.py`, SKILL.md v1 | peak recall, position MAE, cosmic rays | 3 h |
| 2 | matcher (T5) + literature tables (T7, numbers read from sources) + `rl_match.py` | id_top1, id_top3, hint_correct | 3 h |
| 3 | polarization (T6) + `rl_polar.py` | pattern_acc, irrep_acc | 1.5 h |
| 4 | relations (T8, the ten) + material reference notes + measurement questions | properties metric on new cases | 3 h |
| 5 | literature figure grounding (Valency + iopic-bond view_figure) | qualitative; one demo report | 1.5 h |
| 6 | final held-out run, both arms; ablation table (step by step) | headline | 2 h |
| 7 | one-pager, figure, 4 min video, form | | 4 h |

About 20 h of work for about 25 h left. Cut lines in order: step 5, extra materials in step 4, synthetic tier in step 6.

Steps 1 to 4 can be built by the existing loop (contract tests already define T1 to T8) in the main checkout, while
this session builds the runner, scripts and skill text in a worktree. The ablation table (dev score after each step)
is itself a write-up figure: it shows which tool earns its place.

## Decisions and findings (01:20 CEST)

- Decided: headless Claude Code harness; dev on Sonnet, final on Opus; scorer extended with property_acc;
  loop builds T1 to T8 while this session builds the skill. Revised after baselines: develop against Haiku 5.5,
  final held-out run on Haiku and Sonnet (Opus if credits), each bare vs skill.
- Baseline finding: bare Sonnet 5.5 is at ceiling on synthetic cases (dev_hard: id 1.0, property 1.0, irrep 0.69);
  bare Haiku 5.5 is not (id 0.62, hint 0.50, irrep 0.47, pattern 0.71, property 0.60). About $0.10 per case.
- Scorer fixes (both arms equally): irrep alternatives in parentheses, descriptive material names, only standard
  property keys scored; new split dev_hard/ (15 cases) kept out of the loop's contract tests.

## Decisions needed from Aditya (answered)

1. Eval harness: headless Claude Code on Max (recommended, no key needed, tests the actual skill) or the existing
   SDK runner with an API key.
2. Model for dev iterations: same model for both arms is mandatory; Sonnet for dev steps and Opus for the final, or
   Opus throughout (costlier, smaller headroom for tools to show gains).
3. Extend the scorer and test set with property cases (layer number, defect level, strain/doping) built from papers
   in the build set: needed to measure the part of the skill you care about most.
4. Build path: run the loop for T1 to T8 in parallel with this session (recommended), or build directly here.
