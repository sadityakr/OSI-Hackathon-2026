# Polarization-resolved Raman symmetry and material model: research report

Prepared 2026-10-20 for the Open Scientific Intelligence Hackathon (Oct 21-22, 2026). Scope: an ML model that takes (polarization-resolved) Raman spectra of 2D materials, labels each peak with its phonon irreducible representation (irrep), and ranks candidate materials, trained on synthesized spectra from ab initio Raman tensor databases and validated on published experimental data.

Note on sources: the sandbox could not download Materials Cloud, RRUFF or PMC files directly (egress blocked, bot checks). Everything below about file contents comes from the published papers, record landing pages and tool pages that were readable. Items marked VERIFY must be checked in the first hour of the hackathon.

---

## 1. Prior art and novelty

### 1.1 ML for material identification from Raman spectra

- CNNs on RRUFF minerals (Liu et al. 2017 and many followers) classify a single unpolarized spectrum into a mineral class. The recent review "Recent Advances in Raman Spectral Classification with Machine Learning" (PMC12788301, 2026) summarises this line: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12788301/
- Contrastive Raman matching: Li, Schmidt, Alstrom, "Raman Spectrum Matching with Contrastive Representation Learning", Analyst 2022, one-shot matching with conformal prediction sets, no preprocessing: https://arxiv.org/abs/2202.12549
- RamanFormer (ITU, 2024, J. Chem. Inf. Model.) is a transformer for mixture component quantification, not solid-state identification: https://pubmed.ncbi.nlm.nih.gov/38854537/ ; RamanFormerSSL is its self-supervised sibling: https://research.itu.edu.tr/en/publications/ramanformerssl-a-self-supervised-learning-based-transformer-model/
- Google RSPTE (Raman Spectroscopy Pre-Trained Encoder, IEEE Access 2026): Barlow Twins self-supervised encoder for medicine, biology, mineralogy; no public weights found: https://research.google/pubs/raman-spectroscopy-pre-trained-encoder-a-self-supervised-learning-approach-for-data-efficient-domain-independent-spectroscopy-analysis/
- RamanPFN (arXiv 2608.02157, Aug 2026): tabular foundation model, 74 public Raman datasets, 129 regression and 21 classification targets; in-context inference, nothing on crystals or symmetry: https://arxiv.org/abs/2608.02157
- SMAE masked autoencoder for Raman (arXiv 2504.16130), bacteria: https://arxiv.org/abs/2504.16130
- Taghizadeh, Leffers, Pedersen, Thygesen, Nat. Commun. 11, 3011 (2020): 733 monolayers, resonant first-order Raman from third-order perturbation theory in GPAW, nine polarization setups (xx, xy, yx, yy, xz, yz, zx, zy, zz), three laser energies; identification = L2 distance between unit-area spectra after 6 cm-1 Gaussian smoothing, demonstrated only on MoS2 and WTe2: https://www.nature.com/articles/s41467-020-16529-6 (arXiv https://arxiv.org/abs/2001.06313)
- RamanGPT (Abel, Lee, Campbell, Choudhary, arXiv 2606.03764, June 2026): ALIGNN forward model trained on the Bagheri-Komsa Computational Raman Database (5,099 materials, 200 bins over 50 to 1000 cm-1) and a QLoRA LLM inverse model; cosine-similarity matcher at atomgpt.org/raman. Unpolarized, no symmetry labels: https://arxiv.org/abs/2606.03764
- "Phonon-informed Crystal Structure Classification" (arXiv 2601.01423, Jan 2026): ResNet ensemble classifies a structure-type cluster from Gamma-point phonon or Raman frequency lists (13,034-material Raman set, 62.7 percent accuracy); uses irreps only upstream to filter Raman-active modes: https://arxiv.org/abs/2601.01423
- DDPM plus CNN for 2D material identification from experimental Raman (Qi et al. 2023, arXiv 2312.01389, reports 100 percent on a small set): https://arxiv.org/abs/2312.01389
- Autoencoder workflow to bridge computed and experimental Raman (amino acid mixtures, J. Phys. Chem. A 2026): https://pubmed.ncbi.nlm.nih.gov/42622326/

### 1.2 ML and polarization or angle-resolved Raman

Searches (web, Valency semantic search over arXiv and PubMed) found no paper that trains a model to output irrep labels per Raman peak, and none that uses angle-resolved polarized series as model input for symmetry assignment. Closest items:

- Lazzaroni, Sharma, Rossi, "Investigating anharmonicities in polarization-orientation Raman spectra of acene crystals with machine learning" (PRB 2026, arXiv 2510.04843): ML interatomic potentials and ML polarizability tensors used to simulate PO-Raman of anthracene and naphthalene. ML is used for simulation, not for assignment: https://arxiv.org/abs/2510.04843
- "Predicting lattice orientation of LiNbO3 using ML-aided Raman" (APS March 2023, kNN on unpolarized spectra with EBSD labels): https://meetings-archive.aps.org/mar/2023/g00/43
- Malenfant-Thuot et al., deep learning of Raman tensors and Born charges (J. Phys. Condens. Matter 2024) and Raman of defective 2D materials (2025): ML predicts tensors from structure, does not read spectra: https://arxiv.org/abs/2410.20417
- Group-theory tools (Bilbao Polarization Selection Rules, phonopy irreps) do the forward problem analytically: https://cryst.ehu.es/cryst/polarizationselrules.html

