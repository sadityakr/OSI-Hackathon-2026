# Catalog of open experimental Raman data: 2D magnets and general libraries

Compiled 2026-10-21 for the OSI Hackathon project. Nothing was downloaded. Direct URLs below follow the patterns shown on the record pages; only items marked "verified" had their file lists read from a record page during this search.

## Access caveats from this search

- The Zenodo REST API (zenodo.org/api/records?q=...) and zenodo.org/search are blocked for the fetch tool (robots disallowed), and the sandbox proxy returns 403 on direct curl. Zenodo search was therefore done through web search, and individual record pages (zenodo.org/records/<id>) were read directly where they were not rate limited. Records that never surfaced in web search can still exist. Re-run the API queries on the Windows PC (commands at the bottom).
- Zenodo record 3572358 and 15035552 were rate limited (HTTP 429) and not read. TU Darmstadt TUdatalib pages (handle 4928, 4929) returned an Anubis bot-protection page and could not be read. rruff.net/about pages show a human-verification prompt (does not affect the zip directory listing).
- No verified raw polarization-resolved angle series or temperature series of a 2D magnet was found in an open repository. The best leads are flagged in the picks section.

## 1. 2D magnets (CrSBr and relatives)

| Record | Material(s) | What is in it | Files and format | Metadata available | Licence | Direct URL | Suitability (1-5) and reason |
|---|---|---|---|---|---|---|---|
| Zenodo 15048152 (DOI 10.5281/zenodo.15048152), "Dataset for publication: Magneto-Raman effect in van der Waals layered two-dimensional CrSBr antiferromagnet", Wdowik, Varade, Vejpravova, Legut, published 2025-03-18 | CrSBr | Supplement to arXiv:2503.15298. Page has no description; the paper concerns magneto-Raman (field and temperature dependent) response plus DFT. Contents of the zip NOT verified (may mix experimental spectra and calculations) | CrSBrPaper1.zip, 41.5 MB, md5 8fbee5523b0920682c62f3c8aeff50d2 (verified from record page). Internal format unknown | Linked to paper only; no README text on page | CC BY 4.0 | https://zenodo.org/records/15048152/files/CrSBrPaper1.zip?download=1 | 4: only open CrSBr Raman-related deposit found; must unzip to confirm it contains experimental spectra and any angle or temperature series |
| TUdatalib handle 4929 (and neighbour 4928), "Interplay of vibrational, electronic, and magnetic states in CrSBr" (Markina et al., arXiv 2509.10267) | CrSBr | Dataset record with the same title as the paper (Raman at 1.96 eV, temperature and polarization dependence per the paper). Page unreadable (bot protection) so files, size, licence unverified. The arXiv text itself says data are "available upon request" and does not cite this record | Unknown | Unknown | Unknown (TUdatalib default is often CC BY, check) | https://tudatalib.ulb.tu-darmstadt.de/handle/tudatalib/4929 (open in a browser; no direct file URL known) | 4 if files are open: this is the most likely true temperature and polarization series. Needs a manual browser check |
| NIMS MDR 968757e5-08f8-4055-80b8-4d17278de0b2, "Resonant Raman scattering of few layers CrBr3" (Kipczak et al., Sci. Rep. 14, 7484, 2024) | CrBr3 | Only the article PDF is deposited, not spectra (verified). Study has 4 excitation energies, polarization-resolved 12-layer data, temperature series on 20-layer sample | s41598-024-57622-w.pdf, 1.6 MB | Article only | CC BY 4.0 | https://mdr.nims.go.jp/filesets/adf8030e-2e63-4c29-9898-2158a82267b8/download | 1: PDF only, no numeric data. Useful only as a text source or for digitizing figures |
| Zenodo 14243883, CrSBr small-angle neutron scattering (Rybakov et al.) | CrSBr | Neutron scattering, not Raman | SmallScience_2024_ProbingShortRangeCorrelations.zip, 407.5 MB | n/a | CC BY 4.0 | https://zenodo.org/records/14243883/files/SmallScience_2024_ProbingShortRangeCorrelations.zip?download=1 | 1: not Raman; listed so nobody re-checks it |
| CrI3, CrCl3, CrPS4, FePS3, NiPS3, MnPS3, Fe3GeTe2, CrGeTe3 | all | Searches (web search for Zenodo, Figshare, Materials Cloud, NOMAD, OSF, Dryad) returned only papers and supplementary PDFs, no deposited raw Raman spectra | none found | | | | 0: nothing open found; ask authors or digitize figures |

### Computational (not experimental) but useful as references for a 2D Raman agent

