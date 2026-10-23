"""Layer-number relations for MoS2 and WS2 from the separation of the E2g1 and A1g Raman modes.

In few-layer MoS2 and WS2 the in-plane E2g1 mode softens and the out-of-plane A1g mode stiffens as layers are
added, so their separation Delta = omega(A1g) - omega(E2g1) grows with layer number. Both relations look the value
up in the table the paper printed and return the nearest layer number plus every layer number the measurement
cannot exclude; they do not interpolate between table rows.

Input: `delta_E2g_A1g_cm1` (Delta in cm-1), optional `laser_nm` and `delta_err_cm1` (uncertainty of Delta).
Process: validity check (Delta range, laser range), nearest tabulated level, candidates within the uncertainty.
Output: layer_label ("1L" ... "bulk"), layer_number (int, None for bulk), candidates, confidence.
"""

from __future__ import annotations

from .base import Relation, SelfTest, Source, nearest_level

LEE_2010 = Source(citation="Lee, Yan, Brus, Heinz, Hone, Ryu 2010, ACS Nano 4, 2695",
                  locator="Fig. 2b (E2g1 and A1g positions and their difference vs layer number, 514.5 nm)",
                  doi="10.1021/nn1003937", arxiv="1005.2509")

BERKDEMIR_2013 = Source(citation="Berkdemir et al. 2013, Sci. Rep. 3, 1755",
                        locator="Table 1 (2LA(M), E2g1, A1g positions per layer number at 488, 514.5, 647 nm)",
                        doi="10.1038/srep01755")


def _layer_result(delta: float, levels: dict[str, float], err: float) -> dict:
    best, candidates = nearest_level(delta, levels, err)
    if len(candidates) > 1:
        confidence = "low"
    elif best in ("1L", "2L"):
        confidence = "high"
    else:
        confidence = "moderate"
    return {"layer_label": best, "layer_number": None if best == "bulk" else int(best[:-1]),
            "candidates": candidates, "confidence": confidence,
            "delta_E2g_A1g_cm1": delta, "reference_delta_cm1": levels[best]}


class MoS2LayerNumberFromSeparation(Relation):
    name = "mos2_layer_number_from_separation"
    material = "MoS2"
    aliases = ("2H-MoS2", "molybdenum disulfide")
    inputs = {"delta_E2g_A1g_cm1": "omega(A1g) - omega(E2g1) in cm-1, from a Lorentzian fit of both modes"}
    optional_inputs = {"laser_nm": "excitation wavelength in nm",
                       "delta_err_cm1": "1-sigma uncertainty of the separation in cm-1 (default 0.5)"}
    outputs = {"layer_label": "1L, 2L, 3L, 4L or bulk", "layer_number": "int, None for bulk",
               "candidates": "layer labels within the uncertainty of the measured separation",
               "confidence": "high (one candidate, 1L or 2L), moderate (one candidate), low (several)"}
    equation = ("Delta = omega(A1g) - omega(E2g1). Tabulated (Lee 2010, Fig. 2b, 514.5 nm): 1L 19.1, 2L 21.4, "
                "3L 23.1, 4L 24.3, bulk 25.2 cm-1. layer = argmin_N |Delta - Delta_N|; candidates = all N with "
                "|Delta - Delta_N| <= delta_err.")
    # Lee 2010 rows: 1L 403.1 - 384.0, 2L 404.8 - 383.4, 3L 405.9 - 382.8, 4L 406.7 - 382.4, bulk 407.4 - 382.2
    levels = {"1L": 19.1, "2L": 21.4, "3L": 23.1, "4L": 24.3, "bulk": 25.2}
    validity = {"delta_range_cm1": [18.1, 26.2], "laser_nm": [488.0, 633.0],
                "substrate": "SiO2/Si (285 nm oxide in the source)", "sample": "mechanically exfoliated 2H-MoS2"}
    source = LEE_2010
    self_tests = [
        SelfTest({"delta_E2g_A1g_cm1": 19.1}, {"layer_label": "1L", "layer_number": 1}, locator="Fig. 2b, 1L"),
        SelfTest({"delta_E2g_A1g_cm1": 21.4}, {"layer_label": "2L", "layer_number": 2}, locator="Fig. 2b, 2L"),
        SelfTest({"delta_E2g_A1g_cm1": 23.1}, {"layer_label": "3L", "layer_number": 3}, locator="Fig. 2b, 3L"),
        SelfTest({"delta_E2g_A1g_cm1": 24.3}, {"layer_label": "4L", "layer_number": 4}, locator="Fig. 2b, 4L"),
        SelfTest({"delta_E2g_A1g_cm1": 25.2}, {"layer_label": "bulk", "layer_number": None},
                 locator="Fig. 2b, bulk"),
    ]
    out_of_range_example = {"delta_E2g_A1g_cm1": 30.0}
    caveats = ["Table measured at 514.5 nm with 2.7 cm-1 spectral resolution on 285 nm SiO2/Si (Lee 2010); "
               "3L, 4L and bulk differ by about 1 cm-1, so they are separable only with a well-calibrated fit.",
               "Strain, doping and substrate shift E2g1 and A1g and therefore Delta; a CVD or transferred flake "
               "can be misassigned by one layer."]

    def check(self, delta_E2g_A1g_cm1, laser_nm=None, delta_err_cm1=None):
        lo, hi = self.validity["delta_range_cm1"]
        if not lo <= delta_E2g_A1g_cm1 <= hi:
            return (f"separation {delta_E2g_A1g_cm1} cm-1 outside {lo} to {hi} cm-1 (Lee 2010 tabulates 19.1 "
                    "to 25.2 cm-1); not few-layer 2H-MoS2 or the peaks are misassigned")
        if laser_nm is not None:
            lo, hi = self.validity["laser_nm"]
            if not lo <= laser_nm <= hi:
                return f"laser {laser_nm} nm outside {lo} to {hi} nm"
        if delta_err_cm1 is not None and delta_err_cm1 < 0:
            return "delta_err_cm1 must be non-negative"
        return None

    def compute(self, delta_E2g_A1g_cm1, laser_nm=None, delta_err_cm1=None):
        err = 0.5 if delta_err_cm1 is None else float(delta_err_cm1)
        out = _layer_result(float(delta_E2g_A1g_cm1), self.levels, err)
        if laser_nm is not None and abs(laser_nm - 514.5) > 1.0:
            out["_notes"] = [f"table measured at 514.5 nm, applied here at {laser_nm} nm"]
        return out