### 1.3 What is and is not novel

Not novel: material identification from a single unpolarized spectrum against a DFT library (Taghizadeh 2020, RamanGPT 2026); CNN or transformer spectral classifiers; contrastive matching.

Novel, as far as the searches show: (a) a learned model whose output is a per-peak irrep label, (b) using the angle-dependent parallel and cross polarized intensity series as the model input, which is the physically correct carrier of symmetry information, (c) training on synthetic polarization series generated from full 3x3 Raman tensors of a 5,000-material database, and (d) joint symmetry-plus-identity output that constrains identification by point group. The honest pitch is "the inverse problem of Loudon's tables, learned from a database and tested on real 2D magnets". The literature-figure retrieval agent is a complement, not the novelty.

---

## 2. Training data sources

### 2.1 Computational Raman Database (Bagheri and Komsa, Sci. Data 10, 80, 2023). PRIMARY

- Paper: https://www.nature.com/articles/s41597-023-01988-5 (CC BY 4.0). Website: https://ramandb.oulu.fi (browse, Raman Simulator with P_in and P_out, polar plot, laser wavelength, temperature, broadening; per-structure pages show "raw data of calculated tensors").
- Data: Materials Cloud Archive, v1 doi:10.24435/materialscloud:ze-58 (record 1440, Computational_Raman_Database.zip, 145.7 MiB) and v1.0.1 doi:10.24435/materialscloud:pg-h3 (record 2283, Computational_Raman_Database_v1.0.1.zip, 152.8 MB, MD5 e2aaea03df70fda95dbd970c60456882, plus a change log). Licence CC BY 4.0. Direct links: https://archive.materialscloud.org/record/2283 (failover mirror if main is down: https://materialscloud-archive-failover.cineca.it/record/2283). Programmatic: `curl -L -o crd.zip "https://archive.materialscloud.org/record/file?filename=Computational_Raman_Database_v1.0.1.zip&record_id=2283"` (VERIFY exact file endpoint on the record page; the record JSON export lists the file list).
- Contents (from the paper): one JSON, 5,099 materials (4,137 3D, 385 2D, 72 1D, 277 0D, rest mixed), 725,163 modes of which 428,081 Raman-active or unknown; per mode: eigenvalue (cm-1), eigenvector, irreducible representation (Mulliken, from Bilbao point group tables), 3x3 Raman tensor for Raman-active and unknown-activity modes; per material: structure, point group and space group, Raman and IR activity lists, Born charges, dielectric constants, band gap, dimensionality, Materials Project id. Method: VASP, PAW, PBEsol, finite differences (0.005 A) of the dielectric tensor along phonon eigenvectors from Togo's phonon database; non-resonant, harmonic, no wavelength dependence. Spectra on the website use 300 K and 8 cm-1 broadening. Validation: SiO2 frequencies on average 18.5 cm-1 below experiment; dolomite 2.6 cm-1.
- Key names of the JSON are in the paper's Table 1 (not readable from the sandbox). VERIFY in the first 15 minutes: load the JSON, print keys of one entry, confirm the irrep string per mode and the tensor array shape (3,3) per mode.
- This is the only database confirmed to ship both tensors and irreps for thousands of materials. It makes the whole project feasible.

### 2.2 C2DB Raman (Taghizadeh et al. 2020)