| Record | Material(s) | What is in it | Files and format | Licence | Direct URL | Suitability |
|---|---|---|---|---|---|---|
| Materials Cloud Archive, DOI 10.24435/materialscloud:bq-vp (v2, 2024-10-04), Li, Gao, Shang et al. | 3,504 2D materials | Ab initio (FHI-aims DFPT) Raman spectra | data.zip 4.2 MiB, README.txt 523 B | CC BY 4.0 (metadata CC BY-SA 4.0) | https://doi.org/10.24435/materialscloud:bq-vp | 3: simulated 2D reference peaks, good for matching and as a prior |
| Materials Cloud DOI 10.24435/materialscloud:pg-h3 (v2, 2024-08-05), Bagheri and Komsa | 5,099 materials | Raman tensors and vibrational data from DFT | Computational_Raman_Database_v1.0.1.zip, about 145.7 MiB, JSON | CC BY 4.0 | https://doi.org/10.24435/materialscloud:pg-h3 | 3: large simulated library, includes polarization-capable tensors |
| C2DB ab initio Raman library (Taghizadeh et al., Nat. Commun. 2020, arXiv 2001.06313) | 2D materials | Computed Raman; experimental spectra were digitized from figures, not distributed | hosted at https://cmrdb.fysik.dtu.dk/c2db | not stated | https://cmrdb.fysik.dtu.dk/c2db | 2: simulated only |

## 2. General open Raman collections

| Record | Material(s) | What is in it | Files and format | Metadata available | Licence | Direct URL | Suitability (1-5) and reason |
|---|---|---|---|---|---|---|---|
| RRUFF Raman (rruff.info, redirects to rruff.net), listing verified, files dated 2026-06-23 | Minerals (thousands of spectra, 532, 785 nm and others) | Experimental spectra, grouped by quality rating (excellent, fair, poor, unrated) and by whether the sample was oriented. Naming per RamanSPy and Li et al.: raw and processed variants exist; the "LR-Raman" zip is the low-resolution set. Internal text-file layout (headers with mineral name, RRUFF ID, laser, orientation) not verified here because rruff.net/about is behind a check | excellent_oriented.zip 77M; excellent_unoriented.zip 229M; fair_oriented.zip 271K; fair_unoriented.zip 59M; poor_unoriented.zip 33M; unrated_oriented.zip 39M; unrated_unoriented.zip 12M; LR-Raman.zip 227M (all verified sizes). Each zip holds plain-text x,y spectra | Mineral name, RRUFF ID, laser wavelength, orientation (per file name and header; verify after unzip) | Free for use with citation of Lafuente et al. 2015 (RRUFF terms page not read; no formal SPDX licence) | https://rruff.net/zipped_data_files/raman/excellent_oriented.zip | 5 as library: big, stable, labelled, used by RamanSPy (rruff loader, base URL https://rruff.info/zipped_data_files/raman/), GEMS, RamanBench; no 2D materials though |
| RamanSPy bundled loaders (ramanspy.datasets) | Bacteria, cells, COVID, adenine, wheat, minerals | Seven loaders. bacteria (Ho et al. 2019: train 60k, val 3k, test 3k, clinical2018 12k, clinical2019 2.5k, labels) from the authors' Dropbox; volumetric_cells (THP-1 hiPSC, Zenodo 256329); MDA_MB_231_cells (low and high SNR pairs, about 160k train, 13k test, Google Drive); covid19 (Kaggle); adenine (Zenodo 3572359); wheat_lines (Zenodo 7644521); rruff | adenine: ILSdata.csv; wheat_lines: Data.mat (sizes not read); others are loader-dependent | Labels and class names | Not stated by RamanSPy; per-source terms apply | https://zenodo.org/record/3572359/files/ILSdata.csv?download=1 and https://zenodo.org/record/7644521/files/Data.mat?download=1 | 3: good for testing pipelines and denoising, but biological, not 2D materials |
| Raman Open Database (ROD), solsa.crystallography.net/rod | Minerals and crystals (SOLSA project) | 1,133 entries, latest deposit 2019-10-15. Bulk, rsync or API access not described on landing page (COD-style rsync may exist, unverified) | Unknown | Linked to COD-style crystal records | Public domain (contributors placed data in the public domain, per site) | https://solsa.crystallography.net/rod/ | 3: small, clean, public domain, but small and bulk download unclear |
| DTU data: "Datasets for replicating Raman Spectrum Matching with Contrastive Representation Learning" (Li, Schmidt, Alstrom, Analyst 2022) | Minerals (RRUFF raw and preprocessed: 487 classes, 1,700 spectra raw; 1,310 classes, 4,864 spectra preprocessed), organics (72 classes, 216 spectra, Zhang et al. 2020), bacteria (Ho et al.) | Prepared train and test splits for the matching paper | One download, 129.11 MB (file names not shown) | Class labels | Not stated | https://data.dtu.dk/articles/dataset/Datasets_for_replicating_the_paper_Raman_Spectrum_Matching_with_Contrastive_Representation_Learning_/20222331 (click Download; no direct URL) | 4: ready-made benchmark splits for a matching agent |
| Hugging Face JunhanCai/GEMS-Raman-Dataset | Minerals (RRUFF_CL, RRUFF_FT), QMe14S (simulated pretraining), bacteria, skin cancer, wheat, microplastic | 7 subdirectories, 0 to 3500 cm-1 on 3,500 points, min-max normalized, PyTorch and NumPy arrays | 8.86 GB total; README.md 2.94 kB | Subset names only | MIT | https://huggingface.co/datasets/JunhanCai/GEMS-Raman-Dataset (use huggingface-cli download) | 3: convenient ML splits, but normalized and resampled, so raw intensity is lost |
| Hugging Face chlange/SubstrateMixRaman | Bioprocess mixtures (8 metabolites) | 6,960 spectra (train 4.85k, val 1.41k, test 702), 1,878 columns | CSV plus auto Parquet, 91.8 MB | Concentrations | CC BY 4.0 | https://huggingface.co/datasets/chlange/SubstrateMixRaman/resolve/main/train.csv | 2: regression test set, not materials |
| raman-data PyPI package and RamanBench (arXiv 2605.02003; GitHub ml-lab-htw/raman_data, ml-lab-htw/RamanBench; HF Space HTW-KI-Werkstatt/RamanBench) | 93 datasets in the package, 77 in the benchmark (325,862 spectra); includes RRUFF raw and preprocessed, MLROD (Mars minerals), pharma, bioprocess | Loader package that pulls from Kaggle, Hugging Face, Zenodo, Figshare, Mendeley, GitHub, Google Drive. Benchmark text states no 2D-material datasets | Downloads on demand, `pip install raman-data` | `dataset.metadata` gives source and paper | Package MIT; each dataset keeps its own licence | https://pypi.org/project/raman-data/ | 4: one-stop way to fetch many open sets for a test harness |
| Kaggle (catalog only) | covid19 (Yin et al. 2021, used by RamanSPy) and others pulled by raman-data | Kaggle needs credentials in ~/.kaggle/kaggle.json | n/a | n/a | per dataset | https://www.kaggle.com/search?q=raman | 2: needs account; reachable through raman-data |
| RamanPFN (arXiv 2608.02157) | 74 public datasets, 129 regression targets, 21 classification tasks | No code or data links on arXiv page; PDF text unreadable here | none | | | | 1: no own data; reuses public sets |
| Zenodo 7907659, "Raman data" (Suchorab, Gaweda, NOMATEN) | 5 samples (nuclear-materials related) | WITec project files, need WITec Control FIVE | Raman data.zip, 66.1 MB | sample ids | ODbL 1.0 | https://zenodo.org/records/7907659/files/Raman%20data.zip?download=1 | 2: proprietary format, one-off |
| NIST, SDBS, others | n/a | SDBS is not open. No NIST experimental Raman library with open bulk download was verified in this search | | | | | 0: not found |

