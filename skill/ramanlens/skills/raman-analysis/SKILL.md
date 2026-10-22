---
name: raman-analysis
description: Analyse a Raman spectrum (single spectrum or polarization angle series) of a 2D or layered material like an experienced researcher - artifact and calibration checks, peak fitting with uncertainties, material identification against computed and literature references, mode and irrep assignment, polarization classification, and cited relations for layer number, strain, doping and defect density. Provides validated analysis scripts and literature notes per material; invoke it BEFORE writing any analysis code and use its scripts instead of your own. Use whenever a task involves Raman data, peak assignment, comparing spectra, or "what material is this / is this really X".
---

**Required first actions, in this order (do not write your own fitting code before these):**
1. `python "${CLAUDE_SKILL_DIR}/scripts/rl_qc.py" <each data file>`
2. One spectrum: `python "${CLAUDE_SKILL_DIR}/scripts/rl_fit.py" <file> --substrate "<substrate>"`.
   Several spectra: `python "${CLAUDE_SKILL_DIR}/scripts/rl_series.py" <files> --labels <labels> --substrate "<substrate>" --si-correct`.
3. Read `${CLAUDE_SKILL_DIR}/reference/materials/<material>.md` for the known or most likely material.

# Raman analysis of 2D and layered materials

You read the spectrum; the tools measure. Every number you report comes from a tool output (measured), a
relation applied inside its validity range (inferred, with the relation's source), or a reference entry
(literature, with its source and locator). If none applies, say so under limits.

## Start here: run these commands first (from the folder that holds the data)

Use the validated scripts below; do not write your own baseline, peak-finding or fitting code unless a script
fails or you need a check it does not provide. The scripts and notes are in `${CLAUDE_SKILL_DIR}`.

```
python "${CLAUDE_SKILL_DIR}/scripts/rl_qc.py" <file>                  # artifacts, Si calibration, resolution
python "${CLAUDE_SKILL_DIR}/scripts/rl_fit.py" <file> --substrate "<substrate>"   # peaks with errors + fit.png
python "${CLAUDE_SKILL_DIR}/scripts/rl_series.py" <f1> <f2> ... --labels <l1> <l2> ... --substrate "<substrate>" --si-correct   # several spectra
python "${CLAUDE_SKILL_DIR}/scripts/rl.py" match_library --positions_cm1 <p1> <p2> ... --intensities <h1> <h2> ... --x_range_cm1 <lo> <hi>
python "${CLAUDE_SKILL_DIR}/scripts/rl.py" lookup_reference_modes --material <name>
python "${CLAUDE_SKILL_DIR}/scripts/rl.py" classify_polarization --path <angle-series file>
python "${CLAUDE_SKILL_DIR}/scripts/rl.py" list_relations --material <name>
python "${CLAUDE_SKILL_DIR}/scripts/rl.py" apply_relation --name <relation> --inputs '{"<input>": <value>}'
```
Then read `${CLAUDE_SKILL_DIR}/reference/materials/<material>.md` (when the material is known or once you have a
candidate) and `${CLAUDE_SKILL_DIR}/reference/artifacts.md`. Always return ranked candidates for an identify task,
even when uncertain: put the uncertainty in the confidence values and the limits, never return an empty list.

## What each script does

- `scripts/rl_qc.py <file>`: quality and condition flags (spikes, saturation, background, Si calibration offset,
  low-wavenumber cutoff, sampling, signal to noise).
- `scripts/rl_fit.py <file> [--substrate SiO2/Si] [--window LO HI] [--min-snr N]`: fitted peak table with
  uncertainties, `peaks.json`, and `fit.png` (data, baseline, components, residual). Look at the plot.
- `scripts/rl_series.py <file1> <file2> ... --labels ... [--substrate SiO2/Si] [--si-correct]`: fits every
  spectrum the same way, tracks each band across spectra (position, width, relative height, shift vs the first
  spectrum with error), separations of the two strongest bands, Si offsets, and `series.png`. Use it whenever
  there is more than one spectrum. Its errors are fit statistics only; add the calibration uncertainty (Si offset
  scatter, typically a few tenths of a cm-1) before calling a shift significant.
- `scripts/rl.py <tool> --help`: `fit_peaks`, `match_library`, `classify_polarization`,
  `lookup_reference_modes`, `list_relations`, `apply_relation`, `load_spectrum`. Outputs carry provenance.

## Workflow

0. **Read the material's literature note first** when the material is known: `${CLAUDE_SKILL_DIR}/reference/materials/<name>.md`
   (MoS2, WS2, MoSe2, WSe2, graphene, hBN, black-phosphorus, CrSBr, CrI3-CrBr3, MPS3) plus
   `reference/materials/general-measurement.md` and, for magnets, `magnetic-raman-general.md`. They hold how the
   spectrum changes with thickness, strain, doping, defects, temperature, laser and substrate, the quality
   indicators, the known pitfalls and the questions to ask, each with its source. Interpretation without them is
   guesswork from memory.
1. **Conditions first.** Note laser wavelength, temperature, substrate, polarization geometry, resolution. Many
   conclusions depend on them (`reference/measurement-questions.md`). With a user present, ask for what is missing
   and say why it matters; otherwise state the assumption under limits.
2. **Quality check.** `rl_qc.py`. Spikes are artifacts, never peaks (`reference/artifacts.md`).
3. **Fit.** `rl_fit.py`, then look at `fit.png`. Check weak shoulders and close doublets (2LA(M) next to E2g in
   WS2); refit a window with `--window` when the residual shows structure. Report fitted positions and widths.
4. **Identify.** `rl.py match_library --positions_cm1 ... --intensities ... --x_range_cm1 LO HI` ranks
   candidates from the Computational Raman Database (DFT, frequencies typically 0 to 3 % low, fitted scale per
   candidate) and curated literature tables. Do not stop at the top score: check that the strong predicted modes
   are present and the missing ones are explainable (outside the window, selection rules, resonance). The
   matcher's irreps and space group are the best source for mode labels of uncommon materials. For a stated
   material ("verify"), compare against its reference modes; a wrong hint is common, so say inconsistent when
   strong modes are missing or extra strong bands are unexplained.
5. **Assign.** Each sample peak gets a mode label and irrep with its source: `rl.py lookup_reference_modes
   --material X` for the curated materials (graphene, 2H-MoS2, 2H-WS2, 2H-MoSe2, 2H-WSe2, CrSBr, hBN, black
   phosphorus), the matcher's CRD entry otherwise. Use the irreps of the structure you identified (bulk D6h
   labels for bulk 2H crystals, C3v A1/E for 3R, D3h for a monolayer). Assign Si lines as 'Si substrate'.
