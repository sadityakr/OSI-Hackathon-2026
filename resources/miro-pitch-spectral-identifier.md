# Miro pitch of interest: Spectral Identifier (Ramanujan theta + GTSF)

Source: Miro teaming board, frame "Marco 1" (screenshot saved as `miro-pitch-spectral-identifier.png`). Captured 2026-10-20.

## Team

- Wilmer Gaspar Espinoza (contact: wilmergasparespinoza@gmail.com)
- Pushpender Kumar
- Adewunmi Olaniyi
- **Looking for teammates**

## Motivation

Create an open-source tool that identifies materials from Raman and FTIR spectra using mathematical descriptors (Theta-Ramanujan + GTSF).

## Problem definition

Current spectral identification tools are limited, closed, or hard to extend. Researchers need transparent, reproducible and AI-ready methods for material matching and anomaly detection.

## Hackathon target

Improve **Spectral Identifier v1**: add real RRUFF spectra examples, strengthen GTSF descriptors, and produce clear scientific reports. Deliver a working open-source prototype.

## Poster graphic text

"Materials spectrum based on Ramanujan theta function": material structure (quantum states and lattice properties) -> Ramanujan theta function (mathematical modeling of quantum states) -> spectrum of response (thermal, optical and quantum responses).

## Notes and questions for Aditya

- Relevant fit: Raman spectroscopy is standard characterization in 2D materials and thin-film work; RRUFF is an open mineral Raman/IR/XRD database (https://rruff.info).
- Unclear what "GTSF" stands for and what the theta-function descriptor actually computes physically; worth asking before joining. Judges score novelty and relevance, so the physical justification of the descriptor matters.
- Existing baselines to compare against: cosine/correlation matching, peak-table matching, PCA/UMAP embeddings, CNN classifiers on RRUFF.
- Potential contribution angle: an agentic pipeline that takes a raw spectrum, preprocesses (baseline, cosmic rays, normalization), queries RRUFF, and writes a scientific report with uncertainty; MCP Bond (Valency) could supply literature citations for the Valency prize track.
