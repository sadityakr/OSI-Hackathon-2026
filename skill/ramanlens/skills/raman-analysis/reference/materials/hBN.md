# Hexagonal boron nitride (hBN): expert reading notes

Numbers only where read in the cited source (locator in brackets). [consensus] = several groups agree;
[disputed] = sources disagree. hBN is a wide-gap insulator: no Kohn anomaly, no double resonance, so its
Raman spectrum is far poorer in information than graphene's; most of what it tells is strain, isotope
content, thickness via intensity, and crystal quality via width.

## Signature
- One strong high-frequency line, the in-plane E2g (often called "G band" by analogy with graphene), at about
  1366 cm-1 in bulk crystals (Gorbachev et al. 2011, Small 7, 465; arXiv 1008.2868, p.3). Bulk value
  1366.6 +- 0.2 cm-1 over 6 crystals (Cai et al. 2017, Nanoscale 9, 3059; arXiv 2008.01656, p.7).
  [consensus]
- Bulk width: HWHM about 9 cm-1 (Gorbachev 2011, p.4); FWHM about 9 cm-1 for bulk flakes in heterostructures
  (Purdie et al. 2018, Nat. Commun. 9, 5387; doi 10.1038/s41467-018-07558-3, p.6, via Lit-RAG).
- Low-frequency interlayer shear E2g near 50 cm-1 in bulk; needs a low-frequency setup (Janzen et al. 2023,
  arXiv 2306.13358, p.7).
- Monolayer signal is weak: about 50 times smaller than graphene G under the same conditions (Gorbachev
  2011, p.3). Long integration and Si second-order background become relevant.

## Thickness and stacking
- Integrated E2g intensity is proportional to N for the first several layers on a given substrate; once
  calibrated, this distinguishes 1, 2 and more layers (Gorbachev 2011, p.4, Fig. 4a inset). [consensus]
- Position as a layer test [disputed]:
  - Gorbachev 2011 (pp.1, 4, Fig. 4b): 1L upshifted typically 2 to 4 cm-1 (sample dependent, +- 2 cm-1),
    2L usually downshifted 1 to 2 cm-1; attributed to shorter B-N bond plus random strain.
  - Cai 2017 (pp.7-8, Fig. 1): substrate-bound 1L 1369.6 +- 0.6, 2L 1369.0 +- 0.5, 3L 1367.5 +- 0.2 cm-1;
    suspended 1L to 3L 1367.0 to 1367.3 cm-1, close to bulk. DFT finds the intrinsic E2g nearly N-independent.
    Conclusion: shifts in thin hBN come mainly from substrate strain, not thickness.
  - Practical reading: a 1 to 4 cm-1 upshift is consistent with 1L but not proof; use intensity steps,
    optical contrast or AFM.
- Optical contrast of 1L on SiO2 is small (under 1.5 % white light) and changes sign near 530 nm; about
  2.5 % per layer on about 80 nm SiO2 (Gorbachev 2011, pp.1-3). Monolayers can look like bilayers without
  annealing (same, p.3).

## Strain and doping
- Strain dominates thin-hBN shifts; it may vary within the laser spot as the flake follows substrate
  roughness, which also broadens the line (Gorbachev 2011, p.4). 1L HWHM 10 to 12 cm-1 vs about 9 bulk.
- Annealing at 400 C on SiO2/Si increased roughness and upshifted 1L by 3.0 +- 0.7 cm-1 (2L 2.7, 3L 2.2);
  bulk unchanged (Cai 2017, pp.13-16, Fig. 4). Thermal-expansion mismatch with SiO2 is the proposed cause.
- Doping: monolayer BN is not subject to surface doping (insulator), so doping is not a usual explanation
  of shifts (Cai 2017, p.7, citing earlier work).

## Defects and quality
- Width is the main quality indicator, but isotope disorder sets a floor: natural boron (about 20 % 10B,
  80 % 11B) gives FWHM about 7.5 to 8 cm-1; monoisotopic crystals about 3 to 4 cm-1 (Janzen 2023, pp.3, 7).
  A natural-abundance crystal cannot be narrower than this floor regardless of quality. [consensus]
- Isotope shifts are large: about 1393 cm-1 for h10B14N, 1357 for h11BN, down to about 1335 cm-1 for h11B15N
  (Janzen 2023, pp.3, 7, Fig. 4b). A line far from 1366 may be isotope engineering, not strain.
- No defect-activated band analogous to graphene D is established for hBN in the sources read here; I do
  not have a sourced Raman defect metric beyond width and position. [not verified]

## Temperature and heating
- E2g softens on heating: a 1L line moved to 1367.7 cm-1 at 75 C and 1366.4 cm-1 at 100 C (Cai 2017, p.7).
  Heating therefore cannot explain upshifts of thin hBN on SiO2.
- Example measurement practice: power kept below 300 uW at 0.5 NA to avoid heating (Janzen 2023, p.7).
  hBN absorbs little visible light, so heating is usually a lesser concern than for graphene. [inference]

## Excitation wavelength
- hBN E2g does not disperse with laser energy (no double resonance or Kohn anomaly), unlike graphene D
  (Purdie 2018, p.6). Changing the laser separates an hBN line from a graphene D peak.
- Wide gap: visible excitation is far from resonance; UV benefits wide-gap layered materials (Ferrari and Basko
  2013, Nat. Nanotechnol. 8, 235; arXiv 1306.5856, p.12). [qualitative]

## Polarization and substrate
- In-plane E2g of a hexagonal crystal gives no in-plane angular contrast in parallel or crossed
  backscattering. [inference from symmetry, not from a source read here]
- In heterostructures the hBN line is the sum of top and bottom flakes (Purdie 2018, p.6); thickness
  assignments from intensity need each flake measured separately.
- hBN encapsulation narrows graphene 2D (16 to 20 vs above 22 cm-1 on SiO2) and the hBN line serves to map
  encapsulated areas (Neumann et al. 2015, Nat. Commun. 6, 8429; arXiv 1406.7771, p.2, Fig. 1e,h).

## Pitfalls and artifacts
- hBN E2g at about 1366 cm-1 overlaps graphene D (about 1350 at 514 nm): in encapsulated graphene a peak near
  1360 is not automatically defects; check with a second laser (Purdie 2018, p.6).
- Weak 1L signal: confirm the line is above the Si second-order background and noise.
- Peak position differences of 1 to 3 cm-1 are within strain and calibration scatter; never assign layer
  number from position alone (Gorbachev 2011; Cai 2017).
- Width comparisons only between crystals of the same isotope composition.

## What to ask
- Bulk source (HPHT, flux-grown, CVD), isotope composition; exfoliated, CVD or polymer-transferred.
- Supported or suspended; annealed or not; substrate and oxide thickness.
- Laser, power, resolution (hBN widths of 3 to 9 cm-1 are close to many instruments' resolution).
- Whether low-frequency (shear mode) data exist.

## Reference figures
- Gorbachev 2011, arXiv 1008.2868, Fig. 4: 1L to 3L spectra, intensity vs N, position vs N with sample scatter.
- Cai 2017, arXiv 2008.01656, Fig. 1 and Fig. 4: supported vs suspended positions; upshift after annealing.
- Janzen 2023, arXiv 2306.13358, Fig. 4: E2g position and width for four isotope combinations.
