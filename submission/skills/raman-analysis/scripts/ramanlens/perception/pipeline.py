"""One-call perception pipeline for a single Raman spectrum: spikes, baseline, peaks, substrate line.

The agent tools, the library matcher and the evaluation all need the same sequence of steps on a raw spectrum,
in the same order and with the same defaults, so the sequence lives here once. The pipeline also handles two
things the individual steps do not know about: the laser line and edge-filter region at the low-shift end, and
the silicon substrate line, which is a real band but does not belong to the sample.

Input: a Spectrum (shift in cm-1, intensity, metadata). Optional metadata keys: `substrate` (free text, such as
"SiO2/Si") and `min_shift_cm1` (lowest shift to analyse).
Process: if the axis reaches the laser line (shifts below 10 cm-1), everything below `min_shift_cm1` (default 50)
is excluded, because the Rayleigh line and the notch or edge filter produce bands there. On the rest, cosmic-ray
spikes are removed (preprocess.remove_spikes), an asymmetric least squares baseline is estimated
(preprocess.baseline_als) and peaks are fitted (fit.fit_peaks); fitted features wider than 100 cm-1, or wider than
50 cm-1 and below 5 % of the strongest band, are treated as leftover background. A narrow band at 520.7 +- 2 cm-1 is flagged as
the Si substrate line unless the metadata name a substrate without silicon.
Output: a SpectrumAnalysis with the peak table (.peaks, each a fit.Peak with .is_substrate), spike positions
(.spikes), the baseline on the input axis (.baseline, NaN in the excluded region), the cleaned intensity and
human-readable notes on every automatic decision.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

from ramanlens.perception.fit import Peak, fit_peaks
from ramanlens.perception.io import Spectrum
from ramanlens.perception.preprocess import baseline_als, remove_spikes

# The axis contains the laser line if it reaches below this shift (cm-1).
LASER_LINE_REACH_CM1 = 10.0
# Default lower analysis limit when the laser line is in range. Edge filters typically block up to 50 to 100 cm-1;
# 50 keeps low-frequency modes such as Bi2Se3 near 70 cm-1 while dropping the filter-edge artefacts.
DEFAULT_MIN_SHIFT_CM1 = 50.0
# Silicon zone-centre optical phonon. 520.7 cm-1 is the conventional room-temperature calibration value; papers
# report it within about +-1 cm-1 of that (520 cm-1 in Lee et al. 2010, ACS Nano 4, 2695; 520.9 cm-1 at 514 nm in
# Castellanos-Gomez et al. 2014, arXiv 1403.0499, p. 7), hence the +-2 cm-1 window.
SI_LINE_CM1 = 520.7
SI_WINDOW_CM1 = 2.0
# Crystalline Si gives a narrow line (a few cm-1 FWHM at room temperature); a broad band at the same position is
# more likely the sample's own mode and is not flagged.
SI_MAX_FWHM_CM1 = 8.0
# Fitted features wider than this are treated as background the baseline did not absorb (for example the slow
# ripple an ALS baseline leaves around a strong band on noise-free data), not as Raman bands. Design assumption:
# the bands this toolkit targets (crystalline layered materials, graphene D, G, 2D) are well below 100 cm-1 wide.
MAX_BAND_FWHM_CM1 = 100.0
# A feature that is both broad and weak is also treated as baseline residue: wider than WEAK_BROAD_FWHM_CM1 and
# below WEAK_BROAD_REL_HEIGHT of the strongest band. An ALS baseline sagging between two strong bands leaves such a
# hump (a 1467 cm-1 bump of FWHM 89 at 2 % of the G height between graphene D and G on a synthetic dev case).
# Design assumption, not a literature value: first- and second-order bands of the target materials are narrower
# than 50 cm-1 or, when broader (amorphous carbon), not this weak. Both kinds are listed in the notes.
WEAK_BROAD_FWHM_CM1 = 50.0
WEAK_BROAD_REL_HEIGHT = 0.05

# Matches "Si" as a word (SiO2/Si, Si wafer) or "silicon" (black silicon), but not "SiO2" alone or "SiC".
_SILICON = re.compile(r"(?<![A-Za-z])si(?![A-Za-z0-9])|silicon", re.IGNORECASE)


# @dataclass generates the constructor and repr from the fields: the result is a plain record the tools serialize.
@dataclass
class SpectrumAnalysis:
    """Result of analyze_spectrum. Arrays are on the input shift axis x (ascending)."""

    x: np.ndarray
    y_clean: np.ndarray
    baseline: np.ndarray
    peaks: list[Peak]
    spikes: list[float]
    min_shift_cm1: float | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def sample_peaks(self) -> list[Peak]:
        """Peaks that belong to the sample, i.e. without the flagged substrate line."""
        return [p for p in self.peaks if not p.is_substrate]

    def to_dict(self) -> dict:
        """Peak table and decisions as plain JSON-ready types (arrays are left out)."""
        return {"peaks": [p.to_dict() for p in self.peaks], "spikes_cm1": list(self.spikes),
                "min_shift_cm1": self.min_shift_cm1, "notes": list(self.notes)}


def substrate_may_be_silicon(substrate) -> bool:
    """True when the substrate text is missing or mentions silicon; False for a named non-silicon substrate."""
    if substrate is None or not str(substrate).strip():
        return True
    return bool(_SILICON.search(str(substrate)))


def flag_si_substrate(peaks: list[Peak], substrate=None) -> Peak | None:
    """Mark at most one peak as the Si substrate line (in place) and return it, or None.

    The candidate must lie within SI_WINDOW_CM1 of SI_LINE_CM1 and be narrower than SI_MAX_FWHM_CM1; among
    several candidates the strongest is taken.
    """
    if not substrate_may_be_silicon(substrate):
        return None
    cands = [p for p in peaks if abs(p.position - SI_LINE_CM1) <= SI_WINDOW_CM1 and p.fwhm <= SI_MAX_FWHM_CM1]
    if not cands:
        return None
    si = max(cands, key=lambda p: p.height)
    si.is_substrate = True
    return si


def analyze_spectrum(spectrum: Spectrum, min_shift_cm1: float | None = None, min_snr: float = 5.0) -> SpectrumAnalysis:
    """Run spike removal, baseline, peak fitting and substrate flagging on one spectrum.

    min_shift_cm1: lowest shift analysed. None means: metadata `min_shift_cm1` if present, else
    DEFAULT_MIN_SHIFT_CM1 when the axis reaches the laser line, else no limit. min_snr is passed to fit_peaks.
    """
    meta = spectrum.meta or {}
    order = np.argsort(spectrum.x)
    x = np.asarray(spectrum.x, dtype=float)[order]
    y = np.asarray(spectrum.y, dtype=float)[order]
    notes: list[str] = []

    if min_shift_cm1 is None:
        min_shift_cm1 = meta.get("min_shift_cm1")
    if min_shift_cm1 is None and x.size and x[0] < LASER_LINE_REACH_CM1:
        min_shift_cm1 = DEFAULT_MIN_SHIFT_CM1
        notes.append(f"axis reaches the laser line (starts at {x[0]:.1f} cm-1); shifts below "
                     f"{min_shift_cm1:.0f} cm-1 excluded (Rayleigh line and filter edge)")
    keep = x >= min_shift_cm1 if min_shift_cm1 is not None else np.ones(x.size, dtype=bool)

    xs = x[keep]
    y_clean = y.copy()
    baseline = np.full(x.size, np.nan)
    peaks: list[Peak] = []
    spikes: list[float] = []
    if xs.size >= 7:
        ys_clean, spikes = remove_spikes(xs, y[keep])
        base = baseline_als(ys_clean)
        # ALS weights points below the curve heavily, so on noisy data it settles on the lower noise envelope,
        # several noise sigmas below the noise centre, which biases heights and widths of weak bands. Shift it up by
        # the median residual of band-free points (those within 3 sigma of the residual median).
        r = ys_clean - base
        sigma = np.median(np.abs(np.diff(r))) / 0.6745 / np.sqrt(2)
        quiet = np.abs(r - np.median(r)) < 3 * sigma
        if sigma > 0 and quiet.sum() > 10:
            base = base + float(np.median(r[quiet]))
        y_clean[keep] = ys_clean
        baseline[keep] = base
        peaks = fit_peaks(xs, ys_clean, baseline=base, min_snr=min_snr)
        strongest = max((p.height for p in peaks), default=0.0)
        broad = [p for p in peaks if p.fwhm > MAX_BAND_FWHM_CM1
                 or (p.fwhm > WEAK_BROAD_FWHM_CM1 and p.height < WEAK_BROAD_REL_HEIGHT * strongest)]
        if broad:
            peaks = [p for p in peaks if p not in broad]
            notes.append("broad background feature(s) not reported as bands: " + ", ".join(
                f"{p.position:.0f} cm-1 (FWHM {p.fwhm:.0f})" for p in broad))
    else:
        notes.append("fewer than 7 points in the analysed range; no peaks fitted")
    if spikes:
        notes.append(f"{len(spikes)} cosmic-ray spike(s) removed at " + ", ".join(f"{s:.1f}" for s in spikes) + " cm-1")

    substrate = meta.get("substrate")
    si = flag_si_substrate(peaks, substrate)
    if si is not None:
        origin = f"substrate given as {substrate!r}" if substrate else "substrate not stated, Si assumed"
        notes.append(f"peak at {si.position:.1f} cm-1 (FWHM {si.fwhm:.1f}) flagged as the Si substrate line ({origin})")

    return SpectrumAnalysis(x=x, y_clean=y_clean, baseline=baseline, peaks=peaks, spikes=spikes,
                            min_shift_cm1=min_shift_cm1, notes=notes)
