"""Generate dev interpretation cases (int-*): sets of Raman spectra of a known material plus a rubric answer key.

Identification cases ask "what is this?"; interpretation cases ask what a senior Raman researcher would read from a
set of spectra of a known material: thickness trends, a calibration offset, resonance-enhanced overtones, defect
stages, laser heating, substrate effects. Format and scoring are defined in data/test_set/INTERPRET.md; the rubric
is graded by a blind LLM judge. Synthetic spectra use only positions and widths read from the cited papers (each
constant names its paper and locator); values the curator had to choose are marked "curator" and are never scored.
The one experimental case re-exports two published spectra unchanged.

Input:
    The constants below, each traceable to the paper named next to it (Lee 2010, Berkdemir 2013, Cancado 2011,
    Eckmann 2012, Conley 2013, Chakraborty 2012, Lee 2012, Ferrari 2006, Gorbachev 2011, Castellanos-Gomez 2014,
    Gillet 2017; full citations in the constants). For the experimental case, the Zenodo 14883846 archive
    005_Data.zip (Bukvisova et al. 2025), read in place with zipfile; nothing is extracted into the repository.
Process:
    Each synthetic spectrum is a sum of Lorentzians (published positions and widths) on a fluorescence-like
    baseline (offset, slope, broad hump) with Gaussian noise, plus the Si line when the stated substrate is
    SiO2/Si and an occasional single-pixel cosmic spike. The rubric text is built from the same constants, so the
    numbers in the answer key match the numbers in the spectra. Labels never carry the quantity to be inferred.
Output:
    <out>/dev_interpret/int-<material>-<topic>-<nn>/ with input.json, spectrum_<label>.csv (shift_cm1,intensity,
    x ascending) and rubric.json. Deterministic for a given --seed.
"""

import argparse
import json
import zipfile
from pathlib import Path

import numpy as np

SPLIT = "dev_interpret"
HC_EV_NM = 1239.84  # eV nm, converts laser wavelength to photon energy

# ---------------------------------------------------------------- sources (cite the paper, not this file)
LEE2010 = ("Lee, Yan, Brus, Heinz, Hone, Ryu 2010, Anomalous lattice vibrations of single- and few-layer MoS2, "
           "ACS Nano 4, 2695, doi:10.1021/nn1003937, arXiv:1005.2509")
CONLEY = "Conley et al. 2013, Nano Lett. 13, 3626, arXiv:1305.3880"
CHAKRABORTY = "Chakraborty et al. 2012, Phys. Rev. B 85, 161403, arXiv:1206.1758"
BERKDEMIR = ("Berkdemir et al. 2013, Identification of individual and few layers of WS2 using Raman spectroscopy, "
             "Sci. Rep. 3, 1755, doi:10.1038/srep01755")
CANCADO = ("Cancado, Jorio, Martins Ferreira, Stavale, Achete, Capaz, Moutinho, Lombardo, Kulmala, Ferrari 2011, "
           "Quantifying defects in graphene via Raman spectroscopy at different excitation energies, Nano Lett. 11, "
           "3190, doi:10.1021/nl201432g, arXiv:1105.0175")
ECKMANN = "Eckmann et al. 2012, Nano Lett. 12, 3925, arXiv:1207.2058"
LEE2012 = "Lee, Ahn, Shim, Lee, Ryu 2012, Nat. Commun. 3, 1024, arXiv:1209.0234"
FERRARI = "Ferrari et al. 2006, Phys. Rev. Lett. 97, 187401, arXiv:cond-mat/0606284"
MOHIUDDIN = "Mohiuddin et al. 2009, Phys. Rev. B 79, 205433, arXiv:0812.1538"
GORBACHEV = ("Gorbachev et al. 2011, Hunting for monolayer boron nitride: optical and Raman signatures, Small 7, "
             "465, arXiv:1008.2868")
CASTELLANOS = "Castellanos-Gomez et al. 2014, arXiv:1403.0499"
GILLET = "Gillet et al. 2017, arXiv:1708.05874"
BUKVISOVA = ("Bukvisova, Kalousek, Patocka, Zlamal, Planer, Mahel, Citterberg, Novak, Sikola, Kolibal 2025, "
             "Casimir-like effect driven self-assembly of graphene on molten metals, arXiv:2503.04327")

# ---------------------------------------------------------------- MoS2, Lee 2010
# Fig. 2b (514.5 nm Ar-ion laser, 285 nm SiO2/Si, 2.7 cm-1 resolution, Methods p.5): N -> (E2g1, A1g), cm-1, +-0.3 fig
LEE_POS = {1: (384.0, 403.1), 2: (383.4, 404.8), 3: (382.8, 405.9), 4: (382.4, 406.7), "bulk": (382.2, 407.4)}
LEE_SI = 520.0  # cm-1, Methods p.5: "the Si Raman band at 520 cm-1 was used as an internal frequency reference"
GAMMA_E2G_MOS2 = 2.1  # cm-1, p.4: Gamma(E2g1) about 2.1, largely independent of thickness
# p.4-5: Gamma(A1g) rises from 3 to 6 cm-1 as thickness falls from 6L to 2L, and is larger for 2L than for 1L.
# 2L 6.0 and bulk 3.0 are the paper's end points; 1L 5.0 and 4L 4.5 are curator interpolations inside that range.
GAMMA_A1G_MOS2 = {1: 5.0, 2: 6.0, 4: 4.5, "bulk": 3.0}
# p.4: integrated intensities rise roughly linearly up to 4L, then fall; single layers are stronger than bulk
# (optical interference on SiO2/Si). Relative A1g areas below follow that statement; the bulk value is curator.
AREA_A1G_MOS2 = {1: 1.0, 2: 2.0, 4: 4.0, "bulk": 0.7}
AREA_E_OVER_A = 1.0  # curator: integrated E2g/A1g ratio (Lee Fig. 3a not re-read here); not scored

# ---------------------------------------------------------------- WS2, Berkdemir 2013 Table 1 (514.5 nm)
WS2_POS = {1: (351.1, 355.2, 417.2), "bulk": (350.0, 355.3, 420.1)}  # 2LA(M), E2g1, A1g, cm-1 (table)
WS2_LA_M = 176.0  # cm-1, LA(M), listed in Table 1 for the 488 nm 1L row; used here as a weak band (curator)
# Curator values, the paper gives no linewidths: FWHM of 2LA(M) (a two-phonon band, broader), E2g1, A1g.
GAMMA_WS2 = {"2LA": 9.0, "E2g": 4.0, "A1g": 4.5, "LA": 10.0}
# 2LA(M)/A1g intensity ratio at 514.5 nm, Table 1: 2.2 (1L), 1.01 (2L), 0.72 (3L), 0.47 (bulk); Results text:
# "the ratio is always larger than 2 only for monolayer films". Used here as a height ratio (the paper's maps use
# peak maxima, Fig. 2 caption; whether Table 1 uses heights is not explicit).
WS2_2LA_OVER_A1G = {1: 2.2, "bulk": 0.47}