class WS2LayerNumberFromSeparation(Relation):
    name = "ws2_layer_number_from_separation"
    material = "WS2"
    aliases = ("2H-WS2", "tungsten disulfide")
    inputs = {"delta_E2g_A1g_cm1": "omega(A1g) - omega(E2g1) in cm-1, from a Lorentzian fit of both modes"}
    optional_inputs = {"laser_nm": "excitation wavelength in nm",
                       "delta_err_cm1": "1-sigma uncertainty of the separation in cm-1 (default 0.5)"}
    outputs = MoS2LayerNumberFromSeparation.outputs
    equation = ("Delta = omega(A1g) - omega(E2g1). Tabulated (Berkdemir 2013, Table 1, 514.5 nm): 1L 62.0, "
                "2L 63.4, 3L 64.6, bulk 64.8 cm-1. layer = argmin_N |Delta - Delta_N|; candidates = all N with "
                "|Delta - Delta_N| <= delta_err.")
    # Berkdemir 2013 Table 1 at 514.5 nm: 1L 417.2 - 355.2, 2L 418.4 - 355.0, 3L 419.0 - 354.4, bulk 420.1 - 355.3
    levels = {"1L": 62.0, "2L": 63.4, "3L": 64.6, "bulk": 64.8}
    # Table 1 also lists 488 nm (1L: 417.5 - 355.9 = 61.6) and 647 nm (1L 61.9 to bulk 65.8): the same separations
    # within about 1 cm-1, so the 514.5 nm levels are used from 488 to 647 nm.
    validity = {"delta_range_cm1": [61.0, 66.0], "laser_nm": [488.0, 647.0],
                "substrate": "SiO2/Si (CVD layers in the source; bulk on powder)"}
    source = BERKDEMIR_2013
    self_tests = [
        SelfTest({"delta_E2g_A1g_cm1": 62.0, "laser_nm": 514.5}, {"layer_label": "1L", "layer_number": 1},
                 locator="Table 1, 514.5 nm, 1L: A1g 417.2, E2g1 355.2"),
        SelfTest({"delta_E2g_A1g_cm1": 63.4, "laser_nm": 514.5}, {"layer_label": "2L", "layer_number": 2},
                 locator="Table 1, 514.5 nm, 2L: A1g 418.4, E2g1 355.0"),
        SelfTest({"delta_E2g_A1g_cm1": 61.6, "laser_nm": 488.0}, {"layer_label": "1L", "layer_number": 1},
                 locator="Table 1, 488 nm, 1L: A1g 417.5, E2g1 355.9"),
    ]
    out_of_range_example = {"delta_E2g_A1g_cm1": 70.0}
    caveats = ["3L (64.6) and bulk (64.8 cm-1) are not separable by this relation (Berkdemir 2013, Table 1).",
               "At 514.5 nm the 2LA(M) band at about 351 cm-1 sits 4 cm-1 below E2g1 (Berkdemir 2013, Table 1); "
               "a single-Lorentzian fit of the pair pulls E2g1 low and Delta high. Fit both components."]

    def check(self, delta_E2g_A1g_cm1, laser_nm=None, delta_err_cm1=None):
        lo, hi = self.validity["delta_range_cm1"]
        if not lo <= delta_E2g_A1g_cm1 <= hi:
            return (f"separation {delta_E2g_A1g_cm1} cm-1 outside {lo} to {hi} cm-1 (Berkdemir 2013 tabulates "
                    "61.6 to 65.8 cm-1); not few-layer 2H-WS2 or the peaks are misassigned")
        if laser_nm is not None:
            lo, hi = self.validity["laser_nm"]
            if not lo <= laser_nm <= hi:
                return f"laser {laser_nm} nm outside {lo} to {hi} nm (the lasers of Berkdemir 2013, Table 1)"
        if delta_err_cm1 is not None and delta_err_cm1 < 0:
            return "delta_err_cm1 must be non-negative"
        return None

    def compute(self, delta_E2g_A1g_cm1, laser_nm=None, delta_err_cm1=None):
        err = 0.5 if delta_err_cm1 is None else float(delta_err_cm1)
        return _layer_result(float(delta_E2g_A1g_cm1), self.levels, err)
