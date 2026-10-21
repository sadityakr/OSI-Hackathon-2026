"""Graphene relations: defect distance from I(D)/I(G), strain and doping from the G and 2D positions, layer test from the 2D band shape.

These are the three standard readings of a graphene Raman spectrum. Each relation uses the equation and the
constants printed in its source paper, with the validity range the paper states; where the paper leaves a number
out (a linear doping rate, a single-layer 2D width) the relation reports less instead of filling the gap.

Input: peak-height ratios, peak positions in cm-1, the number of Lorentzian components of the 2D band, the laser
wavelength in nm (see each relation's `inputs`).
Process: validity check, then the closed-form equation (L_D), a 2x2 vector decomposition (strain and doping), or
a lookup of the 2D line shape (layer test).
Output: RelationResult values per relation (L_D_nm and n_D_cm2; strain_percent and doping_type; layer class).
"""

from __future__ import annotations

import math

import numpy as np

from .base import Relation, SelfTest, Source

CANCADO_2011 = Source(citation="Cancado et al. 2011, Nano Lett. 11, 3190",
                      locator="Eqs. (3) to (6), p. 4 of arXiv 1105.0175v2; validity statement p. 4",
                      doi="10.1021/nl201432g", arxiv="1105.0175")

LEE_2012 = Source(citation="Lee, Ahn, Shim, Lee, Ryu 2012, Nat. Commun. 3, 1024",
                  locator="origin (1581.6, 2676.9) p. 4; unit vectors e_T (slope 2.2) and e_H (slope 0.70) p. 5; "
                          "G strain sensitivities in the Fig. 3 legend; 514 nm limit p. 9 of arXiv 1209.0234",
                  arxiv="1209.0234")  # DOI not verified in this build; the arXiv id locates the paper

FERRARI_2006 = Source(citation="Ferrari et al. 2006, Phys. Rev. Lett. 97, 187401",
                      locator="p. 2 (single sharp 2D peak in graphene, 4 components in bilayer, 2 in bulk graphite) "
                              "and Fig. 2 of arXiv cond-mat/0606284",
                      arxiv="cond-mat/0606284")  # DOI not verified in this build

HC_NM_EV = 1239.84  # h c in eV nm, converts laser wavelength to photon energy


