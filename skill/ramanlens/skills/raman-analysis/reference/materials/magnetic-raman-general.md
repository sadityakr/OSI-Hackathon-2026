# How magnetic order shows up in Raman spectra of layered magnets

Cross-material reasoning guide. Material specifics: CrSBr.md, CrI3-CrBr3.md, MPS3.md. "corpus p." = page of the
group Lit-RAG PDF copy. A Raman spectrum alone rarely proves magnetic order; it gives signatures that must be tied to
a temperature or field series and a symmetry argument.

## Five mechanisms and their fingerprints
1. Spin-phonon coupling (frequency renormalization). Phonon frequencies deviate from the anharmonic trend below the
   ordering temperature because exchange depends on atomic positions. Size can be tiny: 0.26 to 0.37 cm-1 in 1L CrBr3
   (Wu et al. 2022, Adv. Mater. 34, 2108506, corpus p.3). In bulk CrSBr Ag3 stalls between T_C and T_N and jumps at
   about 25 K (Pawbake et al. 2023, PRB 107, 075421, arXiv 2211.12939, p.4, Fig. 3).
2. Zone folding. An AFM supercell maps zone-boundary phonons to Gamma, so new sharp peaks appear below T_N: FePS3
   (M point to Gamma, peaks near 100 cm-1) (Vaclavkova et al. 2021, PRB 104, 134437, arXiv 2108.10945, corpus p.2);
   CrSBr (c-axis doubling, Z-point B3g at 57 cm-1, tilted geometry) (Pawbake 2023, p.4-5). No folding is expected when
   magnetic and chemical cells coincide, as in MnPS3 (Oliva et al. 2023, PRB 107, 104415, corpus p.2).
3. Magnetostriction / symmetry lowering. Degenerate modes split below the transition and the parts separate into XX
   and XY channels: NiPS3 P2 near 180 cm-1 (Kim et al. 2019, Nat. Commun. 10, 345, arXiv 1901.10890, corpus p.4),
   CoPS3 P2 near 149 cm-1, splitting > 8 cm-1 (Liu Q. et al. 2021, PRB 103, 235411, corpus p.4).
4. Magnetic order in the Raman tensor (symmetry-forbidden scattering). Time-reversal-odd antisymmetric tensor terms let
   a mode appear in a channel that lattice symmetry forbids: CrI3 mode near 129 cm-1 in crossed linear polarization
   below T_C, with layer-parity selection (Wang et al. 2022, ACS Nano 16, 6960, corpus p.23-24).
5. Magnons. One-magnon: sharp, shifts linearly with field (g about 2, 0.94 cm-1/T in 1L CrI3), helicity selection in
   circular basis (Cenker et al. 2021, Nat. Phys. 17, 20, arXiv 2001.07025, corpus p.3). Two-magnon: broad band in
   crossed polarization that grows and blueshifts on cooling below T_N, weakens and redshifts on warming (NiPS3, Kim
   2019, corpus p.3-4; CoPS3 near 350 and 600 cm-1, Liu 2021, corpus p.4-5). Magnon-phonon anticrossings
   (magnon-polarons) appear when field tunes a magnon through a phonon (FePS3, Vaclavkova 2021, Fig. 1b).
- Also: Fano asymmetry that switches on below T_N (NiPS3 P9, Kim 2019; CoPS3 P8, Liu 2021), and intensity changes from
  magnetically modified electronic resonances (CrSBr, Markina et al. 2026, npj Quantum Mater. 11, 11, corpus p.6;
  second-order bands below 160 K, Pawbake 2023, p.5).

## Temperature series across T_C / T_N: how to analyse
- Fit position, width and area of each mode versus T. Model the high-T part with an anharmonic (three- and
  four-phonon) decay law and look for systematic deviation below the transition (procedure in Wu 2022, corpus p.2-3).
  Kim 2019 extracted T_N from Delta P2 with a spin-induced frequency-shift model (corpus p.4).
- Use differences that cancel calibration drift: Delta P2 between XX and XY on the same spectrum (Kim 2019) is more
  robust than an absolute position.
- Sample densely near the expected transition; CrSBr has three regimes (PM, iFM between about 132 and 160 K, AFM)
  (Pawbake 2023, p.1, p.4; Markina 2026, corpus p.3).
