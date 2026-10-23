# Setup: <setup-id>

Owner or lab: <name> | Created: <YYYY-MM-DD> | Last updated: <YYYY-MM-DD>

## Fingerprint (how a run recognises data from this instrument)

- File format and extension (e.g. .txt two-column, .wdf, .spc, .csv export):
- Header fields or instrument name in the files:
- Laser lines seen in the data:
- Spectral range and point spacing (cm-1):
- Other identifying metadata (file naming pattern, exporting software):

## Configuration

- Lasers (nm) and power at the sample (measured or nominal; say which):
- Grating(s) (lines/mm) and resolution (cm-1):
- Objective (magnification, NA), spot size:
- Detector (CCD model, cooling):
- Polarization optics (analyser, half-wave plate, geometry: parallel / crossed / rotating sample):
- Sample environment (cryostat, magnet, window material, vacuum, heater):
- Low-wavenumber cutoff (notch, edge or Bragg filters):

## Calibration routine

Standard used (Si wafer, neon lamp, ...), how often, reference value with its source. Each measurement goes in
`calibration.json`.

## Known artifacts and caveats

<!-- One entry each: what (spurious line, filter ghost, plasma line, window band, etaloning, background),
position in cm-1, how to recognise it, how to handle it, dataset and date first seen, later sightings. -->

## Analysis defaults that work here

<!-- Fit windows, MIN_SNR, despiking threshold, baseline settings, with the run that showed they work. -->

## Open questions

<!-- Unknown fields above, and what to ask the user next time. -->
