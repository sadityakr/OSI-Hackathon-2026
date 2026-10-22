# Material notes: modes, diagnostics, pitfalls

Numbers are read from the cited papers (locators in brackets). Positions shift by 1 to 3 cm-1 with substrate,
strain, doping, temperature and calibration; compare patterns and differences, not single absolute values.
For materials not listed here, use `rl_match.py` (Computational Raman Database) and the literature tools.

## Graphene and graphite (D6h bulk; G is E2g)
- Bands at 514 nm: G about 1580 cm-1, 2D about 2700 cm-1; graphene G sits 3 to 5 cm-1 above graphite
  (Ferrari et al., PRL 97, 187401, 2006, p.2). D (about half of 2D) and D' (about 1620) need defects.
- Layers: 1L has a single symmetric Lorentzian 2D; 2L has four components; above about 5 layers the spectrum
  resembles graphite (Ferrari 2006). Turbostratic graphite also gives a single Lorentzian 2D, about twice as wide
  and upshifted about 20 cm-1, so a single Lorentzian alone is not proof of a monolayer (Lee et al. 2012).
  I(2D)/I(G) depends on substrate interference (Yoon et al. 2009); do not use it alone for layer number.
- D and 2D disperse with laser energy (about 50 and 100 cm-1/eV; Ferrari and Basko, Nat. Nanotechnol. 8, 235,
  2013): never compare 2D positions measured with different lasers.
- Defects: relations `graphene_defect_distance_from_ID_IG` (point defects, I_D/I_G heights, L_D >= 10 nm) and
  the Eckmann rule in relations.md (I_D/I_D'). I_D/I_G peaks near L_D about 3 nm, so one ratio maps to two defect
  densities; the G width separates them (about 14 cm-1 in stage 1, much larger in stage 2) (Cancado et al. 2011).
- Strain and doping: relation `graphene_strain_doping_from_G_2D` (vector decomposition of G and 2D positions, 514.5 nm).
  Uniaxial strain rates: G+ -10.8, G- -31.7, 2D -64 cm-1/% with G splitting (Mohiuddin et al., PRB 79, 205433,
  2009).

## MoS2 (2H: D6h bulk, D3h monolayer; E2g1 -> E', A1g -> A1' in 1L; 3R: C3v, modes A1 and E)
- Positions vs layers at 514.5 nm on 285 nm SiO2/Si (Lee et al., ACS Nano 4, 2695, 2010, Fig. 2b):
  1L 384.0 / 403.1 (Delta 19.1), 2L 383.4 / 404.8 (21.4), 3L 382.8 / 405.9 (23.1), 4L 382.4 / 406.7 (24.3),
  bulk 382.2 / 407.4 (25.2) cm-1 for E2g1 / A1g. Relation `mos2_layer_number_from_separation`.
- Polytype: 3R-MoS2 uses C3v labels (A1, E), not the 2H D6h labels; the stacking also shows in low-frequency modes.
  1T has no E2g1 (Raman-inactive in octahedral form, Lee 2010).
- Defects: a defect-activated LA(M) band near 227 cm-1 grows with defect density (Mignuzzi et al., PRB 91,
  195411, 2015); its quantitative L_D calibration is not encoded here.
- Strain: E' softens -4.5 cm-1/% under uniaxial strain and splits; A' does not shift measurably (Conley et al.,
  Nano Lett. 13, 3626, 2013). Electron doping softens A1g (4 cm-1 at 1.8e13 cm-2) and broadens it by 6 cm-1, with E2g1
  nearly unchanged (Chakraborty et al., PRB 85, 161403, 2012). So an A1g shift alone points to doping, an E2g
  shift (with splitting) to strain.

## WS2 (2H)
- At 514.5 nm (Berkdemir et al., Sci. Rep. 3, 1755, 2013, Table 1): 1L 2LA(M) 351.1, E2g1 355.2, A1g 417.2;
  bulk 350.0, 355.3, 420.1 cm-1. A1g stiffens with layer number (417.2 -> 418.4 -> 419.0 -> 420.1 for 1L, 2L,
  3L, bulk); E2g1 barely moves.
- 2LA(M) overlaps E2g1 (about 4 cm-1 apart) and dominates near resonance (514 to 532 nm): fit both. In 1L the
  2LA(M)/A1g intensity ratio is about 2 at 514 nm and decreases with thickness (Berkdemir 2013). LA(M) near 176.

## MoSe2 and WSe2
- MoSe2 bulk: A1g 242, E2g1 285, E1g 169 (resonant) cm-1 (Nam et al. 2015, arXiv 1511.01225). Monolayer values
  not encoded.
- WSe2 bulk: A1g and E2g nearly degenerate at 252.2 cm-1; an extra peak sits 5, 6, 11 cm-1 above the main peak
  in 3L, 2L, 1L (Sahin et al. 2013, arXiv 1303.5861).
- Both show strong resonance effects; relative intensities depend on the laser.

## hBN
- Bulk E2g about 1366 cm-1 (HWHM about 9); 1L upshifted 2 to 4 cm-1 (sample dependent +-2), HWHM 10 to 12; 2L
  usually 1 to 2 cm-1 downshifted (Gorbachev et al., Small 7, 465, 2011). Strain causes shifts of the same size,
  so position alone is a weak layer test; intensity rises in steps with layer number on a given substrate.

## CrSBr (orthorhombic Pmmn, in-plane anisotropic; magnetic below T_N about 132 K bulk)
- Room temperature: Ag modes at 114, 244, 344 cm-1 (4L, Mondal et al. 2025, arXiv 2410.22164) and 117, 257, 345
  cm-1 (bulk, 633 nm, Pawbake et al., PRB 107, 075421, 2023); 121, 254, 346 at 5 K. B2g modes (92, 194, 301)
  appear only with a tilted sample (Pawbake 2023).
- Polarization: Ag1 and Ag3 are maximal along b; Ag2 rotates between a and b depending on excitation energy and
  thickness (Mondal 2025). Know the laser before claiming a crystal axis from Ag2.
- Below T_N, additional lines and changes in the Ag2 tensor appear (Mondal 2025; Pawbake 2023).

## Black phosphorus (orthorhombic)
- Ag1 362.1, B2g 439.5, Ag2 467.7 cm-1 at 514 nm on thin flakes (Castellanos-Gomez et al. 2014, arXiv 1403.0499).
- Orientation: B2g polarization pattern is robust; Ag patterns depend on wavelength and thickness through
  birefringence and dichroism, so the naive Ag2 rule for the armchair axis can fail (Kim et al. 2015, arXiv
  1510.03263). Degrades in air within hours; heating matters on polymer substrates.

## Magnetic layered materials (CrI3 and others)
- Magnetic order can activate modes forbidden by lattice symmetry: in ordered CrI3, A1g appears in crossed
  polarization and switches with the AFM/FM state in 2L (Zhang et al., Nano Lett. 2020). Temperature and field
  must be stated before interpreting such features.
