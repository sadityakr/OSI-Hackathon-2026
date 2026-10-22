# Black phosphorus (BP, phosphorene): expert reading notes

Numbers only where read in the cited source (locator in brackets). [consensus] = several groups agree;
[disputed] = sources disagree or one group only. BP is orthorhombic, strongly in-plane anisotropic,
birefringent and dichroic, and it degrades in air under light: every BP spectrum must be read with its
polarization geometry and its exposure history.

## Signature
- Three high-frequency modes in backscattering from the layer plane: Ag1 (out-of-plane), B2g and Ag2
  (in-plane, along zigzag and armchair) near 362, 440 and 467 cm-1. At 514 nm on 1.6 to 9 nm flakes:
  362.1, 439.5, 467.7 cm-1, with Si at 520.9 in the same setup (Castellanos-Gomez et al. 2014, 2D Mater. 1,
  025001; arXiv 1403.0499, p.7). At 532 nm: 361, 438, 466 cm-1 (Favron et al. 2015, Nat. Mater. 14, 826;
  arXiv 1408.0345, p.4). [consensus]
- Mode character and directions: Ag1 out-of-plane, B2g along zigzag, Ag2 along armchair (Ling et al. 2015,
  Nano Lett.; arXiv 1502.07804, p.3).

## Thickness and stacking
- High-frequency positions barely move with thickness: the shift was below what 0.5 cm-1 resolution could use
  for counting layers (Castellanos-Gomez 2014, p.8). [consensus]
- Favron 2015 (pp.10, 13, Figs. 4-5; 532 nm, pristine flakes): Ag1 and B2g do not shift significantly but
  broaden for n <= 5 (about 1.5 cm-1 down to 2L); Ag2 shifts up non-monotonically, +2.6 cm-1 at 2L and +2 cm-1
  at 1L vs bulk; Ag2 FWHM 3.3 (bulk) to 6.8 (2L) to 5.3 cm-1 (1L). Extra near-degenerate modes (Davydov-type,
  IR-derived) sit near Ag2 in few layers; two modes are resolved in 2L at 77 K.
- Intensity ratio I(Ag1)/I(Si) gives thickness within 1 to 2 nm, but Si intensity depends on its orientation
  to the laser polarization, so the substrate must be aligned for comparisons; B2g/Si and Ag2/Si vary with
  flake orientation (Castellanos-Gomez 2014, p.8, Fig. 3c).
- Low-frequency interlayer breathing modes (below 100 cm-1, Ag symmetry) are much more thickness-sensitive
  than the high-frequency modes; bulk shear about 19 and 52, breathing about 87 cm-1 (Ling 2015, abstract,
  p.6). A further ultralow-frequency compression mode was reported (Dong et al. 2016, PRL 116, 087401; arXiv
  1503.06577, title only, not read).
- hBN-encapsulated flakes of 3L and thicker show a new peak about 4 cm-1 above Ag1, assigned to surface-layer
  vibrations; encapsulation narrows all lines (Urban et al., Nanoscale, doi 10.1039/C7NR05588A; arXiv 1711.08294, abstract).

## Strain and doping
- Strain response is predicted and measured to be anisotropic and has been used to find the crystal axes
  (Fei and Yang 2014, APL 105, 083120, arXiv 1407.0736; Zhang et al. 2017, arXiv 1702.08522). I did not read
  either text: no strain coefficients are given here. [not verified]
- Water uptake gives strong p-type doping in FETs over hours (Island et al. 2015, 2D Mater. 2, 011002; arXiv
  1410.2608, abstract). A Raman signature of doping in BP is not established in the sources read. [unknown]

## Defects and quality (degradation is the main defect channel)
- Photo-oxidation needs all three of water, oxygen and visible light; vacuum, O2 alone, H2O alone, or dark
  storage showed no degradation (Favron 2015, pp.4-5, Fig. 1d). [consensus with Island 2015]