# ---------------------------------------------------------------- graphene
POS_G = 1580.0           # cm-1, Cancado p.2 (G around 1580, D around 1350, D' around 1620 at 514.5 nm)
POS_D_5145, POS_DP = 1350.0, 1620.0
DISP_D = 52.0            # cm-1/eV, Cancado p.5: d(omega_D)/dE_L about 52; the 2D disperses twice as fast
E_5145 = 2.41            # eV, Cancado p.2 (514.5 nm line)
POS_2D_5145 = 2700.0     # cm-1, Ferrari 2006 p.2: 2D about 2700 at 514 nm
GAMMA_G, GAMMA_D, GAMMA_2D = 14.0, 15.0, 32.0  # cm-1, Cancado p.5 and Fig. 5c (Gamma_G about 14 in stage 1);
#                                               Fig. 5a reading (Gamma_D about 15, Gamma_2D 30 to 35, L_D > 5 nm)
GAMMA_DP = 14.0          # cm-1, curator (not stated in Cancado or Eckmann)
H_2D_OVER_G = 3.0        # curator approximate reading of Cancado Fig. 1 (L_D 14 and 24 nm traces)
LD_PREFACTOR = (1.8e-9, 0.5e-9)  # Cancado Eq. 4: L_D^2 (nm^2) = (1.8 +- 0.5) 1e-9 lambda^4 (I_D/I_G)^-1, L_D >= 10 nm
ID_IDP_VACANCY = 7.0     # Eckmann 2012 abstract: I_D/I_D' about 13 sp3, 7 vacancy-like, 3.5 boundary-like
LEE2012_ORIGIN = (1581.6, 2676.9)  # cm-1, (G, 2D) of unstrained undoped graphene at 514.5 nm, Lee 2012
SI_LINE = 520.9          # cm-1, Castellanos-Gomez 2014 p.7 (514 nm, same setup as the flakes)
SI_2ND = (950.0, 980.0)  # cm-1, Si second-order features near 950 and 980, Gillet 2017 Fig. 1 (experimental)
GAMMA_SI = 3.5           # cm-1, curator (resolution-limited Si line)

# ---------------------------------------------------------------- hBN, Gorbachev 2011 (514.5 nm, SiO2/Si)
HBN_BULK = 1366.0        # cm-1, bulk E2g, HWHM about 9 (text)
HBN_BULK_FWHM = 18.0     # 2 x HWHM 9
HBN_1L_SHIFT = 3.0       # cm-1, 1L upshift typically 2 to 4 (sample dependent +-2); 3 is the middle of the range
HBN_1L_FWHM = 22.0       # 2 x HWHM 11 (1L HWHM 10 to 12)


def lorentz(x, x0, fwhm):
    """Unit-height Lorentzian with full width at half maximum fwhm."""
    g = fwhm / 2.0
    return g * g / ((x - x0) ** 2 + g * g)


def height_for_area(area, fwhm):
    """Lorentzian area = pi/2 x height x FWHM, so height = area / FWHM up to a constant shared by all peaks."""
    return area / fwhm


def render(x, peaks, scale, rng, snr, si=None, spike=False, fluo=(0.1, 0.4)):
    """Spectrum from [(position, fwhm, height)] peaks, with baseline, noise, optional Si line and cosmic spike.

    Heights are relative to `scale` (counts). snr = scale / noise sigma. si = (position, relative height) or None.
    Returns (y, spike_position or None).
    """
    y = np.zeros_like(x)
    for pos, fwhm, h in peaks:
        y += h * lorentz(x, pos, fwhm)
    if si is not None:
        y += si[1] * lorentz(x, si[0], GAMMA_SI)
        for p in SI_2ND:  # weak second-order Si features (heights and widths curator)
            if x[0] < p < x[-1]:
                y += 0.02 * si[1] * lorentz(x, p, 25.0)
    y = scale * y
    lo, hi = x[0], x[-1]
    y += scale * (rng.uniform(0.05, 0.25) + rng.uniform(-0.05, 0.15) * (x - lo) / (hi - lo)
                  + rng.uniform(*fluo) * np.exp(-(((x - rng.uniform(lo, hi)) / rng.uniform(400, 900)) ** 2)))
    y += rng.normal(0, scale / snr, size=x.size)
    spike_pos = None
    if spike:  # cosmic ray: one or two pixels, far above the peaks, narrower than the instrument resolution
        i = int(rng.integers(int(0.1 * x.size), int(0.9 * x.size)))
        y[i] += scale * rng.uniform(1.5, 3.0)
        if rng.uniform() < 0.5:
            y[i + 1] += scale * rng.uniform(0.3, 1.0)
        spike_pos = round(float(x[i]), 1)
    return np.round(np.clip(y, 0, None), 1), spike_pos


def csv_text(x, y):
    return "shift_cm1,intensity\n" + "\n".join(f"{a:.2f},{b}" for a, b in zip(x, y)) + "\n"


def axis(lo, hi, rng, step=(0.5, 0.7)):
    return np.arange(lo, hi, rng.uniform(*step))


def write_case(root, case_id, inp, rubric, spectra):
    """spectra: {file name: csv text}. Writes into <root>/dev_interpret/<case_id>/."""
    d = Path(root) / SPLIT / case_id
    d.mkdir(parents=True, exist_ok=True)
    for name, text in spectra.items():
        (d / name).write_text(text)
    (d / "input.json").write_text(json.dumps(inp, indent=2) + "\n")
    (d / "rubric.json").write_text(json.dumps(rubric, indent=2) + "\n")
    print(SPLIT, case_id, sorted(spectra))


def item(i, kind, weight, text, locator):
    return dict(id=i, kind=kind, weight=weight, text=text, locator=locator)


def wrong(i, penalty, text):
    return dict(id=i, penalty=penalty, text=text)


def cond(laser_nm, **kw):
    return dict(laser_nm=laser_nm, temperature_K=kw.pop("temperature_K", 295), **kw)


# ================================================================ case 1: MoS2 thickness series
def mos2_spectrum(n, rng, shift=0.0, snr=60, spike=False):
    e, a = LEE_POS[n]
    e, a = e + rng.normal(0, 0.1) + shift, a + rng.normal(0, 0.1) + shift
    x = axis(150.0, 650.0, rng)
    area_a = AREA_A1G_MOS2[n]
    ga = GAMMA_A1G_MOS2[n]
    peaks = [(e, GAMMA_E2G_MOS2, height_for_area(AREA_E_OVER_A * area_a, GAMMA_E2G_MOS2)),
             (a, ga, height_for_area(area_a, ga))]
    si_rel = {1: 1.2, 2: 1.0, 4: 0.7, "bulk": 0.08}[n]  # curator: Si attenuated under thicker flakes
    scale = rng.uniform(800, 1500)
    y, sp = render(x, peaks, scale, rng, snr, si=(LEE_SI + shift, si_rel), spike=spike)
    return x, y, sp


