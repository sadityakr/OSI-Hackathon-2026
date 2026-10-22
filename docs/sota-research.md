# State of the art for agent-driven Raman analysis (research, 2026-10-22)

Three research sub-agents (web search plus Valency Bond), 00:30 CEST. Links came verbatim from tool results and have
not yet been through verify-links. [V] = number seen in the source text; [T] = training data, not verified.

## Finding 1: no public ML model is worth integrating for 2D-materials Raman

- No public weights cover 2D materials. The 2D-material classifiers that exist (Qi et al., arXiv 2312.01389, 594
  spectra, 100 % claimed) ship no code or data. "Raman foundation models" (RamanPFN, arXiv 2608.02157; RSPTE) have no
  released checkpoints. Confidence: moderate-high.
- RamanBench (Koddenbrock, Lange et al., arXiv 2605.02003, 2026): 28 models on 74 experimental data sets; tabular
  foundation models (TabPFN v2.5) win, especially below 50 training samples; "no method generalizes across data sets";
  no out-of-distribution test. pip `raman-bench`, `raman-data`. Useful as a citation, not as an agent tool.
- Contrastive spectrum matching (Li, Schmidt, Alstrom, Analyst 2022, doi:10.1039/D2AN00403H): RRUFF top-1 94.6 % vs
  1-NN cosine 38.8 % (raw) and 81.1 % (preprocessed). Lesson: preprocessing dominates classical matching quality.
- Structure-to-spectrum (RamanGPT, Abel et al., arXiv 2606.03764, ALIGNN on the CRD): 200 bins of about 4.75 cm-1,
  too coarse for 1 to 3 cm-1 layer shifts; adds nothing over querying the CRD directly.
- Layer number, strain, doping and defect density are read from 1 to 10 cm-1 shifts and width or intensity ratios.
  These come from physics relations on fitted peaks, not from global classifiers.

## Finding 2: what helps LLMs read spectra is extracted peaks plus retrieval, not vision

- IR-Agent (Noh et al., ICLR 2026, arXiv 2508.16112): expert tools raise top-1 from 0.073 to 0.103 (o3-mini); the
  retriever (similar-spectrum search) contributes most.
- SpectraLLM (arXiv 2508.08441): text prompts from extracted peaks beat rendered spectrum images, which the authors
  call "lossy and error-prone".
- No published LLM agent does Raman of 2D materials or inorganic solids (absence, moderate confidence). The
  bare-vs-tools comparison is novel.

## Finding 3: processing stack

- Depend on numpy, scipy, pybaselines (1.2.1, BSD-3, 50+ baselines), lmfit (1.3.4, BSD-3, Lorentzian, Voigt,
  BreitWigner/Fano, uncertainties). RamanSPy (Georgiev et al., Anal. Chem. 2024) last released June 2024; skip.
  ramanchada2 (CHARISMA, MIT, 1.5.0 Oct 2026) only if neon calibration spectra appear. rampy is GPL-2; avoid in MIT repo.
- Spikes: Whitaker and Hayes 2018 (Chemom. Intell. Lab. Syst. 179, 82), modified z-score on first differences;
  across a series, Barton and Hennelly 2019 (Appl. Spectrosc. 73, 893).
- Baselines: arPLS (Baek et al., Analyst 2014) or asPLS (Zhang et al. 2020). No independent head-to-head Raman review
  found; choose by downstream task (Liland et al., Appl. Spectrosc. 64, 1007, 2010). Broad carbon bands: fit a local
  linear background with the peaks rather than an aggressive global baseline. BWF can absorb a PL slope; select line
  shape by BIC.
- Fitted widths include the instrument function; Si 520.7 cm-1 is a convention (about 0.5 cm-1), check offset.

## Finding 4: the ten relations worth encoding first (all from named sources)

| # | Relation | Source | Status |
|---|---|---|---|
| 1 | Graphene strain vs doping from (omega_G, omega_2D), origin (1581.6, 2676.9), slopes 2.2 (strain), 0.70 (hole doping), 514.5 nm only | Lee et al. 2012, Nat. Commun. 3, 1024, arXiv 1209.0234 | [V] |
| 2 | Graphene L_D^2 = (1.8e-9) lambda^4 (I_D/I_G)^-1, n_D = 1.8e22/lambda^4 (I_D/I_G); heights; L_D >= 10 nm | Cancado et al. 2011, Nano Lett. 11, 3190, arXiv 1105.0175 | [V] |
| 3 | Stage 1 vs 2 disambiguation by Gamma_G (about 14 cm-1 in stage 1) | Cancado 2011; Ferrari and Basko 2013, arXiv 1306.5856 | [V] |
| 4 | MoS2 layer number from E2g-A1g separation (trend; thresholds need figure check) | Lee et al. 2010, ACS Nano 4, 2695, arXiv 1005.2509 | [V] trend |
| 5 | Linear chain model for shear and breathing modes, any layered material | Zhang et al. 2013, PRB 87, 115413, arXiv 1212.6796 | [V] |
| 6 | Graphene 1L test from 2D line shape; turbostratic red flag (single Lorentzian, about 2x width, +20 cm-1) | Ferrari et al. 2006, PRL 97, 187401; Lee 2012 | [V] |
| 7 | WS2 2LA(M) overlap with E2g near resonance: forced multi-peak fit | Berkdemir et al. 2013, Sci. Rep. 3, 1755; Mitioglu et al. 2014, arXiv 1406.3511 | [V] |
| 8 | Laser heating from temperature coefficients (graphene G -0.016 cm-1/K; 1L WS2, MoS2 values) | Calizo 2007 Nano Lett. 7, 2645; Huang 2016 Sci. Rep.; Sahoo 2013 arXiv 1302.5865 | [V] |
| 9 | Defect type from I_D/I_D' (about 13 sp3, 7 vacancy, 3.5 boundary) | Eckmann et al. 2012, Nano Lett. 12, 3925, arXiv 1207.2058 | [V], doping caveat (arXiv 1405.4264) |
| 10 | Artifact and condition rules: Si lines, interference makes intensity ratios substrate dependent (I2D/IG changes 370 %), D and 2D dispersion (about 50 and 100 cm-1/eV) | Yoon et al. 2009, arXiv 0908.4322; Ferrari and Basko 2013 | [V], Si 2nd-order positions [T] |

To verify before encoding: Mignuzzi 2015 LA(M) constants (MoS2 defects), MoS2 Delta-omega thresholds, Si
second-order positions. Several of these arXiv PDFs are already in `data/raw/pdfs/` (1005.2509, 1105.0175, 1207.2058,
1212.6796, 1405.4264).

Further qualitative rules with sources (CrSBr Ag2 polarization rotates with excitation energy, Mondal et al. 2025,
arXiv 2410.22164; CrI3 magnetism-activated crossed A1g; BP Ag patterns depend on wavelength and thickness, Kim et al.
2015 arXiv 1510.03263; MoS2 doping softens A1g, Chakraborty 2012 arXiv 1206.1758) go into the skill's reference
notes, not into numeric relations.

## Questions an expert asks about the measurement

Laser wavelength (dispersion, resonance, which relations apply), power and spot (heating, damage), objective NA,
grating and calibration (1 to 3 cm-1 thresholds), polarization configuration (selection rules), substrate and oxide
thickness (interference, Si lines, strain), temperature and field (magnetic phases), low-frequency filter cutoff
(shear and breathing modes visible or not).