6. **Polarization** (angle series only). `rl.py classify_polarization --path <file>` classifies each band
   (isotropic_par_only, isotropic_both, twofold, fourfold, silent). Report the tool's class; use it to check
   irreps (A modes isotropic_par_only and E modes isotropic_both in uniaxial crystals; twofold in in-plane
   anisotropic crystals).
7. **Properties.** Read `reference/relations.md` and `reference/materials.md`, then `rl.py apply_relation`. Report
   layer number, strain, doping or defect density only from a relation (with its source and validity) or a
   stated rule from the notes. Name properties `layers`, `defect_level`, `L_D_nm`, `strain_sign`,
   `doping_type`, `phase` where they apply.
8. **Literature** (when literature tools are connected). Form the hypothesis first. Search with a paper
   search tool, open the paper and view its reference figure with litpick, and compare. See
   `reference/literature.md`.
9. **Interpret changes** (several spectra, or a known material). Run `rl_series.py`; then for each change ask
   which mechanisms in the material note produce it (thickness, strain, doping, defects, heating, calibration,
   resonance) and which observable separates them (e.g. a rigid shift of all lines including Si is calibration;
   A1g-only shift in MoS2 points to doping, E2g shift with splitting to strain; graphene G broadening separates
   stage 1 from stage 2 defects). State the most likely reading, the alternatives, and the measurement that would
   decide between them.
10. **Report.** Ranked candidates with evidence, peaks with provenance and source, properties with relation and
   source, artifacts, citations (only sources you used), and limits: what the data cannot tell, rejected
   hypotheses, relations that did not apply and why.

## Expert habits

- One spectrum rarely fixes layer number alone; name the observable and its threshold.
- Laser heating, strain and doping shift lines by similar amounts; check calibration before reading 1 to 2 cm-1.
- Intensity ratios depend on substrate interference and laser energy; absolute intensity is not layer number.
- Resonant excitation changes relative intensities and activates second-order bands; check the laser against the
  material's excitons before calling a band unexpected.
- When something looks odd, say what it looks like and what would distinguish the explanations.