def case_mos2_thickness(root, rng):
    cid = "int-MoS2-thickness-01"
    layers = [1, 2, 4, "bulk"]
    order = list(rng.permutation(4))  # which label gets which thickness
    labels = ["A", "B", "C", "D"]
    assign = {labels[i]: layers[order[i]] for i in range(4)}
    spike_label = labels[int(rng.integers(0, 4))]
    files, spectra, spikes = {}, [], {}
    for lab in labels:
        x, y, sp = mos2_spectrum(assign[lab], rng, spike=(lab == spike_label))
        files[f"spectrum_{lab}.csv"] = csv_text(x, y)
        spectra.append(dict(file=f"spectrum_{lab}.csv", label=f"flake {lab}", conditions=cond(514.5)))
        if sp:
            spikes[lab] = sp
    inp = dict(case_id=cid, kind="interpret", task="interpret", material="2H-MoS2", spectra=spectra,
               context="Four flakes mechanically exfoliated from a natural molybdenite (2H-MoS2) crystal onto Si "
                       "with 285 nm SiO2, measured under ambient conditions with a 514.5 nm Ar-ion laser, 40x "
                       "objective, backscattering, spectral resolution about 2.7 cm-1. The flakes look different "
                       "in the optical microscope but we have no AFM yet.",
               question="How thick is each flake? What changes between the spectra and what does it tell you? "
                        "Anything I should be careful about?")
    delta = {n: round(LEE_POS[n][1] - LEE_POS[n][0], 1) for n in layers}
    by_n = {v: k for k, v in assign.items()}
    sp_lab, sp_pos = next(iter(spikes.items()))
    rubric = dict(
        case_id=cid,
        source=dict(paper=LEE2010, dataset="synthetic (eval/synth/make_interpret_dev.py)",
                    locator="Fig. 2a,b (positions vs N), p.3-4 text (trends, intensity, widths), Methods p.5"),
        items=[
            item("f1", "finding", 2, "E2g1 softens (moves down) and A1g stiffens (moves up) with increasing "
                 "thickness, so the mode separation grows with layer number", "Lee 2010 p.3, Fig. 2a,b"),
            item("n1", "quantitative", 2, f"Flake {by_n[1]} is a monolayer (separation about {delta[1]} cm-1) and "
                 f"flake {by_n[2]} a bilayer (about {delta[2]} cm-1); the 1L to 2L step of 2 to 3 cm-1 is the most "
                 "robust distinction", "Lee 2010 Fig. 2b; p.3 (Delta(1L) about 3 cm-1 smaller than 2L)"),
            item("n2", "quantitative", 2, f"Flakes {by_n[4]} (about {delta[4]} cm-1) and {by_n['bulk']} (about "
                 f"{delta['bulk']} cm-1) are 4 layers or thicker, {by_n['bulk']} the thicker or bulk-like one; "
                 "the separation converges to bulk from about 4 layers, so these two can only be bounded, not "
                 "counted, from positions alone", "Lee 2010 p.3 ('for films of four or more layers, the "
                 "frequencies of both modes converge to the bulk values'), Fig. 2b"),
            item("c1", "caveat", 1, "Absolute Raman intensity is not a layer-number measure on SiO2/Si: optical "
                 "interference makes the intensity rise up to about 4 layers and then fall, and a monolayer can "
                 "be stronger than bulk", "Lee 2010 p.4, Fig. 3a"),
            item("c2", "caveat", 1, "Strain and doping also shift the modes and therefore the separation (uniaxial "
                 "strain softens E' by about 4.5 cm-1/% with A' nearly unchanged; electron doping softens and "
                 "broadens A1g), so a separation shift of 1 cm-1 is not a unique thickness signal",
                 f"{CONLEY}, text; {CHAKRABORTY}, text"),
            item("f2", "finding", 1, "A1g is broader for the few-layer flakes (largest near the bilayer) than for "
                 "the thick flake, while E2g1 width stays about 2 cm-1", "Lee 2010 p.4, Fig. 3b"),
            item("q1", "question", 1, "Checks or asks about the frequency calibration, using the Si line near "
                 "520 cm-1 as an internal reference (sub-cm-1 differences matter here)",
                 "Lee 2010 Methods p.5 (Si band at 520 cm-1 used as internal frequency reference)"),
        ],
        wrong_claims=[
            wrong("w1", 1, "Assigns layer numbers from absolute or relative peak intensity alone"),
            wrong("w2", 1, "States that E2g1 stiffens with thickness, or that the separation shrinks with thickness"),
            wrong("w3", 1, f"Treats the one- or two-pixel spike near {sp_pos} cm-1 in flake {sp_lab} as a Raman band"),
        ],
        notes=(f"Synthetic. Truth: {', '.join(f'flake {k} = {v}' for k, v in assign.items())} (bulk means "
               f"Lee's bulk values). Positions from Lee 2010 Fig. 2b at 514.5 nm (verified reading +-0.3 cm-1), "
               f"jittered 0.1 cm-1. Widths: E2g1 {GAMMA_E2G_MOS2} cm-1 (p.4); A1g {GAMMA_A1G_MOS2} (2L and bulk "
               "end points from p.4, 1L and 4L curator interpolations). A1g areas 1:2:4 for 1L:2L:4L and 0.7 for "
               "bulk follow Lee's statement (rise to 4L, 1L stronger than bulk), values curator. E2g/A1g area "
               "ratio 1.0 for all (curator, not scored). Si at 520.0 cm-1 (Lee's reference), attenuated under "
               "the thick flake (curator). Cosmic spike placed by the generator. The case brief asked for 532 nm; "
               "Lee's thickness values (Fig. 2b) are at 514.5 nm, so the case uses 514.5 nm."))
    write_case(root, cid, inp, rubric, files)


