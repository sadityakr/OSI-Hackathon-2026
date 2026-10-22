# RamanLens test set

Ground-truth Raman cases used for two things: the contract tests that the build loop must turn green, and the comparison between a bare agent (Claude plus Python) and the tooled agent (Claude plus RamanLens tools).

## Splits and who may read what

| Folder | Purpose | Builder loop may read `truth.json`? |
|---|---|---|
| `dev/` | develop and debug tools; scored inside the loop | yes |
| `heldout/` | final comparison only; scored by a person running `eval/` | **no** (permission deny rule in `loop/settings.json`, plus `tests/contract/test_no_heldout_leak.py`) |

Everything is in git so collaborators can inspect it. The protection is against the builder agent tuning its tools to the answers, not against people.

A case never appears in both splits, and a paper whose data is in `heldout/` is never used to write a relation (the relation build set lives in `data/build_set/`).

## Case layout

```
<split>/<case_id>/
  input.json     what the agent is given (besides the spectrum)
  spectrum.csv   the data
  truth.json     the answer key with its source
```

`case_id` is `<tier>-<material>-<nn>`, for example `syn-WS2-01`, `exp-MoS2-02`. Tiers: `syn` (synthetic from the Computational Raman Database), `exp` (open experimental data).

### spectrum.csv

- Single spectrum: columns `shift_cm1,intensity`.
- Polarization series: long format, columns `shift_cm1,intensity,angle_deg,config` with `config` in {`parallel`, `crossed`}. `angle_deg` is the angle of the incident linear polarization relative to the lab x axis; the sample c axis is along the beam (backscattering).

### input.json

```json
{
  "case_id": "syn-WS2-01",
  "kind": "single | angle_series",
  "task": "identify | verify",
  "material_hint": null,
  "laser_nm": 532,
  "temperature_K": 295,
  "substrate": null,
  "geometry": "backscattering, beam along c",
  "question": "Which material is this? Assign the peaks."
}
```

- `task = identify`: `material_hint` is null; the agent returns ranked candidates.
- `task = verify`: `material_hint` names a material (sometimes wrong on purpose); the agent must say whether the spectrum is consistent with it, based on literature or reference data.

### truth.json

```json
{
  "case_id": "syn-WS2-01",
  "material": "WS2",
  "formula": "WS2",
  "polytype": "2H",
  "spacegroup": "P6_3/mmc (194)",
  "pointgroup": "6/mmm",
  "hint_is_correct": null,
  "layers": null,
  "peaks": [
    {"position_cm1": 356.0, "tolerance_cm1": 5.0, "irrep": "E2g", "label": "E2g^1", "pattern": "isotropic_both"}
  ],
  "properties": {},
  "source": {
    "kind": "synthetic | experimental",
    "dataset": "DOI or URL of the dataset",
    "paper": "author year, journal, DOI of the paper that interprets the data",
    "figure": "Fig. 2a (where the interpretation was read)",
    "licence": "CC BY 4.0"
  },
  "notes": "free text: anything an evaluator should know"
}
```

Field rules:

- `material` is the common name the scorer compares after normalization (case, whitespace, polytype prefix stripped); `formula` is the reduced formula.
- `hint_is_correct` is `true`/`false` for `verify` cases, `null` otherwise.
- `peaks` lists only the peaks a competent reader should find and assign. `irrep` uses Mulliken labels as in the source (CRD for synthetic cases, the paper for experimental ones). `pattern` is only set for `angle_series` cases.
- `properties` holds categorical or numeric conclusions the source paper states, for example `{"layers": 1}`, `{"strain_sign": "tensile"}`, `{"defect_level": "low"}`. Only what the source states; never inferred by us.

### Polarization pattern classes (backscattering along c, in-plane polarizations)

| `pattern` | parallel I(theta) | crossed I(theta) | typical irreps |
|---|---|---|---|
| `isotropic_par_only` | constant | zero | A1g, A1 in uniaxial crystals |
| `isotropic_both` | constant | constant, equal to parallel | E modes (degenerate pair summed) |
| `twofold` | 180 deg period, maxima along a crystal axis | varies | Ag in orthorhombic or monoclinic crystals |
| `fourfold` | cos^2(2 theta) shaped | sin^2(2 theta) shaped | B1g, B2g |
| `silent` | zero or below 2 % of the strongest band | same | modes with only out-of-plane tensor components (E1g in 2H-TMDs); listed in `notes`, not in `peaks` |

