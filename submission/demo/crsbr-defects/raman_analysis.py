"""Raman skill analysis notebook template (Marimo).

Built by the literature-in-the-loop meta skill for the raman-analysis skill. The analysing agent copies this file
next to the data as raman_analysis.py and edits ONLY the cells marked FILL. Every other cell computes from the
data, so every number in the interpretation can be traced to a cell. Run check:
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
        "material": "CrSBr, 4 layers",
        "substrate": "SiO2/Si",
        "laser_nm": 532,
        "temperature_K": 295,
        "question": "What changed in the Raman spectra of a 4L CrSBr flake across three processing steps "
                    "(E along a and along b), and is the material still good for a device?",
        "assumed": [
            "Laser 532 nm (2.33 eV) and room temperature: not given. Inferred from Ag2 being strongest along a and "
            "Ag1/Ag3 along b, which is the 2.33 eV pattern [2]; at 1.96 eV Ag2 would also be along b. This matters "
            "because the defect modes are resonantly enhanced at 1.58 eV [1] and may be weaker here.",
            "Step 0 is the untreated flake and steps 1 to 3 are cumulative. What each step was (heating, water, "
            "ion irradiation, lithography, ...) is not given, so mechanisms are not assigned to steps.",
            "Step 0 was taken with a different instrument setting: its Si line is 9 cm-1 wide against 3.7 cm-1 for "
            "steps 1 to 3 (see section 2). Step 0 intensities and widths are not directly comparable with the rest.",
        ],
    }
    # (label, file relative to this notebook, value of the series variable or None when unknown)
    SPECTRA = [
        ("s0 a", "step0_untreated_E-along-a.csv", 0),
        ("s0 b", "step0_untreated_E-along-b.csv", 0),
        ("s1 a", "step1_E-along-a.csv", 1),
        ("s1 b", "step1_E-along-b.csv", 1),
        ("s2 a", "step2_E-along-a.csv", 2),
        ("s2 b", "step2_E-along-b.csv", 2),
        ("s3 a", "step3_E-along-a.csv", 3),
        ("s3 b", "step3_E-along-b.csv", 3),
    ]
    SERIES = {"name": "step", "unit": ""}
    # Bands to track: name -> (low, high) search window in cm-1, taken from the CrSBr note
    # (Ag windows from Mondal 2025 / Pawbake 2023; 302 is the B2g / resonant-mode region).
    BANDS = {
        "Ag1": (105.0, 125.0),
        "Ag2": (232.0, 258.0),
        "302": (295.0, 310.0),
        "Ag3": (336.0, 352.0),
    }
    MIN_SNR = 3.0  # detection threshold in noise units for the windowed band fits
    return BANDS, MIN_SNR, SAMPLE, SERIES, SPECTRA


@app.cell
def _():
    # FILL 2/6: what the literature reports for this system. One row per reported number you will compare with.
    # band: a key of BANDS or None; reported_cm1: the value; locator: figure or table, "read from Fig. N" when
    # read off a plot (about +-1 cm-1); ref: number in the reference list.
    LIT_VALUES = [
        {"quantity": "Ag1, 4L, 300 K, 2.33 eV", "band": "Ag1", "reported_cm1": 114.0, "uncertainty_cm1": 1.0,
         "source": "Mondal et al. 2025", "locator": "p.2 text", "ref": 2},
        {"quantity": "Ag2, 4L, 300 K, 2.33 eV", "band": "Ag2", "reported_cm1": 244.0, "uncertainty_cm1": 1.0,
         "source": "Mondal et al. 2025", "locator": "p.2 text", "ref": 2},
        {"quantity": "Ag3, 4L, 300 K, 2.33 eV", "band": "Ag3", "reported_cm1": 344.0, "uncertainty_cm1": 1.0,
         "source": "Mondal et al. 2025", "locator": "p.2 text", "ref": 2},
        {"quantity": "Ag1, bulk, 300 K, 633 nm", "band": "Ag1", "reported_cm1": 117.0, "uncertainty_cm1": 1.0,
         "source": "Pawbake et al. 2023", "locator": "p.3 text", "ref": 3},
        {"quantity": "Ag2, bulk, 300 K, 633 nm", "band": "Ag2", "reported_cm1": 257.0, "uncertainty_cm1": 1.0,
         "source": "Pawbake et al. 2023", "locator": "p.3 text", "ref": 3},
        {"quantity": "Ag3, bulk, 300 K, 633 nm", "band": "Ag3", "reported_cm1": 345.0, "uncertainty_cm1": 1.0,
         "source": "Pawbake et al. 2023", "locator": "p.3 text", "ref": 3},
        {"quantity": "B2g (tilted geometry only), bulk, 300 K", "band": "302", "reported_cm1": 301.0,
         "uncertainty_cm1": 1.0, "source": "Pawbake et al. 2023", "locator": "p.3 text", "ref": 3},
    ]
    # Published figures opened with iopic-bond view_figure.
    FIGURES = [
        {"image_path": "C:/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/data/raw/iopic-bond/papers/"
                       "2212.01754/parsed/12572f6bdc3223ca/figures/fig2.png",
         "caption": "Torres 2022, Fig. 2: 1L/2L/3L CrSBr pristine, after air, heating, water and He+; "
                    "D1 (shoulder below Ag1) and D3 (above Ag3) mark defects (1.58 eV excitation)", "ref": 1},
        {"image_path": "C:/Users/sadit/Desktop/P_Projects/Hackathons/OSI Hackathon/data/raw/iopic-bond/papers/"
                       "2212.01754/parsed/12572f6bdc3223ca/figures/fig3.png",
         "caption": "Torres 2022, Fig. 3: He+ dose series; Ag modes broaden and fade, D1, D3, D* grow, "
                    "STEM shows amorphisation at high dose", "ref": 1},
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

    mo.vstack([mo.md("## 3. Tracked bands (windowed fits, fit errors only; add calibration uncertainty)"),
               mo.ui.table(track, selection=None, page_size=max(10, len(track)))])
    return pos, track


@app.cell
def _(BANDS, SPECTRA, mo, np, spectra):
    # 3b. Band strength relative to the Si line (added cell). Windowed Lorentzian heights are not used here:
    # a weak band that the fit misses is a data point too. Each band is integrated above a straight baseline
    # between the window edges and divided by the Si 520.7 line integrated the same way. Same-flake spectra
    # share the substrate, so the Si line is the internal intensity reference. Detection limit: 3 sigma of the
    # integral from the rms of the 150 to 200 cm-1 region, which holds no CrSBr band.
    def _area(_s, _lo, _hi):
        _m = (_s.x >= _lo) & (_s.x <= _hi)
        _x, _y = _s.x[_m], _s.y[_m]
        _base = np.interp(_x, [_x[0], _x[-1]], [np.mean(_y[:3]), np.mean(_y[-3:])])
        return float(np.trapezoid(_y - _base, _x)), _x

    strength = {}
    _rows = []
    for _label, _s in spectra.items():
        _si, _ = _area(_s, 495, 545)
        _q = (_s.x >= 150) & (_s.x <= 200)
        _rms = float(np.std(np.diff(_s.y[_q])) / np.sqrt(2))
        _dx = float(np.median(np.diff(_s.x)))
        _row = {"spectrum": _label}
        for _band, (_lo, _hi) in BANDS.items():
            _a, _xx = _area(_s, _lo, _hi)
            _lim = 3 * _rms * _dx * np.sqrt(len(_xx))
            _ratio = _a / _si
            strength[(_label, _band)] = (_ratio, _a > _lim, _lim / _si)
            _row[_band] = f"{_ratio:.4f}" if _a > _lim else f"< {_lim / _si:.4f}"
        _rows.append(_row)

    def strength_txt(label, band):
        """Band area over Si area as text, or the detection limit when the band is not detected."""
        _r, _ok, _lim = strength[(label, band)]
        return f"{_r:.3f}" if _ok else f"< {_lim:.3f} (not detected)"

    mo.vstack([mo.md("## 3b. Band area relative to the Si line (integrated; limit = 3 sigma)"),
               mo.ui.table(_rows, selection=None, page_size=max(10, len(_rows)))])
    return (strength_txt,)


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
    # FILL 3/6: method notes. Each analysis choice that came from the literature, with its reference number.
    mo.md("""
    ## 6. Method notes
    - Lorentzian line shapes on an asymmetric least squares baseline (Eilers and Boelens 2005).
    - Each Ag band is refitted in its own window, with windows set around the Ag positions of [2] and [3]; the Ag2
      window is 232 to 258 cm-1 because 4L and bulk differ by about 13 cm-1 between sources [2][3].
    - Si 520.7 cm-1 is used for the calibration offset, and as the internal intensity reference in section 3b
      (same substrate in all spectra). Intensity ratios to Si depend on flake interference and laser energy, so
      they are used for trends, not as absolute scattering strengths [2].
    - a and b are assigned from which Ag mode is strongest along each direction, as in [2]; this holds for a laser
      of 2.33 eV or above and not at 1.96 eV, where Ag2 switches to b [2].
    """)
    return


@app.cell
def _(track):
    def fw(label, band):
        """Tracked FWHM of a band as text, for use in the interpretation cell."""
        for _t in track:
            if _t["spectrum"] == label and _t["band"] == band and "fwhm" in _t:
                return f"{_t['fwhm']:.1f}"
        return "n/a"

    return (fw,)


@app.cell
def _(fw, mo, pos, strength_txt):
    # FILL 4/6: interpretation. Numbers come from the fit through pos(), fw() and strength_txt().
    mo.md(f"""
    ## 7. Interpretation
    - [measured] The untreated flake (s0) is 4L-like CrSBr: Ag1 {pos("s0 b", "Ag1")}, Ag2 {pos("s0 a", "Ag2")},
      Ag3 {pos("s0 b", "Ag3")}, against 114, 244, 344 cm-1 reported for 4L at 2.33 eV [2] and 117, 257, 345 in bulk [3].
      Ag2 dominates with E along a and Ag1 and Ag3 with E along b (band area / Si area: Ag2 a {strength_txt("s0 a", "Ag2")}
      vs b {strength_txt("s0 b", "Ag2")}; Ag3 b {strength_txt("s0 b", "Ag3")} vs a {strength_txt("s0 a", "Ag3")}),
      the 2.33 eV pattern with a and b assigned as in [2] (laser inferred, see assumptions). High confidence it is CrSBr.
    - [measured] The Raman signal of the flake collapses step by step relative to the Si line. Ag2 along a:
      s0 {strength_txt("s0 a", "Ag2")}, s1 {strength_txt("s1 a", "Ag2")}, s2 {strength_txt("s2 a", "Ag2")},
      s3 {strength_txt("s3 a", "Ag2")}. Ag3 along b: s0 {strength_txt("s0 b", "Ag3")}, s1 {strength_txt("s1 b", "Ag3")},
      s2 {strength_txt("s2 b", "Ag3")}, s3 {strength_txt("s3 b", "Ag3")}. At step 3 no Ag mode is detected along
      either axis, although the Si line is strong.
    - [measured] Where bands survive (s1, s2) they broaden and soften. FWHM Ag2 a: s0 {fw("s0 a", "Ag2")},
      s1 {fw("s1 a", "Ag2")}, s2 {fw("s2 a", "Ag2")} cm-1; Ag3 b: s0 {fw("s0 b", "Ag3")}, s1 {fw("s1 b", "Ag3")},
      s2 {fw("s2 b", "Ag3")} cm-1. Positions (Si corrected): Ag1 b {pos("s0 b", "Ag1")} to {pos("s1 b", "Ag1")} to
      {pos("s2 b", "Ag1")}; Ag2 a {pos("s0 a", "Ag2")} to {pos("s1 a", "Ag2")} to {pos("s2 a", "Ag2")}; Ag3 b
      {pos("s0 b", "Ag3")} to {pos("s1 b", "Ag3")} to {pos("s2 b", "Ag3")}. The s1 to s2 step is on the same
      instrument setting (Si lines within 0.1 cm-1), so that part is not a calibration effect.
    - [inferred] Ag1 and Ag2 move down by about 3 to 4 cm-1 while Ag3 moves by about 1: this is the pattern reported
      for fewer layers (Ag1, Ag2 soften, Ag3 nearly layer independent) [1], so the flake may be thinner or
      interlayer-decoupled where it was probed. Moderate to low confidence: defects broaden and shift the same
      modes, and Raman shifts are a poor layer counter [4].
    - [inferred] The line shapes at s1 and s2 (read by eye from a log-scale overlay of the raw spectra, tmp/lineshapes.png,
      not a fit) show red-side shoulders on Ag1 and Ag2 and a wing around Ag3. This resembles the defect modes D1 (below Ag1), D2 (below Ag2) and D3 (above Ag3) after
      air, heat, water or He+ exposure [1] (Fig. 2, Fig. 3). At 532 nm and this signal level the shoulders cannot be
      fitted separately, so assignment to D1/D2/D3 is low confidence.
    - [measured] The 302 cm-1 feature stays at 0.3 to 0.6 % of the Si line in every spectrum where it is detected
      (all except s0 b), including s0 a, and is the only feature left at s3. Silicon has a second-order band near 300 cm-1 (rl_qc output
      of the skill), and CrSBr B2g modes need a tilted sample [3]. Read it as substrate, not as new CrSBr physics.
    - [inferred] Step 3 has no CrSBr Raman signal. Most likely readings: (a) the crystal is amorphised or removed
      under the spot, as in the high-dose He+ STEM and the 1L water/heat cases of [1] (Fig. 2e, Fig. 3e-g);
      (b) the beam was not on the flake; (c) resonance enhancement was lost, so the modes fell below the detection
      limit. (a) is favoured only by the monotonic trend s0 to s2; the data cannot exclude (b).
    - [inferred] Device verdict: the material after step 2 is degraded (band area down by 6 to 7 times relative to
      Si, widths up by about 2 times). After step 3 no crystalline CrSBr signal is detected. Not
      device-ready on this evidence. If step 3 was a deliberate damaging step, this is the expected outcome; if not,
      check the spot and the flake before drawing a conclusion.
    """)
    return


@app.cell
def _(mo):
    # FILL 5/6: limits and questions for the user.
    mo.md("""
    ## 8. Limits and questions
    - The processing steps are unknown, so no change is tied to a mechanism. Questions: what was done at each step,
      and are the steps cumulative on the same spot?
    - Laser wavelength, power and exposure time are unknown. Laser heating or photo-damage during measurement can
      itself degrade thin CrSBr. Please give wavelength, power at the sample and integration time.
    - Step 0 has a Si line of 9 cm-1 FWHM against 3.7 cm-1 for the others, while its Ag modes are narrower than that.
      The cause is not known (focus, spot on thicker or different Si, different setup). Treat the s0 to s1 change
      in intensity and width as less certain than s1 to s2.
    - Shifts are fit errors plus a Si calibration scatter of a few tenths of a cm-1; the 3 to 4 cm-1 Ag1 and Ag2
      shifts exceed it, the 1 cm-1 Ag3 shift is marginal.
    - Layer number after each step is not measured. AFM or optical contrast of the flake after every step would
      separate thinning from defects; an optical image at the Raman spot would separate "flake gone" from "spot
      missed" at step 3.
    - PL near 1.31 eV is stronger along b and independently confirms the axes and the presence of intact CrSBr [2];
      Raman at 1.58 eV (resonant) enhances defect modes D1, D3 and Ag modes [1] and would settle whether defects are
      present at step 3. Electrical or magnetic (MOKE, magneto-Raman) tests are the real device criterion; Raman
      only shows lattice integrity.
    """)
    return


@app.cell
def _(mo):
    # FILL 6/6: references. Only papers opened this session or cited with a locator in the skill's notes.
    mo.md("""
    ## References
    1. Torres et al., 2022, Probing defects and spin-phonon coupling in CrSBr via resonant Raman scattering,
       arXiv:2212.01754 (Figs. 1, 2, 3 opened). [link](https://arxiv.org/abs/2212.01754)
    2. Mondal et al., 2025, npj 2D Materials, polarized Raman of CrSBr versus thickness and laser energy,
       arXiv:2410.22164 (values from the skill's CrSBr note, p.2 to 4). [link](https://arxiv.org/abs/2410.22164)
    3. Pawbake et al., 2023, Phys. Rev. B 107, 075421, magneto-Raman of CrSBr, arXiv:2211.12939 (values from the
       skill's CrSBr note, p.3). [link](https://arxiv.org/abs/2211.12939)
    4. Ye et al., 2022, ACS Nano 16, 11876, layer-dependent magnetism and Raman of CrSBr
       (as cited in the skill's CrSBr note, journal p.5, not opened). [link](https://doi.org/10.1021/acsnano.2c01151)
    """)
    return


if __name__ == "__main__":
    app.run()