# ================================================================ case 2: MoS2 calibration offset
def case_mos2_calibration(root, rng):
    cid = "int-MoS2-calibration-01"
    offset = 2.5  # cm-1, curator: rigid instrument offset on day 2, applied to every line including Si
    files, spectra = {}, []
    for lab, sh, snr in (("day1", 0.0, 70), ("day2", offset, 55)):
        x, y, _ = mos2_spectrum(2, rng, shift=sh, snr=snr)
        files[f"spectrum_{lab}.csv"] = csv_text(x, y)
        spectra.append(dict(file=f"spectrum_{lab}.csv", label=lab.replace("day", "day "),
                            conditions=cond(514.5)))
    d2 = round(LEE_POS[2][1] - LEE_POS[2][0], 1)
    inp = dict(case_id=cid, kind="interpret", task="interpret", material="2H-MoS2", spectra=spectra,
               context="The same exfoliated MoS2 flake on 285 nm SiO2/Si, same spot, measured on two days a week "
                       "apart with a 514.5 nm laser. In between the sample sat in ambient air; a colleague thinks "
                       "adsorbates may have doped or strained it.",
               question="Did the flake change between day 1 and day 2? What do the spectra say?")
    rubric = dict(
        case_id=cid,
        source=dict(paper=f"{LEE2010}; {CHAKRABORTY}; {CONLEY}", dataset="synthetic (eval/synth/make_interpret_dev.py)",
                    locator="Lee 2010 Fig. 2b and Methods p.5; Chakraborty text; Conley text"),
        items=[
            item("f1", "finding", 2, f"Both E2g1 and A1g sit about {offset} cm-1 higher on day 2, by the same "
                 f"amount, so the mode separation is unchanged (about {d2} cm-1)", "measured; Lee 2010 Fig. 2b"),
            item("f2", "finding", 3, f"The Si substrate line moved by the same +{offset} cm-1 (from about "
                 f"{LEE_SI:.0f} to {LEE_SI + offset:.1f} cm-1); Si is a fixed reference, so the rigid shift is a "
                 "spectrometer calibration offset, not a change of the flake",
                 "Lee 2010 Methods p.5 (Si 520 cm-1 used as internal frequency reference)"),
            item("n1", "quantitative", 2, f"After referencing each spectrum to Si, the MoS2 positions agree within "
                 f"the fit uncertainty, and the separation (about {d2} cm-1) points to a bilayer on both days",
                 "Lee 2010 Fig. 2b"),
            item("f3", "finding", 1, "No sign of doping or strain after correction: electron doping would soften "
                 "and broaden A1g, and strain would shift E2g1 much more than A1g; neither is seen and the widths "
                 "are unchanged", f"{CHAKRABORTY}; {CONLEY}"),
            item("q1", "question", 1, "Asks whether the spectrometer, grating position or calibration changed "
                 "between the days, or recommends recording a reference line (Si or a lamp) with every session",
                 "Lee 2010 Methods p.5"),
        ],
        wrong_claims=[
            wrong("w1", 2, "Interprets the day-2 shift as strain (for example compressive) or doping by adsorbates"),
            wrong("w2", 1, "Reports a change of layer number or of crystal quality between the days"),
        ],
        notes=(f"Synthetic. Both spectra: bilayer MoS2 from Lee 2010 Fig. 2b (E2g1 {LEE_POS[2][0]}, A1g "
               f"{LEE_POS[2][1]} cm-1) with independent 0.1 cm-1 jitter, Si at {LEE_SI} cm-1. Day 2: every line "
               f"including Si shifted by +{offset} cm-1 (curator), widths and intensities unchanged apart from "
               "noise and baseline."))
    write_case(root, cid, inp, rubric, files)


# ================================================================ case 3: WS2 resonance and 2LA(M) overlap
def ws2_spectrum(n, rng, snr):
    la2, e, a = (p + rng.normal(0, 0.1) for p in WS2_POS[n])
    x = axis(120.0, 600.0, rng)
    h_a = 1.0
    peaks = [(WS2_LA_M + rng.normal(0, 0.5), GAMMA_WS2["LA"], 0.15 if n == 1 else 0.05),  # curator heights
             (la2, GAMMA_WS2["2LA"], WS2_2LA_OVER_A1G[n] * h_a),
             (e, GAMMA_WS2["E2g"], 0.5 if n == 1 else 0.6),  # curator E2g/A1g height
             (a, GAMMA_WS2["A1g"], h_a)]
    scale = rng.uniform(800, 2000)
    y, _ = render(x, peaks, scale, rng, snr, si=(SI_LINE, 1.5 if n == 1 else 0.1))
    return x, y


def case_ws2_resonance(root, rng):
    cid = "int-WS2-resonance-01"
    files, spectra = {}, []
    for lab, n, snr in (("1", 1, 60), ("2", "bulk", 80)):
        x, y = ws2_spectrum(n, rng, snr)
        files[f"spectrum_spot{lab}.csv"] = csv_text(x, y)
        spectra.append(dict(file=f"spectrum_spot{lab}.csv", label=f"spot {lab}", conditions=cond(514.5)))
    l1, e1, a1 = WS2_POS[1]
    lb, eb, ab = WS2_POS["bulk"]
    inp = dict(case_id=cid, kind="interpret", task="interpret", material="2H-WS2", spectra=spectra,
               context="CVD-grown WS2 on SiO2/Si, 514.5 nm laser. Spot 1 is on a thin triangular island, spot 2 on "
                       "a thick region; we need the thickness of the island.",
               question="Assign the peaks and tell me what the difference between the two spots means. Is spot 1 "
                        "a monolayer?")
    rubric = dict(
        case_id=cid,
        source=dict(paper=BERKDEMIR, dataset="synthetic (eval/synth/make_interpret_dev.py)",
                    locator="Table 1 (514.5 nm positions and 2LA(M)/A1g ratios), Results (overlap, Fig. 1e fit)"),
        items=[
            item("f1", "finding", 3, f"The band near 350 to 356 cm-1 is two overlapping modes, the second-order "
                 f"2LA(M) (about {l1} cm-1 in 1L) and the first-order E2g1 (about {e1} cm-1), and must be fitted "
                 "with two components", "Berkdemir 2013 Results ('the multi-peak Lorentzian fitting shown in "
                 "Figure 1e clearly separates their individual contributions'), Table 1"),
            item("f2", "finding", 2, "At 514.5 nm 2LA(M) is about twice as strong as A1g at spot 1 (ratio above "
                 "2, the monolayer fingerprint) and much weaker relative to A1g at the thick spot (about 0.5)",
                 "Berkdemir 2013 Results ('approximately twice the intensity of the first-order A1g'; 'larger "
                 "than 2 only for monolayer films') and Table 1 (2.2, 1.01, 0.72, 0.47 for 1L, 2L, 3L, bulk)"),
            item("n1", "quantitative", 2, f"A1g stiffens from about {a1} cm-1 (spot 1) to about {ab} cm-1 (spot "
                 f"2), consistent with a monolayer at spot 1 and a bulk-like region at spot 2",
                 "Berkdemir 2013 Table 1 (1L 417.2, 2L 418.4, 3L 419.0, bulk 420.1 at 514.5 nm)"),
            item("n2", "quantitative", 1, f"The A1g minus E2g1 separation is about {a1 - e1:.0f} cm-1 for spot 1 and "
                 f"about {ab - eb:.0f} cm-1 for spot 2, but only after E2g1 is separated from 2LA(M)",
                 "Berkdemir 2013 Table 1"),
            item("c1", "caveat", 1, "A1g and separation steps between 2L, 3L and bulk are about 1 cm-1, so "
                 "beyond the monolayer the layer number is weakly constrained by positions",
                 "Berkdemir 2013 Table 1 (3L 419.0 vs bulk 420.1 cm-1)"),
            item("q1", "question", 1, "Checks calibration against the Si line and/or asks about the laser line, "
                 "since the 2LA(M) intensity depends strongly on excitation (resonance)",
                 "Berkdemir 2013 Table 1 (488, 514.5 and 647 nm rows); Methods (Si 520 cm-1 used for "
                 "calibration)"),
        ],
        wrong_claims=[
            wrong("w1", 2, "Assigns the maximum of the 350 to 356 cm-1 band to E2g1 alone and builds the layer "
                  "number on that position or on the separation from it"),
            wrong("w2", 1, "Calls the 2LA(M) band a defect or impurity peak"),
        ],
        notes=(f"Synthetic. Positions from Berkdemir 2013 Table 1, 514.5 nm: 1L 2LA(M) {l1}, E2g1 {e1}, A1g {a1}; "
               f"bulk {lb}, {eb}, {ab} cm-1; 2LA(M)/A1g {WS2_2LA_OVER_A1G} (Table 1, Europe PMC "
               f"PMC3639451 full text). LA(M) {WS2_LA_M} cm-1 as a weak band (Table 1 lists it for 488 nm). Curator choices: "
               f"FWHM {GAMMA_WS2} (the paper gives none), E2g1/A1g height 0.5 (1L) and 0.6 "
               "(bulk), Si heights (Si at 520.9 cm-1). The thick spot uses "
               "Berkdemir's bulk values, which were measured on powder."))
    write_case(root, cid, inp, rubric, files)


