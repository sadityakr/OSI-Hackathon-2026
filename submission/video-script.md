# Video script (max 4 min, no speed-up)

Screen recording plus voice. Timings are targets; [TBD] numbers come from `submission/figure.md`.

## 0:00 to 0:30, the problem
Show: a CrSBr or MoS2 Raman spectrum, then a stack of paper titles.
Say: "Every 2D-materials lab measures Raman spectra every day. The hard part is not finding the peaks. It is knowing
what a 2 wavenumber shift means: thickness, strain, doping, heating, or a calibration error. That knowledge sits in
hundreds of papers and in the heads of senior researchers. Existing tools stop at naming the material."

## 0:30 to 1:20, what RamanLens is
Show: `skill/ramanlens/` tree, SKILL.md, one literature note (MoS2.md) with its citations.
Say: "RamanLens is a Claude Code skill. Validated scripts do the measuring: despiking, baseline, peak fits with
uncertainties, band tracking across spectra, a matcher over 385 computed layered crystals. Physics relations turn
peaks into layer number or defect density and refuse to extrapolate. Literature notes for ten materials, built from
about a hundred papers through Valency Bond, tell the agent what each change means and what usually goes wrong,
every number with its figure or table."

## 1:20 to 2:30, live example
Show: run Claude Code on the MoS2 thickness case (or a CrSBr temperature series): the agent runs rl_qc and
rl_series, reads the MoS2 note, applies the Lee 2010 relation, opens the published figure through iopic-Bond, and
writes the report with caveats and questions.
Say: point at one caveat (Si calibration, interference on SiO2/Si) and one citation with a figure locator.

## 2:30 to 3:10, does it help? the evaluation
Show: `submission/figure.png`.
Say: "We compared six arms on held-out cases from papers we never used to build the skill: classical library
search, our pipeline without an LLM, and Claude Haiku and Sonnet, each with and without the skill. An independent
agent wrote the interpretation rubrics from each paper's conclusions; a blind judge graded them."
Then the three headline numbers: identification vs library search [TBD], Haiku with vs without the skill [TBD],
caveats and citations [TBD].

## 3:10 to 3:35, one case
Show: `submission/case-study.md` (the table of rubric items, bare vs skill).
Say: "This is the held-out case where the skill helped most, with the paper's own conclusions as the key. Bare
misses the caveats and cites from memory; the skill flags the artifact and cites the paper with a figure locator."

## 3:35 to 4:00, what it means
Say: "A frontier model already knows the textbook. What the skill adds is what a senior researcher adds: symmetry
and polarization done right, artifacts caught, and every claim traceable to a measurement or a figure in a paper.
Code and data are open at github.com/sadityakr/osi-hackathon-2026."