class GrapheneDefectDistance(Relation):
    name = "graphene_defect_distance_from_ID_IG"
    material = "graphene"
    aliases = ("monolayer graphene", "single-layer graphene")
    inputs = {"I_D_over_I_G": "ratio of the D and G peak HEIGHTS (not areas)",
              "laser_nm": "excitation wavelength in nm"}
    outputs = {"L_D_nm": "mean distance between point defects in nm (Eq. 4)",
               "L_D_err_nm": "uncertainty from the +-0.5 on the 1.8e-9 constant",
               "n_D_cm2": "point-defect density in cm-2 (Eq. 6)",
               "L_D_nm_energy_form": "the same from Eq. 3 (laser energy form), as a cross-check"}
    equation = ("L_D^2 [nm^2] = (1.8 +- 0.5) x 1e-9 lambda_L^4 (I_D/I_G)^-1 (Eq. 4), lambda_L laser wavelength in "
                "nm; n_D [cm-2] = (1.8 +- 0.5) x 1e22 / lambda_L^4 (I_D/I_G) (Eq. 6); equivalently L_D^2 = "
                "(4.3 +- 1.3) x 1e3 / E_L^4 (I_D/I_G)^-1 with E_L in eV (Eq. 3). I_D, I_G are peak heights.")
    validity = {"L_D_nm": ">= 10 (low-defect regime, stage 1)", "laser": "visible excitation (paper: 514.5, "
                "632.8, 785 nm)", "laser_nm": [400.0, 786.0], "sample": "single-layer graphene, point defects"}
    source = CANCADO_2011
    # The paper prints no (L_D, I_D/I_G) pair in its text (the data are plotted in Figs. 3, 4). The self-tests
    # check Eq. 4 against the independently printed energy form Eq. 3 and n_D against Eq. 5, at the three lasers
    # of the paper (p. 2: 2.41 eV / 514.5 nm, 1.96 eV / 632.8 nm, 1.58 eV / 785 nm).
    self_tests = [
        SelfTest({"I_D_over_I_G": 0.5, "laser_nm": 514.5}, {"L_D_nm": 15.967, "n_D_cm2": 1.231e11},
                 {"L_D_nm": 0.3, "n_D_cm2": 0.08e11}, locator="Eq. 3 and Eq. 5 at E_L = 2.41 eV"),
        SelfTest({"I_D_over_I_G": 1.0, "laser_nm": 632.8}, {"L_D_nm": 17.070, "n_D_cm2": 1.077e11},
                 {"L_D_nm": 0.3, "n_D_cm2": 0.08e11}, locator="Eq. 3 and Eq. 5 at E_L = 1.96 eV"),
        SelfTest({"I_D_over_I_G": 2.0, "laser_nm": 785.0}, {"L_D_nm": 18.574, "n_D_cm2": 0.910e11},
                 {"L_D_nm": 0.3, "n_D_cm2": 0.08e11}, locator="Eq. 3 and Eq. 5 at E_L = 1.58 eV"),
    ]
    out_of_range_example = {"I_D_over_I_G": 4.0, "laser_nm": 514.5}  # gives L_D about 5.6 nm < 10 nm
    caveats = ["I_D/I_G rises with defect density until L_D is about 3 nm and falls below it (Cancado 2011, "
               "abstract), so one ratio maps to two L_D values; this relation assumes the low-defect branch. "
               "A broad G band or a D band comparable in width to G points to the high-defect branch.",
               "Equations hold for point defects; edges and grain boundaries also give a D band."]

    def check(self, I_D_over_I_G, laser_nm):
        if I_D_over_I_G <= 0:
            return "I_D/I_G must be positive (no D band means no measurable defect density with this relation)"
        lo, hi = self.validity["laser_nm"]
        if not lo <= laser_nm <= hi:
            return (f"laser {laser_nm} nm outside {lo} to {hi} nm; Cancado 2011 states validity for visible "
                    "excitation and measured at 514.5, 632.8 and 785 nm")
        return None

    def compute(self, I_D_over_I_G, laser_nm):
        r, lam = float(I_D_over_I_G), float(laser_nm)
        L_D = math.sqrt(1.8e-9 * lam**4 / r)
        out = {"L_D_nm": L_D, "L_D_err_nm": L_D * 0.5 * (0.5 / 1.8),  # d(L_D)/L_D = 1/2 d(C)/C
               "n_D_cm2": 1.8e22 / lam**4 * r,
               "L_D_nm_energy_form": math.sqrt(4.3e3 / (HC_NM_EV / lam) ** 4 / r),
               "I_D_over_I_G": r, "laser_nm": lam}
        if L_D < 10.0:
            out["_not_applicable"] = (f"L_D = {L_D:.1f} nm is below 10 nm, outside the stated validity "
                                      "(L_D >= 10 nm, Cancado 2011 p. 4)")
        return out


