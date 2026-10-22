# MoSe2: expert Raman notes

Scope: 2H-MoSe2. Numbers appear only where they were read in the cited source; the locator says where.
"Consensus" means several independent sources agree; "single source" means one paper. MoSe2 differs from MoS2:
the out-of-plane A1g/A1' dominates and the in-plane E2g1/E' is weak, and the spectrum changes drastically with
the laser line.

## Signature and irreps
- Bulk D6h: A1g, E1g, E2g Raman active; E1g forbidden in backscattering, A2u Raman inactive
  (Kim K. et al. 2016, ACS Nano, doi:10.1021/acsnano.6b04471, arXiv:1608.03944, p.6). 1L is D3h (A1', E').
- Bulk: A1g 242, E2g1 285, E1g 169 cm-1 (the last only under resonance) (Nam D. et al. 2015, Sci. Rep.,
  doi:10.1038/srep17113, arXiv:1511.01225, pp.4 to 5).
- 1L at 465 nm: A1' at 242 cm-1, about 10 times stronger than any other feature; E' at 288 cm-1
  (Soubelet P. et al. 2016, PRB 93, 155407, arXiv:1603.05172, p.2, Fig. 1a). At 632.8 nm the E mode near
  290 cm-1 is much weaker than A1 near 243 cm-1 (Soubelet 2016, p.1, citing earlier work).
- E' is predicted to be split into LO and TO by about 4 cm-1 at Gamma because of the polar bond
  (Soubelet 2016, p.1, from ab initio work). Single source, theory.

## Thickness
- Multilayers show two extra lines at 170 (E-type) and 354 cm-1 (A-type), assigned to E''/E1g and A''2/A1g; their
  positions do not depend on N, and they are not Raman active in 1L (only weak traces at high excitation energy)
  (Soubelet 2016, p.3, Fig. 3a,b). Their presence is a strong "not a monolayer" indicator.
- Davydov splitting of A1g near 240 cm-1 in few-layer MoSe2, visible only at some excitation energies near
  resonance (2.41 to 2.81 eV), encodes N (Kim 2016, p.7, Fig. 3a; abstract).
- Interlayer shear and breathing modes plus Davydov splittings fit a linear chain model; the second-nearest-layer
  coupling is about 30 % of the nearest one (Kim 2016, abstract).
- Monolayer-to-bulk shifts of A1g and E2g1 for MoSe2 are compiled with the other three TMDs in Zhao W. et al. 2013,
  Nanoscale 5, 9677, arXiv:1304.0911, Fig. 4 (data for MoSe2 taken from an earlier reference).
- A clean "separation vs N" table for MoSe2 was not verified here: do not reuse the MoS2 rule.

## Strain and doping
- No MoSe2-specific Raman strain or doping rate verified. By analogy with MoS2, WS2 and WSe2 (Conley 2013;
  Dadgar 2018), expect in-plane E' to soften and split faster than A1'. Inference, not a MoSe2 measurement.
- Because E' is weak, strain is harder to read from MoSe2 Raman than from MoS2; PL or reflectance are often used
  instead (the strain papers found, e.g. Carrascoso F. et al. 2020, Nano Res., doi:10.1007/s12274-020-2918-2,
  arXiv:2006.06660, abstract, use reflectance).

## Defects and quality
- In thin CVD MoSe2 a feature near 250 cm-1 is a Se-vacancy-induced localized mode; Se vacancies come from heating
  and hydrogen etching during growth (Zhao S. et al. 2019, arXiv:1904.09789, abstract). Single source.
- Phonon confinement broadens and shifts intrinsic modes in defective samples (Zhao S. 2019, abstract).
- Pitfall: the 250 cm-1 defect mode sits between A1g (242) and the resonant features; check the laser line before
  calling it a defect.

## Temperature and heating
- A1g redshifts on heating; first-order coefficients of 1L and 2L MoS2 and MoSe2 lie between about 0.009 and
  0.020 cm-1/K in magnitude, and the supported shift is smaller than the suspended one, attributed to substrate
  interaction (Zhang X. et al. 2015, arXiv:1509.07100, p.7, Table 1 p.8). Column mapping in the extracted table
  was ambiguous, so the per-sample values are not quoted.
- Optothermal thermal conductivities depend on the absorbed power; measured absorption was about 40 % lower than
  previously assumed (Zhang X. arXiv:1509.07100, abstract). Treat literature heating estimates with caution.

## Excitation wavelength and resonance
- Resonances with the A, B and C excitons (near 1.54, 1.74 and 2.61 eV) affect both A- and E-type phonons; intensity
  rises strongly near the C exciton (Soubelet 2016, abstract, p.2). 25 laser lines from 458 to 825 nm.
- Shear modes resonate with the C exciton; breathing-mode intensity keeps growing above it (Soubelet 2016,
  abstract). A1g is selectively enhanced at the A exciton, the shear mode at the C exciton (Kim 2016, abstract).
- At 676 or 735 nm the 1L spectrum changes drastically and A1' is no longer dominant (Soubelet 2016, p.2, Fig. 1b,c).
- Broad second-order peaks (E2g1+LA(M), E1g+LA or 2B2g at M) are strongly enhanced at 1.58 eV (A exciton)
  (Kim 2016, p.7). Laser-specific features between 280 and 320 cm-1 are expected; do not call them impurities.

## Polarization and substrate
- In cross-linear polarization A1g (242) and the 354 cm-1 A-type mode vanish; the 170 cm-1 E-type mode is
  unaffected (Soubelet 2016, p.3, Fig. 3b). Use XX vs XY to assign every multilayer peak.
- Substrate effects on positions were not verified for MoSe2; interference applies as for other TMDs.

## Pitfalls and artifacts
- E' at about 285 to 288 cm-1 is weak and easily lost in noise or confused with resonance bands; an absent E'
  is not evidence of a different material.
- Raman alone can confuse MoSe2 with WSe2 near 250 cm-1 in unpolarized spectra; check E' (MoSe2 near 285 to 288)
  and the WSe2 2LA(M) near 261 (Zhang X. et al. 2015, Chem. Soc. Rev., arXiv:1502.00701, p.13), and use PL energy.
- Never compare relative intensities across laser lines.

## What to ask
- Exact laser line (resonance dominates MoSe2), power and spot size.
- Polarization configuration.
- Growth method (CVD Se vacancies), annealing history, substrate and encapsulation.
- Temperature; resolution and calibration (Si line).

## Reference figures
- Soubelet 2016, arXiv:1603.05172, Fig. 1a to d: 1L MoSe2 at 465, 676 and 735 nm (resonance change).
- Soubelet 2016, arXiv:1603.05172, Fig. 3a,b: 1L to 5L with the 170 and 354 cm-1 lines; co vs cross polarization.
- Kim 2016, arXiv:1608.03944, Fig. 3a: Davydov splitting of A1g for 1 to 6 TL.
- Nam 2015, arXiv:1511.01225, Fig. 2: excitation-energy dependent spectra.
