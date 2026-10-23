# How this skill learns from its runs

Each analysis run may add to this skill. To keep the notes trustworthy, learning goes through two stages:
capture into `inbox.md` (every run, cheap, untrusted) and promotion into `reference/` or `resources/` (only with
evidence). Nothing here applies when the environment variable `SKILL_LEARNING=off` is set: evaluation runs set it
so that held-out cases cannot leak into the skill.

## What goes where

| Item | Goes to | Needs |
|---|---|---|
| Artifact, offset, default or quirk of one instrument | `setups/<setup-id>/setup.md` (calibration values in `calibration.json`) | dataset and date; written at once |
| Caveat, technique, literature pointer for the technique or a material | `learned/inbox.md` | evidence from the run |
| Promoted items, by kind | artifacts: `reference/artifacts.md`; measurement practice: `reference/materials/general-measurement.md` or `reference/measurement-questions.md`; a material: `reference/materials/<name>.md`; a relation: `reference/relations.md`; a mode value: `resources/reference_tables/<material>.json` (literature-backed only, since the loader requires a source and locator) | the promotion criteria below |
| Error in a note found by re-reading its cited source | the note itself, fixed at once | the re-read source with locator, a CHANGELOG line |
| Change to processing code | `learned/inbox.md` first | later: a test on the motivating dataset |

## Promotion criteria (inbox to `reference/` or `resources/`)

An inbox item is promoted when one of these holds:

1. **Literature-backed**: a paper confirms it and the agent read the passage or figure (citation, arXiv id or DOI,
   locator). Promoted like any other note entry, with that citation.
2. **Recurring**: observed in at least two runs on independent datasets (different samples or different days),
   and no note contradicts it. Promoted with the label `observed in N runs (<dates>), no literature source yet`.

How to promote:

- Append to the matching note (`reference/method.md`, `reference/materials/<name>.md`, ...) or add an entry to a
  resource JSON; never delete or reword a cited statement.
- When the item contradicts a cited statement, keep both: write `disputed by runs <dates>: <what was seen>` under
  the original and search the literature for the reason when next relevant.
- A promoted script change keeps the old behaviour behind an option until a second run has used the new one.
- Append a line to `CHANGELOG.md` and mark the inbox entry `status: promoted (<date>, <target file>)`.
- Papers behind evaluation cases (the build-list exclusions) are never used as sources.

## Housekeeping

When `inbox.md` holds more than about 50 open entries, merge duplicates and drop items older than 90 days that
never recurred; record the drops in `CHANGELOG.md`. Keep the skill folder under git: the history is the undo for
any learned change, and the user should see each run's "Skill updates" list.