- Raman intensity loss is the marker: a multilayer lost its Raman signal within about two hours under
  2x10^4 W/cm2 at 532 nm in air (Favron 2015, p.4, Fig. 1c). Decay time scales as fluence^-1 (p.7, Fig. 1e).
  Thinner flakes oxidize faster (bandgap closer to oxygen acceptor levels) (p.8).
- So the measuring laser itself drives degradation: a power series or time series on one spot is a damage
  test, not only a heating test.
- Air exposure for more than a week etched thin regions; Raman on etched thin parts showed no BP peaks
  while thick parts kept them (Castellanos-Gomez 2014, pp.19-20, Fig. 8). Layer-by-layer etching down to 1L
  thickness (Island 2015, abstract): a flake's apparent thickness can change after exfoliation.
- Narrow Ag2 and absence of extra lines near Ag2 in thick flakes suggest pristine material; a sourced
  oxidation-specific Raman band (PxOy) was not identified in these papers (oxides were seen by EELS, Favron
  2015, p.5). [not verified]

## Temperature and heating
- Linear coefficients (633 nm, -150 to 30 C, few-layer): Ag1 -0.0073, B2g -0.013, Ag2 -0.012 cm-1/K; the
  breathing mode near 87 cm-1 is almost temperature independent (harmonic) (Ling 2015, pp.16-17, Fig. 5).
- Heat and light are coupled to degradation in air; measure in vacuum or under capping when using power
  series (Favron 2015, pp.4, 8).

## Excitation wavelength
- Ag1 and Ag2 polarization patterns change with laser wavelength (441.6 to 632.8 nm) and sample thickness;
  B2g pattern does not (Kim et al. 2015, Nanoscale, doi 10.1039/C5NR04349B; arXiv 1510.03263, abstract p.2, Fig. 4). Thickness effect
  explained by anisotropic interference (birefringence, dichroism); wavelength effect unexplained (same).
  [consensus that naive rules fail; mechanism disputed]

## Polarization and substrate
- Kim 2015 procedure (p.17): find principal axes by cross-polarized optical microscopy (or full polar plot),
  then with a short-wavelength laser (441.6 nm) in parallel polarization the direction where Ag1 is stronger
  (Ag2 weaker) is zigzag. Using Ag2 maximum as armchair with a red or green laser can give the wrong axis.
- Raman intensities are very sensitive to polarization of incident and scattered light; any intensity-ratio
  thickness method must fix the crystal orientation (Favron 2015, p.14).
- Encapsulation (hBN, parylene) preserves flakes: 20 to 300 nm parylene C blocked degradation (Favron 2015,
  pp.4, 8); hBN narrows lines (Urban, arXiv 1711.08294).

## Pitfalls and artifacts
- A "thin BP" spectrum with weak BP lines and a strong Si line may be a partly oxidized flake, not a thin one.
- Spectra taken minutes vs hours after exfoliation are not comparable; record exposure time and light dose.
- Si 520 cm-1 intensity used as a reference depends on Si crystal orientation to the polarization
  (Castellanos-Gomez 2014, p.8).
- Do not assign armchair from Ag2 alone; check B2g and the laser (Kim 2015).

## What to ask
- Time in air, light exposure, glove box or capping, vacuum during measurement.
- Laser wavelength and power density; polarization geometry and angle of the flake to the polarizer.
- Thickness by AFM or contrast; substrate oxide thickness (anisotropic interference).
- Temperature; low-frequency data available.

## Reference figures
- Favron 2015, arXiv 1408.0345, Fig. 1: Raman decay with time in air, in different atmospheres and fluences.
- Favron 2015, arXiv 1408.0345, Fig. 4: spectra of 1L to 5L and bulk at 532 nm.
- Kim 2015, arXiv 1510.03263, Fig. 4: polar plots of Ag1, B2g, Ag2 at five laser wavelengths.
- Castellanos-Gomez 2014, arXiv 1403.0499, Fig. 3 and Fig. 8: spectra vs thickness, Ag1/Si ratio; aged flake.
