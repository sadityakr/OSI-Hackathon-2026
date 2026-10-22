"""Raman analysis of six CrSBr flakes (Marimo notebook).

Built from the raman-analysis skill template. Cells marked FILL carry the sample description, literature values,
interpretation and references; every other cell computes from the data. Run check:
    marimo export html raman_analysis.py -o raman_analysis.html
"""

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Raman analysis")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from ramanlens.perception.io import Spectrum, read_spectrum
    from ramanlens.perception.pipeline import analyze_spectrum

    SI_REFERENCE_CM1 = 520.7  # crystalline Si first-order line at room temperature
    return SI_REFERENCE_CM1, Spectrum, analyze_spectrum, mo, np, plt, read_spectrum


@app.cell
def _():
    # FILL 1/6: sample, conditions and data. Values the user did not give go into "assumed".
    SAMPLE = {
        "material": "CrSBr (six exfoliated flakes, same crystal)",
        "substrate": "SiO2/Si",
        "laser_nm": 532,
        "temperature_K": 295,
        "question": "How thick is each of the six flakes?",
        "assumed": [
            "Substrate SiO2/Si (not stated; standard for exfoliated CrSBr). It sets thin-film interference of the Ag2/Ag3 intensity ratio.",
            "Unpolarized or unknown polarization relative to the a/b axes: Ag2 is polarization and energy dependent, so only positions and widths are used, not intensity ratios.",
            "Spectra window is 51 to 431 cm-1 with no Si line, so no per-spectrum calibration offset can be measured; the 1.2 cm-1 point spacing limits shift precision.",
        ],
    }
    # (label, file relative to this notebook, value of the series variable or None when unknown)
    SPECTRA = [
        ("A", "spectrum_A.csv", None),
        ("B", "spectrum_B.csv", None),
        ("C", "spectrum_C.csv", None),
        ("D", "spectrum_D.csv", None),
        ("E", "spectrum_E.csv", None),
        ("F", "spectrum_F.csv", None),
    ]
    SERIES = {"name": "flake", "unit": ""}
    # Bands to track: name -> (low, high) search window in cm-1, taken from the material note.
    BANDS = {
        "Ag1": (100.0, 120.0),
        "Ag2": (232.0, 252.0),
        "B2g/resonant ~302": (294.0, 310.0),
        "Ag3": (335.0, 350.0),
    }
    MIN_SNR = 3.0  # detection threshold in noise units for the windowed band fits
    return BANDS, MIN_SNR, SAMPLE, SERIES, SPECTRA


@app.cell
def _():
    # FILL 2/6: what the literature reports for this system. Values read from Torres Fig. 1h are about +-1 cm-1.
    LIT_VALUES = [
        {"quantity": "Ag1, 1L (1.58 eV)", "band": "Ag1", "reported_cm1": 106.7, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag1, 2L (1.58 eV)", "band": "Ag1", "reported_cm1": 111.0, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag1, 3L (1.58 eV)", "band": "Ag1", "reported_cm1": 112.7, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag1, 4L to 5L (1.58 eV)", "band": "Ag1", "reported_cm1": 113.4, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag1, bulk (1.58 eV)", "band": "Ag1", "reported_cm1": 113.9, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag2, 1L (1.58 eV)", "band": "Ag2", "reported_cm1": 240.8, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag2, 2L (1.58 eV)", "band": "Ag2", "reported_cm1": 243.3, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag2, 3L to bulk (1.58 eV)", "band": "Ag2", "reported_cm1": 244.5, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag3, all N (1.58 eV)", "band": "Ag3", "reported_cm1": 343.5, "uncertainty_cm1": 1.0,
         "source": "Torres et al. 2022", "locator": "read from Fig. 1h", "ref": 1},
        {"quantity": "Ag1, 4L (2.33 eV)", "band": "Ag1", "reported_cm1": 114.0, "uncertainty_cm1": 1.0,
         "source": "Mondal et al. 2025", "locator": "p.2 (skill note, not reopened)", "ref": 2},
        {"quantity": "Ag2, 4L (2.33 eV)", "band": "Ag2", "reported_cm1": 244.0, "uncertainty_cm1": 1.0,
         "source": "Mondal et al. 2025", "locator": "p.2 (skill note, not reopened)", "ref": 2},
        {"quantity": "Ag3, 4L (2.33 eV)", "band": "Ag3", "reported_cm1": 344.0, "uncertainty_cm1": 1.0,
         "source": "Mondal et al. 2025", "locator": "p.2 (skill note, not reopened)", "ref": 2},
    ]
    # Published figures you opened with iopic-bond view_figure (use its image_path).
    FIGURES = [
        {"image_path": "C:/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/data/raw/iopic-bond/papers/2212.01754/parsed/12572f6bdc3223ca/figures/fig1.png",
         "caption": "Torres 2022, Fig. 1g-h: layer-dependent Raman spectra (1.58 eV) and Ag mode positions versus layer number", "ref": 1},
    ]
    return FIGURES, LIT_VALUES