- 733 monolayers, resonant spectra at three laser energies and nine polarization setups, 300 K, Gaussian sigma 3 cm-1. Access: spectra "freely available" via C2DB web (https://c2db.fysik.dtu.dk/), full database now "provided upon request" (ASE db file c2db.db or c2db.tar.gz with data.json per material, docs at https://2dhub.org/c2db/c2db.html). The web front page does not list Raman among searchable keys; per-mode Raman tensors are not stated to be stored. Mode irreps are shown in the paper figures only. Treat as a secondary source for 2D-specific resonant spectra, not for tensors. Request access early if wanted; it may not arrive in time.

### 2.3 Materials Project Raman (Liang, Dwaraknath, Persson, Sci. Data 6, 135, 2019)

- Only 55 compounds, 205 matched peaks vs RRUFF. JSON on figshare doi:10.6084/m9.figshare.7427393 with keys `eigenvals, eigenvecs, dielectric_tensor, raman_tensor, wavenumbers, intensity, metadata{mp_id, formula, structure, point_group, space_group, crystal_system}` plus RRUFF experimental records. No irreps stored. DFPT VASP PBE+U, 532 nm, 300 K. Useful only as a tiny paired computed-vs-experiment benchmark. Not served through the MP API as a Raman endpoint (MP docs list no Raman collection). Paper PDF: https://perssongroup.lbl.gov/papers/liang-2019-raman.pdf

### 2.4 2D Raman database (Li, Gao, ..., Shang, Sci. Data 12, 2025, doi 10.1038/s41597-025-04593-w)

- 3,504 2D materials, FHI-aims all-electron DFPT (LDA polarizabilities, PBE+TS relaxations), harmonic, first order, orientation-averaged powder spectra. Data: Materials Cloud record 2379, doi:10.24435/materialscloud:bq-vp, data.zip only 4.4 MB plus README.txt, CC BY 4.0: https://archive.materialscloud.org/record/2379 ; PMC full text https://pmc.ncbi.nlm.nih.gov/articles/PMC11880192/ ; scripts https://github.com/DownFly/FHI-aims-Raman-calculation-Script ; website http://mathtc.nscc-tj.cn/raman
- The paper describes stored data as geometry, frequencies and intensities. The 4.4 MB size makes full tensors for 3,504 materials unlikely. Use as a 2D-specific frequency and intensity library for the identification head; do not plan on tensors from it. VERIFY README.

### 2.5 Other computed sources

- Togo phonon database (phonondb, CC BY 4.0, now at https://github.com/atztogo/phonondb): Gamma-point eigenvectors; irreps can be regenerated with phonopy `--irreps` if needed. No tensors.
- JARVIS-DFT: a "JARVIS-DFPT (piezoelectric, IR, Raman, dielectric, BEC)" section exists but the documented dataset table lists no Raman set (https://jarvis-tools.readthedocs.io/en/master/databases.html). Skip.
- Matminer phonon_dielectric_mp (1,296 compounds, ABINIT DFPT): no Raman tensors.

### 2.6 Experimental data

- RRUFF (https://rruff.info, redirects to https://www.rruff.net): bulk zips at https://www.rruff.net/zipped_data_files/raman/ : excellent_oriented.zip 77 MB, excellent_unoriented.zip 229 MB, fair_oriented.zip 271 KB, fair_unoriented.zip 59 MB, poor_unoriented.zip 33 MB, unrated_oriented.zip 39 MB, unrated_unoriented.zip 12 MB, LR-Raman.zip 227 MB. Plain text per spectrum with header lines (name, RRUFF id, laser 532, 780 or 785 nm, orientation) and two-column wavenumber, intensity. The site is behind a bot check for search pages; the zip directory listing was readable. Licence: free for research, cite Lafuente et al. 2015. The "oriented" sets are polarization-resolved on known crystal faces, which is a rare public source of polarized spectra for 3D crystals, and the MP ids in Bagheri-Komsa let you join them to computed tensors for a sim-to-real sanity check.
- No open, machine-readable angle-resolved Raman dataset for 2D materials was found. Published figures must be digitized (Section 6). Candidate papers with clean angle plots: CrSBr (Section 5), black phosphorus (Ribeiro et al., ACS Nano 2015; Kim et al. Nanoscale 2015 https://pubs.rsc.org/en/content/articlehtml/2015/nr/c5nr04349b), ReS2 and ReSe2 (Nanoscale Horiz. 2020 https://pubs.rsc.org/en/content/articlehtml/2020/nh/c9nh00487d), MoS2 (arXiv 2001.04202), CrI3 (PRB 98, 085406). The TU Darmstadt data repository for "Interplay of vibrational, electronic, and magnetic states in CrSBr" (https://tudatalib.ulb.tu-darmstadt.de/handle/tudatalib/4929) likely holds raw angle series but was behind a bot wall; try from a browser.

---

## 3. Physics of synthesis

### 3.1 Intensity of one mode

For a Raman-active mode nu with 3x3 Raman tensor R^nu (derivative of the electronic susceptibility with respect to the normal coordinate), unit incident polarization vector e_i and unit scattered polarization vector e_s, the Stokes intensity at shift omega is

I(omega) = I_0 * sum_nu [ (n(omega_nu) + 1) / omega_nu ] * | e_s^T R^nu e_i |^2 * L(omega - omega_nu; Gamma_nu)

where I_0 absorbs the laser intensity and the omega_s^4 factor (omega_s = omega_L - omega_nu is the scattered photon frequency, omega_L the laser frequency; for omega_L much larger than omega_nu this factor is nearly constant across the spectrum), n(omega_nu) = 1/(exp(h_bar omega_nu / k_B T) - 1) is the Bose-Einstein occupation at temperature T, the 1/omega_nu comes from the zero-point amplitude of the mode, and L is a Lorentzian of full width Gamma_nu (typically 2 to 10 cm-1), L(x; Gamma) = (Gamma/2pi) / (x^2 + (Gamma/2)^2). Bagheri and Komsa write the cross section as d sigma / d Omega proportional to (omega_S^4 / c^4) * h_bar (n+1)/(2 omega_nu) * I_Raman / 45 with the powder activity I_Raman = 45 a^2 + 7 gamma^2, a = (R_xx + R_yy + R_zz)/3 and gamma^2 = 1/2[(R_xx - R_yy)^2 + (R_xx - R_zz)^2 + (R_yy - R_zz)^2 + 6(R_xy^2 + R_xz^2 + R_yz^2)]. Taghizadeh et al. use the same (n+1)/omega_nu form with u_in^alpha R_alphabeta u_out^beta. Use the single-crystal form above for polarization series and the powder activity only for the unpolarized reference.

### 3.2 Backscattering angle dependence

Laser along z (normal to the 2D sheet), sample in the xy plane. With the analyser rotated together with the incident polarization (sample fixed) at angle theta from the crystal x axis:

e_i = (cos theta, sin theta, 0), e_s(parallel) = e_i, e_s(cross) = (-sin theta, cos theta, 0).

Only the in-plane 2x2 block of R matters. Writing R_xx = a, R_yy = b, R_xy = R_yx = d (real, nonresonant):

I_par(theta) = | a cos^2 theta + b sin^2 theta + 2 d sin theta cos theta |^2
I_cross(theta) = | (b - a) sin theta cos theta + d (cos^2 theta - sin^2 theta) |^2

If the tensor elements are complex (resonant excitation, absorbing samples), write a = |a| e^{i phi_a} etc.; the cross terms then carry cos(phi_a - phi_b), which is what makes the CrSBr and black phosphorus patterns switch with laser energy. The model should be trained with random phases so it does not rely on the nonresonant shape.

### 3.3 Tensor shapes per point group (Loudon 1964; Bilbao Crystallographic Server)

Loudon, Adv. Phys. 13, 423 (1964) tabulates all 32 point groups; the Bilbao "Raman and Hyper-Raman tensors" and "Polarization Selection Rules" tools (https://cryst.ehu.es/cryst/transformtensor.html, https://cryst.ehu.es/cryst/polarizationselrules.html) generate them in any orientation and give backscattering selection rules. In-plane consequences for the groups most common in 2D materials (z out of plane):

- D2h (mmm; CrSBr, black phosphorus Cmce, 1T' phases): Ag = diag(a, b, c): I_par = |a cos^2 + b sin^2|^2, two-fold, I_cross = |b - a|^2 sin^2 cos^2, four-fold with zeros along axes; B1g = xy element only: I_par = d^2 sin^2(2 theta), I_cross = d^2 cos^2(2 theta); B2g (xz) and B3g (yz) vanish in normal backscattering.
- D3h (mmm2; 1H-MoS2 monolayer): A1' = diag(a, a, b): I_par = a^2 isotropic, I_cross = 0; E' (two components, elements d in xx = -yy and xy): I_par = d^2 and I_cross = d^2, both isotropic; E'' (xz, yz) silent in backscattering.
- D6h (6/mmm; bulk 2H-MoS2, graphite): A1g as A1', E2g as E', E1g silent.
- D3d (-3m; 1T-TMDs, CrI3 monolayer, Bi2Se3): A1g = diag(a, a, b): parallel only; Eg has elements c, d: I_par = c^2 and I_cross = c^2 isotropic (Eg appears in both channels, A1g only in parallel; the PRB 98, 085406 CrI3 work confirms A1g vanishes in cross).
- C2v (mm2) and Cs (m): A1 (or A') = diag(a, b, c) same two-fold pattern as Ag of D2h; B1, B2 (A'') carry xy or xz, yz. Cs loses the distinction, so the vocabulary collapses.
- Ci (-1; ReS2, ReSe2): all 18 Raman modes are Ag with fully general symmetric tensors (a, b, d all nonzero); angle series alone cannot separate them by irrep, only orientation can be determined.

Practical consequence: the irrep vocabulary is point-group dependent. Train the irrep head on a unified set of in-plane "pattern classes" that are what the data actually distinguish: {A-type diagonal isotropic (A1', A1g, A1 with a = b), A-type diagonal anisotropic (Ag of D2h, A1 of C2v, A' of Cs), E-type doubly degenerate (E', E2g, Eg, E), off-diagonal B-type (B1g, B2, A'')}, plus a "silent in backscattering" class. Map pattern class plus predicted point group to the Mulliken label via a lookup table built from the database irreps. Report Mulliken labels only when the point group is also predicted or supplied.

### 3.4 What an unpolarized single spectrum does and does not carry

An unpolarized spectrum at normal incidence measures sum over e_s of |e_s^T R e_i|^2 averaged over e_i, which reduces to combinations of the in-plane invariants a^2 + b^2, (a - b)^2 and d^2. It does not carry the angular dependence, so A-type vs E-type modes are only indirectly distinguishable through frequency and relative intensity priors learned from the library. The depolarization ratio rho = I_cross / I_par at one angle already separates "pure A diagonal" (rho = 0 for isotropic A, rho > 0 and angle dependent for anisotropic Ag) from E-type (rho = 1, isotropic) and B-type (rho varies 0 to infinity). A full angle series gives, per peak, the Fourier components of I_par(theta) and I_cross(theta) (constant, cos 2theta, cos 4theta and their phases), from which the pattern class is determined essentially analytically. This is the honest statement for the write-up: the symmetry head is well-posed with polarized input, ill-posed with unpolarized input; the material head works with both but gains a hard point-group constraint from the former.

### 3.5 Augmentation for realism

Apply to synthetic spectra (computed from tensors, then broadened) before training:
- Frequency scaling: global factor 0.97 to 1.03 and per-peak jitter of 3 to 10 cm-1 (PBEsol vs experiment differs by up to 18.5 cm-1 for SiO2; MP PBE mean deviation -9.7 cm-1, SD 18.6).
- Linewidth: Gamma from 2 to 15 cm-1, Lorentzian or Voigt.
- Intensity: per-peak multiplicative noise (log-normal, sigma 0.3 to 0.7) to mimic resonance and wavelength effects; random complex phases on tensor elements (phi uniform in 0 to pi with probability 0.5) to mimic resonant anisotropy.
- Baseline: polynomial or broad Gaussian fluorescence, plus Si substrate line at 520.7 cm-1 (random intensity) and the broad SiO2 band near 300 and 950 cm-1, plus a laser-edge tail below 100 cm-1 and a random low-frequency cutoff (50 to 100 cm-1) from the notch filter.
- Noise: Gaussian plus Poisson, SNR 5 to 100; occasional cosmic spikes.
- Thickness, strain, doping, temperature: shifts of a few cm-1 (MoS2 A1g - E2g separation grows 18 to 25 cm-1 with layers; strain about -2 to -4 cm-1 per percent for E' of MoS2), covered by per-peak jitter plus a small random splitting of E-type peaks (strain lifts degeneracy).
- Angle grid: random theta offset (unknown crystal orientation), 12 to 37 angles, angle-dependent intensity noise and a small polarization leakage (mix 2 to 5 percent of the other channel) to mimic imperfect analysers.
- Missing channels: randomly drop the cross series so the model works with parallel only or unpolarized only.

---

## 4. Model options and compute budget

### 4.1 Task definitions

- Task A, per-peak symmetry: input = list of detected peaks, each with frequency and the angle series I_par(theta_k), I_cross(theta_k); output = pattern class (5 classes) and, given the point group, the Mulliken irrep.
- Task B, point group: input = whole spectrum or peak set; output = one of about 10 to 15 layer-relevant point groups (multi-class, highly imbalanced; use top-3 accuracy).
- Task C, material identification: embedding of the query spectrum compared to embeddings of all library entries; metric = top-1 and top-5 recall under augmentation; report per 2D subset (385 2D entries in CRD, plus the 3,504 2D entries of the Shang database for frequencies only).

### 4.2 Dataset size

CRD gives 428,081 Raman-active modes over 5,099 materials. Synthesising 50 random augmented instances per material, each with 24 angles times 2 channels times 1,024 bins in float16, is 5,099 x 50 x 48 x 1,024 x 2 bytes = 25 GB on disk; generate on the fly instead (numpy vectorised, under 1 ms per spectrum) and store only tensors and irreps. Peak-list representation is far cheaper: at most 60 peaks per material x (1 + 48) floats. A 2D-only subset (385 CRD plus Shang) is small enough to augment 500 times.

### 4.3 Architectures

1. Peak-set transformer (recommended primary). Detect peaks (scipy find_peaks on the angle-summed spectrum), build tokens [omega, Fourier coefficients of I_par and I_cross up to cos 4theta and sin 4theta, raw 2 x 24 angle samples], 4 encoder layers, d_model 128, 4 heads, no positional encoding beyond the frequency feature. Heads: per-token pattern class (cross-entropy), pooled point group (cross-entropy), pooled 128-d embedding (InfoNCE against library embeddings generated with a second augmentation). Parameters about 1 M. Training: 200 k synthetic samples per epoch, 20 epochs, batch 256, well under one hour on an RTX 3060 (12 GB; the reported 20 GB is not a 3060 spec, an RTX 3060 has 12 GB, a 3090 or 4090 has 24 GB; plan for 12 GB and enjoy the surplus if real). Invariant to angle offset if trained with random offsets.
2. 1D CNN on the 2-channel stacked angle image (fallback). Input (2 x 24 angles) x 1,024 bins treated as a 48-channel 1D signal; 6 conv blocks, global pooling, same three heads but symmetry as a per-bin segmentation map (bin-wise irrep label where a peak exists). Simpler, robust to peak-detection errors, about 2 M parameters, 1 to 2 hours training. Less interpretable.
3. Transformer over spectral tokens (patches of 16 bins): works but needs more data and time; skip.
4. Retrieval only (no training): per-peak Fourier fit gives pattern class analytically; identification by Taghizadeh-style L2 or cosine on smoothed spectra plus point-group filter. This is the zero-risk baseline and should be implemented first; the learned model must beat it on the augmented test set.

Frameworks: PyTorch 2.x plus Lightning for the loop; RamanSPy (https://pypi.org/project/ramanspy) or rampy for baseline removal, cosmic-ray removal and normalisation of experimental spectra; pymatgen or spglib to map point groups; phonopy only if irreps must be regenerated.

### 4.4 Sim-to-real gap

- Augmentation above is the main tool (frequency scaling, resonance phases, substrate lines).
- Taghizadeh matching trick: smooth both sides with 6 cm-1 Gaussian and compare unit-area spectra within a window; add a global frequency-scale search (0.95 to 1.05) at test time.
- Peak-level matching at test time: Hungarian assignment between experimental peaks and library modes with a tolerance of 15 cm-1, then score by both frequency and pattern-class agreement; this is cheap and gives interpretable evidence per peak.
- Autoencoder domain adaptation (J. Phys. Chem. A 2026 amino acid workflow) is a day-2 extra; conformal prediction sets (Li et al. 2022) are a cheap way to report calibrated top-k.
- RRUFF oriented spectra joined via MP id to CRD entries provide a real polarized validation set for 3D crystals in minutes.

---

## 5. Experimental validation cases

| Material | Point group | Modes (cm-1) and irreps | Angle behaviour (backscatter, normal incidence) | Source |
|---|---|---|---|---|
| CrSBr (bulk and few-layer, Aditya has samples) | D2h (Pmmn) | Ag1 115 (114), Ag2 244 to 245.5, Ag3 344; B2g, B3g Raman allowed by symmetry but silent at normal incidence | At 2.33 eV: Ag1, Ag3 maximal along b, Ag2 maximal along a; at 1.96 eV all three along b; Ag2 switches a to b across 1.58 to 2.33 eV (resonant complex tensor); BWF line shape of Ag2 at 785 nm, E parallel b | Klein et al. "The bulk vdW layered magnet CrSBr is a quasi-1D material" https://arxiv.org/abs/2205.13456 ; "Raman polarization switching in CrSBr" https://arxiv.org/abs/2410.22164 ; "Interplay of vibrational, electronic and magnetic states in CrSBr" https://arxiv.org/abs/2509.10267 ; mini-review https://arxiv.org/abs/2609.07425 |
| MoS2 monolayer and bulk | D3h (1L), D6h (bulk) | E' (E2g1) about 383 to 385, A1' (A1g) about 403 to 408; separation grows with layer number | A1g: I_par = a^2 cos^2 theta when the analyser is rotated with fixed incident polarization, zero in cross; E2g isotropic in both channels at 532 nm; at 633 nm E2g becomes two-fold (resonance), a good "hard negative" | Anisotropic electron-photon-phonon coupling in MoS2 https://arxiv.org/abs/2001.04202 ; Taghizadeh 2020 Fig. 3 |
| Black phosphorus | D2h (Cmce) | Ag1 about 360, B2g about 437, Ag2 about 464 (at 441.6 nm; 362, 439, 467 commonly at 532 nm) | B2g: I_par proportional to sin^2(2theta), I_cross proportional to cos^2(2theta) at all wavelengths; Ag patterns need complex a, c, phase phi_ca and switch with wavelength and thickness | Kim et al. Nanoscale 2015 https://pubs.rsc.org/en/content/articlehtml/2015/nr/c5nr04349b ; Ribeiro et al. ACS Nano 2015 |
| ReS2, ReSe2 | Ci (P-1) | 18 Ag modes, ReS2 130 to 440 (modes 3 and 5 at 151 and 212 used for orientation), ReSe2 100 to 300 | All modes figure-8 shaped with different principal directions; irrep head must output "all Ag, orientation only" | Nanoscale Horiz. 2020 https://pubs.rsc.org/en/content/articlehtml/2020/nh/c9nh00487d |
| CrI3 | D3d (1L), C3i bulk R-3 | Ag about 75, 108 to 110 (A1g), 128 (dominant Ag), Eg about 223 and others | A1g absent in cross; Eg in both; in the FM phase an antisymmetric element b gives cross-polarized Ag signal near resonance (ratio 0.5 to 1.5 at 633 nm): a documented failure mode of the nonmagnetic tensor model | PRB 98, 085406 https://link.aps.org/accepted/10.1103/PhysRevB.98.085406 ; "Large cross-polarized Raman signal in CrI3" https://arxiv.org/abs/2010.06633 |

CrSBr test protocol: digitize or, better, use Aditya's own angle series (parallel configuration, 532 nm, 10 degree steps). Expected model output: three peaks all "A-type anisotropic diagonal", point group D2h or C2v family, material top-1 CrSBr if CrSBr is in CRD (check by formula; mp-id for Pmmn CrSBr should exist; if absent, add its tensors computed from the literature or from a quick phonopy plus finite-difference run is not feasible in two days, so instead report top-k on the library and show the symmetry head is correct).

---

## 6. Literature-grounding backup

- Full text: arXiv HTML (https://arxiv.org/html/<id>) exists for most 2024+ papers and is the lightest source; ar5iv for older; PDF from https://arxiv.org/pdf/<id>. Aditya's Lit-RAG already does this, so reuse it.
- Figures and captions: PyMuPDF (fitz) `page.get_images()` plus caption text by proximity is the fastest (seconds per paper, no model); pdffigures2 (Scala, JVM) is the most accurate classical tool for figure-caption pairing; Docling and Marker give markdown with figure crops and captions and run on CPU in about 10 to 60 s per paper; Nougat and GROBID are heavier and add little here. Recommendation: PyMuPDF with a 300 dpi render of pages whose text contains "Raman" and "polar" or "angle", then Claude vision to pick the panel and read axis labels.
- Digitizing curves: WebPlotDigitizer (https://github.com/automeris-io/WebPlotDigitizer) is interactive; the Python `plotdigitizer` package (https://pypi.org/project/plotdigitizer) runs headless with three calibration pixel points but handles only single black-and-white traces; for polar plots and multi-trace panels, Claude vision reading peak maxima angles and relative intensities (coarse, 10 percent) is faster and adequate for a demo. Lightest stack for two days: Valency search (citation graph, abstract) plus arXiv HTML fetch plus PyMuPDF figure crop plus Claude vision for the panel description and a coarse angle readout.

---

## 7. Two-day plan (deadline Oct 23, 02:00 CEST)

Day 1, Oct 21
- 08:00 to 09:00: download CRD v1.0.1 zip (and the 2D Shang data.zip, RRUFF excellent_oriented.zip); inspect JSON keys; confirm irreps and 3x3 tensors; count 2D entries and point-group histogram. Go or no-go decision at 09:00.
- 09:00 to 11:00: `synth.py`: tensor to I_par(theta), I_cross(theta), powder spectrum; augmentation; unit tests against the analytic D2h, D3h, D3d cases; pattern-class lookup from irrep strings per point group.
- 11:00 to 12:30: analytic baseline: peak detection, Fourier fit, pattern class, L2 and cosine retrieval, point-group filter. Evaluate on held-out synthetic set.
- 13:00 to 16:00: peak-set transformer in Lightning; three heads; train on the fly; first curves.
- 16:00 to 18:00: CrSBr test: load Aditya's own angle series or digitized Klein 2022 and 2410.22164 data; run baseline and model; black phosphorus B2g case from Kim 2015 digitization.
- 18:00 to 20:00: minimum viable demo: one notebook or Streamlit page that takes a folder of angle spectra, outputs peak table with pattern class and irrep, point group top-3, material top-5, and a polar plot. Commit. Cut line 1: if the transformer is not better than the baseline by 20:00, ship the baseline plus retrieval and call the ML part "learned re-ranker".

Day 2, Oct 22
- 08:00 to 10:00: RRUFF oriented spectra joined to CRD by MP id; measure real-data identification top-5; add resonance-phase augmentation if CrSBr Ag2 is mislabelled.
- 10:00 to 12:00: literature agent: for the top-3 candidate materials, Valency search, arXiv HTML fetch, PyMuPDF figure crop, Claude vision summary of the published angle pattern; show it beside the model output.
- 13:00 to 15:00: evaluation figure (confusion matrix of pattern classes, retrieval recall vs augmentation strength, CrSBr polar plots measured vs synthesized) and ablation unpolarized vs polarized input (the key scientific claim).
- 15:00 to 18:00: one-page write-up with the figure; README; licence notes (CC BY 4.0 for CRD and Shang, RRUFF citation).
- 18:00 to 21:00: 4-minute video (screen capture of the demo on CrSBr, 30 s of physics, 30 s of results, 30 s of limits). Cut line 2: drop the literature agent if the model and write-up are not done by 15:00. Cut line 3: drop RRUFF if the join takes more than an hour.
- 21:00 to 24:00: buffer, submission by 01:00 CEST on Oct 23.

---

## 8. Risks and open questions

1. CRD JSON content: tensors and irreps are stated in the paper, but key names and whether tensors are given in the crystal Cartesian frame (needed for angle series) are unverified. Mitigation: inspect in hour one; tensors in the standard setting from VASP are Cartesian in the POSCAR frame, which is fine.
2. Download access: Materials Cloud main site has had maintenance windows (the CINECA failover exists); RRUFF has bot checks on search pages but served the zip directory. Download from the Windows PC with a browser if curl fails.
3. Few 2D entries: only 385 of 5,099 CRD materials are 2D; CrSBr itself may be absent. The symmetry head trains on all 5,099 (symmetry physics is dimension independent); identification restricted to 2D is a smaller problem. Check CrSBr, MoS2, black phosphorus, ReS2, CrI3 presence first.
4. Resonance: DFT tensors are nonresonant and real; CrSBr, black phosphorus and MoS2 at 633 nm show patterns that require complex elements, and CrI3 in the FM phase needs an antisymmetric term. Train with random phases and state clearly that the model predicts pattern classes, which survive resonance for B-type and E-type modes, while A-type anisotropic axes can flip.
5. Intensity reliability: DFT relative intensities carry large errors; retrieval should weight frequencies over intensities and the model must be trained with strong intensity noise.
6. Frequency offsets of 10 to 20 cm-1 between PBEsol and experiment; handle via scaling search and tolerance.
7. Peak detection on noisy experimental data is the weakest link of the peak-set model; keep the CNN fallback or feed the transformer with soft peaks.
8. Licences: CRD and Shang data CC BY 4.0 (fine); C2DB requires a request; RRUFF free for research with citation; MP data CC BY 4.0. All compatible with an open hackathon repo.
9. Experimental test data must be digitized from figures unless Aditya's own CrSBr series is used; digitization adds about 10 percent intensity error, acceptable for pattern classes.
10. Vocabulary: Mulliken labels depend on point group and axis convention (Bilbao standard setting vs paper conventions, e.g. B2g vs B3g swap with axis relabelling). Report pattern classes as the primary metric and Mulliken labels as secondary.

---

## 9. Key references

- Bagheri, Komsa, "High-throughput computation of Raman spectra from first principles", Sci. Data 10, 80 (2023): https://www.nature.com/articles/s41597-023-01988-5 ; data v1.0.1 https://archive.materialscloud.org/record/2283 (doi 10.24435/materialscloud:pg-h3), v1 https://materialscloud-archive-failover.cineca.it/record/1440 (doi 10.24435/materialscloud:ze-58); site https://ramandb.oulu.fi
- Taghizadeh, Leffers, Pedersen, Thygesen, Nat. Commun. 11, 3011 (2020): https://www.nature.com/articles/s41467-020-16529-6 ; https://arxiv.org/abs/2001.06313 ; C2DB https://c2db.fysik.dtu.dk/ and https://2dhub.org/c2db/c2db.html
- Liang, Dwaraknath, Persson, Sci. Data 6, 135 (2019): https://perssongroup.lbl.gov/papers/liang-2019-raman.pdf ; data doi 10.6084/m9.figshare.7427393
- Li, Gao, Xie, Zhu, Shi, Zeng, Zhan, Chen, Shang, Sci. Data 12 (2025) doi 10.1038/s41597-025-04593-w: https://pmc.ncbi.nlm.nih.gov/articles/PMC11880192/ ; data https://archive.materialscloud.org/record/2379 ; scripts https://github.com/DownFly/FHI-aims-Raman-calculation-Script
- RRUFF: https://www.rruff.net ; zips https://www.rruff.net/zipped_data_files/raman/
- Togo phonon database: https://github.com/atztogo/phonondb ; WMD mirror https://github.com/WMD-group/phononDB
- Abel, Lee, Campbell, Choudhary, RamanGPT (2026): https://arxiv.org/abs/2606.03764
- Chen et al., Phonon-informed crystal structure classification (2026): https://arxiv.org/abs/2601.01423
- Li, Schmidt, Alstrom, contrastive Raman matching (2022): https://arxiv.org/abs/2202.12549
- RamanFormer (2024): https://pubmed.ncbi.nlm.nih.gov/38854537/ ; RamanPFN (2026): https://arxiv.org/abs/2608.02157 ; Google RSPTE (2026): https://research.google/pubs/raman-spectroscopy-pre-trained-encoder-a-self-supervised-learning-approach-for-data-efficient-domain-independent-spectroscopy-analysis/
- Lazzaroni, Sharma, Rossi, PO-Raman of acenes with ML (2025/2026): https://arxiv.org/abs/2510.04843
- Qi et al., DDPM-CNN 2D identification (2023): https://arxiv.org/abs/2312.01389
- Loudon, "The Raman effect in crystals", Adv. Phys. 13, 423 (1964); Bilbao Raman tensor tools https://cryst.ehu.es/cryst/transformtensor.html and https://cryst.ehu.es/cryst/polarizationselrules.html
- CrSBr: Klein et al. https://arxiv.org/abs/2205.13456 ; Raman polarization switching https://arxiv.org/abs/2410.22164 ; vibrational, electronic, magnetic interplay https://arxiv.org/abs/2509.10267 ; mini-review https://arxiv.org/abs/2609.07425
- MoS2 anisotropic coupling: https://arxiv.org/abs/2001.04202
- Black phosphorus: Kim et al., Nanoscale 2015 https://pubs.rsc.org/en/content/articlehtml/2015/nr/c5nr04349b
- ReS2, ReSe2 orientation: https://pubs.rsc.org/en/content/articlehtml/2020/nh/c9nh00487d
- CrI3: https://link.aps.org/accepted/10.1103/PhysRevB.98.085406 ; https://arxiv.org/abs/2010.06633
- Tools: RamanSPy https://pypi.org/project/ramanspy ; plotdigitizer https://pypi.org/project/plotdigitizer ; WebPlotDigitizer https://github.com/automeris-io/WebPlotDigitizer ; pdffigures2 https://github.com/allenai/pdffigures2
