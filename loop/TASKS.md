# RamanLens build backlog

One task per loop iteration, top to bottom. A task is done only when its acceptance tests pass **and** every test
that passed before still passes. Mark with `[x]` when done, `[blocked: <reason>]` when a real attempt failed
(then move on). Do not reorder; do not delete tasks. Add new tasks only at the bottom under "Discovered".

Test commands (from the repo root):
- fast: `.venv/Scripts/python.exe -m pytest tests -q -m "not slow"`
- one file: `.venv/Scripts/python.exe -m pytest tests/contract/test_perception.py -q`
- all: `.venv/Scripts/python.exe -m pytest tests -q`

## Backlog

- [x] **T1 Readers.** `ramanlens/perception/io.py`: `Spectrum` (x, y, meta; x ascending), `AngleSeries`
  (x, spectra: dict[(config, angle_deg)] -> y on a common axis, meta), `read_spectrum(path)`, `read_series(path)`.
  Two-column csv/txt with or without header; long-format angle csv as in `data/test_set/README.md`.
  Accept: `test_perception.py::test_read_single_spectrum`, `::test_read_angle_series`.
- [blocked: contract test_spike_removal_finds_injected_spike is self-contradictory (see Discovered); module done, baseline test green] **T2 Preprocessing.** `ramanlens/perception/preprocess.py`: `remove_spikes(x, y) -> (y_clean, spike_positions)`
  (narrow outliers vs a median filter, never real peaks), `baseline_als(y, lam=1e5, p=0.01)` (asymmetric least
  squares, Eilers and Boelens 2005). Accept: `::test_spike_removal_finds_injected_spike`, `::test_baseline_als_removes_slope_keeps_peak`.
- [x] **T3 Peak fitting.** `ramanlens/perception/fit.py`: `Peak` dataclass (position, fwhm, height, area,
  position_err, shape, is_substrate=False), `fit_peaks(x, y, ...)` (prominence-based detection on the
  baseline-corrected signal, grouped multi-Lorentzian fit with lmfit or scipy, uncertainties from the covariance).
  Accept: `::test_fit_recovers_exact_lorentzians`, `::test_fit_resolves_close_doublet`.
- [blocked: contract test_cosmic_rays_not_reported_as_peaks_on_dev crashes on json.loads of the free-text notes of exp dev cases (see Discovered); pipeline done, recall and Si acceptance tests green, same cosmic check green in tests/unit/test_pipeline.py] **T4 Pipeline.** `ramanlens/perception/pipeline.py`: `analyze_spectrum(spectrum) -> result` with `.peaks`,
  `.spikes`, `.baseline`; flags the Si line (520.7 +- 2 cm-1, narrow) as `is_substrate`. Accept:
  `::test_fit_recall_on_dev_single_cases`, `::test_cosmic_rays_not_reported_as_peaks_on_dev`,
  `test_library.py::test_si_substrate_line_is_flagged`.
- [x] **T5 Reference library and matcher.** `ramanlens/perception/library.py`: load the CRD
  (`data/raw/crd/crd.json`, or cache a 2D subset; note `raman_tensors` can be a list or a dict keyed by mode index,
  and irrep labels are per band through `IRbands`; `scratch/crd/crd_loader.py` is a buggy starting point). Compute
  which modes are visible in backscattering along the layer normal (in-plane tensor components). `match(positions,
  intensities=None, top_k=5)` returns candidates (.material, .score, .matched, .source) using a fitted global
  frequency scale per candidate (DFT runs 0 to 3 % low) and a penalty for strong predicted modes that are missing.
  Curated literature tables (T7) take precedence over the CRD when they exist. Accept:
  `test_library.py::test_ws2_ranks_top3_from_textbook_peaks`, `::test_identify_top3_on_dev_single_cases`.
- [x] **T6 Polarization.** `ramanlens/perception/polarization.py`: `classify_curves(theta_deg, par, crossed)`
  -> {"pattern", "max_parallel_angle_deg"} with the classes in `data/test_set/README.md` (fit a Fourier series in
  2 theta and 4 theta; robust to noise and to unknown sample rotation); `analyze_series(series)` fits peaks on the
  summed spectrum, extracts each peak's intensity per angle and config, classifies it. Accept: all of `test_polarization.py`.
- [ ] **T7 Literature reference tables.** `ramanlens/literature/reference_tables.py`: `get_table(name)` for
  graphene, 2H-MoS2, CrSBr, 2H-WS2 (add more if cheap: 2H-WSe2, 2H-MoSe2, hBN, black phosphorus). Each mode:
  position_cm1, label, irrep, conditions (laser, layers, temperature), source (doi or arxiv, locator = figure or
  table). Never use the papers listed as excluded in `data/test_set/README.md` (they hold held-out answers).
  **Every number must be read from the source** (Valency Bond search, arXiv abstract or full text); never
  from memory. If a number cannot be verified, leave the mode out and note it. Store tables as JSON in
  `ramanlens/literature/tables/`. Accept: `test_library.py::test_reference_tables_for_demo_materials`.