Black phosphorus and ReS2: searches for deposited angle-resolved Raman raw data returned only papers (arXiv 1610.03382, 1909.11423 and RSC supplementary PDFs). No deposited numeric dataset found.

## CrSBr papers: raw data deposited?

- Pawbake et al., PRB 107, 075421 (arXiv 2211.12939): no. No data availability statement at all; the PDF text has no repository link. Measurements are unpolarized, 5 K to 300 K, 633 nm.
- Torres et al., Adv. Funct. Mater. 2023 (arXiv 2212.01754): no. "Available from the corresponding author on reasonable request"; no repository.
- Mondal et al., 2024, npj 2D Mater. (arXiv 2410.22164, Raman Polarization Switching in CrSBr): no. "Available from the corresponding authors upon request"; no repository.
- Sahu et al., Nanoscale 2025 (arXiv 2502.01794): promised. Statement says data and analyses are in the "HeyRACK repository" with the persistent link "TBC with the proof". Repository not located by web search; check the published Nanoscale paper (DOI 10.1039/D5NR00562K) data statement.
- Uykur et al. (arXiv 2405.07853): no. No data statement and no repository; corresponding author e.uykur@hzdr.de.
- Markina et al., journal version in npj Quantum Materials (arXiv 2509.10267, journal DOI 10.1038/s41535-026-00850-2): arXiv text says upon request, BUT a TUdatalib record with the identical title exists (handle 4929, also 4928). Unverified; most promising.
- Additional: Markina et al. (arXiv 2608.18909, ion-irradiated CrSBr, temperature and polarization-resolved Raman): arXiv page lists no data link.
- Additional: Wdowik et al. (arXiv 2503.15298, magneto-Raman CrSBr): yes, Zenodo 15048152 (see table). The arXiv page itself was rate limited and not read, so the data statement is unconfirmed.

