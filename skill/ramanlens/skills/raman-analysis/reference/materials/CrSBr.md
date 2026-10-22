# CrSBr: expert Raman notes

Numbers are as printed in the cited source unless marked "(fig)" (read from a plot, about +-1 cm-1). Locators
"p." for arXiv PDFs are arXiv page numbers; "corpus p." are page numbers of the group Lit-RAG PDF copy.
Not used here by design: Wdowik et al. 2025 (arXiv 2503.15298) and Sahu et al. 2025 (arXiv 2502.01794), which sit
behind held-out evaluation data.

## Structure, magnetism, irreps
- Orthorhombic Pmmn (D2h), 6 atoms per primitive cell, 15 optical + 3 acoustic modes (Pawbake et al. 2023, PRB 107,
  075421, arXiv 2211.12939, p.3). Gamma = 3Ag + 2B1u + 3B2g + 2B2u + 3B3g + 2B3u; Ag, B2g, B3g Raman active
  (Torres et al. 2022, arXiv 2212.01754, p.2, Eq. 1).
- In normal-incidence backscattering (light along c) only the three Ag modes are expected; B2g and B3g have
  off-diagonal xz / yz tensors and stay weak (Torres 2022, p.2, Eq. 2; consensus).
- Magnetism: intralayer FM with spins along b (easy axis), A-type interlayer AFM below T_N; intermediate phase (iFM)
  between T_N and T_C (Pawbake 2023, p.1). Reported values differ slightly by source: T_C = 160 K, T_N = 134 K
  (Torres 2022, p.8); T_C about 165 K, T_N about 132 K (Markina et al. 2026, npj Quantum Mater. 11, 11,
  doi:10.1038/s41535-026-00850-2, corpus p.3). A low-temperature phase near T* about 40 K is DISPUTED: reported by
  Pawbake 2023 (p.2, p.4) and others, absent in high-quality crystals per Uykur et al. 2024 (arXiv 2405.07853, p.1).
- Easy (b), intermediate (a) and hard (c) axes; exfoliated flakes are rectangular with the long edge along a
  (Mondal et al. 2025, npj 2D Mater., arXiv 2410.22164, p.1; Torres 2022, p.2).

## Signature at room temperature
- Ag1, Ag2, Ag3: 114, 244, 344 cm-1 (4L, 2.33 and 1.96 eV, Mondal 2025, p.2); 117, 257, 345 cm-1 (bulk, 633 nm,
  Pawbake 2023, p.3); 115, 245.5, 344 cm-1 (bulk, 2.33 eV, Klein et al. 2023, ACS Nano 17, 5316,
  doi:10.1021/acsnano.2c07316, corpus p.5, Fig. 3). Note the Ag2 spread (244 to 257) between sources; treat Ag2
  position with the source's calibration in mind.
- B2g at 92, 194, 301 cm-1 appear only with the sample tilted 60 deg to the beam (Pawbake 2023, p.3, Fig. 1c).
- Atomic character: Ag1 and Ag2 carry Br motion and mediate interlayer coupling; Ag3 is mostly intralayer
  (Torres 2022, p.2, Fig. 1e).

## Thickness
- Ag1 and Ag2 redshift as layer number decreases, Ag3 is nearly layer independent (Torres 2022, p.3, Fig. 1h,
  resonant 1.58 eV). From Fig. 1h (fig): Ag1 about 107 cm-1 in 1L versus about 113 in bulk; Ag3 near 344 for all N.
  Ye et al. 2022 (ACS Nano 16, 11876, doi:10.1021/acsnano.2c01151, corpus p.6) also report a gradual downshift with
  decreasing N. Consensus on direction; exact per-layer values vary with laser and substrate.
- Polarization behaviour of all three Ag modes is the same from about 3.5 to 62 nm (Mondal 2025, p.4-5, Fig. 4);
  for thick flakes (62 nm) thin-film interference changes the Ag2/Ag3 intensity ratio (Mondal 2025, p.4-5).
- Layer number is better taken from optical contrast or AFM than from Raman shifts (Ye 2022, corpus p.5).

## Polarization relative to crystal axes
- Ag1 and Ag3 are maximal for E parallel to b at all tested energies (1.96 to 2.33 eV) (Mondal 2025, p.3-4).
- Ag2 switches by 90 deg with laser energy: maximal along a at 2.33 and 2.25 eV, near isotropic at 2.06 eV, along b
  at 1.96 eV, back along a at 1.58 eV (Mondal 2025, p.3-4, Fig. 3; Klein 2023, corpus p.5, Fig. 3d-f).
- Fits need a complex Raman tensor (relative phase phi_ab between R_xx and R_yy), otherwise four-lobed Ag2 patterns
  (2.25 eV) cannot be reproduced (Mondal 2025, p.6, Eq. 2).
- PL at 1.31 eV (300 K) is stronger along b; it is an independent axis check (Mondal 2025, p.2, Fig. 1d-e).

