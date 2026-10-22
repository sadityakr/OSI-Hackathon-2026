"""Generate synthetic property cases (graphene defect density and type, MoS2 layer number) from published relations.

Identification cases do not exercise the relation registry. These cases do: each spectrum is built so that a
published Raman relation yields a known property (inter-defect distance L_D, defect level, defect type, layer
number), and the answer key carries that relation's paper and locator. Every number used below was read from the
cited paper; where a value had to be chosen by the curator, the truth notes say so. The cases go to dev_hard/ so
the build loop's contract tests, which iterate over dev/, are not affected.

Input:
    Nothing but the constants in this file, each traceable to the paper named next to it:
    Cancado et al. 2011, Nano Lett. 11, 3190, arXiv:1105.0175 (L_D relation, Eq. 4; peak widths, Fig. 5);
    Eckmann et al. 2012, Nano Lett. 12, 3925, arXiv:1207.2058 (I(D)/I(D') per defect type, p. 6);
    Lee et al. 2010, ACS Nano 4, 2695, arXiv:1005.2509 (MoS2 E2g and A1g positions, Fig. 4b; widths, Fig. 3b).
Process:
    For each case, place Lorentzian peaks at the published positions with published widths, set peak heights so
    the relation gives the intended property, then add a sloped and curved fluorescence baseline and Gaussian
    noise. The truth L_D range propagates the paper's +-0.5 uncertainty on the Eq. 4 prefactor.
Output:
    <out>/dev_hard/syn-graphene-01..03 and syn-MoS2-03..04, each with spectrum.csv, input.json, truth.json
    (schema in data/test_set/README.md). Deterministic for a given --seed.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # make_synthetic lives next to this file

from make_synthetic import SI_LINE, lorentz, write_case  # noqa: E402

SPLIT = "dev_hard"
HC_EV_NM = 1239.84  # eV nm, converts laser wavelength to photon energy
FLATTERS = "Synthetic from published relation; flatters the tools arm (the tools encode the same relation)."

# Cancado 2011, arXiv:1105.0175
CANCADO = "Cancado, Jorio, Martins Ferreira, Stavale, Achete, Capaz, Moutinho, Lombardo, Kulmala, Ferrari 2011, " \
          "Nano Lett. 11, 3190, doi:10.1021/nl201432g, arXiv:1105.0175"
LD_PREFACTOR = (1.8e-9, 0.5e-9)  # nm^-2 ... Eq. 4: L_D^2 (nm^2) = (1.8 +- 0.5) 1e-9 lambda^4 (I_D/I_G)^-1, lambda in nm
POS_D_5145, POS_G, POS_DP = 1350.0, 1580.0, 1620.0  # cm-1, p. 2 text (D ~1350, G ~1580, D' ~1620 at 514.5 nm)
DISP_D = 52.0  # cm-1/eV, p. 5: d(omega_D)/dE_L ~ 52 cm-1/eV, and the 2D disperses twice as fast
E_5145 = 2.41  # eV, the 514.5 nm line as stated in the paper
GAMMA_D, GAMMA_G, GAMMA_2D = 15.0, 14.0, 32.0  # cm-1, Fig. 5a (Gamma_D ~15, Gamma_2D ~30-35 for L_D > 5 nm),
#                                               Fig. 5c and p. 5 text (Gamma_G ~14 cm-1 in stage 1)
GAMMA_DP = 14.0  # cm-1, D' width: not given in either paper; curator's choice equal to Gamma_G
H_2D_OVER_G = 3.0  # 2D/G height ratio read approximately from Fig. 1 (L_D = 14 and 24 nm traces); curator reading

# Eckmann 2012, arXiv:1207.2058
ECKMANN = "Eckmann, Felten, Mishchenko, Britnell, Krupke, Novoselov, Casiraghi 2012, Nano Lett. 12, 3925, " \
          "doi:10.1021/nl300901a, arXiv:1207.2058"
ID_IDP = {"sp3": 13.0, "vacancy-like": 7.0, "boundary-like": 3.5}  # p. 6 (and abstract): I(D)/I(D') per defect type

# Lee 2010, arXiv:1005.2509, read from Fig. 4b (532 nm, supported on SiO2/Si, blue triangles), +-0.3 cm-1 reading
LEE = "Lee, Yan, Brus, Heinz, Hone, Ryu 2010, ACS Nano 4, 2695, doi:10.1021/nn1003937, arXiv:1005.2509"
MOS2 = {  # layers: (E2g pos, A1g pos, Gamma_E (Fig. 3b), Gamma_A (Fig. 3b), integrated E/A ratio (Fig. 3a right axis))
    1: (383.8, 403.4, 2.0, 3.9, 0.87),
    3: (382.3, 405.9, 2.3, 4.9, 1.30),
}


def defect_level(ld_nm):
    """Curator's rule (stated in every truth note): L_D >= 25 nm low, 10 to 25 nm medium, below 10 nm high.

    Cancado 2011 calls L_D >= 10 nm the low-defect-density regime where Eq. 4 holds; the low/medium split at 25 nm
    is ours, chosen so that the two density cases fall in distinct classes.
    """
    return "low" if ld_nm >= 25 else ("medium" if ld_nm >= 10 else "high")


def ld_from_ratio(ratio, lam_nm, prefactor):
    return float(np.sqrt(prefactor * lam_nm ** 4 / ratio))


def ratio_for_ld(ld_nm, lam_nm):
    return LD_PREFACTOR[0] * lam_nm ** 4 / ld_nm ** 2


def background_and_noise(x, y, scale, rng, snr):
    """Fluorescence-like baseline (offset, slope, broad hump) plus Gaussian noise; snr = scale / noise sigma."""
    lo, hi = x[0], x[-1]
    y = y + scale * (rng.uniform(0.05, 0.3) + rng.uniform(-0.05, 0.15) * (x - lo) / (hi - lo)
                     + rng.uniform(0.1, 0.4) * np.exp(-(((x - rng.uniform(lo, hi)) / rng.uniform(400, 900)) ** 2)))
    y = y + rng.normal(0, scale / snr, size=x.size)
    return np.round(np.clip(y, 0, None), 1)


def csv_rows(x, y):
    return "shift_cm1,intensity\n" + "\n".join(f"{a:.2f},{b}" for a, b in zip(x, y))


def base_input(case_id, laser_nm, substrate, question):
    return dict(case_id=case_id, kind="single", task="identify", material_hint=None, laser_nm=laser_nm,
                temperature_K=295, substrate=substrate, geometry="backscattering, beam along the layer normal",
                question=question)


GRAPHENE_Q = ("Which material is this? Assign the peaks and characterize the sample: defects (level, mean "
              "inter-defect distance L_D if it can be estimated, and their likely type).")


def graphene_case(case_id, lam_nm, ratio_dg, ratio_ddp, rng, snr, props, extra_note, figure):
    e_l = HC_EV_NM / lam_nm
    pos_d = POS_D_5145 + DISP_D * (e_l - E_5145) + rng.normal(0, 1.0)
    pos_2d = 2 * pos_d + rng.normal(0, 2.0)  # 2D is the overtone of D (Cancado p. 2) and disperses twice as fast
    pos_g = POS_G + rng.normal(0, 1.0)
    pos_dp = POS_DP + rng.normal(0, 1.0)
    x = np.arange(1100.0, 3000.0, rng.uniform(0.9, 1.2))
    amp = rng.uniform(3000, 12000)  # G height in counts
    h = dict(D=ratio_dg, G=1.0, Dp=ratio_dg / ratio_ddp, D2=H_2D_OVER_G)
    y = amp * (h["D"] * lorentz(x, pos_d, GAMMA_D) + h["G"] * lorentz(x, pos_g, GAMMA_G)
               + h["Dp"] * lorentz(x, pos_dp, GAMMA_DP) + h["D2"] * lorentz(x, pos_2d, GAMMA_2D))
    y = background_and_noise(x, y, amp, rng, snr)
    peaks = [dict(position_cm1=round(pos_d, 1), tolerance_cm1=8.0, irrep=None, label="D"),
             dict(position_cm1=round(pos_g, 1), tolerance_cm1=5.0, irrep="E2g", label="G"),
             dict(position_cm1=round(pos_dp, 1), tolerance_cm1=6.0, irrep=None, label="D'"),
             dict(position_cm1=round(pos_2d, 1), tolerance_cm1=12.0, irrep=None, label="2D")]
    inp = base_input(case_id, lam_nm, "SiO2/Si", GRAPHENE_Q)
    truth = dict(case_id=case_id, material="graphene", formula="C", polytype=None, spacegroup=None,
                 pointgroup=None, hint_is_correct=None, layers=1, peaks=peaks, properties=props,
                 source=dict(kind="synthetic", dataset="generated by eval/synth/make_property_dev.py",
                             paper=CANCADO + "; " + ECKMANN, figure=figure,  # Eckmann sets I_D/I_D'
                             licence="CC BY 4.0 (generated data)"),
                 notes=f"{FLATTERS} Heights (peak maxima, as the papers use): I_D/I_G = {ratio_dg:.4f}, "
                       f"I_D/I_D' = {ratio_ddp:.1f}, I_2D/I_G = {H_2D_OVER_G} (approximate reading of Cancado "
                       f"Fig. 1). Widths (FWHM, cm-1): D {GAMMA_D}, G {GAMMA_G}, D' {GAMMA_DP} (curator choice, "
                       f"not in the papers), 2D {GAMMA_2D}. D position = 1350 + 52 (E_L - 2.41 eV) cm-1 "
                       f"(Cancado p. 2 and p. 5), 2D = 2 x D. Defect level rule (curator, not the paper's): L_D >= "
                       f"25 nm low, 10-25 nm medium, < 10 nm high; Cancado calls L_D >= 10 nm the low-density "
                       f"regime. Noise: G height / sigma = {snr:.0f}. {extra_note}")
    write_case(Path(OUT), SPLIT, case_id, inp, truth, csv_rows(x, y))
    print(SPLIT, case_id, props)


def mos2_case(case_id, layers, rng, snr):
    pe, pa, ge, ga, area_ratio = MOS2[layers]
    pe += rng.normal(0, 0.2)
    pa += rng.normal(0, 0.2)
    x = np.arange(150.0, 650.0, rng.uniform(0.5, 0.7))
    amp = rng.uniform(2000, 8000)  # E2g height in counts
    h_e, h_a = 1.0, (1.0 / area_ratio) * ge / ga  # Lorentz area ~ height x FWHM, so height ratio = area ratio x widths
    y = amp * (h_e * lorentz(x, pe, ge) + h_a * lorentz(x, pa, ga)
               + rng.uniform(1.0, 3.0) * lorentz(x, SI_LINE + rng.normal(0, 0.2), 3.5))
    y = background_and_noise(x, y, amp, rng, snr)
    peaks = [dict(position_cm1=round(pe, 1), tolerance_cm1=1.5, irrep="E2g", label="E^1_2g"),
             dict(position_cm1=round(pa, 1), tolerance_cm1=1.5, irrep="A1g", label="A1g"),
             dict(position_cm1=SI_LINE, tolerance_cm1=2.0, irrep="F2g", label="Si substrate", substrate=True)]
    inp = base_input(case_id, 532, "SiO2/Si (285 nm oxide)",
                     "Which material is this? Assign the peaks and determine the number of layers.")
    truth = dict(case_id=case_id, material="MoS2", formula="MoS2", polytype="2H", spacegroup="P6_3/mmc (194)",
                 pointgroup="6/mmm", hint_is_correct=None, layers=layers, peaks=peaks,
                 properties={"layers": layers},
                 source=dict(kind="synthetic", dataset="generated by eval/synth/make_property_dev.py", paper=LEE,
                             figure="Fig. 4b (E2g and A1g positions vs thickness, 532 nm, supported, blue "
                                    "triangles), Fig. 3b (linewidths), Fig. 3a (integrated E2g/A1g ratio)",
                             licence="CC BY 4.0 (generated data)"),
                 notes=f"{FLATTERS} Positions read by the curator from Lee 2010 Fig. 4b to about +-0.3 cm-1, then "
                       f"jittered by 0.2 cm-1: E2g {MOS2[layers][0]}, A1g {MOS2[layers][1]}, "
                       f"difference {MOS2[layers][1] - MOS2[layers][0]:.1f} cm-1. Widths (FWHM) E2g {ge}, A1g {ga} "
                       f"cm-1 from Fig. 3b (measured at 514.5 nm with 2.7 cm-1 resolution). Integrated E2g/A1g "
                       f"ratio {area_ratio} from Fig. 3a. Neighbouring layer numbers differ by only 1 to 2.5 cm-1 "
                       f"in the mode spacing, so this case needs sub-cm-1 fitting. Noise: E2g height / sigma = "
                       f"{snr:.0f}.")
    write_case(Path(OUT), SPLIT, case_id, inp, truth, csv_rows(x, y))
    print(SPLIT, case_id, {"layers": layers})


def main():
    global OUT
    ap = argparse.ArgumentParser(description="Generate synthetic property cases (graphene L_D, defect level and "
                                             "type; MoS2 layer number) from published relations into "
                                             "<out>/dev_hard/.")
    ap.add_argument("--out", default="data/test_set", help="test-set root; cases go to <out>/dev_hard/")
    ap.add_argument("--seed", type=int, default=20261023, help="random seed; output is deterministic for a seed")
    args = ap.parse_args()
    OUT = args.out
    rng = np.random.default_rng(args.seed)

    lo_pf, hi_pf = LD_PREFACTOR[0] - LD_PREFACTOR[1], LD_PREFACTOR[0] + LD_PREFACTOR[1]
    # Two defect densities at 532 nm (Cancado Eq. 4), vacancy-like D/D' ratio as for Cancado's Ar+-bombarded samples.
    for case_id, ld_target, snr in (("syn-graphene-01", 30.0, 60), ("syn-graphene-02", 17.0, 40)):
        r = ratio_for_ld(ld_target, 532.0)
        rng_ld = [round(ld_from_ratio(r, 532.0, lo_pf), 1), round(ld_from_ratio(r, 532.0, hi_pf), 1)]
        props = {"L_D_nm": rng_ld, "defect_level": defect_level(ld_target)}
        graphene_case(case_id, 532.0, r, ID_IDP["vacancy-like"], rng, snr, props,
                      f"Intended L_D = {ld_target} nm; the range uses the Eq. 4 prefactor 1.8 +- 0.5.",
                      "Eq. 4 (L_D from I_D/I_G and laser wavelength, valid for L_D >= 10 nm); Fig. 5a,c (widths)")

    # Defect type (Eckmann p. 6: I(D)/I(D') ~ 13 sp3, ~ 7 vacancy-like, ~ 3.5 boundary-like), 514.5 nm as in the paper.
    r = 0.6
    ld = ld_from_ratio(r, 514.5, LD_PREFACTOR[0])
    graphene_case("syn-graphene-03", 514.5, r, ID_IDP["vacancy-like"], rng, 150,
                  {"defect_level": defect_level(ld), "defect_type": "vacancy-like"},
                  f"Defect type: vacancy-like (Eckmann 2012, I(D)/I(D') ~ 7; sp3 ~ 13, boundaries ~ 3.5). "
                  f"defect_type is not scored by eval/score.py. Implied L_D = {ld:.1f} nm (Cancado Eq. 4).",
                  "Eckmann p. 6 and abstract (I(D)/I(D') per defect type, 514.5 nm, stage 1); "
                  "Cancado Eq. 4 for the defect level")

    mos2_case("syn-MoS2-03", 1, rng, 40)
    mos2_case("syn-MoS2-04", 3, rng, 40)


OUT = "data/test_set"

if __name__ == "__main__":
    main()