- Widths: linewidth anomalies near T_N can come from reduced spin fluctuations (CrSBr Ag3 FWHM inflection near 140 K,
  Pawbake 2023, p.4) or from short-range order above T_N (MnPS3 near 120 K, Oliva 2023, corpus p.6).
- A small change does not give T_N to better than the temperature spacing; state the bracket, not a single value.
- Thickness-dependent T_N claims are often disputed (FePS3: Lee 2016 vs Wang 2016; NiPS3 1L: Kim 2019 vs Kim T. Y.
  2021, Nano Lett. 21, 10114, corpus p.2, p.5). Report the disagreement rather than choosing silently.

## Magnetic field
- Record field magnitude, direction relative to the easy axis and sweep direction. Spin-flip in 2L CrI3 near 0.6 to
  0.75 T out of plane (Cenker 2021, corpus p.12; Occhialini et al. 2025, PRX 15, 031005, corpus p.6); in bulk CrSBr AFM
  folded modes vanish above about 0.8 T in a 30 deg tilted field (Pawbake 2023, p.5, Fig. 4).
- A field-linear peak shift of about 0.94 cm-1/T (g about 2; measured in 1L CrI3) identifies a one-magnon mode; phonons should not
  shift linearly (Cenker 2021, corpus p.3; Liu S. et al. 2021, PRL 127, 097401, corpus p.2).
- Faraday rotation in objectives and windows can mix polarization channels in field; check with a reference sample
  (general practice, not verified from a source here).

## Laser heating near T_N
- Local heating raises the true spot temperature above the cryostat reading, shifting or smearing the apparent T_N;
  Raman T_N markers in FePS3 were found sensitive to laser power and wavelength (Martin-Perez et al. 2023, ACS Nano,
  doi:10.1021/acsnano.2c11654, corpus p.2).
- Powers used in the sources: below 0.3 mW (CrSBr bulk, Pawbake 2023, p.2), 0.17 mW (MnPS3, Sun et al. 2019, JPCL 10,
  3087, corpus p.2), about 100 uW (CrSBr, Mondal et al. 2025, arXiv 2410.22164, p.7), 0.4 to 1.5 mW (encapsulated CrI3,
  Cenker 2021, corpus p.6). Ask for a power series at the lowest T: positions and the transition feature should not
  move with power.

## Degradation of air-sensitive layered magnets
- CrI3: minutes in humid air under light; photo-assisted aquation; needs full hBN sandwich (Shcherbakov et al. 2018,
  Nano Lett. 18, 4214, arXiv 1805.09186, corpus p.1-5).
- CrSBr: 2L and thicker stable in air at about 55 % humidity; 1L forms defects (D1 near Ag1, D3 near 350 cm-1)
  (Torres et al. 2022, arXiv 2212.01754, p.4-5).
- MPS3: 2L FePS3 stable 6 days (Lee et al. 2016, Nano Lett. 16, 7433, Suppl. Fig. S16); 1L MnPS3 gave no Raman signal,
  possibly photodegradation (Sun 2019, corpus p.3).
- Degradation signs: falling signal, broadening, new defect peaks, rising background. A "magnetic" change that
  appears only after long exposure is suspect.

## Excitation energy
- Near-resonant excitation changes intensities, polarization patterns and lineshapes (CrSBr Ag2 axis switching,
  Mondal 2025, p.3-4; Fano Ag2 at 1.58 eV, Klein et al. 2023, ACS Nano 17, 5316, corpus p.5-6). Magnetic changes in
  intensity can be resonance effects mediated by excitons rather than direct spin-phonon coupling (Markina 2026,
  corpus p.6; authors' interpretation).

## What to ask before interpreting
- Temperature (and how it was measured), field, laser energy and power, spot size, polarization geometry and its
  orientation to crystal axes, sample tilt.
- Thickness, substrate, encapsulation, time and light exposure in air.
- Is there a reference spectrum above the ordering temperature from the same spot and setup?

## Reference figures
- arXiv 2211.12939 (Pawbake 2023) Fig. 2: Raman T map through PM, iFM, AFM in CrSBr.
- arXiv 1901.10890 (Kim 2019) Fig. 4: phonon splitting as order parameter in NiPS3; Fig. 3: two-magnon versus T.
- arXiv 2001.07025 (Cenker 2021) Fig. 2: one-magnon Zeeman shift and T dependence in 1L CrI3.
- arXiv 2108.10945 (Vaclavkova 2021) Fig. 1: zone-folded modes and magnon-phonon coupling in FePS3.
