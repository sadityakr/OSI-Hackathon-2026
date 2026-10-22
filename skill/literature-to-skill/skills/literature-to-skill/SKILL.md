---
name: literature-to-skill
description: Build an analysis skill for an experimental technique (Raman, PL, XRD, magnetotransport, ...) from the published literature - finds the method and material-system papers through Valency Bond, reads their figures through iopic-bond, writes cited reference notes, relations with validity ranges, analysis scripts and a Marimo notebook template that an analysing agent fills for each measurement. Use when asked to create, extend or refresh a skill for analysing a kind of measurement or a new material system.
---

# Literature to skill

You turn what the literature knows about analysing one kind of measurement into a skill another agent executes.
The finished skill is RamanLens (`skill/ramanlens/skills/raman-analysis/`); read its `SKILL.md`,
`reference/` and `templates/raman_notebook.py` as the worked example before you start.

## Inputs to settle first

Technique, the material systems in scope, the variables users scan (thickness, temperature, field, strain, gate
voltage, angle), the file formats and metadata users have, and what a senior researcher checks first. Ask the
user for what you cannot infer.

## The literature does two jobs; collect both

1. **Method**: how to analyze this kind of data. Line shapes, background, calibration references, standard
   relations and where they stop being valid, artifacts and pitfalls, what must be known about the measurement.
2. **System**: what has been reported for each material. Characteristic features and their values, how they move
   with each scanned variable, anomalies, disagreements between groups, and the figures that show this best.

Search with Valency Bond by concept, never by numbers ("layer dependence of Raman modes in CrSBr", "Si
calibration Raman spectrometer"). Prefer records with an arXiv id. Use iopic-bond `ingest_paper`, `list_figures`
and `view_figure` to read the figures: the conclusions are in the prose, the evidence for how to read data is in
the plots. Keep a build list of every paper used; papers behind evaluation cases never enter it.

## What you write (layout of the new skill)

```
skills/<technique>-analysis/
  SKILL.md                     required first commands, workflow, deliverable, expert habits
  scripts/                     validated processing (QC, fit, series tracking); reuse an existing package when one exists
  reference/method.md          job 1, every rule with paper and locator
  reference/relations.md       equations with every variable defined, validity range, source, self-test value
  reference/measurement-questions.md   what to ask the user and why it changes the answer
  reference/materials/<name>.md        job 2 per material, ending with the best figures (paper, arXiv id, Fig.)
  reference/literature.md      how to ground a run on the system literature at analysis time
  reference/notebook.md        how the analysing agent fills the template
  templates/<technique>_notebook.py    the Marimo template
```

Every number in a note carries author, year, arXiv id or DOI, and a figure or table locator; numbers read from a
plot say so (with the reading uncertainty). Write what is uncertain or disputed as such.

## The notebook template contract

The template is what makes each analysis reproducible and auditable. Build it for the technique, then run it on
one real dataset before you finish.

- **FILL cells only for judgement**: sample and conditions with assumptions; data files and the series variable;
  features to track with search windows from the material notes; literature values and figure paths; method
  notes; interpretation; limits and questions; references.
- **Computed cells for everything numeric**: load and plot raw data; quality and calibration per dataset; fits
  with uncertainties; feature tracking across the series; the literature table next to the measured values and
  the published figures shown with `mo.image`.
- **Numbers in the interpretation come from computation**: expose a helper (like `pos(label, band)`) that the
  interpretation f-string calls, so no value is typed by hand.
- **Provenance**: every interpretation bullet tagged measured, inferred or literature, with a reference number.
- **Runs clean**: `marimo export html <file> -o <file>.html` and `marimo check <file>` pass on the test dataset.
  Marimo rules: each global defined in one cell, cell-local names start with an underscore, no cross-cell
  mutation, last expression is the output.

## Check before you hand over

1. Run the new skill headless on a case it was not built from and read the notebook it produced.
2. Every citation in the notes resolves to a paper in the build list, with a locator.
3. The analysing agent opened at least one system figure during that run; if not, tighten the workflow step.
