# Measurement and analysis pitfalls common to 2D-material Raman

Numbers only where read in the cited source (locator in brackets). [practice] marks common laboratory
practice that I could not tie to a source read for this note; treat it as advice, not evidence. Material
specifics are in graphene.md, hBN.md, black-phosphorus.md; spectrum-level artifacts also in ../artifacts.md.

## Calibration and spectral accuracy
- A first-order (linear) pixel-to-wavelength calibration of a single-grating spectrograph gave Raman shift
  errors of 5.0 to -6.8 cm-1 across the detector; with only 3 Hg lines, up to 18 cm-1; adding the quadratic
  term brought it within +-0.3 cm-1 (Lee et al. 2012, Nat. Commun. 3, 1024; arXiv 1209.0234, Methods p.10).
  Their check: graphite G 1581.5 +- 0.3 cm-1 over 12 spots.
- The error depends on where on the detector a line falls, so a single Si-line check near 520 cm-1 does not
  validate a 2D band near 2700 cm-1 [inference from the same mechanism].
- Si first order is quoted as 520 (Lee et al. 2010, ACS Nano 4, 2695; arXiv 1005.2509) and 520.9 cm-1
  (Castellanos-Gomez et al. 2014, arXiv 1403.0499, p.7) in different setups: small offsets between labs are
  normal, so compare shifts relative to an internal reference measured in the same session.

## Resolution, grating and instrument line shape
- Measure resolution from the Rayleigh line: 1.9 vs 9.4 cm-1 on two instruments in one study; spectra then fit
  with Voigt profiles and the Lorentzian FWHM taken as the lifetime width (Das et al. 2008, Nat. Nanotechnol.
  3, 210; arXiv 0709.1174, p.2). About 0.6 cm-1 with a triple-filter low-frequency setup (Zhang et al. 2013,
  PRB 87, 115413; arXiv 1212.6796, p.2); 2.7 cm-1 in Lee 2010 (docs/verified-reference-numbers.md).
- Widths near the resolution (hBN 3 to 9 cm-1, BP Ag2 3 to 7 cm-1; see material notes) are instrument-limited:
  never compare raw FWHM across setups without the resolution. A 0.5 cm-1 resolution was not enough to count BP
  layers from positions (Castellanos-Gomez 2014, p.8).

## Laser heating, power density and photodamage
- Do a power series: Ferrari et al. 2006 saw no change from about 4 to 0.04 mW at 100x (arXiv
  cond-mat/0606284, p.2); typical working powers 1 mW with about 1 um spot (Cancado et al. 2011, arXiv
  1105.0175, p.2), 0.23 mW (Zhang 2013, p.2), below 300 uW at 0.5 NA (Janzen et al. 2023, arXiv 2306.13358,
  p.7). Quote power density, not power: the same mW gives different heating at different NA.
- Temperature coefficients depend on support: graphene 2D -0.034 cm-1/K supported vs -0.072 suspended
  (Calizo 2007, arXiv 0708.1223, Table I; Chen et al. via Lee et al. 2011, arXiv 1103.3337, p.2). Do not
  convert a shift into a temperature with a coefficient from a different geometry.
- Optothermal estimates need a peak-vs-T calibration, the absorbed (not incident) power, and a measured spot
  size; using two spot sizes helps (Malekpour and Balandin 2018, J. Raman Spectrosc. 49, 106; arXiv
  1710.09749, pp.4, 18).
- Stokes/anti-Stokes thermometry fails under resonance when incident and scattered windows differ (Ferrari
  and Basko 2013, Nat. Nanotechnol. 8, 235; arXiv 1306.5856, p.12).
- Photodamage is dose-dependent: BP oxidation rate scales with fluence (Favron et al. 2015, arXiv 1408.0345,
  p.7); MnPS3 degraded at about 50 uW when one spot was illuminated 500 s or longer (Lim et al. 2021, Curr.
  Appl. Phys. 21, 1; doi 10.1016/j.cap.2020.09.017, pp.6-7, via Lit-RAG). Irreversible change in a repeat
  spectrum means damage, reversible shift means heating.

## Objective NA, focus and polarization
- A tightly focused beam has longitudinal (out-of-plane) field components that can excite modes forbidden for
  purely in-plane fields (Grosche et al. 2020, Opt. Express, doi 10.1364/OE.388943; arXiv 1905.12325,
  abstract). How large this leakage is for a standard 100x/0.9 objective was not quantified in what I read.
  [magnitude not verified]
- In birefringent crystals the classical Raman tensor fails because polarization changes with depth; an
  effective tensor is needed (Kranert et al. 2016, PRL 116, 127401, abstract). In thin anisotropic flakes on
  SiO2/Si, anisotropic interference changes polar patterns with thickness (Kim et al. 2015, arXiv 1510.03263).
