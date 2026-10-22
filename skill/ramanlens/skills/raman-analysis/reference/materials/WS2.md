# WS2: expert Raman notes

Scope: 2H-WS2. Numbers appear only where they were read in the cited source; the locator says where.
"Consensus" means several independent sources agree; "single source" means one paper. The defining practical
issue for WS2 is the 2LA(M) overtone sitting a few cm-1 below E2g1: almost every misreading starts there.

## Signature and irreps
- Bulk D6h zone-centre modes A1g + 2A2u + 2B2g + B1u + E1g + 2E1u + 2E2g + E2u; A1g, E1g, E2g Raman active,
  E1g forbidden in backscattering (Hait S. et al. 2022, J. Appl. Phys. 132, 133901, doi:10.1063/5.0107655,
  p.4). 1L is D3h (E2g1 to E', A1g to A1'), odd N D3h, even N D3d (Yang J. et al. 2017, arXiv:1706.01677, p.5).
- At 514.5 nm, 1L: 2LA(M) 351.1, E2g1 355.2, A1g 417.2 cm-1; bulk 350.0, 355.3, 420.1; LA(M) near 176 at 488 nm
  (Berkdemir A. et al. 2013, Sci. Rep. 3, 1755, Table 1).
- Resonant 1L spectrum also contains bands at 176, 193, 231, 353 (2LA), 583 and 702 (4LA) cm-1, all zone-edge
  combinations (Zhang X. et al. 2015, Chem. Soc. Rev. 44, 2757, arXiv:1502.00701, p.14, Fig. 11c, Table III).

## Thickness
- A1g stiffens with N (417.2, 418.4, 419.0, 420.1 cm-1 for 1L, 2L, 3L, bulk at 514.5 nm) while E2g1 barely moves
  (Berkdemir 2013, Table 1). Consensus on the trend. So the A1g-E2g1 separation grows only a few cm-1.
- The A1g-E2g1 separation: about 62 cm-1 in 1L to 66 in bulk, as relayed by Mitioglu A. A. et al. 2014,
  PRB 89, 245442, arXiv:1406.3511, p.2.
- 1L flags at resonance: 2LA(M)/A1g intensity ratio about 2 at 514 nm, decreasing with N (Berkdemir 2013).
  The ratio depends on polarization (see below), so use it only with known polarization.
- A peak near 310 cm-1 is present in multilayers and absent in 1L (Zhao W. et al. 2013, Nanoscale 5, 9677,
  arXiv:1304.0911, p.10, Fig. 5b). Assignment unclear in that paper (proposed shear-related combination).
- Low-frequency shear and breathing series determine N (Yang 2017, abstract). At A-exciton resonance the
  Raman-forbidden lowest shear mode of odd N appears as strong as the allowed even-N one, with a Fano line shape
  (Yang 2017, abstract): do not use its presence as a parity test at that laser.

## Strain and doping
- Uniaxial strain on 1L WS2 redshifts the modes, in-plane modes faster, and splits E'; WS2 shows much larger
  changes in mode positions and intensities than WSe2 under the same strain; at large strain the polarization
  response of a mode changes (Dadgar A. M. et al. 2018, Chem. Mater., doi:10.1021/acs.chemmater.8b01672,
  arXiv:1705.05412, abstract; WS2 data Fig. 3b, calculated shifts Fig. 4c,d). Strain rates for WS2 not extracted here.
- Doping: no WS2-specific Raman doping rate verified. By analogy with MoS2 (Chakraborty 2012, see MoS2.md) an
  A1g shift with broadening would point to electron doping; this is an inference, not a WS2 measurement.

## Defects and quality
- No WS2-specific defect calibration verified. LA(M) near 176 cm-1 is present already in pristine spectra near
  resonance (Berkdemir 2013, 488 nm), so its presence alone is not a defect marker in WS2, unlike LA(M) in
  off-resonant MoS2 (inference from the two sources).
