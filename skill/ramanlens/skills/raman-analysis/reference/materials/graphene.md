# Graphene and few-layer graphene: expert reading notes

Numbers only where read in the cited source (locator in brackets). [consensus] = several groups agree or a
review states it; [disputed] = sources disagree or the claim is one group's. Positions shift with strain,
doping, temperature and calibration: interpret patterns and correlations, not one absolute value.

## Signature
- G (zone-centre E2g) near 1580 cm-1 and 2D (second order of zone-boundary TO phonons) near 2700 cm-1 at
  514 nm; D near 1350 cm-1 needs a defect or edge; 1L 2D is a single sharp peak about 4x higher than G; 1L G
  sits 3 to 5 cm-1 above bulk graphite (Ferrari et al. 2006, PRL 97, 187401; arXiv cond-mat/0606284, p.2).
  [consensus]
- D' near 1620 cm-1, D+D', 2D' and D+D'' are further double-resonance bands; 2D is present without defects
  (Ferrari and Basko 2013, Nat. Nanotechnol. 8, 235; arXiv 1306.5856, Fig. 1g, pp.3-6).
- Peak areas are more robust than heights: perturbations that only change phonon lifetimes conserve area
  (Ferrari and Basko 2013, p.14). State whether a ratio is I (height) or A (area).

## Thickness and stacking
- 2L Bernal: 2D broader, upshifted, four components; up to 5 layers the 2D shape still changes; above 5
  layers hardly distinguishable from graphite (Ferrari 2006, p.2, Fig. 2b,c). [consensus]
- A single-Lorentzian 2D is not proof of 1L: turbostratic graphite also has one 2D peak, about twice as wide
  and upshifted about 20 cm-1, often with a D peak (Ferrari and Basko 2013, p.9). Grown (CVD) films need this
  check. [consensus]
- Twisted bilayer (Kim et al. 2012, PRL 108, 246103; arXiv 1201.4221, pp.4-6, Figs. 2-3; 633 nm): below about
  8 deg strong-coupling spectra; above about 13 deg close to 1L. G intensity rises more than thirty-fold near
  10 to 11 deg at 633 nm; the resonance angle grows with laser energy (about 13 deg at 514 nm). 2D blueshift vs
  1L is non-monotonic (up to 22 cm-1 at 10 deg). Below 10 deg the 2D area is about half that of two decoupled
  layers.
- Twist also activates non-dispersive superlattice peaks (one in 1350 to 1550 cm-1, one near 1620 cm-1;
  Ferrari and Basko 2013, p.9) named R and R' in later work. A huge G with weak 2D at one laser line means
  "check twist resonance", not "thick flake".
- Bernal (ABA) vs rhombohedral (ABC) trilayer: distinct 2D line shapes; ABA has a higher intensity-weighted mean
  2D shift than ABC with similar dispersion (Lui et al. 2011, Nano Lett. 11, 164; arXiv 1011.3021, SI p.9).
  Thicker stacks have intermediate stackings; far-field imaging can miss sub-micron domains (Lu et al. 2025,
  Nature 637; doi 10.1038/s41586-024-08470-1, p.7, via Lit-RAG).
- Shear (C) mode near 31 cm-1 in 2L scales with N but lies below many notch/edge filters; absence of C is not
  evidence of 1L (Ferrari and Basko 2013, p.2). LO+ZO' combination near 1700 to 1750 cm-1 also tracks N.

## Strain and doping
- Uniaxial strain splits G into G+ and G- (-10.8 and -31.7 cm-1/%), 2D -64 cm-1/% (Mohiuddin 2009 via Ferrari
  and Basko 2013, p.20, Eq. S10). Biaxial strain shifts without splitting (same, p.20). [consensus]
- G stiffens and narrows for both electron and hole doping (non-adiabatic Kohn anomaly); 2D rises for holes and
  softens only at high electron doping; I(2D)/I(G) falls strongly with doping (Das et al. 2008, Nat.
  Nanotechnol. 3, 210; arXiv 0709.1174, abstract and pp.4-5). [consensus]
- Separate strain and doping by the (Pos G, Pos 2D) vector plot: strain line slope 2.2 +- 0.2 (Lee et al. 2012,
  Nat. Commun. 3, 1024; arXiv 1209.0234, p.3, Fig. 2). Model assumptions (514.5 nm origin, hole doping) limit
  transfer to other lasers or electron doping. [disputed in detail, widely used]
- Very high doping suppresses 2D when 2|E_F| exceeds the scattered photon energy (Ferrari and Basko 2013,
  pp.18-19, Fig. S3). Annealing on SiO2 raises G and 2D by about 25 cm-1 (hole doping) (Lee 2012, p.3).

