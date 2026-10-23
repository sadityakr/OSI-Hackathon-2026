# Literature-in-the-Loop: Scientific Analysis Grounded in Published Research

**Analysis Paralysis** — Aditya Kumar, Pratyush Kumar Das, Sourish Dey

*Final write-up as submitted to the 4th Open Scientific Intelligence Hackathon (October 2026).*

Scientific measurements rarely have a single interpretation. A Raman peak can shift because of thickness, strain, defects, doping, or temperature, and identifying the material is only the beginning. We built Literature-in-the-Loop, a framework that connects experimental measurements with published scientific evidence, performs reproducible analysis, and records how conclusions are reached. Starting with Raman spectroscopy of 2D materials, we also explored its applicability across five additional areas of the physical sciences and mathematics.

## Approach

Literature-in-the-Loop is a meta-skill for Claude Code that converts published scientific knowledge into reusable analysis workflows.

- **Literature discovery:** The Valency Bond MCP searches the scientific citation graph, while our litpick MCP retrieves papers, extracts figures, and connects them to measurements with traceable citations.
- **Scientific analysis:** Our Raman skill includes data-quality checks, silicon calibration, peak fitting, uncertainty estimation, symmetry assignments, and physical interpretation. It covers 10 materials, approximately 100 papers, and a matcher built from 385 layered crystals.
- **Explainability:** Each analysis is recorded in an interactive Marimo notebook, exposing the measurements, assumptions, intermediate calculations, literature figures, and conclusions.
- **Continuous learning:** New techniques and instrument-specific artifacts are logged and reviewed before being incorporated into the skill, with changes tracked through Git.

To test broader applicability, we developed five additional scientific demonstrations:

| Field | Scientific application |
|---|---|
| Materials science | X-ray diffraction and lattice-parameter recovery |
| Chemistry | NMR signal analysis |
| Physics | Photoluminescence and band-gap estimation |
| Astronomy | Galaxy emission-line fitting and diagnostics |
| Mathematics | Self-avoiding walks and growth-constant estimation |

For these demonstrations, we compared simple baseline approaches against methods incorporating domain-specific physical constraints, using paired synthetic measurements and consistent error-analysis visualisations.

## Results

**Raman spectroscopy:** On held-out identification cases, our non-LLM measurement pipeline improved top-1 material identification from 0.52 to 0.58 relative to classical library search. Polarization-pattern accuracy improved from 0.00 to 0.89. On seven held-out interpretation cases, literature citation specificity improved from 1.00 to 1.57 on a 0–2 scale, although interpretation rubric performance declined from 0.50 to 0.41. This highlights the distinction between better evidence retrieval and better scientific reasoning.

In a real-data demonstration involving six CrSBr flakes, the system retrieved a published reference figure, reproduced the relative thickness ordering of four flakes, and appropriately declined to classify two samples outside the reference's supported range.

**Cross-domain demonstrations:** We tested five additional applications using 100 paired synthetic realisations per field, comparing simple baseline estimators with methods incorporating established physical constraints. The mean parameter-error reductions were 99.4% for XRD, 98.8% for NMR, 84.7% for photoluminescence, 42.0% for astronomy emission-line fitting, and 99.5% for self-avoiding walks. These results demonstrate the potential of domain-specific modelling, but are deliberately simplified, matched-model comparisons rather than independent validation of the complete AI agent. Full error distributions, bootstrap confidence intervals, and reproducible code are included in our supplementary report.

These cross-domain tests are preliminary demonstrations rather than independent validation of the complete literature-enabled agent. The Raman evaluation provides the more direct held-out evidence, while also identifying areas requiring improvement.

## Next steps

We aim to expand the framework into a reusable scientific knowledge system connecting measurements, instruments, papers, figures, physical relations, and analysis histories. Priorities include improving held-out scientific interpretation, evaluating the full agent on independent experimental datasets, and developing dedicated skills for other measurement techniques.

Our broader goal is to make scientific AI not only capable of analysing data, but also transparent about how it reaches conclusions, what evidence supports them, and when the available measurements are insufficient.

## Links

- Code and reproducibility: this repository
- Supplementary results: [cross-domain benchmark report (PDF)](supplementary/OSI_Supplement.pdf) | [comparison figure](supplementary/summary.png) | [benchmark data and reproducible code](supplementary/)
- Video demonstration: Literature-in-the-Loop project walkthrough (Google Drive, linked from the submission post)