# ================================================================ case 4: graphene defect series with a stage-2 point
def graphene_peaks(lam_nm, rng, ratio_dg, stage2=False):
    e_l = HC_EV_NM / lam_nm
    pos_d = POS_D_5145 + DISP_D * (e_l - E_5145) + rng.normal(0, 0.8)
    pos_2d = POS_2D_5145 + 2 * DISP_D * (e_l - E_5145) + rng.normal(0, 1.5)
    if not stage2:
        return [(pos_d, GAMMA_D, ratio_dg), (POS_G + rng.normal(0, 0.5), GAMMA_G, 1.0),
                (POS_DP + rng.normal(0, 0.8), GAMMA_DP, ratio_dg / ID_IDP_VACANCY),
                (pos_2d, GAMMA_2D, H_2D_OVER_G)]
    # Stage 2 (Cancado p.2-3: G broadens and merges with D', I_D/I_G falls, no well-defined second-order peaks,
    # only a weak bump from about 2300 to 3200 cm-1). Widths, G position and bump heights below are curator values.
    return [(pos_d + 5.0, 60.0, ratio_dg), (1592.0, 45.0, 1.0), (2700.0, 250.0, 0.12), (2930.0, 200.0, 0.08)]


def ld_nm(ratio, lam_nm, pf):
    return float(np.sqrt(pf * lam_nm ** 4 / ratio))


