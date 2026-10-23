"""Raman skill analysis notebook template (Marimo).

Built by the literature-in-the-loop meta skill for the raman-analysis skill. The analysing agent copies this file
next to the data as raman_analysis.py and edits ONLY the cells marked FILL. Every other cell computes from the
data, so every number in the interpretation can be traced to a cell. Every cell is hide_code=True, so the
notebook opens as a report; the code stays one click away in `marimo edit`. Run check:
    marimo export html raman_analysis.py -o raman_analysis.html --no-include-code
"""

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Raman analysis")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from ramanlens.perception.io import Spectrum, read_spectrum
    from ramanlens.perception.pipeline import analyze_spectrum

    SI_REFERENCE_CM1 = 520.7  # crystalline Si first-order line at room temperature
    return SI_REFERENCE_CM1, Spectrum, analyze_spectrum, mo, np, plt, read_spectrum


@app.cell(hide_code=True)
def _():
    # FILL 1/8: sample, conditions and data. Values the user did not give go into "assumed".
    SAMPLE = {
        "material": "MATERIAL",
        "substrate": "SiO2/Si",
        "laser_nm": 532,
        "temperature_K": 295,
        "question": "What the user asked, in one sentence.",
        "assumed": ["Conditions you assumed because they were missing, and why they matter."],
        # Folder name under the skill's setups/, or "unknown"; and the caveats from its setup.md that apply here.
        "setup": "unknown",
        "setup_caveats": [],
    }
    # (label, file relative to this notebook, value of the series variable or None when unknown)
    SPECTRA = [
        ("sample 1", "spectrum_1.csv", None),
    ]
    SERIES = {"name": "sample", "unit": ""}  # e.g. {"name": "temperature", "unit": "K"}
    # Bands to track: name -> (low, high) search window in cm-1, taken from the material note.
    BANDS = {
        "band 1": (100.0, 130.0),
    }
    MIN_SNR = 3.0  # detection threshold in noise units for the windowed band fits
    return BANDS, MIN_SNR, SAMPLE, SERIES, SPECTRA


@app.cell(hide_code=True)
def _():
    # FILL 2/8: what the literature reports for this system. One row per reported number you will compare with.
    # band: a key of BANDS or None; reported_cm1: the value; locator: figure or table, "read from Fig. N" when
    # read off a plot (about +-1 cm-1); ref: number in the reference list.
    LIT_VALUES = [
        {"quantity": "band 1 position, condition", "band": "band 1", "reported_cm1": 0.0, "uncertainty_cm1": 1.0,
         "source": "Author et al. YEAR", "locator": "Fig. N", "ref": 1},
    ]
    # Published figures you opened with lit-pic view_figure (use its image_path).
    FIGURES = [
        # {"image_path": "C:/.../fig_1.png", "caption": "Author YEAR, Fig. N: what it shows", "ref": 1},
    ]
    return FIGURES, LIT_VALUES


@app.cell(hide_code=True)
def _(SAMPLE, SERIES, SPECTRA, mo):
    _assumed = "\n".join(f"- {a}" for a in SAMPLE["assumed"]) or "- none"
    _caveats = "\n".join(f"- {c}" for c in SAMPLE.get("setup_caveats", [])) or "- none recorded"
    mo.md(f"""
    # Raman analysis: {SAMPLE['material']}

    **Question.** {SAMPLE['question']}

    **Conditions.** substrate {SAMPLE['substrate']}, laser {SAMPLE['laser_nm']} nm, {SAMPLE['temperature_K']} K,
    {len(SPECTRA)} spectra, series variable: {SERIES['name']} {('(' + SERIES['unit'] + ')') if SERIES['unit'] else ''}

    **Assumed.**
    {_assumed}

    **Setup.** {SAMPLE.get('setup', 'unknown')}; caveats that apply:
    {_caveats}
    """)
    return


@app.cell(hide_code=True)
def _(mo, pos):
    # FILL 8/8, written LAST (after the interpretation) but shown here: the TL;DR for a human or agent who reads
    # nothing else. Three to five bullets: the answer to the question, the key numbers through pos(label, band),
    # the confidence and what it rests on, the main caveat, the next measurement. Same tags as the interpretation;
    # nothing here that is not in sections 4 to 8.
    mo.callout(mo.md(f"""
    **TL;DR**

    - [measured] ANSWER to the question, with band 1 in sample 1 at {pos("sample 1", "band 1")}.
    - Confidence: high / moderate / low, because REASON. Main caveat: CAVEAT. Next measurement: MEASUREMENT.
    """), kind="info")
    return


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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

    mo.vstack([mo.md("## 3. Tracked bands (windowed fits, fit errors only; add calibration uncertainty)"),
               mo.ui.table(track, selection=None, page_size=max(10, len(track)))])
    return pos, track


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
def _(mo):
    # FILL 3/8: method notes. Each analysis choice that came from the literature, with its reference number.
    mo.md("""
    ## 6. Method notes
    - Lorentzian line shapes on an asymmetric least squares baseline (Eilers and Boelens 2005).
    - CHOICE, and why, [ref]
    """)
    return


@app.cell(hide_code=True)
def _(mo, pos):
    # FILL 4/8: interpretation. Five to ten bullets, most likely reading first. Each bullet: one claim, its tag
    # [measured] / [inferred] / [literature] / [learned] (a promoted run observation, with its CHANGELOG date), the number it rests on (use pos(label, band) so the number comes
    # from the fit), and the reference number. Then alternatives and the measurement that would decide.
    mo.md(f"""
    ## 7. Interpretation
    - [measured] CLAIM: band 1 in sample 1 at {pos("sample 1", "band 1")}.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # FILL 5/8: limits and questions for the user.
    mo.md("""
    ## 8. Limits and questions
    - What the data cannot tell, and the measurement that would.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # FILL 6/8: references. Only papers opened this session or cited with a locator in the skill's notes.
    mo.md("""
    ## References
    1. Authors, YEAR, Title, Journal or arXiv. [link](https://arxiv.org/abs/ID)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # FILL 7/8: skill updates from this run (learned/README.md in the skill). Each item: where it went
    # (setups/<id>/setup.md, learned/inbox.md, or a promoted note) and one line on what. "none" when the run
    # added nothing or SKILL_LEARNING=off.
    mo.md("""
    ## Skill updates from this run
    - none
    """)
    return


if __name__ == "__main__":
    app.run()