- The band near 297 cm-1 is the backscattering-forbidden E1g, and the one near 325 cm-1 is E2g2+LA (Kumar D. et al.
  2019, J. Phys. Condens. Matter, doi:10.1088/1361-648X/ab3fec, arXiv:1906.10661, abstract). Hait 2022 (p.4)
  instead assigns about 325 cm-1 to an out-of-plane acoustic mode at M. Disputed.
- Phase: 1T and 1T' monolayer WS2 give different spectra and temperature behaviour (Kumar 2019, abstract).

## Temperature and heating
- Supported 1L WS2: temperature evolution of first-order and combination modes is anomalous, attributed to
  detuning of the resonance and to strain from substrate thermal-expansion mismatch; some combination modes
  disappear (Kumar 2019, abstract). Nonlinear shifts in supported WS2 were also noted by Taube A. et al. 2014,
  ACS AMI, doi:10.1021/am502359k, p.5.
- Consequence: temperature changes intensities (resonance) as well as positions; a laser-heating estimate from
  peak positions needs a coefficient measured on the same substrate. No WS2 coefficient verified here.

## Excitation wavelength and resonance
- 2LA(M) lies about 4 to 5 cm-1 below E2g1 and becomes stronger than the main peaks for 1.96, 2.33 and 2.41 eV
  (A and B exciton resonance) (Yang 2017, p.5; Mitioglu 2014, abstract). Consensus.
- E2g1 is enhanced near the C exciton; A1g resonates with A, B and C (Yang 2017, p.5).
- Bulk resonance spans 1.96 to 2.41 eV because of the broad B exciton (Zhang X. 2015, p.13). 633 nm is resonant
  with the A exciton of WS2 (Zhao 2013, p.9).
- Peaks X1 and X2, independent of thickness, appear near exciton resonances; X1 vanishes in cross polarization,
  X2 does not (Yang 2017, abstract). Unassigned.

## Polarization and substrate
- 2LA intensity is minimal when excitation and detection are orthogonal and exceeds E2g1 in parallel; A1g behaves
  similarly, E2g1 is isotropic (Mitioglu 2014, p.4, Fig. 3; Yang 2017, p.5). Measure in cross polarization to
  isolate E2g1 (Yang 2017, p.5). Consensus.
- Substrate interference changes absolute and relative intensities; Yang 2017 corrects for it (p.4). Substrate
  strain enters through thermal-expansion mismatch (Kumar 2019).

## Pitfalls and artifacts
- Fitting a single Lorentzian to the 2LA/E2g1 doublet misplaces E2g1 and can give a wrong layer number
  (Mitioglu 2014, abstract). Always fit both, constrained by polarization data when possible.
- Reported 1L positions differ between groups (Hait 2022, p.4: 2LA 353.98, E2g 357.97, A1g 418.23 cm-1;
  Berkdemir 2013: 351.1, 355.2, 417.2) partly from fitting model and calibration; compare to the same source.
- Intensity ratios are only comparable at the same laser line, polarization and substrate.

## What to ask
- Laser line (resonance changes the spectrum completely), power and spot size.
- Polarization: unpolarized, parallel or crossed; analyser present?
- Substrate and oxide thickness; CVD or exfoliated; transferred; encapsulated.
- Measurement temperature; phase (2H vs 1T or 1T') if chemically processed.
- Fit model used for the 350 cm-1 region.

## Reference figures
- Zhao 2013, arXiv:1304.0911, Fig. 5: 1L to 5L and bulk at 532 nm, normalized to 2LA(M); 310 cm-1 band inset.
- Mitioglu 2014, arXiv:1406.3511, Fig. 3: 2LA/E2g1 and A1g regions vs polarization angle (1L).
- Yang 2017, arXiv:1706.01677, Fig. 1c,d: thickness dependence of main and weak peaks at 2.54 eV.
- Berkdemir 2013, Sci. Rep. 3, 1755, Fig. 3 (open access, not on arXiv): 1L to bulk at 514.5 nm.