def case_graphene_defects(root, rng):
    cid = "int-graphene-defects-01"
    lam = 532.0
    targets = [24.0, 16.0, 11.0]  # nm, curator: stage-1 L_D values inside Cancado's L_D >= 10 nm validity range
    ratios = [LD_PREFACTOR[0] * lam ** 4 / t ** 2 for t in targets]
    r4 = ratios[1]  # dose 4: stage 2 with the same height ratio as dose 2, to make the ambiguity explicit
    files, spectra = {}, []
    spike_dose = 2
    for dose, (r, st2) in enumerate([(ratios[0], False), (ratios[1], False), (ratios[2], False), (r4, True)], 1):
        x = axis(450.0, 3200.0, rng, step=(0.9, 1.1))
        peaks = graphene_peaks(lam, rng, r, stage2=st2)
        y, sp = render(x, peaks, rng.uniform(2000, 6000), rng, 50, si=(SI_LINE, 2.0), spike=(dose == spike_dose))
        if sp:
            spike_pos = sp
        files[f"spectrum_dose{dose}.csv"] = csv_text(x, y)
        spectra.append(dict(file=f"spectrum_dose{dose}.csv", label=f"dose {dose}",
                            conditions=cond(532, power_mW=1.0)))
    inp = dict(case_id=cid, kind="interpret", task="interpret", material="graphene", spectra=spectra,
               context="Mechanically exfoliated single-layer graphene on SiO2/Si, treated in four steps of "
                       "increasing dose (dose 1 lowest), one spectrum per step on the same flake. 532 nm, about "
                       "1 mW, 100x objective.",
               question="How does the defect density evolve with dose? Can you give numbers?")
    pf_lo, pf_hi = LD_PREFACTOR[0] - LD_PREFACTOR[1], LD_PREFACTOR[0] + LD_PREFACTOR[1]
    ld_txt = "; ".join(f"dose {i + 1}: I_D/I_G about {r:.2f}, L_D about {t:.0f} nm (range "
                       f"{ld_nm(r, lam, pf_lo):.0f} to {ld_nm(r, lam, pf_hi):.0f} nm)"
                       for i, (r, t) in enumerate(zip(ratios, targets)))
    rubric = dict(
        case_id=cid,
        source=dict(paper=f"{CANCADO}; {ECKMANN}", dataset="synthetic (eval/synth/make_interpret_dev.py)",
                    locator="Cancado Eq. 4, p.2-3 (stages 1 and 2), p.5-6 and Fig. 5c (G width); Eckmann abstract"),
        items=[
            item("f1", "finding", 2, "Doses 1 to 3: D (and D') grow relative to G while G stays narrow (about 14 "
                 "cm-1) and 2D stays sharp, so these are in stage 1 and the point-defect density rises with dose",
                 "Cancado p.2 (stage 1: D appears and I_D/I_G increases, D' appears) and p.5-6 (Gamma_G about "
                 "14 cm-1 until the onset of stage 2)"),
            item("n1", "quantitative", 3, f"L_D from I_D/I_G (peak heights) with Cancado Eq. 4 at 532 nm: {ld_txt}",
                 "Cancado Eq. 4 (L_D^2 = (1.8 +- 0.5)e-9 lambda^4 (I_D/I_G)^-1, valid for L_D >= 10 nm)"),
            item("c1", "caveat", 1, "Uses the excitation-wavelength dependence (lambda^4 at 532 nm) rather than "
                 "constants for 514.5 nm; the same I_D/I_G means a different L_D at another laser line",
                 "Cancado abstract, Eq. 3-4"),
            item("f2", "finding", 3, "Dose 4 has a lower I_D/I_G than dose 3 but a much broader G (merged with "
                 "D') and no well-defined 2D: it is past the I_D/I_G maximum (stage 2, L_D below about 3 nm), so "
                 "the defect density is higher, not lower, and Eq. 4 does not apply",
                 "Cancado abstract and p.3 (maximum at L_D about 3 nm; stage 1 and 2 can share I_D/I_G but not "
                 "Gamma_G), Fig. 5c"),
            item("f3", "finding", 1, f"I_D/I_D' is about {ID_IDP_VACANCY:.0f} in the stage-1 spectra, which "
                 "Eckmann associates with vacancy-like defects (sp3 about 13, boundaries about 3.5), valid only "
                 "in the low-density regime", "Eckmann 2012 abstract"),
            item("c2", "caveat", 1, "States whether peak heights or areas are used; Cancado's relation is "
                 "calibrated on heights (I_D/I_G), and area ratios differ when D and G widths differ",
                 "Cancado p.1 (I_D/I_G heights vs A_D/A_G areas)"),
            item("q1", "question", 1, "Asks what the treatment is (ion bombardment, plasma, chemistry), since the "
                 "point-defect relation assumes point-like defects and the D/D' ratio depends on defect type",
                 "Cancado p.1 (point-like defects); Eckmann 2012 abstract"),
        ],
        wrong_claims=[
            wrong("w1", 2, "Concludes that dose 4 has fewer defects than dose 3, or gives it an L_D above 10 nm "
                  "from Eq. 4"),
            wrong("w2", 1, "Computes L_D with the 514.5 nm calibration (or ignores the laser wavelength)"),
            wrong("w3", 1, f"Treats the narrow spike near {spike_pos} cm-1 in dose {spike_dose} as a Raman band"),
        ],
        notes=(f"Synthetic, 532 nm. Stage-1 spectra (doses 1-3): I_D/I_G set from Cancado Eq. 4 for L_D "
               f"{targets} nm (curator choice), D at 1350 + 52 (E_L - 2.41 eV), 2D at 2700 + 104 (E_L - 2.41 eV) "
               f"(Cancado p.5 dispersion, Ferrari 2006 2D about 2700), G 1580, D' 1620 (Cancado p.2). FWHM D "
               f"{GAMMA_D}, G {GAMMA_G}, 2D {GAMMA_2D} (Cancado Fig. 5), D' {GAMMA_DP} (curator); 2D/G height "
               f"{H_2D_OVER_G} (curator reading of Cancado Fig. 1); I_D/I_D' {ID_IDP_VACANCY} (Eckmann, "
               f"vacancy-like). Dose 4 (stage 2): I_D/I_G = {r4:.2f} (same as dose 2), D FWHM 60, G at 1592 with "
               "FWHM 45 (merged G + D'), weak broad bumps at 2700 and 2930 (all curator values chosen to follow "
               "Cancado's qualitative stage-2 description). The L_D ranges propagate the +-0.5 prefactor "
               "uncertainty only. Defect type deliberately omitted from the context."))
    write_case(root, cid, inp, rubric, files)


# ================================================================ case 5: graphene laser heating
# Calizo et al. 2007, Nano Lett. 7, 2645, arXiv:0708.1223, abstract and Table I (single layer, 83 to 373 K, 488 nm):
# chi_G = -(1.6 +- 0.2)e-2 and chi_2D = -(3.4 +- 0.4)e-2 cm-1/K, omega = omega0 + chi T.
CALIZO = "Calizo, Balandin, Bao, Miao, Lau 2007, Nano Lett. 7, 2645, arXiv:0708.1223"
CHI_G, CHI_2D = -0.016, -0.034
DT_HEAT = {0.5: 0.0, 2.0: 50.0, 5.0: 125.0}  # K, curator: laser-induced temperature rise relative to 0.5 mW
WIDEN_PER_K = 0.03  # cm-1/K extra G FWHM, curator (no linewidth coefficient taken from a paper)
HEAT = {p: (CHI_G * t, CHI_2D * t, WIDEN_PER_K * t) for p, t in DT_HEAT.items()}  # power: dG, d2D, extra FWHM