class GrapheneStrainDoping(Relation):
    name = "graphene_strain_doping_from_G_2D"
    material = "graphene"
    aliases = GrapheneDefectDistance.aliases
    inputs = {"omega_G_cm1": "G peak position in cm-1", "omega_2D_cm1": "2D peak position in cm-1"}
    optional_inputs = {"laser_nm": "excitation wavelength in nm (must be 514 nm)",
                       "strain_type": "'uniaxial' (default) or 'biaxial'; sets the G shift per % strain"}
    outputs = {"delta_omega_G_strain_cm1": "G shift along the strain direction e_T",
               "delta_omega_G_doping_cm1": "G shift along the hole-doping direction e_H",
               "strain_percent": "strain in %, tensile positive",
               "doping_type": "'hole' or 'undetermined (low density)'",
               "a_cm1": "length along e_T", "b_cm1": "length along e_H"}
    equation = ("OP = (omega_G - 1581.6, omega_2D - 2676.9) = a e_T + b e_H, with unit vectors e_T along slope "
                "d(omega_2D)/d(omega_G) = 2.2 (strain) and e_H along slope 0.70 (hole doping). Strain from the G "
                "part of a e_T: epsilon [%] = delta_omega_G_strain / (-23.5) uniaxial or / (-69.1) biaxial.")
    validity = {"laser_nm": [513.0, 516.0], "sample": "single-layer graphene",
                "doping": "holes only (the paper excludes electron doping)",
                "omega_G_cm1": [1560.0, 1610.0], "omega_2D_cm1": [2620.0, 2720.0]}
    source = LEE_2012
    slope_strain, slope_hole = 2.2, 0.70
    origin = (1581.6, 2676.9)
    g_per_percent = {"uniaxial": -23.5, "biaxial": -69.1}
    doping_threshold_cm1 = 1.0  # design choice: G-shift doping parts below this are within the nonlinear region
    self_tests = [
        SelfTest({"omega_G_cm1": 1581.6, "omega_2D_cm1": 2676.9, "laser_nm": 514.5},
                 {"strain_percent": 0.0, "delta_omega_G_doping_cm1": 0.0},
                 {"strain_percent": 1e-9, "delta_omega_G_doping_cm1": 1e-9},
                 locator="p. 4: freestanding graphene F1, strain-free and nearly undoped, is the origin"),
        SelfTest({"omega_G_cm1": 1591.5, "omega_2D_cm1": 2693.0, "laser_nm": 514.5}, {"doping_type": "hole"},
                 locator="p. 7: sample K4 after 400 C, (1591.5, 2693), 'strong hole doping'"),
        SelfTest({"omega_G_cm1": 1598.4, "omega_2D_cm1": 2698.0, "laser_nm": 514.5}, {"doping_type": "hole"},
                 locator="p. 7: sample K4 after 500 C, (1598.4, 2698), 'strong hole doping'"),
    ]
    out_of_range_example = {"omega_G_cm1": 1585.0, "omega_2D_cm1": 2640.0, "laser_nm": 633.0}
    caveats = ["Carrier density is not converted to cm-2: the source maps G shift to n along a nonlinear "
               "measured trajectory, not a linear rate (Lee 2012, Fig. 3 legend).",
               "Near the origin (|n| about 1e12 cm-2) the decomposition is ambiguous; errors up to 0.03 % strain "
               "and 1.5e12 cm-2 (Lee 2012, pp. 5 to 6).",
               "Strain sensitivities -23.5 (uniaxial) and -69.1 +- 3.4 cm-1/% (biaxial) are quoted by Lee 2012 "
               "from other references (Fig. 3 legend); the strain type must be known."]

    def check(self, omega_G_cm1, omega_2D_cm1, laser_nm=None, strain_type=None):
        if laser_nm is not None and not 513.0 <= laser_nm <= 516.0:
            return (f"laser {laser_nm} nm: the 2D band disperses with laser energy, so the origin and slopes "
                    "hold only for 514 nm excitation (Lee 2012, p. 9)")
        if strain_type is not None and strain_type not in self.g_per_percent:
            return f"strain_type must be one of {list(self.g_per_percent)}"
        for key, val in (("omega_G_cm1", omega_G_cm1), ("omega_2D_cm1", omega_2D_cm1)):
            lo, hi = self.validity[key]
            if not lo <= val <= hi:
                return f"{key} = {val} outside {lo} to {hi} cm-1; not a graphene G/2D pair at 514 nm"
        return None

    def compute(self, omega_G_cm1, omega_2D_cm1, laser_nm=None, strain_type=None):
        e_T = np.array([1.0, self.slope_strain]) / math.hypot(1.0, self.slope_strain)
        e_H = np.array([1.0, self.slope_hole]) / math.hypot(1.0, self.slope_hole)
        op = np.array([omega_G_cm1 - self.origin[0], omega_2D_cm1 - self.origin[1]])
        a, b = np.linalg.solve(np.column_stack([e_T, e_H]), op)
        g_strain, g_doping = a * e_T[0], b * e_H[0]
        kind = strain_type or "uniaxial"
        out = {"a_cm1": float(a), "b_cm1": float(b),
               "delta_omega_G_strain_cm1": float(g_strain), "delta_omega_G_doping_cm1": float(g_doping),
               "strain_percent": float(g_strain / self.g_per_percent[kind]) + 0.0, "strain_type": kind,
               "_notes": [] if strain_type else ["strain_type not given; uniaxial sensitivity assumed"]}
        if g_doping > self.doping_threshold_cm1:
            out["doping_type"] = "hole"
        elif g_doping >= -self.doping_threshold_cm1:
            out["doping_type"] = "undetermined (low density)"
        else:
            out["_not_applicable"] = (f"the point lies on the electron-doping side of the strain line "
                                      f"(G doping part {g_doping:.1f} cm-1); the source covers hole doping only")
        return out


