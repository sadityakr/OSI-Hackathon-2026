# Valency MCP Bond: evaluation for Raman literature grounding

Date: 2026-10-20. Probes run through the Bond MCP tools connected to this account (server version 0.4.0).

## What Bond provides

Tool surface relevant to us: `semantic_search_papers` (embedding search, all sources), `search_by_abstract` and `search_by_abstract_batch` (full-text search over abstracts, semantic fallback), `search_by_title`, `get_paper_by_id`, `find_similar_papers`, `get_citing_papers` (forward citations via OpenAlex), `export_papers_bibtex`, filters by category, date, DOI, source. Every paper object carries `id` (arXiv id with version, or PubMed id), `doi`, `url`, `citation_count`, and `source`.

What Bond does not provide: full text, figures, extracted data, backward references (only forward citations), and no numeric or spectral search. It is a discovery and citation layer, nothing more. Everything after "which paper" is ours.

## Probe results

### 1. Concept queries (the way the agent should query)

| Query intent | Top results | Verdict |
|---|---|---|
| CrSBr Raman: mode assignment, polarization, temperature across T_N | Mondal et al. "Raman polarization switching in CrSBr" (2410.22164), Pawbake et al. spin-phonon coupling in bulk CrSBr (2211.12939, PRB 2023), Torres et al. resonant Raman and defects (2212.01754, AFM 2023), Sahu et al. resonance and anti-Stokes (2502.01794), Uykur et al. phonon and magnon dynamics (2405.07853), plus two PubMed-only entries (ACS Nano 2026 zone folding, Nano Lett 2025 Raman tensor elements) | Excellent. All the canonical CrSBr Raman papers in the top 12, confidence "good_match", 9 of 12 are arXiv so PDFs are fetchable |
| MoS2 layer counting from E2g to A1g separation | Lee et al. 2010 (1005.2509, 4,885 citations) first, then Zhang/Tan shear and breathing modes (1212.6796), Li et al. quantitative Raman thickness identification (1308.3835), Plechinger shear mode (1205.1916), Tan group substrate-intensity method (1602.05378) | Excellent. The textbook reference is rank 1 |
| Graphene defect density from I(D)/I(G) and linewidths | Cançado et al. 2011 (1105.0175, 3,715 citations) first, Eckmann et al. nature of defects (1207.2058), Bruna et al. doping dependence (1405.4264), Venezuela/Lazzeri/Mauri theory (1103.4582), plus the 2025 "Graphene Atlas" universal defect framework (2503.12459) | Excellent, confidence "high_confidence_match" |
| Exact title lookup, Lee 2010 | Found both the PubMed and arXiv records | Works; duplicates across sources must be merged by DOI |

Latency: 0.4 to 1.5 s per call.

### 2. Numeric peak queries (what a naive agent might do)

Query `Raman 115 244 344 cm-1` (the CrSBr Ag modes): keyword search found nothing, semantic fallback returned baotite, tungstates, pyroxene. Useless. Abstracts rarely contain peak positions, and embeddings do not encode numbers. Design consequence: the agent must never search by frequencies. It forms a material hypothesis first (from the library matcher or the user's metadata), then queries Bond by concept.

### 3. Citation graph

`get_citing_papers` on Pawbake 2022 returned 54 citing works with `in_corpus` flags and Valency ids where available; sorted by year this surfaces the 2026 CrSBr alloy, Cl-substitution and spin-phonon papers. `find_similar_papers` on Cançado 2011 returned the expected graphene defect cluster (Eckmann, Bruna, Jorio, Dresselhaus review). Both are useful for expanding from one anchor paper to the reference set for a material. Forward citations only: to walk backwards we rely on the PDF's own reference list (Lit-RAG parsing code).

### 4. Duplicates and sources

The same paper often appears twice, once from arXiv and once from PubMed. The arXiv record is the one we want (PDF access). Merge on DOI, prefer `source == "arxiv"`, keep the PubMed record only when no arXiv version exists (several CrSBr papers from ACS journals are PubMed-only; for those we can only cite, not fetch figures).

### 5. PDF access

Bond returns arXiv ids; PDFs come from `https://arxiv.org/pdf/<id>`. This cloud sandbox cannot reach arxiv.org (egress allowlist), so figure extraction must run on Aditya's PC in Claude Code, which is the plan anyway.

## Verdict

Bond is good enough, with one rule: concept queries only, built from a material hypothesis plus the property of interest. For the three target materials it returns the canonical papers at the top, carries citation counts for ranking, gives arXiv ids for PDF retrieval, and the citation tools expand an anchor into a reference set. Recall is high for arXiv-era physics (2010 onward). Older foundational work that exists only as journal articles (Tuinstra and Koenig 1970, Loudon 1964) is not in the corpus and must be hard-coded in the relation registry.

## Tests to run once PDFs can be fetched (on the PC)

1. Retrieval test (Bond only, 30 min): for each of 10 material-property pairs (CrSBr mode assignment, CrSBr temperature dependence, CrSBr polarization, MoS2 layer count, MoS2 strain, MoS2 doping, graphene defects, graphene doping, graphene strain, graphene layer count via 2D band), record whether the known reference paper is in the top 5. Target: at least 8 of 10. Store the query templates that work in `src/ramanlens/literature/queries.py`.
2. PDF availability test (15 min): for the top 5 of each pair, count how many have an arXiv id. Expect above 70 percent for 2D materials.
3. Figure extraction test (1 h, needs Lit-RAG parsing code): on 10 arXiv PDFs, extract figures with captions; count how many Raman spectrum panels are found and correctly captioned. Target: the Raman figure is found in at least 8 of 10, caption attached in at least 7.
4. Panel selection test (30 min): give Claude vision the extracted figures of a paper and the question "which panel shows the Raman spectrum and what are its axes"; check against manual inspection on the same 10 papers.
5. Digitization test (1 h): digitize one clean spectrum from 5 papers; compare extracted peak positions with values stated in the paper text. Target: within 2 cm-1.
6. End-to-end dry run (1 h): one MoS2 spectrum from a public repository through the full loop; time it, count tool calls, read the report critically.

Tests 1 and 2 need only Bond and can be run tonight from Claude Code with the Valency MCP configured. Tests 3 to 6 need the Lit-RAG parsing and figure code copied into `src/ramanlens/literature/`.
