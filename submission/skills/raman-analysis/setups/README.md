# Setups: instrument-specific knowledge

One folder per instrument (spectrometer, cryostat stage, transport rig). A setup holds what is true of that
instrument and not of the technique: its artifacts, calibration history and analysis defaults. These are measured
facts, so they need a dataset and a date, not a paper, and they never go into `reference/`.

## Finding the setup at the start of a run

1. Read the fingerprint section of every `*/setup.md` and compare it with the data files (format, header fields,
   instrument name, laser lines or excitation, axis spacing, range).
2. One match: read that `setup.md` and `calibration.json` and apply its caveats and defaults.
3. No match or several: ask the user which instrument was used. Unattended: state the assumption under limits.
4. New instrument: copy `_template/` to `<setup-id>/` (short lowercase id, e.g. `lab-renishaw-532`), fill what the
   files and the user tell you, write `unknown` for the rest.

## Writing to a setup

- An artifact or offset seen once with clear evidence (a line in a blank spectrum, the Si line off its reference)
  is written at once, with dataset and date.
- Every measurement of a calibration standard goes into `calibration.json`, so later runs can tell drift from a
  real shift.
- An item seen on two different setups is probably about the technique: add it to `learned/inbox.md` as well.

Setup folders describe a lab's instruments. Ask the user before sharing the skill publicly with them included.
