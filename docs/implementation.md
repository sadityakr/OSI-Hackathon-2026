# RamanLens implementation notes

Companion to `docs/architecture.md`. The architecture doc says what the layers are; this one records concrete decisions about how to build them, as they are made. Updated 2026-10-20 evening.

## 1. Material hypothesis pipeline (layer A, before any literature call)

Bond cannot search by peak positions (see `docs/bond-evaluation.md`), so a material hypothesis must exist before the first literature query. Order of evidence:

1. User metadata: if the sample is declared (material, substrate, laser wavelength, temperature), take it as the primary hypothesis and keep the matcher output as a cross-check only.
2. Curated literature mode tables: graphene, 2H-MoS2, CrSBr and whatever else the registry holds. These take precedence over the CRD for the demo materials because the CRD does not contain them (see section 3).
3. CRD matcher: peak list vs. the Raman-active modes of all CRD entries, with a global frequency scale factor fitted per candidate (DFT frequencies run a few percent low) and a tolerance of about 10 cm-1. Score = matched peaks weighted by intensity minus penalty for strong predicted modes that are absent. Return top 5 with per-peak evidence.
4. Optional re-ranker: a retrieval embedding trained on CRD-synthesized spectra (day 2 if the matcher is brittle). Same architecture as the symmetry model's encoder, so one training run can serve both.

Evaluation of this step, planned as a comparison for the write-up: on the held-out spectra, report top-1 and top-5 identification accuracy for (a) the CRD matcher, (b) the retriever if built, and (c) Claude vision given only the plotted spectrum image and asked for its top 3 materials. Whichever wins becomes the default hypothesis generator; the comparison itself is a result worth a paragraph.

Third-party pretrained Raman models: scout for public weights with 2D-materials training data for at most one hour on day 1. Expected outcome is that none exist (public models are trained on molecules, minerals, bacteria, pharmaceuticals); record that as a finding and rely on the CRD-trained retriever.

## 2. Where retrieved arXiv figures are used (layer C)

In decreasing order of value:

1. **Reference spectrum where no database exists.** For graphene, 2H-MoS2 and CrSBr the CRD is silent, so the published panel is the reference. The agent retrieves the Raman panel from the top-ranked paper for the hypothesis, digitizes peak positions and relative intensities, and compares them to the fit. Output: a side-by-side figure plus a table of measured vs. reference positions with the citation. This is the step that makes the reading checkable.
2. **Calibration curves that exist only as plots.** Separation vs. layer number (MoS2), I(D)/I(G) vs. L_D, the G and 2D position correlation plot for strain vs. doping, mode frequency vs. temperature for CrSBr. Digitized curves, with the paper as source and a self-test from numbers in the text, are how the day-2 tool-building loop turns a paper into a registry relation.
3. **Evidence for assignments and anomalies.** Polarization or temperature series panels carry the mode labels in their annotations. Claude vision reads them off the panel; the agent shows the panel as justification. Example: Mondal et al. 2024 for the laser-energy-dependent Ag2 axis in CrSBr.
4. **The report and one-pager figure.** Measured spectrum beside the retrieved panel with the citation underneath.

Rules for the agent:

- Fetch figures only after a hypothesis exists, from the top two or three papers per (material, property), never for all candidates.
- Keep a panel only if Claude vision confirms it is a spectrum or a calibration curve with readable axes; discard maps, images, schematics.
- Cache by arXiv id: PDF, parsed structure, extracted figures, vision verdict per panel, digitized traces. The same ten papers will be hit for every MoS2 spectrum.
- Prefer the arXiv version; when a paper is PubMed-only, cite without a figure and say so in the report.
- Record the figure number and panel label in every provenance entry so the write-up can cite "Fig. 2b of arXiv:1005.2509".

Do not fetch figures for: unknown-material identification (matcher's job), relations given as equations in the text, or papers where the Raman data is a map or 2D plot.

## 3. Consequences of the CRD coverage check (2026-10-20)

Verified against `crd.json` (details in `data/README.md`): CrSBr, graphene and 2H-MoS2 are absent; MoS2 exists only as 3R; 2H-WS2, 2H-WSe2, h-BN, CrBr3, InSe, GaSe, HfS2, Bi2Se3 are present. "2D" entries are layered bulk cells, not monolayers.

Decisions:

- First end-to-end test material: **2H-WS2** (in the CRD, textbook spectrum, many arXiv papers). It exercises every layer including the matcher.
- MoS2 and CrSBr are the literature-only cases that demonstrate why the figure layer matters. The one-pager should say explicitly that for the materials people care most about, the computed database is silent and the papers are the database.
- Curated literature mode tables for the three demo materials are mandatory, not optional. Write them on day 1 morning with sources.
- Matcher uses the bulk CRD modes with a note that monolayer frequencies can differ by a few cm-1 and that shear and breathing modes below 50 cm-1 are absent in monolayers.

## 4. Order of work on day 1 (refined)

1. Move the CRD zip to `data/raw/crd/` and unzip; promote `scratch/crd/crd_loader.py` to `src/ramanlens/perception/library.py` with the band-to-mode irrep mapping.
2. Literature mode tables for graphene, 2H-MoS2, CrSBr with sources (registry seed).
3. Reader, preprocess, peak fitter; test on one public WS2 or MoS2 spectrum.
4. Bond client with concept-query templates; run the retrieval test from `docs/bond-evaluation.md` (10 material-property pairs).
5. Port Lit-RAG parsing and figure extraction into `literature/pdf/`; run the figure extraction test on 10 arXiv PDFs.
6. Panel selection with Claude vision; digitizer; cache.
7. Agent CLAUDE.md with tool descriptions and report format; one end-to-end WS2 run by 20:00.

Cut lines, in order: drop the digitizer (show the panel without overlay), drop the retriever, drop the third-party model scouting.

## 5. Open items

- Lit-RAG modules to port: which files, what they depend on (GROBID? PyMuPDF?). Aditya to copy them in.
- Public spectra: pick two or three Zenodo records (WS2, MoS2, graphene) and record them in `data/README.md`.
- Valency MCP in Claude Code: token and server config.
- Public repo and licence.
