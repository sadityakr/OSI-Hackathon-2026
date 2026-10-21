# RamanLens architecture

Status: design, 2026-10-20. No code yet; this is the contract we build against. See `ideas/ranking.md` for the decision and `docs/bond-evaluation.md` for the literature-layer evaluation.

## 1. The problem, and the shape of the solution

A researcher with a new Raman spectrum does four things: fits the peaks, recalls which material and which modes they correspond to, applies known relations (separation gives layer number, width gives disorder, shift gives strain or doping), and checks against published spectra. Each step is slow by hand and the last one is usually skipped. Existing ML tools do step two only, as a black box, and none do step four.

RamanLens is an agent that performs all four steps and leaves a trail: every number it reports is traceable to a fit, a relation with a source, or a retrieved figure. The agent runs in Claude Code on Aditya's PC; tools are Python functions and MCP servers; the LLM reasons, calls tools, writes short analysis scripts when a relation needs composing, and produces the report.

Design rule inherited from the Kerr agent pattern: perception models are tools. The symmetry classifier, the library embedding and any third-party Raman model return structured outputs; the agent decides what they mean.

## 2. Layers

```
spectrum (+ metadata: material guess, laser, substrate, T, polarization) 
        |
        v
[A] Perception tools  ->  peak table, baseline, quality flags, library candidates, (pattern classes)
        |
        v
[B] Relation registry  ->  properties with values, validity, uncertainty, source paper
        |
        v
[C] Literature layer   ->  reference papers (Bond), figures and captions (PDF parsing), digitized reference peaks
        |
        v
[D] Agent (Claude Code) ->  orchestration, hypothesis loop, custom scripts, report with provenance
```

### A. Perception tools (`src/ramanlens/perception/`)

- `io`: readers for two-column txt/csv, Renishaw wdf (via `renishawWiRE` if needed), Horiba txt, Zenodo bundles; normalizes to (shift_cm1, intensity, metadata).
- `preprocess`: cosmic-ray removal, baseline (asymmetric least squares, or polynomial with user override), normalization, calibration check against Si 520.7 cm-1 when a substrate line is present.
- `fit`: peak detection (prominence based), Lorentzian/Voigt/Fano fits, returns per peak: position, FWHM, area, height, shape parameter, fit uncertainty. Supports multi-peak regions (graphene 2D band decomposition into 1 or 4 components).
- `library`: matcher against reference mode tables. Sources, in order of trust: curated literature tables for the target materials; the Computational Raman Database (Bagheri and Komsa 2023, tensors and irreps, once downloaded to `data/raw/crd/`); RRUFF for minerals if needed. Returns ranked candidate materials with matched and unmatched peaks.
- `grouptheory`: for a given point group (and later a structure), the expected number and irreps of Raman-active modes, so "extra peak" and "missing peak" are computable statements.
- `series` (day 2): angle-series Fourier fit and pattern class per peak (A isotropic, A anisotropic, E, off-diagonal B, silent); temperature-series Balkanski fit and anomaly detection. The trained symmetry classifier, if built, lives here as an alternative backend.
- `ml_models` (optional): adapters for any third-party model with public weights that proves useful (candidates to scout: Google Raman pre-trained encoder, RamanPFN, RamanSPy models). Adapter returns a structured prediction plus a confidence; the agent treats it as one more opinion.

### B. Relation registry (`src/ramanlens/relations/`)

One Python module per material family, one function per relation. Every relation is an object with:

```
name:           "mos2_layer_number_from_separation"
material:       "MoS2"
inputs:         {"delta_E2g_A1g": "cm-1"}
outputs:        {"layer_number": "int", "confidence": "str"}
equation:       text with every variable defined
validity:       {"laser_nm": [488, 633], "substrate": "any", "delta_range_cm1": [17, 26]}
source:         {"bond_id": "1005.2509v1", "doi": "10.1021/nn1003937", "figure": "Fig. 2b"}
self_test:      inputs and expected outputs taken from the source paper
```

Relations fail closed: outside their validity range they return "not applicable" with the reason. The registry is queryable by material and by input quantity so the agent can discover what it can compute from a given peak table.

Seed set (hand-written, day 1): graphene (layer number from 2D band shape, defect density and L_D from I(D)/I(G) with laser correction, doping and strain from the G and 2D correlation), MoS2 (layer number from separation, strain from E2g shift, doping from A1g shift and width), CrSBr (mode assignment Ag1 to Ag3 with polarization axes, temperature anomaly flags at T_N, resonance warning for 2.0 to 2.4 eV excitation). Day 2: the tool-building agent adds relations from papers (section 5).