## Excitation energy and lineshape
- Near-gap excitation (1.58 eV) gives non-Lorentzian Ag modes, extra resonant peaks polarized along b, and a Fano
  (BWF) Ag2 for E parallel to b with 1/q = -0.24; along a Ag2 is Lorentzian (Klein 2023, corpus p.5-6; Torres 2022,
  p.3, Fig. 1f).
- Second-order bands (370 to 780 cm-1, widths 20 to 30 cm-1) appear below about 160 K with 1.96 eV excitation,
  growing on cooling; attributed partly to resonance with the B exciton at 1.82 eV (Pawbake 2023, p.5, Fig. 5).

## Temperature and magnetic order
- Ag3 hardens on cooling, is nearly flat between T_C and T_N, hardens again, then jumps at about 25 K; its FWHM
  shows an inflection near 140 K (Pawbake 2023, p.4, Fig. 3; bulk, 633 nm).
- Intensities of most modes rise in the iFM window 130 to 160 K (Pawbake 2023, p.4).
- Zone folding along c below T_N: a B3g mode at 57 cm-1 (Z point) appears below about 130 K while the 71 cm-1 B3g
  (Gamma, seen below 260 K) disappears; a mode near 194 cm-1 grows near T_C; tilted geometry needed (Pawbake 2023,
  p.4-5, Fig. 4a).
- Sharp 467 cm-1 peak (FWHM 2 cm-1) only below about 40 K, origin unresolved (Pawbake 2023, p.5).
- Thin flakes (3L, 1.58 eV): Ag1 intensity rises strongly below T_C and saturates at T_N; frequencies stay constant
  below T_N, unlike anharmonic behaviour (Torres 2022, p.8).
- Polarization b/a ratios change near T_N under 1.96 eV for 5 to 76 nm flakes (Ag1 step-like); the authors argue the
  spin-phonon effect is indirect, via exciton resonances (Markina 2026, corpus p.4, p.6, Fig. 2). Interpretation
  not yet independently confirmed.
- Infrared (not Raman): a magnetic mode near 360 cm-1 below T_N and splitting of the 180 cm-1 a-axis phonon
  (Uykur 2024, arXiv 2405.07853, p.3-4). Do not assign a 360 cm-1 Raman feature to it without polarization and T data.

## Magnetic field
- Bulk, 5 K, field 30 deg from c: the 57 cm-1 AFM mode fades and the 71 cm-1 mode returns above about 0.8 T, and
  B2g near 305 cm-1 gains intensity; saturation field from magneto-PL 0.75 T in that geometry (Pawbake 2023, p.5,
  Fig. 4b-d). The critical field depends on field direction and layer number (odd/even effect, Ye 2022, corpus p.11,
  Fig. 3).

## Defects, degradation, quality
- D1: shoulder 5 to 10 cm-1 below Ag1, surface related, grows with air or water exposure, strongest in thin flakes
  (Torres 2022, p.4-5, Fig. 2). D3: peak near 350 cm-1 (blue of Ag3) in 1L only after air plus heating, can exceed
  Ag3; marks Cr/S defects (Torres 2022, p.5). He+ irradiation adds D2 (red of Ag2) and broad D* at 90 to 100 cm-1.
- 2L and thicker flakes are air stable at about 55 % humidity; 1L degrades (amorphous after water exposure)
  (Torres 2022, p.4-5). Defect peaks are resonantly enhanced at 1.58 eV and polarized along b (Torres 2022, p.8).
- Quality: sharp Lorentzian Ag modes at 2.33 eV, no D1/D3, correct b-axis polarization of Ag3.

## Pitfalls
- Claiming the a or b axis from Ag2 without knowing the laser energy (Mondal 2025).
- Reading a D1 shoulder as Ag1 splitting, or D3 as a new magnetic mode (Torres 2022).
- Expecting zone-folded or B modes in normal incidence: Pawbake needed a tilted sample.
- Comparing Ag2 positions across labs (244 to 257 cm-1 spread above).

## What to ask
- Laser energy, power, polarization geometry and angle to the a/b axes; sample tilt.
- Temperature (and whether above T_C, between T_C and T_N, or below T_N); field magnitude and direction.
- Layer number (AFM or contrast), substrate, encapsulation, air exposure history.

## Reference figures
- arXiv 2211.12939 (Pawbake 2023) Fig. 2: temperature map 5 to 300 K with PM / iFM / AFM regions; Fig. 4: 57 and
  71 cm-1 modes versus T and field.
- arXiv 2410.22164 (Mondal 2025) Fig. 2: 4L spectra and polarization maps at 2.33 and 1.96 eV (Ag2 switch); Fig. 4:
  polar plots versus thickness.
- arXiv 2212.01754 (Torres 2022) Fig. 1f-h: resonant versus non-resonant spectra and layer dependence; Fig. 2:
  defect modes after air, heat, water.