class GrapheneLayersFrom2DShape(Relation):
    name = "graphene_layers_from_2D_shape"
    material = "graphene"
    aliases = GrapheneDefectDistance.aliases
    inputs = {"n_2D_components": "number of Lorentzian components needed to fit the 2D band (1, 2 or 4)"}
    optional_inputs = {"I_2D_over_I_G": "ratio of the 2D and G peak heights",
                       "laser_nm": "excitation wavelength in nm"}
    outputs = {"layer_class": "'monolayer', 'bilayer' or 'bulk graphite (or more than 5 layers)'",
               "confidence": "high, moderate or low"}
    equation = ("Line-shape lookup (Ferrari 2006, p. 2): one sharp 2D component about 4 times the G height -> "
                "monolayer; four components (2D1B, 2D1A, 2D2A, 2D2B) -> bilayer; two components 2D1, 2D2 at about "
                "1/4 and 1/2 of the G height -> bulk graphite.")
    validity = {"n_2D_components": [1, 2, 4], "laser_nm": [510.0, 640.0],
                "sample": "Bernal-stacked graphene; turbostratic graphite also shows a single (twice as wide) 2D peak"}
    source = FERRARI_2006
    classes = {1: "monolayer", 4: "bilayer", 2: "bulk graphite (or more than 5 layers)"}
    self_tests = [
        SelfTest({"n_2D_components": 1, "I_2D_over_I_G": 4.0}, {"layer_class": "monolayer", "confidence": "high"},
                 locator="p. 2: 'a single, sharp 2D peak in graphene, roughly 4 times more intense than the G peak'"),
        SelfTest({"n_2D_components": 4}, {"layer_class": "bilayer"}, locator="p. 2 and Fig. 2e: bilayer 2D has 4 "
                 "components"),
        SelfTest({"n_2D_components": 2}, {"layer_class": "bulk graphite (or more than 5 layers)"},
                 locator="p. 2: 'The 2D peak in bulk graphite consists of two components 2D1 and 2D2'"),
    ]
    out_of_range_example = {"n_2D_components": 1, "laser_nm": 785.0}
    caveats = ["Spectra of more than 5 layers are hardly distinguishable from bulk graphite (Ferrari 2006, p. 2); "
               "3 to 5 layers are not classified by this relation.",
               "Turbostratic graphite has a single 2D peak with FWHM about 50 cm-1, almost double that of graphene "
               "(Ferrari 2006, p. 3); check the width when one component is found."]

    def check(self, n_2D_components, I_2D_over_I_G=None, laser_nm=None):
        if n_2D_components not in self.classes:
            return (f"{n_2D_components} components: the source describes 1 (monolayer), 4 (bilayer) and 2 "
                    "(bulk graphite) only")
        if laser_nm is not None and not 510.0 <= laser_nm <= 640.0:
            return f"laser {laser_nm} nm outside the 514 and 633 nm excitations of Ferrari 2006"
        if I_2D_over_I_G is not None and I_2D_over_I_G <= 0:
            return "I_2D_over_I_G must be positive"
        return None

    def compute(self, n_2D_components, I_2D_over_I_G=None, laser_nm=None):
        cls = self.classes[int(n_2D_components)]
        notes = []
        if cls == "monolayer":
            if I_2D_over_I_G is None:
                confidence = "moderate"
                notes.append("I_2D/I_G not given; monolayer graphene has a 2D peak about 4 times the G height")
            elif I_2D_over_I_G >= 2.0:  # design choice: half the stated factor of 4
                confidence = "high"
            else:
                confidence = "low"
                notes.append(f"I_2D/I_G = {I_2D_over_I_G} is well below the ~4 of monolayer graphene: doping, "
                             "defects or turbostratic stacking")
        else:
            confidence = "moderate"
        return {"layer_class": cls, "confidence": confidence, "_notes": notes}