### C. Literature layer (`src/ramanlens/literature/`)

- `bond`: thin client over the Valency MCP tools. Query templates are concept queries built from (material, property), never from frequencies (see `docs/bond-evaluation.md`). Merges arXiv and PubMed duplicates on DOI, prefers arXiv, ranks by citation count and recency, expands one anchor paper with `find_similar_papers` and `get_citing_papers`.
- `pdf`: fetch arXiv PDF, parse structure, extract figures with captions and the reference list. **This code is copied from Aditya's Lit-RAG project (GitLab, private); it is not a dependency and Lit-RAG is not mentioned in the deliverable.** Interface to port: `parse_pdf(path) -> Document(sections, figures[{image, caption, page, panel_labels}], references)`.
- `panels`: select the Raman spectrum panel(s) in a paper using Claude vision on the extracted figures; read axis ranges and legend.
- `digitize`: extract a trace from a selected panel (plotdigitizer headless for single traces, LLM vision for peak positions as a cross-check); returns peak positions with an estimated error.
- `cache`: everything keyed by arXiv id so repeated runs do not refetch.

### D. Agent (`src/ramanlens/agent/`)

Runs in Claude Code with a project CLAUDE.md that describes the tools and the report format. Loop:

1. Ingest spectrum and metadata; run preprocess and fit; produce the peak table.
2. Form material hypotheses: from metadata if given, else from the library matcher; keep the top 3.
3. For each hypothesis, query Bond for the reference papers on mode assignment and on the properties the peak table makes computable; fetch the top arXiv PDFs; extract the Raman panel; digitize reference peaks; compare.
4. Apply applicable relations from the registry; write a short script when a relation needs composing (e.g. separating strain and doping from two shifts).
5. Write the report; attach the figure comparison; list every source; state what could not be determined and why.

The agent may write and run its own scripts in a sandboxed `work/` folder (numpy, scipy, matplotlib available). Scripts it writes are saved with the report for reproducibility.

## 3. Report format

Markdown plus a JSON sidecar.

- Header: sample metadata, instrument, preprocessing applied.
- Peak table: position, FWHM, area, assignment (mode label, irrep if known), source of assignment.
- Reading: one paragraph per property; each sentence of the form "value (method, source)". Three provenance classes: measured, inferred, literature.
- Figure: measured spectrum overlaid with or beside the retrieved reference panel, with the paper citation.
- Limits: what the spectrum cannot tell, which relations were out of range, which hypotheses were rejected.
- Sources: Bond ids with URLs; BibTeX exported via Bond.

## 4. Evaluation

Held-out set of 20 to 30 published spectra across the three materials, each with the paper's own categorical interpretation (material, layer regime, disorder level, strain or doping sign, anomaly present). Papers used for the registry or for tool generation are excluded. Metrics: agreement per field; ablation with the literature layer disabled; time and tool calls per spectrum. Notebook in Marimo. Details and candidate papers in `data/test_set/README.md` (to be written after the Bond retrieval test).

## 5. Tool-building loop (day 2, the novelty hook)

Given a paper with Raman data and an explicit interpretation, a second agent writes a new relation object (equation, validity, source) plus its self-test from the paper's reported numbers, runs the test, and proposes it for the registry. Only tested relations enter. The build set of papers is logged in `data/build_set/`. This is "the agent learns to read Raman spectra from the papers that taught us", with a guardrail.

## 6. Dependencies and environment

- Python 3.11, numpy, scipy, lmfit, matplotlib, pandas; PyMuPDF for PDFs; Lit-RAG parsing code vendored into `literature/pdf`; optional torch for the symmetry classifier.
- Valency MCP Bond configured in Claude Code on the PC (bearer token), see https://docs.valency.io/.
- Network: arXiv and Materials Cloud reachable from the PC, not from the cloud sandbox. All fetching happens on the PC.
- GPU: RTX 3060, 12 GB, only needed if the symmetry classifier or a third-party model is used.

## 7. What is explicitly out of scope for the hackathon

Instrument control, mapping data, non-2D materials beyond what the CRD matcher happens to cover, backward citation walking beyond the PDF reference list, and any claim that the agent replaces expert judgment. The pitch is assistance with receipts.