@app.cell
def _(SAMPLE, SERIES, SPECTRA, mo):
    _assumed = "\n".join(f"- {a}" for a in SAMPLE["assumed"]) or "- none"
    mo.md(f"""
    # Raman analysis: {SAMPLE['material']}

    **Question.** {SAMPLE['question']}

    **Conditions.** substrate {SAMPLE['substrate']}, laser {SAMPLE['laser_nm']} nm, {SAMPLE['temperature_K']} K,
    {len(SPECTRA)} spectra, series variable: {SERIES['name']} {('(' + SERIES['unit'] + ')') if SERIES['unit'] else ''}

    **Assumed.**
    {_assumed}
    """)
    return


@app.cell
def _(SPECTRA, mo, np, plt, read_spectrum):
    spectra = {}
    for _label, _file, _v in SPECTRA:
        spectra[_label] = read_spectrum(mo.notebook_dir() / _file)

    _fig, _ax = plt.subplots(figsize=(9, 4.5))
    _off = 0.0
    for _label, _s in spectra.items():
        _y = (_s.y - np.min(_s.y)) / (np.ptp(_s.y) or 1.0)
        _ax.plot(_s.x, _y + _off, lw=0.8, label=_label)
        _off += 1.1
    _ax.set_xlabel("Raman shift (cm$^{-1}$)")
    _ax.set_ylabel("normalized intensity, offset")
    _ax.legend(fontsize=7, loc="upper right")
    _ax.set_title("1. Raw spectra")
    _fig.tight_layout()
    _fig
    return (spectra,)


@app.cell
def _(SAMPLE, SI_REFERENCE_CM1, Spectrum, analyze_spectrum, mo, np, spectra):
    # 2. Quality: spikes and Si calibration offset per spectrum (offset = fitted Si line - 520.7 cm-1).
    full = {}
    si_offset = {}
    _rows = []
    for _label, _s in spectra.items():
        _s.meta = {**(_s.meta or {}), "substrate": SAMPLE["substrate"]}
        _r = analyze_spectrum(_s)
        full[_label] = _r
        _off = None
        _m = (_s.x >= 505) & (_s.x <= 535)
        if "si" in str(SAMPLE["substrate"]).lower() and _m.sum() > 10:
            _rs = analyze_spectrum(Spectrum(_s.x[_m], _s.y[_m], {}), min_snr=5)
            _si = [p for p in _rs.peaks if 515 <= p.position <= 525]
            if _si:
                _off = max(_si, key=lambda p: p.height).position - SI_REFERENCE_CM1
        si_offset[_label] = _off
        _rows.append({
            "spectrum": _label,
            "range (cm-1)": f"{_s.x.min():.0f} to {_s.x.max():.0f}",
            "step (cm-1)": round(float(np.median(np.diff(_s.x))), 2),
            "spikes removed": len(_r.spikes),
            "Si offset (cm-1)": None if _off is None else round(_off, 2),
            "notes": "; ".join(_r.notes),
        })
    mo.vstack([mo.md("## 2. Quality and calibration"), mo.ui.table(_rows, selection=None, page_size=max(10, len(_rows)))])
    return full, si_offset


