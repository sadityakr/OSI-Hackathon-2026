# Results of every evaluation run

Exported from `eval/runs/` by `eval/export_results.py`. Full agent transcripts are not published.
Layout: `<run>/<arm>/<case>/report.json` (what the arm answered), `judge.json` (rubric grades, interpretation cases),
`usage.json` (model, tokens, cost in USD as reported by Claude Code, turns, seconds); `<run>/scores.json`
(identification, `eval/score.py`) and `<run>/judge_scores.json` (interpretation, `eval/judge.py`, Opus judge).

Arms: `bare` = Claude Code with Python only; `skill` = plus the RamanLens skill and literature MCP servers;
`libsearch` = classical library search; `pipeline` = RamanLens tools without an LLM. Model per run below.

## For evaluating bare vs skill by reading the answers

`<run>/COMPARISON_bare_vs_skill.md` puts both arms' reports for every case side by side with the automatic grades
(interpretation: judge score, per-item grades, summary, observations, caveats, questions, citations; identification:
candidates, peaks with irreps and patterns, properties). Start with `v3-int-sonnet` and `v3-int-haiku` (dev
interpretation) and `v3-id-devhard-haiku` (dev identification). Regenerate with `python eval/compare_arms.py <run>`. Case inputs and answer keys:
`data/test_set/<split>/<case>/` (`truth.json` or `rubric.json`).

## Which runs count

| Run | Split | Arms | Model | Status |
|---|---|---|---|---|
| `final-id` | heldout, identification (37) | libsearch, pipeline | none | **headline**: top-1 0.52 (libsearch) vs 0.58 (pipeline), polarization pattern 0.00 vs 0.89. The LLM arms did not finish before the deadline |
| `final-int` | heldout, interpretation (7) | pipeline, bare, skill | Haiku 5.5 | **headline**: rubric 0.50 (bare) vs 0.41 (skill), citation specificity 1.00 vs 1.57 |
| `final-id-sonnet`, `final-int-sonnet` | heldout | bare, skill | Sonnet 5.5 | not finished before the deadline; not reported |
| `v3-int-haiku`, `v3-int-sonnet` | dev_interpret (7) | bare, skill | Haiku, Sonnet | valid dev result, skill v3 |
| `v3-id-devhard-haiku` | dev_hard (15) | bare, skill | Haiku | valid dev result, skill v3 |
| `base-dev`, `base-dev_hard` | dev, dev_hard | libsearch, pipeline | none | valid non-LLM baselines |
| `dev-step0`, `devhard-step0` | dev, dev_hard | bare | Sonnet | valid bare baselines (scorer later fixed; rescored) |
| `devhard-haiku`, `dev-haiku`, `int-dev-haiku`, `int-dev-sonnet` | dev splits | bare, skill | Haiku, Sonnet | **superseded**: skill v1; the runner's "current folder only" rule made agents skip the skill's scripts; some int-dev skill reports were judged before they finished |
| `devhard-haiku-v2`, `int-dev-haiku-v2`, `int-dev-sonnet-v2` | dev splits | bare, skill | Haiku, Sonnet | **superseded**: skill v2, same folder-rule problem for Haiku |
| `v3-id-dev-haiku` | dev | bare, skill | Haiku | **void**: stopped by the Claude usage limit |

## Dev results with skill v3 (before the final run)

| Haiku 5.5, bare -> skill | dev_hard identification | dev interpretation |
|---|---|---|
| material top-1 | 0.46 -> 1.00 | |
| irrep accuracy | 0.47 -> 0.84 | |
| polarization pattern | 0.71 -> 0.88 | |
| cosmic rays rejected | 0.67 -> 1.00 | |
| rubric score | | 0.74 -> 0.79 |
| caveat items | | 0.61 -> 0.88 |
| citation specificity (0 to 2) | | 1.00 -> 1.86 |

Sonnet 5.5 interpretation: rubric 0.88 -> 0.89, caveats 0.75 -> 0.79, citations 1.57 -> 1.71 (near ceiling on these
textbook dev rubrics). Non-LLM on dev_hard: library search top-1 0.46, pipeline 1.00 (synthetic cases come from
the CRD the pipeline matches against, which flatters it).

## Caveats for anyone reading these numbers

- Synthetic (`syn-*`) cases come from the Computational Raman Database that the pipeline and skill matcher use;
  experimental (`exp-*`, `int-*`) cases are the fair test. Report them separately.
- The interpretation judge is an LLM (Opus 5.5), blind to the arm; rubrics come from the source papers.
- Small n: 7 interpretation cases per split; differences of a few points are within noise.
