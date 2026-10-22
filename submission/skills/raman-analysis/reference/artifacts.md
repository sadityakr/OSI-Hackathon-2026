# Artifacts and red flags in Raman spectra of 2D materials

Each entry: what it looks like, how to tell it from a real band, what to do. Sources in brackets.

## Cosmic-ray spikes
- One to three pixels wide, far narrower than any phonon line at the instrument resolution, present in one
  acquisition only. Real lines have the instrument's minimum width and repeat across accumulations or angles.
- Remove before fitting (modified z-score on the first difference: Whitaker and Hayes, Chemom. Intell. Lab. Syst.
  179, 82, 2018). In an angle series, replace spike pixels from the most similar frame (Barton and Hennelly, Appl.
  Spectrosc. 73, 893, 2019). List them under artifacts, never under peaks.

## Silicon substrate
- First-order Si line near 520.7 cm-1 (a widely used calibration convention; check the offset of the fitted
  position and flag a calibration problem when it exceeds about 1 cm-1; 520 to 520.9 is reported in practice, Lee
  et al. 2010 and Castellanos-Gomez et al. 2014). Second-order Si features near 950 and 980 cm-1 (Gillet et al.
  2017, arXiv 1708.05874, Fig. 1) and a 2TA band computed near 300 cm-1 (same paper, DFPT) can be mistaken for
  sample modes. Brillouin scattering from Si gives a line near
  4.5 cm-1 in ultra-low-frequency setups (Zhang et al., PRB 87, 115413, 2013).
- Assign these as 'Si substrate'. A strong Si line with weak sample bands suggests a thin flake.

## Calibration
- First-order wavelength calibration errors of 5 to 7 cm-1 have been reported (Lee et al., Nat. Commun. 3, 1024,
  2012). Shifts of 1 to 3 cm-1 (layer number, strain, doping) are only meaningful after a calibration check.

## Background
- Broad fluorescence or photoluminescence slopes; remove with an asymmetric least-squares baseline (arPLS or
  asPLS). For broad bands (disordered carbon D and G, amorphous phases) a global baseline can eat real signal: fit
  a local linear background together with the peaks. A Breit-Wigner-Fano line shape can absorb a background slope;
  compare line shapes by BIC.

## Low-wavenumber cutoff
- Notch and edge filters block the region near the laser line (Bragg notch filters reach about 5 to 10 cm-1,
  Zhang et al. 2013). A missing shear or breathing mode below the cutoff is not evidence of absence.

## Plasma lines
- Laser plasma lines have a fixed absolute wavelength, so their Raman shift changes when the laser changes; they
  are very narrow and do not belong to the sample. Suspect them when a narrow line has no assignment.

## Laser heating
- Phonon lines soften and broaden with temperature. Graphene G shifts about -0.016 cm-1/K (Calizo et al., Nano
  Lett. 7, 2645, 2007); 1L WS2 about -0.0093 (E) and -0.0122 (A1g) cm-1/K (Huang et al., Sci. Rep. 2016);
  few-layer MoS2 about -0.013 and -0.012 cm-1/K (Sahoo et al., arXiv 1302.5865). A power series is the test.

## Substrate interference
- On SiO2/Si, absolute intensities and intensity ratios depend on oxide thickness and laser wavelength: graphene
  I(2D)/I(G) changed by almost 370 % for a 60 % change in SiO2 thickness (Yoon et al., PRB 80, 125422, 2009).
  Never read layer number from absolute intensity or from I(2D)/I(G) without the substrate stack.

## Resonance
- Near an excitonic resonance, second-order bands can exceed first-order ones. WS2 at 514 to 532 nm: 2LA(M) lies
  about 4 cm-1 below E2g and overlaps it (Berkdemir et al., Sci. Rep. 3, 1755, 2013; Mitioglu et al., PRB 89,
  245442, 2014). Fit both or the E2g position and layer count are wrong.

## Saturation and clipping
- A flat-topped peak or values at the detector maximum: the peak shape and intensity are wrong; ask for a shorter
  exposure.