def case_graphene_heating(root, rng):
    cid = "int-graphene-heating-01"
    lam = 532.0
    e_l = HC_EV_NM / lam
    g0 = LEE2012_ORIGIN[0]
    d0 = LEE2012_ORIGIN[1] + 2 * DISP_D * (e_l - E_5145)  # 2D disperses at about 2 x 52 cm-1/eV (Cancado p.5)
    files, spectra = {}, []
    for p, (dg, d2d, dw) in HEAT.items():
        x = axis(450.0, 3200.0, rng, step=(0.9, 1.1))
        peaks = [(g0 + dg + rng.normal(0, 0.2), GAMMA_G + dw, 1.0),
                 (d0 + d2d + rng.normal(0, 0.4), GAMMA_2D + 2 * dw, H_2D_OVER_G)]
        scale = 1500 * p  # signal scales with power (curator)
        y, _ = render(x, peaks, scale, rng, 25 * np.sqrt(p) + 15, si=(SI_LINE, 1.5))
        tag = f"{p:g}mW"
        files[f"spectrum_{tag}.csv"] = csv_text(x, y)
        spectra.append(dict(file=f"spectrum_{tag}.csv", label=f"{p:g} mW", conditions=cond(532, power_mW=p)))
    inp = dict(case_id=cid, kind="interpret", task="interpret", material="graphene", spectra=spectra,
               context="Exfoliated single-layer graphene on SiO2/Si, same spot, 532 nm, 100x objective, spectra "
                       "taken one after another at the three laser powers in the labels.",
               question="The G and 2D positions differ between these spectra. Is the graphene strained or doped, "
                        "and which spectrum should I trust for that analysis?")
    rubric = dict(
        case_id=cid,
        source=dict(paper=f"{CALIZO}; {CANCADO}; {LEE2012}",
                    dataset="synthetic (eval/synth/make_interpret_dev.py)",
                    locator="Calizo abstract and Table I (temperature coefficients); Cancado p.2 (power kept "
                            "about 1 mW to avoid heating); Lee 2012 (strain and doping from G and 2D)"),
        items=[
            item("f1", "finding", 3, "G and 2D both move down and broaden monotonically with laser power on the "
                 "same spot, while the Si line stays put: the trend tracks power, which points to laser heating "
                 "of the flake rather than a property of the graphene",
                 "Calizo 2007 p.3 (G and 2D shift down with increasing temperature) and p.4-5 (temperature "
                 "change from increased excitation power); Cancado p.2"),
            item("n2", "quantitative", 2, f"Estimates the temperature rise from the G shift with chi_G about "
                 f"{CHI_G} cm-1/K: about {DT_HEAT[2.0]:.0f} K at 2 mW and {DT_HEAT[5.0]:.0f} K at 5 mW above the "
                 "0.5 mW spectrum (the 2D with about -0.034 cm-1/K gives a consistent estimate)",
                 "Calizo 2007 abstract and Table I (single layer, 83 to 373 K)"),
            item("f2", "finding", 1, "In a G vs 2D position plot the power series moves along a line of slope "
                 "about 2 to 3 (Calizo's coefficients give 0.034/0.016, about 2.1), close to the strain line (about 2.2) of the Lee 2012 vector analysis, so that analysis "
                 "applied naively would misread the heating as strain", "measured; Lee 2012 (strain slope "
                 "2.2 +- 0.2, hole-doping slope 0.70 +- 0.05)"),
            item("c1", "caveat", 2, "Positions measured at different powers cannot be compared or fed into a "
                 "strain/doping (G vs 2D) analysis without correcting for heating; use the lowest power, or a "
                 "power series extrapolated to zero", "Lee 2012 (G-2D correlation method); Cancado p.2"),
            item("q1", "question", 1, "Recommends checking that the lowest-power spectrum is in the linear "
                 "(heating-free) regime, e.g. by measuring at one more lower power, and asks about the spot size "
                 "or power density", "Cancado p.2 (about 1 mW with a 100x objective to avoid heating)"),
            item("n1", "quantitative", 1, "Uses the 0.5 mW spectrum (G about 1582, 2D about 2668 cm-1 at 532 nm) as "
                 "the reference and finds it close to unstrained, undoped graphene within the uncertainty of the "
                 "laser-wavelength correction of 2D", "Lee 2012 origin (1581.6, 2676.9) at 514.5 nm; Cancado p.5 "
                 "(2D dispersion about 104 cm-1/eV)"),
        ],
        wrong_claims=[
            wrong("w1", 2, "Attributes the power-dependent shifts to strain or doping of the sample"),
            wrong("w2", 1, "Recommends the highest-power spectrum for analysis because it has the best signal"),
        ],
        notes=(f"Synthetic, 532 nm. Low-power spectrum: G {g0} (Lee 2012 origin; G is not dispersive in stage 1, "
               f"Cancado Fig. 5b) and 2D {d0:.1f} cm-1 (Lee 2012 origin 2676.9 at 514.5 nm moved to 532 nm with "
               f"2 x 52 cm-1/eV, Cancado p.5). FWHM G {GAMMA_G} (Cancado p.5-6), 2D {GAMMA_2D} (Fig. 5a reading). "
               f"Temperature rises {DT_HEAT} K (curator); shifts and broadening per power {HEAT} (dG, d2D, extra G FWHM in cm-1) are curator "
               "values from Calizo's coefficients and curator temperature rises; the extra width is curator. Calizo "
               "measured at 488 nm on graphene on SiO2/Si; applying the coefficients at 532 nm is an assumption. The "
               "Si line is not shifted. Items f2 and n1 depend on Lee 2012, whose numbers come from the "
               "verified-numbers file, not a re-reading."))
    write_case(root, cid, inp, rubric, files)


# ================================================================ case 6: experimental graphene on Au vs Cu
def read_zip_spectrum(zf, name):
    rows = []
    for line in zf.read(name).decode("latin1").splitlines():
        parts = line.split()
        try:
            rows.append((float(parts[0]), float(parts[1])))
        except (ValueError, IndexError):
            continue  # header lines ("X-Axis", units)
    a = np.array(sorted(rows))
    a = a[a[:, 0] >= 100.0]  # drop the laser-line region
    return csv_text(a[:, 0], a[:, 1].round(1))


def case_graphene_substrate(root, zip_path):
    cid = "int-graphene-substrate-01"
    zp = Path(zip_path)
    if not zp.exists():
        print("skip", cid, "(archive not found:", zp, ")")
        return
    files, spectra = {}, []
    with zipfile.ZipFile(zp) as zf:
        for metal in ("Au", "Cu"):
            files[f"spectrum_{metal}.csv"] = read_zip_spectrum(zf, f"S1/FigS1D {metal} exported_Raman.txt")
            spectra.append(dict(file=f"spectrum_{metal}.csv", label=f"on {metal}",
                                conditions=dict(laser_nm=None, temperature_K=295, power_mW=0.2,
                                                grating_g_per_mm=2400)))
    inp = dict(case_id=cid, kind="interpret", task="interpret", material="graphene", spectra=spectra,
               context="CVD graphene grown in situ on a gold droplet (high ethylene flux, MicroReactor) and on a "
                       "liquid copper droplet (UHV), each rapidly cooled (about 50 K/s) to room temperature and "
                       "measured on the metal. 0.2 mW, 2400 g/mm grating. Laser wavelength not recorded in the "
                       "data file.",
               question="Compare the two spectra. Is the layer graphene in both cases, and why does it look "
                        "different on Au and on Cu?")
    rubric = dict(
        case_id=cid,
        source=dict(paper=BUKVISOVA, dataset="Zenodo 14883846 (CC BY 4.0), 005_Data.zip, S1/FigS1D Au and Cu "
                                             "exported_Raman.txt", locator="Fig. S1D and caption; main text p.3"),
        items=[
            item("f1", "finding", 2, "Both spectra show G (near 1580 cm-1) and 2D (near 2680 to 2700 cm-1), "
                 "confirming graphene on both metals", "Bukvisova 2025 main text p.3 ('we have confirmed that "
                 "the layers ... are graphene'), Fig. S1D"),
            item("f2", "finding", 2, "The D peak (near 1345 to 1350 cm-1) is relatively stronger on Au "
                 "(I_D/I_G about 1 by peak height) than on Cu (about 0.6, poorly constrained because the Cu "
                 "signal is weak)",
                 "Fig. S1D caption ('Higher intensity D peak ... on Au'); ratio measured by the curator"),
            item("f3", "finding", 1, "Reports the authors' explanation: the stronger D on Au is likely related "
                 "to strain from the rapid solidification of the droplet, and labels it as their hypothesis",
                 "Fig. S1D caption"),
            item("c1", "caveat", 2, "Points out that the D band needs a defect (or edge) to be activated, so a "
                 "strong D means more Raman-active defects or domain edges in the spot; strain by itself shifts "
                 "G and 2D, and a strain explanation should be checked against the G and 2D positions",
                 f"{CANCADO} p.2 (D requires a defect for activation); {MOHIUDDIN} (strain shifts G and 2D)"),
            item("q1", "question", 1, "Asks for the laser wavelength, needed for any L_D estimate (I_D/I_G "
                 "scales with lambda^4) and for comparing 2D positions (2D disperses with excitation energy)",
                 f"{CANCADO} Eq. 4 and p.5"),
            item("c2", "caveat", 1, "The Cu spectrum has a much weaker signal, so its D/G ratio and peak widths "
                 "are poorly constrained; comparisons need error bars or longer integration",
                 "measured (Cu G height about 25 counts over a noise of about 9)"),
        ],
        wrong_claims=[
            wrong("w1", 1, "Gives a quantitative L_D or defect density without knowing the laser wavelength"),
            wrong("w2", 1, "States as established fact that the D peak on Au is caused by strain"),
        ],
        notes=("Experimental, unchanged except for dropping shifts below 100 cm-1 and sorting x ascending. The "
               "paper states only what items f1 and f3 and the caption say; it gives no laser wavelength, no "
               "layer number and no peak positions. Curator fits (Lorentzians on a linear baseline): Au D 1344.4, "
               "G 1580.3, 2D 2681.1 cm-1, D/G heights 111/117 about 0.95, 2D/G about 2.9; Cu G about 1580 to "
               "1587 (height about 22 to 26 counts, noise sd about 9), 2D 2695.7 (height about 50), D weak (about "
               "14 counts, poorly constrained). The Au spectrum is also used by the identification case "
               "dev/exp-graphene-01."))
    write_case(root, cid, inp, rubric, files)