- Si substrate intensity depends on Si crystal orientation to the laser polarization (Castellanos-Gomez 2014,
  p.8): sample/Si intensity ratios need fixed sample rotation.
- Ask whether the analyzer is fixed and a half-wave plate rotates the polarization, or the sample rotates;
  grating efficiency is polarization dependent [practice].

## Interference on SiO2/Si
- Graphene I(2D)/I(G) changed by almost 370 % for a 60 % change in SiO2 thickness (Yoon et al. 2009, PRB 80,
  125422; arXiv 0908.4322, abstract, Fig. 2). Intensity ratios between bands at different shifts are
  stack-dependent.
- For MoS2 the sample intensity oscillates with thickness (interference maxima), but the ratio of sample to Si
  intensity becomes monotonic and gives thickness (Li et al. 2012, ACS Nano 6, 7381; arXiv 1308.3835,
  abstract, Fig. 4). Interference also changes optical contrast (Gorbachev et al. 2011, arXiv 1008.2868).

## Encapsulation and overlayers
- hBN encapsulation narrows graphene 2D (16 to 20 vs above 22 cm-1 on SiO2) and changes doping (Neumann et
  al. 2015, arXiv 1406.7771, p.2); it narrows BP lines and reveals a surface mode (Urban et al., arXiv
  1711.08294, abstract). Compare encapsulated with encapsulated only.
- Overlayer lines can overlap sample lines: hBN E2g near 1366 cm-1 on graphene D (Purdie et al. 2018, Nat.
  Commun. 9, 5387, p.6, via Lit-RAG). Measure an overlayer-only reference spot.

## Low-frequency modes and filters
- Shear and breathing modes (tens of cm-1) need notch or Bragg filters reaching about 5 to 10 cm-1 and
  plasma-line cleanup (Zhang 2013, p.2). Many production spectrometers cut above the graphene C mode, so absence
  below the cutoff is not evidence (Ferrari and Basko 2013, p.2). Odd and even layer numbers scale differently
  (Zhang 2013, abstract).

## Spikes, plasma lines, fluorescence, baseline
- Spikes and plasma lines: see ../artifacts.md (sources listed there, not re-verified here).
- Fluorescence or PL backgrounds: fit a local background with the peaks for broad bands; a global baseline can
  remove real broad signal [practice; see ../artifacts.md].

## Fitting line shapes and over-fitting
- Report whether ratios use heights or areas: graphene defect relations use heights (Cancado 2011) and heights
  and areas diverge in stage 2 (Eckmann et al. 2012, arXiv 1207.2058, p.5).
- Number of components needs physics: 1L graphene 2D one, Bernal 2L four (Ferrari 2006, p.2); unresolved
  doublets (BP Ag2 in few layers, resolved only at 77 K, Favron 2015, p.10) appear as broadening. Adding peaks
  without a physical reason fits noise; compare models by an information criterion [practice].
- Fit overlapping neighbours jointly (WS2 2LA(M) and E2g, see ../artifacts.md; hBN and graphene D, Purdie 2018).

## Comparing spectra from different setups
- Different lasers: dispersive bands (graphene D, 2D) move; resonances change relative intensities (Cancado
  2011; Kim et al. 2012, arXiv 1201.4221). Different spectrographs: calibration offsets of several cm-1 (Lee
  2012). Different substrates: interference changes ratios (Yoon 2009). Compare differences measured in one
  session, not absolute values across papers.

## Mapping statistics
- A spectrum averages over the spot: sub-spot strain variations show up as width, not shift (Neumann 2015,
  Fig. 1); mono- and bilayers can vary strongly from sample to sample (Gorbachev 2011, p.4).
- Use many points and correlations: hundreds of map pixels per sample fell on a G-2D line of slope 2.2 (Lee
  2012, p.3, Fig. 2). Report distributions (histograms, median and spread), not one "representative" spectrum.
- Move the spot between acquisitions on sensitive materials (Lim 2021).

## What to ask
- Laser line and power at sample, objective NA, spot size; grating, resolution, calibration lines and date.
- Substrate stack and oxide thickness; encapsulation; suspended or supported.
- Polarization geometry; temperature and atmosphere; exposure time; number of spectra and map size.

## Reference figures
- Yoon 2009, arXiv 0908.4322, Fig. 2: G and 2D intensities and their ratio vs SiO2 thickness.
- Li 2012, arXiv 1308.3835, Fig. 4: MoS2/Si intensity ratios vs layer number, calculated and measured.
- Zhang 2013, arXiv 1212.6796, Fig. 4: shear and breathing positions vs layer number (odd vs even).
- Neumann 2015, arXiv 1406.7771, Fig. 1: maps and 2D-width histograms, hBN vs SiO2 support.
