"""CrSBr relation: assign a Raman peak to the Ag1, Ag2 or Ag3 mode and predict its polarization axis for the laser energy used.

CrSBr is an orthorhombic layered antiferromagnet with an in-plane easy axis b and a hard axis a. Its three main
Raman modes are all of Ag symmetry, and in backscattering their parallel-polarized intensity peaks along a or b.
For Ag1 and Ag3 that axis is always b; for Ag2 it rotates by 90 degrees with excitation energy (Mondal et al.
2025), so a polarization measurement of Ag1 or Ag3 fixes the crystal axes, while Ag2 alone does not unless the
laser energy is known.

Input: `position_cm1` of one fitted peak; optional `laser_eV` or `laser_nm`, `max_parallel_angle_deg` (angle of
maximum parallel-polarized intensity from the polarization classifier), `measured_max_axis` ('a' or 'b').
Process: match the position to the Ag windows, look up the axis for the laser energy, derive the b-axis angle
in the lab frame from the measured angle, check consistency with a measured axis.
Output: mode_label, irrep, expected_max_axis, b_axis_angle_deg, consistent.
"""

from __future__ import annotations

from .base import Relation, SelfTest, Source

MONDAL_2025 = Source(citation="Mondal et al. 2025, npj 2D Mater. (arXiv 2410.22164)",
                     locator="p. 2 (Ag1 114, Ag2 244, Ag3 344 cm-1 in 4L at 300 K; axes at 2.33 and 1.96 eV, "
                             "Figs. 2c,d), p. 3 and Fig. 3 (Ag2 switches from a to b near 2.07 eV; back to a at "
                             "1.58 eV), abstract (Ag1 and Ag3 along b at every laser energy)",
                     arxiv="2410.22164")

HC_NM_EV = 1239.84  # h c in eV nm