# ================================================================ case 7: hBN monolayer vs bulk
def case_hbn_thickness(root, rng):
    cid = "int-hBN-thickness-01"
    files, spectra = {}, []
    # flake 1 = bulk-like thick flake, flake 2 = monolayer (label order fixed; labels carry no thickness)
    for lab, pos, fwhm, h, si_h, snr in (("1", HBN_BULK, HBN_BULK_FWHM, 1.0, 0.3, 80),
                                         ("2", HBN_BULK + HBN_1L_SHIFT, HBN_1L_FWHM, 0.06, 4.0, 15)):
        x = axis(450.0, 1650.0, rng, step=(0.6, 0.8))
        y, _ = render(x, [(pos + rng.normal(0, 0.2), fwhm, h)], rng.uniform(3000, 6000), rng, snr / h,
                      si=(SI_LINE, si_h), fluo=(0.05, 0.2))
        files[f"spectrum_flake{lab}.csv"] = csv_text(x, y)
        spectra.append(dict(file=f"spectrum_flake{lab}.csv", label=f"flake {lab}", conditions=cond(514.5)))
    inp = dict(case_id=cid, kind="interpret", task="interpret", material="hBN", spectra=spectra,
               context="Exfoliated hBN flakes on Si with 290 nm SiO2, 514.5 nm, same integration time and "
                       "power. Flake 2 is barely visible in the optical microscope.",
               question="Is flake 2 a monolayer? How sure can we be from Raman?")
    rubric = dict(
        case_id=cid,
        source=dict(paper=GORBACHEV, dataset="synthetic (eval/synth/make_interpret_dev.py)",
                    locator="p.1, p.3-5 text, Fig. 4a,b (preprint pages)"),
        items=[
            item("f1", "finding", 2, f"The E2g band of flake 2 is upshifted by about {HBN_1L_SHIFT:.0f} cm-1 "
                 f"relative to flake 1 (about {HBN_BULK:.0f} cm-1) and is broader, consistent with a monolayer",
                 "Gorbachev 2011 p.1, p.4 (HWHM 10 to 12 cm-1 for 1L vs 9 for bulk)"),
            item("c1", "caveat", 2, "The monolayer upshift is small (2 to 4 cm-1) and varies from sample to "
                 "sample by about +-2 cm-1, so position alone is not conclusive", "Gorbachev 2011 p.4, Fig. 4b "
                 "caption"),
            item("c2", "caveat", 1, "Random strain from cleavage shifts the band (red shifts of typically 1 to 2 cm-1, dominant "
                 "in bilayers), comparable to the monolayer upshift", "Gorbachev 2011 p.1, p.5 conclusion ('not "
                 "as unambiguous as the Raman signatures for mono- and bi-layer graphene')"),
            item("f2", "finding", 1, "The much weaker E2g signal of flake 2 under the same conditions, compared "
                 "on the same substrate, supports a very thin flake; intensity is the more useful layer measure "
                 "here: the integrated intensity is proportional to the layer number for the first few layers "
                 "once the spectrometer is calibrated for the substrate", "Gorbachev 2011 p.3-4, Fig. 4a inset"),
            item("q1", "question", 1, "Suggests an independent check (optical contrast at a suitable oxide "
                 "thickness, or AFM) and calibration against the Si line", "Gorbachev 2011 (optical contrast); "
                 f"Si line {CASTELLANOS} p.7"),
        ],
        wrong_claims=[
            wrong("w1", 2, "Declares flake 2 a monolayer with certainty from the peak position alone"),
            wrong("w2", 1, "Treats a bilayer as upshifted like a monolayer (Gorbachev: 2L usually downshifted 1 "
                  "to 2 cm-1, Gorbachev p.1)"),
        ],
        notes=(f"Synthetic, 514.5 nm. Flake 1 = bulk (E2g {HBN_BULK}, FWHM {HBN_BULK_FWHM}); flake 2 = monolayer "
               f"(+{HBN_1L_SHIFT} cm-1, FWHM {HBN_1L_FWHM}), from Gorbachev 2011 (p.1, p.4; widths given there as "
               "HWHM). Curator: monolayer height 0.06 of the thick flake, Si heights, noise."))
    write_case(root, cid, inp, rubric, files)


def main():
    ap = argparse.ArgumentParser(description="Generate dev interpretation cases (int-*) with rubrics into "
                                             "<out>/dev_interpret/ (format: data/test_set/INTERPRET.md).")
    ap.add_argument("--out", default="data/test_set", help="test-set root; cases go to <out>/dev_interpret/")
    ap.add_argument("--seed", type=int, default=20261022, help="random seed; output is deterministic for a seed")
    ap.add_argument("--graphene-zip", default="data/raw/spectra/graphene/005_Data.zip",
                    help="Zenodo 14883846 data archive (Bukvisova et al. 2025), read in place")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    case_mos2_thickness(args.out, rng)
    case_mos2_calibration(args.out, rng)
    case_ws2_resonance(args.out, rng)
    case_graphene_defects(args.out, rng)
    case_graphene_heating(args.out, rng)
    case_graphene_substrate(args.out, args.graphene_zip)
    case_hbn_thickness(args.out, rng)


if __name__ == "__main__":
    main()