Classes are computed numerically from the generated curves in synthetic cases (see `eval/synth/make_synthetic.py`), never hand-assigned.

## Known biases (state them in the write-up)

- Synthetic cases come from the same database the tooled agent's matcher uses. They test the pipeline and the polarization logic with exact truth, but they flatter the matcher. To reduce this, the generator applies a random frequency scale of 1.000 to 1.025 (CRD frequencies run 0 to 3 % below experiment for WS2, WSe2, MoS2, HfS2), position jitter, dropped weak modes, noise, a baseline and cosmic spikes. The experimental cases are the fair test of identification.
- Experimental truth is the interpretation published by the dataset's authors, not an independent measurement.

## Experimental cases and their source papers (curated 2026-10-21)

| Split | Cases | Dataset | Paper that interprets it |
|---|---|---|---|
| dev | exp-graphene-01 | Zenodo 14883846 (CC BY 4.0), file `S1/FigS1D Au exported_Raman.txt` | Bukvisova et al. 2025, arXiv:2503.04327, Fig. S1D. Peak positions read from the data by the curator, not stated by the authors; no laser wavelength or layer number given. |
| dev | exp-MoS2-01 | Southampton eprints 488525 (D2829, CC BY 4.0) | Zeimpekis et al., ACS Appl. Energy Mater., doi:10.1021/acsaem.3c03055 (paper not read; truth = dataset's fitted means over spots, this spot is about 3 cm-1 lower). Normalized, 350 to 451 cm-1 only. |
| heldout | exp-WS2-01, -02 | Southampton D0371 = eprints 416765 (CC BY 4.0), `RRS_Spectra.xlsx` | McDonnell et al. 2018, Nano Lett., doi:10.1021/acs.nanolett.7b05184, Fig. 1a. Resonance excitation (599 and 614 nm), monolayer. |
| heldout | exp-MoSe2-01 | Southampton eprints 449632 (D1747, CC BY 4.0) | Viner et al. 2021, 2D Mater. 8, 035047, arXiv:2103.09004. Processed (parallel minus crossed), resonance, 4 K, hBN-encapsulated. |
| heldout | exp-WSe2-01 | Southampton eprints 449632 (D1747) | Peak position from McDonnell et al. 2020, arXiv:2006.05912 (companion paper; cross-paper transfer). |
| heldout | exp-CrSBr-01 to -05 | Zenodo 15048152 (CC BY 4.0) | Wdowik et al. 2025, arXiv:2503.15298, Fig. 3, Fig. 5, Table A3. 03/04 are one 6L flake above and below T_N; 05 is the bulk negative control. Circular, not linear, polarization. |
| heldout | exp-CrSBr-06 to -09, exp-WS2-03 | Zenodo 15048152 (`Figure3.txt`, remaining layer columns); Southampton D0371 (`RRS_Spectra.xlsx`, sheet set 150K, one excitation column) | Wdowik et al. 2025, Fig. 3 and Table A3 (layer-number cases; per-layer positions bracketed by the paper's ML and bulk values); McDonnell et al. 2018, Fig. 1a (monolayer, 150 K). |

Rejected: `rejected/exp-graphene-02` (D, G, 2D barely above background; truth positions not trustworthy).

**Papers excluded from building tools.** Reference tables and relations (`src/ramanlens/literature/`, `src/ramanlens/relations/`) must not take numbers from the papers behind held-out cases: McDonnell et al. 2018 (WS2), Viner et al. 2021 (MoSe2), McDonnell et al. 2020 (WSe2), Wdowik et al. 2025 (CrSBr). Otherwise the tools arm would be checked against its own source.

**Precision on experimental cases.** Truth lists only peaks the paper assigns. Real but unassigned peaks (CrSBr 1L near 302 cm-1, MoSe2 resonance features at 280 to 320 cm-1) count against `peak_precision`, so report precision for synthetic cases only.