## Recommended first picks

1. General library candidate: RRUFF excellent_oriented.zip (77 MB, https://rruff.net/zipped_data_files/raman/excellent_oriented.zip). Clean, labelled, oriented minerals, same data used by RamanSPy, GEMS and RamanBench. Add excellent_unoriented.zip (229 MB) for volume. Also grab the DTU matching splits (manual click) as a ready benchmark.
2. 2D-magnet set: Zenodo 15048152, CrSBrPaper1.zip (41.5 MB, CC BY 4.0). Only open CrSBr Raman-related deposit verified to exist; unzip and check whether experimental spectra are inside.
3. Polarization or temperature series: TUdatalib handle 4929 (Markina et al., CrSBr temperature and polarization Raman). Open it in a browser, solve the bot check, read the file list. If closed, email the corresponding authors; Sahu et al. HeyRACK is the fallback once its link is public. Honest status: no polarization or temperature series is confirmed downloadable today.

## Download commands (Windows PC, run from the project root)

PowerShell:

```powershell
# Folders
New-Item -ItemType Directory -Force data\raw\spectra\CrSBr, data\raw\spectra\rruff, data\raw\spectra\ramanspy | Out-Null

# 2D magnet: CrSBr magneto-Raman dataset (Zenodo 15048152)
Invoke-WebRequest -Uri "https://zenodo.org/records/15048152/files/CrSBrPaper1.zip?download=1" -OutFile data\raw\spectra\CrSBr\CrSBrPaper1.zip
Expand-Archive data\raw\spectra\CrSBr\CrSBrPaper1.zip -DestinationPath data\raw\spectra\CrSBr\CrSBrPaper1 -Force
# md5 check, expected 8fbee5523b0920682c62f3c8aeff50d2
(Get-FileHash data\raw\spectra\CrSBr\CrSBrPaper1.zip -Algorithm MD5).Hash

# General library: RRUFF
Invoke-WebRequest -Uri "https://rruff.net/zipped_data_files/raman/excellent_oriented.zip" -OutFile data\raw\spectra\rruff\excellent_oriented.zip
Invoke-WebRequest -Uri "https://rruff.net/zipped_data_files/raman/excellent_unoriented.zip" -OutFile data\raw\spectra\rruff\excellent_unoriented.zip
Expand-Archive data\raw\spectra\rruff\excellent_oriented.zip -DestinationPath data\raw\spectra\rruff\excellent_oriented -Force

# RamanSPy test data (Zenodo)
Invoke-WebRequest -Uri "https://zenodo.org/record/3572359/files/ILSdata.csv?download=1" -OutFile data\raw\spectra\ramanspy\ILSdata.csv
Invoke-WebRequest -Uri "https://zenodo.org/record/7644521/files/Data.mat?download=1" -OutFile data\raw\spectra\ramanspy\Data.mat

# Zenodo search that the sandbox could not run (JSON lists of records)
foreach ($q in "CrSBr Raman","Raman 2D magnet","polarized Raman dataset","angle-resolved Raman","Raman spectra dataset") {
  $u = "https://zenodo.org/api/records?q=" + [uri]::EscapeDataString($q) + "&size=25"
  $n = ($q -replace '\W','_')
  Invoke-WebRequest -Uri $u -OutFile "data\raw\spectra\zenodo_search_$n.json"
}
```

curl (Git Bash or curl.exe):

```bash
mkdir -p data/raw/spectra/CrSBr data/raw/spectra/rruff
curl -L -o data/raw/spectra/CrSBr/CrSBrPaper1.zip "https://zenodo.org/records/15048152/files/CrSBrPaper1.zip?download=1"
curl -L -o data/raw/spectra/rruff/excellent_oriented.zip "https://rruff.net/zipped_data_files/raman/excellent_oriented.zip"
# optional ML sets
pip install huggingface_hub raman-data
huggingface-cli download JunhanCai/GEMS-Raman-Dataset --repo-type dataset --local-dir data/raw/spectra/gems   # 8.86 GB, check disk first
```

Manual steps: TUdatalib 4929 (https://tudatalib.ulb.tu-darmstadt.de/handle/tudatalib/4929) and the DTU matching datasets page (https://data.dtu.dk/articles/dataset/Datasets_for_replicating_the_paper_Raman_Spectrum_Matching_with_Contrastive_Representation_Learning_/20222331) need a browser click-through.