- [ ] **T8 Relation registry.** `ramanlens/relations/`: `Relation` (name, material, inputs, outputs, equation with
  all variables defined, validity, source with locator, self_tests, out_of_range_example, `apply(**inputs)` ->
  result with `.applicable`, `.reason`, values), `registry.all_relations()`, `find(material=..., input_quantity=...)`,
  `run_self_tests()`. Seed six, each from its paper: MoS2 layer number from the E2g-A1g separation (Lee et al.
  2010, ACS Nano 4, 2695), graphene I(D)/I(G) to L_D with laser-energy correction (Cancado et al. 2011, Nano Lett.
  11, 3190), graphene strain and doping from the G and 2D positions (Lee et al. 2012, Nat. Commun. 3, 1024),
  graphene monolayer test from the 2D band shape (Ferrari et al. 2006, PRL 97, 187401), WS2 layer number
  (Berkdemir et al. 2013, Sci. Rep. 3, 1755), CrSBr Ag mode assignment with polarization axis (verify a source
  first; not Wdowik et al. 2025, which is held-out). Self-test inputs and outputs are numbers stated in the paper. Accept: all of `test_relations.py`.
- [ ] **T9 Agent toolset.** `ramanlens/agent/toolset.py`: `TOOLS` (Anthropic tool definitions) and
  `call(name, input, workdir) -> str` (JSON) for load_spectrum, fit_peaks, match_library, classify_polarization,
  lookup_reference_modes, list_relations, apply_relation. Every tool decorated with `@traced` from
  `ramanlens.tracing` using the span names in its docstring; every output carries provenance (source for
  literature values, method for measured ones). Accept: all of `test_toolset.py`; the full suite green.
- [ ] **T10 Literature figure tools (optional).** If `iopic_bond` is importable (it lives in `iopic-bond/`, owned
  by the collaborator; do not edit it), add thin wrappers find_papers and view_figure to the toolset. Otherwise
  mark `[blocked: iopic_bond not installed]`. Accept: a unit test in `tests/unit/` that skips when iopic_bond is absent.
- [ ] **T11 Hardening on dev.** Run `.venv/Scripts/python.exe -m pytest tests -q`; for each remaining dev failure
  or weak spot (experimental `exp-*` dev cases included), fix the tool, never the test. Write
  `docs/tool-status.md`: what each tool does, its known failure modes, dev metrics.

## Discovered

(append tasks found while working; one line each, with the reason)

- Fix contract `test_perception.py::test_spike_removal_finds_injected_spike` (human only): `x = arange(100, 800, 1)` gives `x[300] = 400`, so the spike lands on the top of the 1000-count band at 400 cm-1; `y_clean[300] < 300` would require deleting that band, which the next assert forbids. Suggested fix: inject at `y[150]` (x = 250, flat) and keep the asserts. `remove_spikes` already finds the spike at 400 and restores the band (y_clean[300] = 1007).
- For T4: `fit_peaks` on exp-graphene-01 reports bands at -32, 0.8 and 37.7 cm-1 (laser line and edge-filter region); the pipeline should ignore shifts below a cutoff (about 50 cm-1 or the first rise of the filter edge). syn-MoS2-01/02 give 412.9 plus 415.4 near A1g; check against the CRD modes whether that is a real pair or a split.
- Human cleanup: `tests/unit/test_tmp_dev_fit_probe.py` has a misleading name (it is a kept slow regression test, fitter recall on dev); the loop cannot rename or delete files from the shell. Rename to `test_fit_dev.py`.
- Fix contract `test_perception.py::test_cosmic_rays_not_reported_as_peaks_on_dev` (human only): it calls `json.loads(c["truth"]["notes"] or "{}")` on every dev single case, but exp-MoS2-01 and exp-graphene-01 have free-text notes, so it raises JSONDecodeError before calling the pipeline. Suggested fix: wrap the json.loads in try/except and skip those cases, as `tests/unit/test_pipeline.py::test_dev_cosmic_rays_found_and_not_fitted` does (green: all 3 dev cosmic rays found, none fitted).
- T2 note: the spike contract test now passes (contract moved the spike to y[150]); T2's blocked mark is stale, both T2 acceptance tests are green.
- Weak spot for T11: syn-WS2-01 A1g (weak, SNR about 4) is fitted at 414.3 cm-1 with FWHM 1.4 (at the new 1.5-pixel floor) instead of about 6; position is within tolerance, width is not trustworthy. exp-MoS2-01 fits 379.8 and 404.5 (about 3 cm-1 below the dataset means, as its README says).
- Concurrent edit during T4: another session added a baseline offset correction to `perception/pipeline.py` (median of band-free ALS residual added to the baseline). Kept as found; it is covered by the T4 tests.
- For T7: `perception/library.literature_library()` imports `all_tables()` from `ramanlens.literature.reference_tables` (tables with `.name`, optional `.formula`, `.modes` with position_cm1, label, irrep, source, optional rel_intensity). Provide `all_tables()` so the matcher picks the tables up; exp-graphene-01 (the one dev identify miss, 7/8) needs the graphene table with D, G, 2D.
- For T9: pass the spectrum's shift range as `match(..., x_range=(lo, hi))`; without it the matcher assumes strong modes far from the measured peaks are only weakly expected.
