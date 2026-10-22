---
name: raman-analysis
description: Analyse a Raman spectrum (single spectrum or polarization angle series) of a 2D or layered material like an experienced researcher - artifact and calibration checks, peak fitting with uncertainties, material identification against computed and literature references, mode and irrep assignment, polarization classification, and cited relations for layer number, strain, doping and defect density. Use whenever a task involves Raman data, peak assignment, or "what material is this / is this really X".
---

# Raman analysis of 2D and layered materials

You read the spectrum; the tools measure. Every number you report comes from a tool output (measured), a
relation applied inside its validity range (inferred, with the relation's source), or a reference entry
(literature, with its source and locator). If none applies, say so under limits.

Scripts live in `scripts/` and notes in `reference/`, both next to this SKILL.md (its base directory is shown when
the skill loads; use absolute paths). Run the scripts from the folder that holds the data, with `python`.

- `scripts/rl_qc.py <file>`: quality and condition flags (spikes, saturation, background, Si calibration offset,
  low-wavenumber cutoff, sampling, signal to noise).
- `scripts/rl_fit.py <file> [--substrate SiO2/Si] [--window LO HI] [--min-snr N]`: fitted peak table with
  uncertainties, `peaks.json`, and `fit.png` (data, baseline, components, residual). Look at the plot.
- `scripts/rl.py <tool> --help`: `fit_peaks`, `match_library`, `classify_polarization`,
  `lookup_reference_modes`, `list_relations`, `apply_relation`, `load_spectrum`. Outputs carry provenance.

## Workflow

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
8. **Literature** (when the Valency and iopic-bond tools are available). Form the hypothesis first; never search by
   peak positions. See `reference/literature.md`: find the paper, view its reference spectrum figure, compare.
9. **Report.** Ranked candidates with evidence, peaks with provenance and source, properties with relation and
   source, artifacts, citations (only sources you used), and limits: what the data cannot tell, rejected
   hypotheses, relations that did not apply and why.

## Expert habits

- One spectrum rarely fixes layer number alone; name the observable and its threshold.
- Laser heating, strain and doping shift lines by similar amounts; check calibration before reading 1 to 2 cm-1.
- Intensity ratios depend on substrate interference and laser energy; absolute intensity is not layer number.
- Resonant excitation changes relative intensities and activates second-order bands; check the laser against the
  material's excitons before calling a band unexpected.
- When something looks odd, say what it looks like and what would distinguish the explanations.