@app.cell
def _(BANDS, MIN_SNR, SERIES, SPECTRA, Spectrum, analyze_spectrum, mo, si_offset, spectra):
    # 3. Band tracking: each band is refitted in its own window (resolves weak or broad bands that a
    # full-spectrum fit merges), and corrected by the Si offset when one was measured.
    _values = {lab: v for lab, _f, v in SPECTRA}
    track = []
    for _label, _s in spectra.items():
        for _band, (_lo, _hi) in BANDS.items():
            _m = (_s.x >= _lo - 15) & (_s.x <= _hi + 15)
            _row = {"spectrum": _label, SERIES["name"]: _values[_label], "band": _band}
            if _m.sum() > 10:
                _r = analyze_spectrum(Spectrum(_s.x[_m], _s.y[_m], {}), min_snr=MIN_SNR)
                _pk = [p for p in _r.peaks if _lo <= p.position <= _hi]
                if _pk:
                    _p = max(_pk, key=lambda p: p.height)
                    _off = si_offset[_label] or 0.0
                    _row.update({
                        "position": round(_p.position - _off, 2),
                        "err": round(_p.position_err or 0.0, 2),
                        "fwhm": round(_p.fwhm, 2),
                        "height": round(_p.height, 1),
                        "Si corrected": si_offset[_label] is not None,
                    })
            track.append(_row)

    def pos(label, band):
        """Tracked position of a band as text, for use in the interpretation cell."""
        for _t in track:
            if _t["spectrum"] == label and _t["band"] == band and "position" in _t:
                return f"{_t['position']:.1f} +- {max(_t['err'], 0.1):.1f} cm-1"
        return "not resolved"

    def fwhm(label, band):
        """Tracked FWHM of a band as text."""
        for _t in track:
            if _t["spectrum"] == label and _t["band"] == band and "fwhm" in _t:
                return f"{_t['fwhm']:.1f} cm-1"
        return "n/a"

    mo.vstack([mo.md("## 3. Tracked bands (windowed fits, fit errors only; add calibration uncertainty)"),
               mo.ui.table(track, selection=None, page_size=max(10, len(track)))])
    return fwhm, pos, track


@app.cell
def _(BANDS, SERIES, mo, plt, track):
    _fig, _axes = plt.subplots(1, len(BANDS), figsize=(3.2 * len(BANDS), 3.2), squeeze=False)
    for _ax, _band in zip(_axes[0], BANDS):
        _pts = [t for t in track if t["band"] == _band and "position" in t]
        _has_v = all(t[SERIES["name"]] is not None for t in _pts)
        _pts = sorted(_pts, key=lambda t: t[SERIES["name"]] if _has_v else t["position"])
        _xs = [t[SERIES["name"]] for t in _pts] if _has_v else list(range(len(_pts)))
        _ax.errorbar(_xs, [t["position"] for t in _pts], yerr=[max(t["err"], 0.1) for t in _pts], fmt="o", ms=4)
        if not _has_v:
            _ax.set_xticks(_xs, [t["spectrum"] for t in _pts], rotation=45, fontsize=7)
        _ax.set_title(_band)
        _ax.set_ylabel("position (cm$^{-1}$)")
        _ax.set_xlabel(f"{SERIES['name']} {SERIES['unit']}".strip() + ("" if _has_v else ", sorted by position"))
    _fig.tight_layout()
    mo.vstack([mo.md("## 4. Band positions across the series"), _fig])
    return


@app.cell
def _(FIGURES, LIT_VALUES, mo, track):
    # 5. What the literature reports for this system, next to the measured values.
    _rows = []
    for _lv in LIT_VALUES:
        _meas = [t["position"] for t in track if t["band"] == _lv["band"] and "position" in t]
        _rows.append({
            "quantity": _lv["quantity"],
            "reported (cm-1)": f"{_lv['reported_cm1']} +- {_lv['uncertainty_cm1']}",
            "source": f"[{_lv['ref']}] {_lv['source']}, {_lv['locator']}",
            "measured range (cm-1)": f"{min(_meas):.1f} to {max(_meas):.1f}" if _meas else "not resolved",
        })
    _figs = [mo.vstack([mo.image(f["image_path"], width=420), mo.md(f"*{f['caption']}* [{f['ref']}]")])
             for f in FIGURES]
    mo.vstack([
        mo.md("## 5. What the literature reports for this system"),
        mo.ui.table(_rows, selection=None, page_size=max(10, len(_rows))),
        mo.hstack(_figs, wrap=True) if _figs else mo.md("*No published figure opened in this session.*"),
    ])
    return