class CrSBrAgModeAssignment(Relation):
    name = "crsbr_ag_mode_assignment_with_polarization_axis"
    material = "CrSBr"
    aliases = ("chromium sulfide bromide",)
    inputs = {"position_cm1": "fitted peak position in cm-1"}
    optional_inputs = {"laser_eV": "excitation photon energy in eV", "laser_nm": "excitation wavelength in nm",
                       "max_parallel_angle_deg": "lab-frame angle of maximum parallel-polarized intensity",
                       "measured_max_axis": "'a' or 'b' if the crystal axes are known independently"}
    outputs = {"mode_label": "Ag1, Ag2 or Ag3", "irrep": "Ag",
               "expected_max_axis": "'a', 'b', 'near isotropic (switching)' or None (not measured at this energy)",
               "b_axis_angle_deg": "lab-frame angle of the b axis, from max_parallel_angle_deg (Ag1, Ag3, or Ag2 "
                                   "when its axis is known)",
               "consistent": "measured axis equals the expected axis (None if not given)"}
    equation = ("Windows: Ag1 108 to 127, Ag2 236 to 262, Ag3 336 to 354 cm-1 (Mondal 2025: 114, 244, 344 at "
                "300 K; Pawbake 2023: 117, 257, 345 at 300 K and 121, 254, 346 at 5 K). Axis of maximum parallel "
                "intensity: Ag1, Ag3 -> b for 1.58 to 2.33 eV; Ag2 -> a for E_L >= 2.12 eV (measured 2.25, 2.33), "
                "near isotropic for 2.02 < E_L < 2.12 (switch near 2.07 eV), b for 1.94 to 2.02 eV (measured "
                "1.96), a at 1.58 eV. b_axis_angle = max_parallel_angle if the mode is along b, else + 90 deg.")
    validity = {"laser_eV": [1.55, 2.36], "temperature": "300 K in the polarization study (4L to 62 nm flakes)",
                "geometry": "backscattering along c (k || c); B2g modes at 92, 194, 301 cm-1 appear only with a "
                            "tilted sample (Pawbake 2023, p. 3)"}
    source = MONDAL_2025
    windows = {"Ag1": (108.0, 127.0), "Ag2": (236.0, 262.0), "Ag3": (336.0, 354.0)}
    b2g = (92.0, 194.0, 301.0)  # Pawbake et al. 2023, PRB 107, 075421 (arXiv 2211.12939), p. 3
    self_tests = [
        SelfTest({"position_cm1": 114.0, "laser_eV": 2.33}, {"mode_label": "Ag1", "expected_max_axis": "b"},
                 locator="p. 2: Ag1 (114 cm-1) maximum along b at 2.33 eV, Fig. 2c"),
        SelfTest({"position_cm1": 244.0, "laser_eV": 2.33}, {"mode_label": "Ag2", "expected_max_axis": "a"},
                 locator="p. 2: Ag2 (244 cm-1) maximum along a at 2.33 eV, Fig. 2c"),
        SelfTest({"position_cm1": 244.0, "laser_eV": 1.96}, {"mode_label": "Ag2", "expected_max_axis": "b"},
                 locator="pp. 2 to 3: all three modes maximum along b at 1.96 eV, Fig. 2d"),
        SelfTest({"position_cm1": 344.0, "laser_eV": 1.96}, {"mode_label": "Ag3", "expected_max_axis": "b"},
                 locator="pp. 2 to 3: Ag3 (344 cm-1) maximum along b at 1.96 eV, Fig. 2d"),
        SelfTest({"position_cm1": 244.0, "laser_eV": 1.58}, {"mode_label": "Ag2", "expected_max_axis": "a"},
                 locator="p. 3: at 1.58 eV the Ag2 polarization switches back to a"),
    ]
    out_of_range_example = {"position_cm1": 500.0}
    caveats = ["Laser energies 2.0 to 2.4 eV and the excitons near 1.65, 1.87 and 1.95 eV (Mondal 2025, p. 4) make "
               "relative intensities resonant; compare axes, not intensity ratios, across lasers.",
               "Ag2 sits at 244 cm-1 in 4L at 300 K (Mondal 2025) and at 254 to 257 cm-1 in bulk (Pawbake 2023); "
               "the window covers both."]

    def _energy(self, laser_eV, laser_nm):
        if laser_eV is not None:
            return float(laser_eV)
        if laser_nm is not None:
            return HC_NM_EV / float(laser_nm)
        return None

    def check(self, position_cm1, laser_eV=None, laser_nm=None, max_parallel_angle_deg=None,
              measured_max_axis=None):
        if not any(lo <= position_cm1 <= hi for lo, hi in self.windows.values()):
            near = [b for b in self.b2g if abs(position_cm1 - b) <= 6.0]
            extra = (f"; {near[0]:g} cm-1 is a B2g mode, seen only with a tilted sample (Pawbake 2023, p. 3)"
                     if near else "")
            return f"{position_cm1} cm-1 is outside the Ag1, Ag2 and Ag3 windows {self.windows}{extra}"
        if laser_nm is not None and laser_nm <= 0:
            return "laser_nm must be positive"
        energy = self._energy(laser_eV, laser_nm)
        if energy is not None and not 1.55 <= energy <= 2.36:
            return (f"laser energy {energy:.2f} eV outside 1.55 to 2.36 eV, the range of the polarization study "
                    "(Mondal 2025: 1.58 and 1.96 to 2.33 eV)")
        if measured_max_axis is not None and measured_max_axis not in ("a", "b"):
            return "measured_max_axis must be 'a' or 'b'"
        return None

    def _ag2_axis(self, energy):
        if energy is None:
            return None, "laser energy not given; the Ag2 axis depends on it (a at 2.25 to 2.33 eV, b at 1.96 eV)"
        if energy >= 2.12:
            return "a", ""
        if energy > 2.02:
            return "near isotropic (switching)", "Ag2 polar plot is close to circular near 2.06 to 2.07 eV"
        if energy >= 1.94:
            return "b", ""
        if energy <= 1.60:
            return "a", ""
        return None, f"Ag2 axis not measured at {energy:.2f} eV (Mondal 2025 used 1.58 and 1.96 to 2.33 eV)"

    def compute(self, position_cm1, laser_eV=None, laser_nm=None, max_parallel_angle_deg=None,
                measured_max_axis=None):
        label = next(k for k, (lo, hi) in self.windows.items() if lo <= position_cm1 <= hi)
        energy = self._energy(laser_eV, laser_nm)
        notes = []
        if label == "Ag2":
            axis, note = self._ag2_axis(energy)
            if note:
                notes.append(note)
        else:
            axis = "b"
        b_angle = None
        if max_parallel_angle_deg is not None and axis in ("a", "b"):
            b_angle = float(max_parallel_angle_deg if axis == "b" else max_parallel_angle_deg + 90.0) % 180.0
        consistent = None if measured_max_axis is None or axis not in ("a", "b") else measured_max_axis == axis
        return {"mode_label": label, "irrep": "Ag", "expected_max_axis": axis, "laser_eV": energy,
                "b_axis_angle_deg": b_angle, "consistent": consistent, "_notes": notes}
