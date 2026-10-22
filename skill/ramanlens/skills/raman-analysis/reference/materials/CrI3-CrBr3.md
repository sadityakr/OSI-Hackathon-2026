# CrI3 and CrBr3 (chromium trihalides): expert Raman notes

Numbers as printed in the cited source. "corpus p." = page of the group Lit-RAG PDF copy (published version or
author manuscript), so figure numbers refer to that version.

## Structure and irreps
- Bulk CrI3 is monoclinic (C2/m, C2h) at room temperature and turns rhombohedral (R-3, C3i) below about 200 to
  220 K (first order). C3i: Ag (diagonal a, a, b tensor) and doubly degenerate Eg. C2h: Ag and Bg. Signature of the
  change: Eg(C3i) splits into Ag + Bg in the monoclinic phase (Wang et al. 2022, ACS Nano 16, 6960, "The magnetic
  genome of 2D vdW materials", doi:10.1021/acsnano.1c09150, corpus p.22-23).
- Few-layer CrI3 stays monoclinic down to 5 K (polarization patterns at 5 and 280 K look alike) (Wang 2022 review,
  corpus p.23, Fig. 14f-g). Consensus; stacking is why few-layer CrI3 is interlayer AFM while bulk is FM.
- CrCl3 analogue: optical irreps 4Ag + 3Au + 4Eg + 3Eu (C3i) versus 6Ag + 4Au + 6Bg + 5Bu (C2h) (Klein et al. 2019,
  Nat. Phys. 15, 1255, doi:10.1038/s41567-019-0651-0, Suppl. corpus p.18).
- Monolayer CrBr3: D3d, Gamma = 4Eg + 2A1g + 2A2g + 4Eu + 2A1u + 2A2u; Eg and A1g Raman active; in XY the A1g modes
  vanish, Eg keep their XX intensity (Wu et al. 2022, Adv. Mater. 34, 2108506, doi:10.1002/adma.202108506,
  corpus p.2).

## Signature
- Monolayer CrI3 (zero field, hBN encapsulated, 632.8 nm): A1g near 127 and 77 cm-1 in co-circular, Eg near 108 cm-1
  in cross-circular (Cenker et al. 2021, Nat. Phys. 17, 20, arXiv 2001.07025, Suppl. Fig. S1, corpus p.15).
- Monolayer CrBr3 at 6 K: Eg 73.7, 142.8, 152.6, 283.9 cm-1; A1g 105.8 and 183.8 cm-1; 594 and 753 nm were both
  needed to see Eg1 and Eg4 (Wu 2022, corpus p.2, Fig. 2).

## Thickness (CrI3)
- Magnetic ground state: 1L FM, 2L layered AFM, 3L FM-like; T_C about 45 K in 2D flakes versus 61 K bulk (Wang 2022
  review, corpus p.23; Jiang et al. 2021, Appl. Phys. Rev. 8, 031305, doi:10.1063/5.0039979, corpus p.55).
- Davydov splitting: each 1L A1g mode becomes N modes in N layers; the highest-frequency (in-phase) member stays fixed
  and the lowest moves down with N. In the layered AFM state, crossed linear polarization picks parity-even modes for
  odd N and parity-odd modes for even N (Wang 2022 review, corpus p.24, Fig. 17; Tsen et al. 2021, IEEE Trans.
  Quantum Eng. 2, doi:10.1109/tqe.2021.3057799, corpus p.24). So the number of peaks near 128 cm-1 and which channel
  they appear in encode N and the magnetic state.

## Temperature and magnetic order
- CrI3: below T_C an A1g-region mode near 129 cm-1 appears in crossed linear polarization with large polarization
  rotation (1L at 15 K versus isotropic behaviour at 60 K); it carries an antisymmetric, time-reversal-odd Raman
  tensor and is called the anomalous magneto-Raman effect (Wang 2022 review, corpus p.23-24, Fig. 16, summarizing
  Huang et al. 2020, Nat. Nanotechnol. 15, 212, arXiv 1910.01804, and others). Consensus on the observation; the
  review attributes it to static layered AF order coupled to finite-momentum (Davydov) phonons.
- CrBr3 1L: all four tracked modes blueshift by 0.26 to 0.37 cm-1 (0.17 to 0.28 %) below about 25 K relative to an
  anharmonic fit, giving T_C about 25 K (Wu 2022, corpus p.3, Fig. 3). Effects this small need about 0.1 cm-1
  precision and a fit of the high-T anharmonic trend; do not claim T_C from one or two temperatures.
- T_C of CrBr3 drops about 10 K from few layers to 1L, CrI3 only about 1 K (Wang 2022 review, corpus p.78).

## Magnetic field and magnons
- 1L CrI3 acoustic magnon: about 2.4 cm-1 (0.3 meV) gap, cross-circular selection locked to the magnetization, Zeeman
  shift 0.94 cm-1/T (g about 2); visible to about 80 K at -7 T although T_C is about 45 K (Cenker 2021, corpus p.3,
  Fig. 2; Suppl. Fig. S3). Needs notch filters and very low-frequency access.
- 2L CrI3: spin-flip (layered AFM to FM) between -0.7 and -0.75 T in Cenker's sample; AFM magnon about 3 cm-1; optical
  magnon near 148 cm-1 (cross-polarized, 8 T) shifting with g about 2 (Cenker 2021, corpus p.12-13, Figs. 3-4).
  MCD gives B_c about 0.6 T (2L) and 1.8 T (5L) (Occhialini et al. 2025, PRX 15, 031005, doi:10.1103/4km4-4rvn,
  corpus p.6).
- Bulk CrI3: above B_c about 2 T a single magnon mode; below, two extra modes dispersing oppositely from surface
  layered-AF layers (Wang 2022 review, corpus p.78, Fig. 69). Phonon intensities in crossed channels also switch at
  the spin flip (review Fig. 16b-d).

## Polarization
- Use circular bases for magnons (selection by helicity) and linear XX / XY for the A1g / Eg split; quote the
  geometry. Under C3i or D3d symmetry Ag/A1g should be absent in XY, so a strong XY signal near 128 cm-1 at low T in
  CrI3 is a magnetic signature, not a misaligned analyzer, only if the analyzer extinction was checked at T > T_C.

## Excitation energy
- CrI3 absorption: d-d transitions at 1.4 and 1.6 eV, charge-transfer at 2.0 and 2.7 eV (Shcherbakov et al. 2018,
  Nano Lett. 18, 4214, arXiv 1805.09186, corpus p.4); Raman intensities are resonance dependent. Cenker used 632.8 nm.
- CrBr3 mode intensities vary with laser wavelength (594 versus 753 nm) (Wu 2022, corpus p.2).

## Degradation and sample quality
- CrI3 in air: liquid droplets form at flake edges within about 20 s under the microscope and the flake is nearly gone
  after 60 s; dry O2 alone is tolerated for >15 h, wet Ar dissolves it in tens of minutes; mechanism is
  photocatalytic substitution of I by water (Shcherbakov 2018, corpus p.1-4). Light exposure, including the Raman
  laser, accelerates it.
- hBN on top only (on SiO2) still degrades via the rough interface; full hBN sandwich is stable >10 days in air and
  >15 h under about 1 W/cm2 lamp light (Shcherbakov 2018, corpus p.4-5).
- Standard practice: exfoliation and hBN encapsulation in a glovebox; laser 0.4 to 1.5 mW chosen "to prevent
  degradation" (Cenker 2021, Methods, corpus p.5-6).
- CrBr3 air stability: NOT verified in the sources read; assume encapsulation is needed and ask.

## Pitfalls
- Comparing bulk (rhombohedral at low T) with few-layer (monoclinic) selection rules.
- Assigning the 129 cm-1 crossed-polarization signal without a T > T_C reference.
- Low-frequency "magnon" features that are substrate quasi-elastic scatter: Cenker checked the same signal on bare
  SiO2/Si (Suppl. Fig. S1b-c).
- Spectra of an unencapsulated CrI3 flake measured in air are of a degraded sample until shown otherwise.

## What to ask
- Encapsulation, glovebox history, time in air, laser power and spot size.
- Layer number (parity matters), temperature relative to T_C, field and its direction, sweep history (hysteresis).
- Polarization basis (linear or circular) and analyzer extinction check.

## Reference figures
- arXiv 2001.07025 (Cenker 2021) Fig. 2: 1L magnon versus field and temperature; Fig. 4: optical magnon in 2L.
- arXiv 1805.09186 (Shcherbakov 2018) Fig. 3: Raman stability of encapsulated CrI3 (panel d, hBN sandwich).
- doi:10.1002/adma.202108506 (Wu 2022) Fig. 2-3: monolayer CrBr3 XX/XY spectra and T-dependent shifts (arXiv id not
  verified).
