# Data provenance

## Computational Raman Database (CRD) v1.0.1

- Source: Bagheri and Komsa, "High-throughput computation of Raman spectra from first principles", Sci. Data 10, 80 (2023). CC BY 4.0.
- Download: https://archive.materialscloud.org/records/0m9r0-g3486/files/Computational_Raman_Database_v1.0.1.zip?download=1 (record https://archive.materialscloud.org/records/0m9r0-g3486, DOI 10.24435/materialscloud:pg-h3). The pre-migration URL `/record/2283` is dead.
- Local: `data/raw/crd/Computational_Raman_Database_v1.0.1.zip` (152,753,693 bytes, MD5 e2aaea03df70fda95dbd970c60456882, verified 2026-10-20). Unzips to `crd.json` (454 MB) and `logs` (changelog: 33 materials recalculated with VASP 6 in v1.0.1).

### Schema (verified 2026-10-20)

`crd.json` is an ASE database JSON dump: a dict keyed by row id `"1"` to `"5099"` plus two bookkeeping keys `ids` (list) and `nextid` (int) that must be skipped. Each row:

- `numbers`, `positions`, `cell`, `pbc`: structure, ASE-style `{"__ndarray__": [shape, dtype, flat_data]}`.
- `key_value_pairs`: `mpid`, `file` (phonondb tarball), `Refs`, `pointgroup` (Hermann-Mauguin, e.g. `6/mmm`), `spacegroup` (e.g. `P6_3/mmc (194)`), `dimensionality` (`3D`, `2D`, `1D`, `0D`, and mixed `02D`, `03D`, `01D`), `bandgap` (DFT), `bandgap_mp`, `cbm`, `vbm`, `mp_e_above_hull`, `negative_freq_Gamma`, `negative_freq_path` (bools), `frequencies_thz` and `frequencies_cm` (numpy array printed as a string, parse with a float regex), `IRlabels` (Python-list string of Mulliken labels, one per degenerate band, first entry `None` for the acoustic band), `IRbands` (Python-list string mapping each band to its mode indices).
- `data`: `chemical_formula`, `natom`, `volume`, `mass`, `lattice_parameters`, `lattice_angles`, `pointgroup`, `Ramanactive` (int array per mode: -1 acoustic, 0 inactive, 1 active), `IRactive` (same), `raman_tensors` (list indexed by mode, `None` for inactive modes, 3x3 nested list for active ones; the list may be shorter than the mode count when trailing modes are inactive), `eigenvec` (per mode, natom x 3), `born` (Born charges as strings), `diel` (dielectric tensor as strings), `diel_mp`.

Pitfall: irrep labels are per band, not per mode. Map through `IRbands`. The loader in `scratch/crd/crd_loader.py` does this correctly (checked on 2H-WS2: E2g 21.6, E1g 296.0, E2g 353.9, A1g 415.7 cm-1 vs experiment 27, 306, 356, 420).

### Coverage (counted 2026-10-20)

- 5,099 materials; 263,805 Gamma modes; 148,344 flagged Raman-active.
- Dimensionality: 3D 4,137; 2D 385 (272 distinct reduced formulas); 0D 277; mixed 02D 102, 03D 75, 01D 50; 1D 72; unknown 1.
- "2D" means a layered bulk crystal as classified from the Materials Project structure, not a monolayer. Mode counts and tensors are for the bulk cell.
- 2D point groups: 2/m 90, -3m 82, 3m 69, mmm 46, 4/mmm 31, 6mm 14, mm2 13, -3 11, 6/mmm 10, others fewer than 7 each.
- No 2D entry has imaginary Gamma modes.

### Target materials: present or absent

| Material | In CRD | Entry | Notes |
|---|---|---|---|
| CrSBr | **No** | | Not in phonondb 2018. Reference modes must come from literature (Pawbake 2022, Torres 2022, Mondal 2024). |
| Graphene / graphite | **No** | | Not present. Graphene relations come entirely from literature (Ferrari, Cançado). |
| MoS2 2H | **No** | | Only the 3R polytype, mp-1434 (row 98, R3m). 2H-MoS2 frequencies must come from literature; or use 2H-WS2 as a structural analogue for tensor shapes. |
| WS2 2H | Yes | row 90, mp-224 | Clean test case for the loader and matcher. |
| WSe2 2H | Yes | row 3285, mp-1821 | |
| MoSe2 | Yes (3R) | row 2750, mp-7581 | |
| h-BN | Yes | rows 1252, 4599 | |
| CrBr3 | Yes | row 4000, mp-27734 | Only Cr compound among 2D entries. |
| CrI3, black P, ReS2, NbSe2, CrPS4, Fe3GeTe2 | No | | |
| Bi2Se3, HfS2, InSe, GaSe | Yes | | |

Consequence for the project: the CRD is a general-purpose matcher and the training set for the optional symmetry model, but the three demo materials (graphene, MoS2 2H, CrSBr) are covered by literature mode tables, not by the CRD. The curated literature tables in the relation registry are therefore not optional.

## Public experimental spectra

To be added as downloaded (source URL, licence, material, laser, substrate, what the paper says about the sample).