@app.cell
def _(mo):
    # FILL 3/6: method notes.
    mo.md("""
    ## 6. Method notes
    - Lorentzian line shapes on an asymmetric least squares baseline (Eilers and Boelens 2005).
    - Layer number is read from the layer-dependent redshift of Ag1 and Ag2 with Ag3 as a layer-independent internal reference, the observable Torres et al. use [1]; they and Ye et al. caution that layer number is better fixed by optical contrast or AFM [3].
    """)
    return


@app.cell
def _(mo, track):
    # Ag2 minus Ag1 spacing per flake: a rigid calibration offset cancels in this difference, so it is the
    # most robust thickness observable available without a Si line in the window.
    def _get(label, band, key):
        for _t in track:
            if _t["spectrum"] == label and _t["band"] == band and key in _t:
                return _t[key]
        return None

    spacing = {}
    _rows = []
    for _label in sorted({t["spectrum"] for t in track}):
        _a1, _a2, _a3 = (_get(_label, b, "position") for b in ("Ag1", "Ag2", "Ag3"))
        _e1, _e2 = (_get(_label, b, "err") for b in ("Ag1", "Ag2"))
        spacing[_label] = None if None in (_a1, _a2) else _a2 - _a1
        _rows.append({
            "flake": _label,
            "Ag2-Ag1 (cm-1)": None if spacing[_label] is None else round(spacing[_label], 2),
            "fit err (cm-1)": None if _e1 is None or _e2 is None else round((_e1**2 + _e2**2) ** 0.5, 2),
            "Ag3 (cm-1)": _a3,
            "Ag1 FWHM": _get(_label, "Ag1", "fwhm"),
        })
    mo.vstack([mo.md("## 4b. Ag2 minus Ag1 spacing (calibration-independent)"),
               mo.ui.table(_rows, selection=None, page_size=10)])
    return (spacing,)


@app.cell
def _(fwhm, mo, pos, spacing):
    # FILL 4/6: interpretation. Numbers come from the fits through pos(), fwhm() and spacing.
    def _sp(k):
        return f"{spacing[k]:.1f} cm-1" if spacing[k] is not None else "n/a"

    mo.md(f"""
    ## 7. Interpretation
    - [measured] Flakes B and D show narrow Ag1/Ag2 (Ag1 FWHM {fwhm("B", "Ag1")} and {fwhm("D", "Ag1")}) at Ag1 {pos("B", "Ag1")} and {pos("D", "Ag1")}, Ag2 {pos("B", "Ag2")} and {pos("D", "Ag2")}, giving Ag2-Ag1 = {_sp("B")} and {_sp("D")}. [literature] Ag1 saturates near 113 to 114 cm-1 and Ag2 near 244 to 245 cm-1 from about 3L to bulk (Torres Fig. 1h, read off, about +-1 cm-1) [1]; 4L at 2.33 eV is 114 / 244 [2]. Reading: **B and D are bulk-like, at least about 4 layers; Raman cannot give an upper bound**, because both modes are flat above that. Confidence: moderate.
    - [measured] Flake F: Ag1 {pos("F", "Ag1")}, Ag2 {pos("F", "Ag2")}, spacing {_sp("F")}, about 0.7 to 0.9 cm-1 larger than B and D (fit error about 0.1 cm-1, same excitation and settings). [inferred] F is thinner than B and D. Against Torres Fig. 1h (spacing read off: 2L about 132.3, 3L about 131.6, 4L about 131.4, bulk about 130.7 cm-1) [1] it sits at about 3L to 4L, but the whole 3L to bulk range is only about 1 cm-1 wide, comparable to the +-1 cm-1 read-off error. Best estimate 3L (range 2L to bulk). Confidence: low to moderate.
    - [measured] Flake A: Ag1 {pos("A", "Ag1")} (FWHM {fwhm("A", "Ag1")}, about twice the others), Ag2 {pos("A", "Ag2")}, spacing {_sp("A")}. [literature] 1L about 134.1 and 2L about 132.3 cm-1 spacing, Ag1 106.7 (1L) and 111 (2L) [1]. Reading: **A is the thinnest, 1L to 2L, best estimate 2L**. 1L vs 2L is not separated by this data. Confidence: low to moderate.
    - [measured] Flakes C and E give Ag1 {pos("C", "Ag1")} and {pos("E", "Ag1")}, Ag2 {pos("C", "Ag2")} and {pos("E", "Ag2")}, all broad (Ag1 FWHM {fwhm("C", "Ag1")} and {fwhm("E", "Ag1")}) with a broad band near 302 cm-1 and broad humps at 80 to 110 cm-1. Spacing {_sp("C")} and {_sp("E")} exceeds the 1L value of about 134.1 cm-1 [1], and Ag1 lies below 1L (106.7), which no layer number explains. **Thickness is not determinable for C and E from these spectra.**
    - [literature] Candidate explanation for C and E: surface defect mode D1 5 to 10 cm-1 below Ag1, strongest in thin flakes and growing with air exposure, which merges with Ag1 and drags the fitted position down [1]; defect and resonant modes near 300 cm-1 are reported along b [1]. This is a hypothesis; it is not tested here.
    - [measured] Ag3 should be nearly layer independent at about 343.5 to 344 cm-1 [1, 2], but here it ranges over {pos("E", "Ag3")} (E) to {pos("B", "Ag3")} (B), with D {pos("D", "Ag3")}, F {pos("F", "Ag3")}, A {pos("A", "Ag3")}, C {pos("C", "Ag3")}. [inferred] A spread of about 2.7 cm-1 is far more than thickness explains, so flake-to-flake calibration, heating or strain differences of at least 1 to 3 cm-1 are possible. That is why absolute positions are not used alone and the spacing is preferred; if the Ag3 deficit were a rigid calibration offset, F would move toward bulk-like.
    - [inferred] Ranking from thinnest to thickest by the calibration-independent spacing: A < F < D about B; C and E unplaced. Absolute layer numbers rest on a figure measured at 1.58 eV [1] compared with data at 2.33 eV; the two published 4L/bulk sets differ by about 1 to 1.4 cm-1 in spacing [1, 2].
    """)
    return