## Defects and quality
- Stage 1 (L_D above about 3 nm): D and D' appear and grow, peaks broaden; stage 2: Pos(G) falls towards 1510,
  I(D)/I(G) drops, second order becomes a bump (Ferrari and Basko 2013, p.10). I(D)/I(G) peaks near L_D 3 nm,
  so one ratio gives two densities; FWHM(G) decides: about 14 cm-1 through stage 1, much larger in stage 2
  (Cancado et al. 2011, Nano Lett. 11, 3190; arXiv 1105.0175, p.5, Fig. 5c). [consensus]
- Defect type from I(D)/I(D') in stage 1: about 13 sp3, about 7 vacancy, about 3.5 boundaries (Eckmann et al.
  2012, Nano Lett. 12, 3925; arXiv 1207.2058, abstract, p.6). Only valid in stage 1. [one group, often reproduced]
- Doping lowers D and D' intensity at fixed defect count; ignoring E_F about 0.5 eV underestimated n_D by more
  than 2x in their example (Bruna et al. 2014, ACS Nano; arXiv 1405.4264, p.5). Check doping before L_D.
- Raman-silent defects: perfect zigzag edges, charged impurities, intercalants, strain give no D peak (Ferrari
  and Basko 2013, p.11). No D peak does not mean defect-free in every sense.
- Edges: D only from armchair-like segments; I(D) proportional to cos^2 theta (cos^4 with parallel analyzer)
  to the edge; I(D)min/I(D)max measures edge disorder (Ferrari and Basko 2013, p.8). A D peak confined to
  edges in a map is an edge effect, not bulk damage.
- Sub-spot strain variations broaden 2D: hBN-encapsulated FWHM(2D) mostly 16 to 20 cm-1 vs above 22 cm-1 on
  SiO2 (Neumann et al. 2015, Nat. Commun. 6, 8429; arXiv 1406.7771, p.2, Fig. 1h). FWHM(2D) is a flatness and
  quality metric.

## Temperature and heating
- Supported 1L: G -0.016, 2D -0.034 cm-1/K, 83 to 373 K (Calizo et al. 2007; arXiv 0708.1223, Table I p.7).
  Suspended 1L: 2D -0.072, G -0.044 cm-1/K (Chen et al., relayed by Lee et al. 2011, PRB 83, 081419; arXiv
  1103.3337, p.2). The difference is substrate thermal-expansion strain: coefficients do not transfer
  between supported and suspended samples. [consensus on the cause]
- Stokes/anti-Stokes thermometry is biased in graphene because incident and scattered resonance windows differ
  (Ferrari and Basko 2013, p.12).

## Excitation wavelength
- D disperses about 52 and 2D about 2x that (about 100) cm-1/eV; G does not disperse in stage 1, about 6
  cm-1/eV in stage 2 (Cancado 2011, p.5; Ferrari and Basko 2013, p.7). Never compare D or 2D positions across
  lasers. I(D)/I(G) scales with lambda^4 (Cancado 2011).
- Twist resonances and doping-blocked 2D are laser-energy specific (Kim 2012; Ferrari and Basko 2013 Fig. S3).

## Polarization and substrate
- I(2D)/I(G) changed by almost 370 % for a 60 % change in SiO2 thickness (Yoon et al. 2009, PRB 80, 125422;
  arXiv 0908.4322, abstract, Fig. 2). Substrate stack must be known before using intensity ratios.
- Strain-axis and edge-type determination use polarization (G+/G- and edge G selection rules; Ferrari and
  Basko 2013, pp.8, 19).
- In hBN-encapsulated samples the hBN E2g (about 1366 cm-1) overlaps D; D disperses with laser, hBN does not,
  so use a second wavelength (Purdie et al. 2018, Nat. Commun. 9, 5387; doi 10.1038/s41467-018-07558-3, p.6,
  via Lit-RAG).

## Pitfalls and artifacts
- 2D at about 2700 cm-1 is outside many short-range acquisitions; a "missing 2D" may be range, not physics.
- Single Lorentzian 2D: test width and D peak before claiming 1L (turbostratic, twisted).
- G position alone cannot separate strain and doping; use the G-2D vector and FWHM(G).
- Defect quantification assumes stage 1, low doping, heights, and a known laser.

## What to ask
- Laser wavelength and power at sample; substrate stack (SiO2 thickness), suspended or supported, encapsulation.
- Exfoliated or CVD or epitaxial; transfer and anneal history; gate or electrolyte; height or area ratios.
- Spectral resolution and calibration reference; mapped area and number of spectra.

## Reference figures
- Ferrari 2006, arXiv cond-mat/0606284, Fig. 2: 2D shape vs layer number at 514 and 633 nm.
- Cancado 2011, arXiv 1105.0175, Figs. 3 and 5: I(D)/I(G) vs L_D for several lasers; FWHM(G) vs L_D.
- Lee 2012, arXiv 1209.0234, Fig. 2: Pos(G) vs Pos(2D) correlation, strain and doping axes.
- Kim 2012, arXiv 1201.4221, Figs. 2-3: G enhancement and 2D width and shift vs twist angle.
