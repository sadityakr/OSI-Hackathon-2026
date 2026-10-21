# Idea ranking and decision (2026-10-20)

## Decision

Build **RamanLens** (working name): an agent that reads a Raman spectrum the way an experienced 2D-materials researcher does and shows its work. Input: a spectrum (or a series). Output: a peak table, a physical reading (material, layer regime, disorder, strain or doping, temperature anomalies where applicable), each claim tied to the relation it used, the paper it came from, and the published reference figure retrieved from the literature and shown next to the measurement.

The learned components (library retrieval embedding, polarized-Raman symmetry classifier, any third-party Raman model) are tools the agent calls, not the project. The physics lives in a registry of cited, tested relations. Literature grounding runs through Valency MCP Bond (discovery, citation graph) and our own PDF parsing and figure extraction (copied from Lit-RAG, not depending on it).

## Candidates considered

| # | Idea | Impact | Innovation | Relevance | Novelty | Risk in 2 days | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Raman interpretation agent with cited relations and figure-level grounding | High: every 2D lab does this by hand | High: physics rules plus retrieval plus vision, agent writes its own analysis scripts | Direct | High: no tool grounds spectral interpretation at the figure level | Low to medium | **Chosen** |
| 2 | Polarized-Raman symmetry classifier trained on DFT Raman tensors (CRD) | Medium | High | Direct | High (no prior ML irrep assignment found) | High: needs digitized angle series, resonance caveat | Optional module inside 1, day 2 |
| 3 | Bond plus figure retrieval as a generic literature tool | Medium | Medium | Indirect | Medium | Low | Folded into 1 as the grounding layer; also the Valency-track story |
| 4 | Automated Raman meta-analysis of one material family | High if it works | High | Direct | High | High: extraction quality | Stretch goal after 1 |
| 5 | Join Miro team "Spectral Identifier" (Ramanujan theta descriptors) | Unclear | Unclear | Direct | Unclear | Medium, no control of the science | Declined |
| 6 | Transport (tunnel junction IV) analysis agent | Medium to high | High | Direct | Very high | Medium, validation on own data | Future module 2; same harness |

## Why 1 over 2

Idea 2 is the more novel scientific result, but its demo depends on data we do not have in machine-readable form and its headline caveat (DFT tensors are nonresonant, real measurements are resonant) takes a minute to explain in a four-minute video. Idea 1 has a demo that validates itself in front of the viewer, uses every asset Aditya already has (Raman expertise, CrSBr samples, Lit-RAG code, Bond), and 2 slots in as a tool if day 1 goes well.

## What makes the write-up defensible

- Every relation in the registry carries its source paper, the equation with all variables defined, and a self-test reproducing a number from that paper.
- Build set and evaluation set are disjoint: papers used to write or generate tools are never used to evaluate the agent.
- The report distinguishes "measured" (fit outputs), "inferred" (relation applied, with validity range) and "literature" (retrieved figure or value), and says what Raman cannot tell.
- Honest ablation: agent with literature grounding vs. agent without, scored against the papers' own interpretation on categorical fields.

## Prizes targeted

- MDRI general prize: the full project.
- Valency track: Bond is the discovery and citation layer in every run; the figure retrieval extends Bond from "which paper" to "which panel".
- Marimo track: the evaluation notebook and the demo UI in Marimo if time permits (cheap to do, drop if not).