@app.cell
def _(mo):
    # FILL 5/6: limits and questions for the user.
    mo.md("""
    ## 8. Limits and questions
    - Raman gives layer number only up to about 4L: Ag1 and Ag2 are flat from about 3L to bulk, so B and D can be 4L or 50 nm. Optical contrast or AFM step height is the decisive measurement; Torres and Ye both rely on it [1, 3].
    - No Si line in the 51 to 431 cm-1 window, so calibration offsets are unmeasured. Ag3 scatters by about 2.7 cm-1 between flakes. A Si 520.7 cm-1 reference in each spectrum would settle whether absolute positions can be used.
    - Reference positions were read from a 1.58 eV (resonant) figure [1]; these data are 2.33 eV. A 2.33 eV thickness series on AFM-characterised flakes would remove that mismatch.
    - Polarization relative to a/b is unknown. Ag2 intensity depends on it and on laser energy [2], so intensity ratios were not used.
    - C and E (broad, weak Ag1/Ag2, 302 cm-1 band) need a fresh-spot spectrum, a longer-air-exposure comparison and AFM; the degradation hypothesis is untested.
    - Questions: substrate and oxide thickness? Which flakes were measured in air for how long? Laser power (heating)? Do you have optical contrast or AFM for any of them?
    """)
    return


@app.cell
def _(mo):
    # FILL 6/6: references.
    mo.md("""
    ## References
    1. Torres et al., 2022, Probing defects and spin-phonon coupling in CrSBr via resonant Raman scattering, arXiv:2212.01754. [link](https://arxiv.org/abs/2212.01754)
    2. Mondal et al., 2025, npj 2D Mater., arXiv:2410.22164 (values from the skill's CrSBr note, p.2; paper not reopened). [link](https://arxiv.org/abs/2410.22164)
    3. Ye et al., 2022, ACS Nano 16, 11876 (cited from the skill's CrSBr note, journal p.5-6; paper not opened). [link](https://doi.org/10.1021/acsnano.2c01151)
    """)
    return


if __name__ == "__main__":
    app.run()
