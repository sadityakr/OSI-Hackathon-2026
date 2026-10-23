"""Build resources/crd_layered_modes.json, the CRD reference library the matcher ships with.

The Computational Raman Database (Bagheri and Komsa 2023, Sci. Data 10, 80, CC BY 4.0) is a 454 MB ASE JSON dump
with Raman tensors for 5,099 crystals. The matcher only needs, for each of the layered crystals, the modes visible
in backscattering along the layer normal, so this script does that computation once and stores the result; the
skill then runs without the raw database.

Input:
    The folder holding the raw CRD (`crd.json`, or the `crd_2d.pkl` cache that ramanlens writes next to it),
    from the Materials Cloud record 0m9r0-g3486.
Process:
    ramanlens.perception.library.load_crd_rows keeps the layered ("2D") rows; crd_entry rotates each Raman tensor
    into the layer frame, sums degenerate partners and drops modes below 2 % of the strongest, exactly as the
    matcher would at run time.
Output:
    resources/crd_layered_modes.json: citation, licence, CRD version and one entry per usable row (formula,
    space group, source string with row id, modes as [position cm-1, relative intensity, irrep, label]).
"""

import argparse
import json
from pathlib import Path

from ramanlens import RESOURCES
from ramanlens.perception.library import CRD_CITATION, crd_entries_from_rows, entry_to_dict, load_crd_rows


def main():
    ap = argparse.ArgumentParser(description="Precompute the layered-CRD observable-mode library for the skill.")
    ap.add_argument("crd_dir", type=Path, help="folder with crd.json or crd_2d.pkl")
    ap.add_argument("--out", type=Path, default=RESOURCES / "crd_layered_modes.json", help="output JSON path")
    args = ap.parse_args()

    entries = crd_entries_from_rows(load_crd_rows(args.crd_dir))
    doc = {"citation": CRD_CITATION, "licence": "CC BY 4.0", "crd_version": "v1.0.1",
           "record": "Materials Cloud Archive 0m9r0-g3486",
           "processing": "observable modes in backscattering along the layer normal, ramanlens.perception.library",
           "entries": [entry_to_dict(e) for e in entries]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    print(f"{len(entries)} entries -> {args.out} ({args.out.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
