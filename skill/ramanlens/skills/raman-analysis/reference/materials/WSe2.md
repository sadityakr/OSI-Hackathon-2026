# WSe2: expert Raman notes

Scope: 2H-WSe2. Numbers appear only where they were read in the cited source; the locator says where.
"Consensus" means several independent sources agree; "single source" means one paper. The defining practical
issue: A1g and E2g1 are nearly degenerate near 250 cm-1, and for years they were misassigned
(De Luca M. et al. 2020, 2D Mater., doi:10.1088/2053-1583/ab5dec, arXiv:1910.12503, abstract).

## Signature and irreps
- Bulk D6h: A1g near 252 cm-1 (out of plane) and E2g1 near 248 cm-1 (in plane) (De Luca 2020, p.4). In bulk on
  90 nm SiO2/Si the pair appears as one peak at 252.2 cm-1 (Sahin H. et al. 2013, arXiv:1303.5861, p.3).
- 1L is D3h (A1', E'); odd N D3h, even N D3d (De Luca 2020, p.4).
- In 1L the two modes become virtually degenerate (Zhao W. et al. 2013, Nanoscale 5, 9677, arXiv:1304.0911,
  p.8). Consensus.
- 2LA(M) is a broad second-order band above the main peak; resonant 1L bands at 116, 136, 261 (2LA), 374 and
  398 cm-1 (Zhang X. et al. 2015, Chem. Soc. Rev. 44, 2757, arXiv:1502.00701, p.13, Fig. 11b, Table III).
- About 40 peaks in 1L to 3L spectra are assigned with DFT in De Luca 2020 (abstract).

## Thickness
- A1g stiffens and E2g1 softens with N, as in MoS2 and WS2 (Zhao 2013, p.8, Fig. 3b).
- The peak above the main line (2LA(M) region) sits 11, 6 and 5 cm-1 above it for 1L, 2L, 3L (Sahin 2013, p.4);
  2LA(M) downshifts about 5 cm-1 from 1L to 3L (Zhao 2013, p.9). Consistent across the two sources.
- A peak near 308 cm-1 is absent in 1L, present in multilayers and softens with N (Zhao 2013, p.10, Fig. 6b).
  Origin not settled in that paper (proposed shear plus E2g1 combination).
- A mode near 176 cm-1 has zero intensity in 1L and bulk backscattering but is allowed in 2L and 3L in both xx
  and xy (De Luca 2020, p.5, calculation and experiment, Fig. 1). Chen X. et al. 2019, Nat. Phys. 15, 221,
  doi:10.1038/s41567-018-0366-7, pp.1 to 2, report an E''(Gamma) peak at 176 cm-1 across a thickness series
  down to 1L; whether it is seen in 1L there was not checked. Treat 176 cm-1 in 1L as disputed.
- Two intralayer modes inactive in bulk become Raman active in few-layer films through reduced symmetry
  (Luo X. et al. 2014, arXiv:1401.0626, abstract).
- The "single degenerate peak means monolayer" rule has limited validity: its reliability depends on the laser,
  and at 532 nm A1' and E' are not resolved even in 2L and thicker (De Luca 2020, p.7). Use multiphonon bands
  and the multilayer-only modes instead (De Luca 2020, abstract).

## Strain and doping
- Uniaxial strain on 1L WSe2 splits the in-plane E' into E'+ and E'-, visible as broadening in cross
  polarization; Grueneisen parameter 0.38 and shear deformation potential 0.10 (Dadgar A. M. et al. 2018,
  Chem. Mater., doi:10.1021/acs.chemmater.8b01672, arXiv:1705.05412, p.2, Fig. 2). One WSe2 mode is nearly
  strain-insensitive, 0.03 cm-1 per % (p.3); WSe2 responds much less than WS2 (abstract).
- Oxygen doping of CVD 1L WSe2 (p-type) blueshifts both A1g and E2g and narrows the Raman peaks (Sun L. et al.
  2026, Nat. Commun., doi:10.1038/s41467-026-78157-w, p.2, Fig. 2a). Single source.

## Defects and quality
- No WSe2-specific Raman defect calibration verified. Narrowing of the main peak accompanied improved
  crystallinity in Sun 2026 (p.2); width is a usable relative quality indicator within one setup.
- Many weak multiphonon bands are intrinsic (De Luca 2020; Zhang X. 2015); do not count them as defect peaks.

## Temperature and heating
- E2g1 redshifts on heating; the first-order coefficient decreases with layer number, and suspended 1L shifts more
  than supported 1L (Easy E. et al. 2021, arXiv:2011.00730, p.9). Table 1 (p.21) lists coefficients of about
  -0.013 to -0.023 cm-1/K for 1L to 3L, supported and suspended (exact column mapping not re-checked).
- Absorbance at 532 nm of suspended 1L, 2L, 3L: 5.7, 10.9, 16.0 % (Easy 2021, p.8); room-temperature thermal
  conductivity 37, 24, 20 W/(m K) for 1L to 3L (abstract). Low thermal conductivity means easy laser heating.

## Excitation wavelength and resonance
- 633 nm is resonant with the B exciton of WSe2 and enhances 2LA(M) and multiphonon bands; 473 nm shows weaker
  resonance features (Zhao 2013, pp.9 to 10).
- At 473 nm only one peak appears in unpolarized and parallel spectra because E2g1 is weak (Zhao 2013, p.8).
- Many peaks can be observed and interpreted without exact resonance (De Luca 2020, p.16).

## Polarization and substrate
- Linear: A1g vanishes in crossed (XY) and E2g1 remains, so XX vs XY separates the degenerate pair (Zhao 2013,
  Fig. 3a at 633 nm; general rule in Zhang X. 2015, pp.6 to 7). 2LA(M) depends only weakly on polarization
  (Zhao 2013, p.8).
- Circular: A1g appears in helicity-conserved (sigma+ sigma+) and E2g in helicity-changed (sigma+ sigma-) spectra,
  resolving the 1L pair (Li L. et al. 2025, Nat. Commun. 16, 4117, doi:10.1038/s41467-025-59325-w, pp.2 to 3).
- Substrate oxide thickness matters (Sahin used 90 nm SiO2); compare like with like.

## Pitfalls and artifacts
- Fitting one Lorentzian at 250 cm-1 hides the A1g/E2g1 pair; a "shift" may be a change in their weight.
- Layer number from the degeneracy criterion alone is unreliable (De Luca 2020, p.7); ask for the laser.
- WSe2 and MoSe2 both have strong lines near 240 to 255 cm-1; check MoSe2 E' near 285 to 288 and PL.

## What to ask
- Laser line and power; spot size; suspended or supported.
- Polarization optics (linear XX/XY, circular).
- Substrate and oxide thickness; CVD or exfoliated; annealing in oxygen or air exposure.
- Temperature; spectrometer resolution (a 2 to 4 cm-1 splitting needs good resolution).

## Reference figures
- Zhao 2013, arXiv:1304.0911, Fig. 3a: 1L to 5L and bulk at 633 nm in XX and XY; Fig. 6: 1L to 5L at 532 nm with
  the 308 cm-1 band.
- Sahin 2013, arXiv:1303.5861, Fig. 2a: thickness-dependent spectra with the extra peak above the main line.
- De Luca 2020, arXiv:1910.12503, Fig. 1: calculated and measured xx/xy spectra of 1L, 2L, 3L.
- Zhang X. 2015, arXiv:1502.00701, Fig. 11b: resonant vs nonresonant 1L WSe2.
