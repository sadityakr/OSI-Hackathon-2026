# RamanLens: a Raman analysis skill that reads spectra like a senior 2D-materials researcher

Aditya Kumar (JGU Mainz), 4th Open Scientific Intelligence Hackathon, Oct 2026. Code and data:
https://github.com/sadityakr/osi-hackathon-2026 (MIT)

## The problem: Raman of 2D materials needs expertise that no tool packages

Raman spectroscopy is the everyday characterization tool for graphene, transition-metal dichalcogenides and 2D
magnets. A researcher usually knows the material; what they need is interpretation: how many layers, how defective,
strained or doped, whether the magnetic order shows, and whether a shift is physics or a calibration error. That
knowledge lives in hundreds of papers and in the habits of experienced spectroscopists. Existing tools do not
package it: classical library search names a material and stops, and no public machine-learning model covers 2D
materials (we found none with weights; RamanBench, Koddenbrock et al. 2026, arXiv 2605.02003, reports that no
method generalizes across data sets).

## What we built: tools that measure, notes that know the literature, an agent that reasons

RamanLens is a Claude Code skill (`skill/ramanlens/`) on a tested Python package (`src/ramanlens/`, 84 tests):
- **Measurement tools**: cosmic-ray removal (Whitaker and Hayes 2018), asymmetric least squares baseline, multi-
  Lorentzian fits with uncertainties, Si-line calibration check, band tracking across a series of spectra,
  polarization classification, and a peak matcher over 385 layered crystals of the Computational Raman Database
  (Bagheri and Komsa 2023) plus curated literature tables.
- **Physics relations** that refuse to extrapolate: MoS2 and WS2 layer number (Lee et al. 2010; Berkdemir et al.
  2013), graphene defect distance (Cancado et al. 2011), strain and doping (Lee et al. 2012), and more.
- **Literature notes** for 10 materials, distilled from about 100 papers through Valency Bond and full-text reading:
  how spectra change with thickness, defects, strain, temperature, laser and substrate, the known pitfalls, and the
  questions an expert asks. Every number carries a paper and figure or table locator.
- **Literature figures at run time**: the agent finds the paper (Valency Bond), parses the arXiv PDF and looks at
  the published reference spectrum (iopic-Bond, our MCP server).

## How we measured it: six arms, blind held-out cases, a blind judge

Same cases for every arm: classical **library search** (cosine similarity on preprocessed spectra, the standard
non-LLM method; Li et al. 2022, Analyst), the **RamanLens pipeline** without an LLM, and **Claude Haiku 5.5 and
Sonnet 5.5**, each **bare** (Python only) and **with the skill**. Held-out cases come from papers excluded from
building the skill: [TBD n] identification cases (synthetic from the CRD, plus experimental CrSBr and WS2 data)
and 7 interpretation cases from published experimental data (CrSBr thickness and magnetic order, Wdowik et al.
2025; resonant WS2, MoSe2, WSe2, McDonnell et al. 2018, 2020). Interpretation rubrics were written from each
paper's own conclusions by an agent the skill builders never saw, and graded by a blind Claude Opus judge.

![Held-out results](figure.png)

## Results

[TBD from submission/figure.md]
- Identification: library search [x], pipeline [x], Haiku bare [x] vs with skill [x].
- Interpretation rubric score: Haiku [x] to [x], Sonnet [x] to [x]; caveats and citation specificity [x].
- Citation check (`eval/verify_citations.py`, arXiv and Crossref lookup of every cited paper): share of citations that
  do not resolve to the stated author and year [x] bare vs [x] skill; share the agent itself marks "from recall, not
  checked" [x] vs [x]. On the Haiku development cases 10 of 35 bare citations were marked from recall against 1 of
  55 for the skill, which also cited about 8 papers per report against 5.
- Case study (`submission/case-study.md`, written by `eval/case_study.py`): the held-out case with the largest skill
  gain, with both reports and the judge's reasons side by side.
- Development finding: a frontier model alone already names common 2D materials and applies textbook relations; the
  skill's value lies in symmetry labels, polarization, artifacts and caveats, and claims a reader can trace to a
  figure in a paper.

## Limits we state

Synthetic cases come from the same database the matcher uses and flatter it; experimental cases are few. The judge
is an LLM, mitigated by paper-derived rubrics and blinding. Interpretation truth is each paper's own reading.

## Impact

A researcher gets an analysis they can audit: every number traced to a fit, a relation with its validity range, or
a published figure. The same recipe (validated tools, literature notes with locators, blind rubric evaluation)
transfers to XRD, PL and transport measurements.
