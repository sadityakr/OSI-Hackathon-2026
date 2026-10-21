# Catalog: open experimental Raman spectra of graphene, TMDs and h-BN

Compiled 2026-10-21 for the OSI Hackathon. Scope: raw numeric experimental spectra (not figure images).

## Read this first: what was and was not verified

- The Zenodo REST API (zenodo.org/api/...) is blocked for my fetch tool (robots disallowed), and Zenodo record pages then returned HTTP 429. So Zenodo was searched through general web search and a few record pages only. A proper Zenodo sweep should be run from the Windows PC (see the query commands at the end).
- Figshare search API returned unrelated recent items, so no Figshare 2D Raman record is confirmed.
- Kaggle, Hugging Face, OSF, NOMAD, GitHub: searched, nothing specific to experimental 2D-material Raman found. See "Negative results".
- Entries marked "page checked" had their landing page read. Exact file names are given only where the page listed them. "Direct URL" is a pattern or landing page where file names were not shown. Anything marked UNVERIFIED is from search snippets or memory.
- Honest overall finding: open raw experimental Raman of 2D materials is scarce and mostly small (a few spectra per paper, often xlsx). There is no large labelled public set of graphene or MoS2 spectra with layer number labels that I could confirm. Digitization (section 8) will likely be needed to build a labelled set.

## 1. Zenodo

| Record | Material(s) | What is in it | Files and format | Metadata available | Licence | Direct URL | Suitability (1-5) and reason |
|---|---|---|---|---|---|---|---|
| 14883846 "Dataset for Casimir-like effect driven self-assembly of graphene on molten metals" (page checked via ReadMe.txt) | Graphene flakes on molten metals, Au/Cu substrates | SEM tiffs, WITec Raman exports, SPM ASCII tables, DFT outputs, Python scripts | Raman as `*_Raman.txt` (WITec export with headings), exact names not shown; also .tiff, `*_SPM.txt`, CONTCAR | WITec headers (instrument settings); sample context in paper | Not shown on ReadMe; check record page | https://zenodo.org/records/14883846/files/ReadMe.txt (record: https://zenodo.org/records/14883846) | 3. Real graphene Raman txt files, but no layer labels and mixed content |
| 10008276 "VAMAS TWA 41 Project 11" (page checked) | Graphene powders and graphene nanoplatelets (keywords; interlaboratory study, ISO-G-SCoPe) | Interlaboratory Raman study dataset | `VAMAS TWA 41 Project 11.zip`, 609.2 MB, MD5 4393cef41531030a4f15656fe1831c5f; inner contents not seen | Interlab metadata likely, UNVERIFIED | CC BY 4.0 | https://zenodo.org/records/10008276/files/VAMAS%20TWA%2041%20Project%2011.zip?download=1 | 3. Many labs, permissive licence, but powders not flakes, internals unknown, large |
| 3572359 SERS interlaboratory study (page checked) | Not 2D materials (SERS analytes) | 3,516 spectra with metadata | `Dataset.zip` 47.2 MB (3,516 txt), plus CSV of all spectra 10.2 MB (called ILSspectra.csv) | labcode, substrate, laser, sample, conc | Not stated on page | https://zenodo.org/record/3572359 | 1. Out of scope, listed only as a format template for multi-lab Raman metadata |
| 6818608 (appeared in search for "Raman graphene"; page fetch rate limited) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | https://zenodo.org/records/6818608 | ? Check manually |
| 15316591 (README.txt surfaced in search; not fetched) | UNVERIFIED | UNVERIFIED | README.txt | UNVERIFIED | UNVERIFIED | https://zenodo.org/records/15316591/files/README.txt | ? Check manually |

## 2. Mendeley Data

| Record | Material(s) | What is in it | Files and format | Metadata available | Licence | Direct URL | Suitability (1-5) and reason |
|---|---|---|---|---|---|---|---|
| jsmbyfmck2 "Data for: Excitation energy dependence of Raman spectra of few-layer WS2" (page checked) | Few-layer WS2 | Electronic Supplementary Information data for the paper | File list not visible on landing page (page showed empty Files section); likely xlsx or txt | Excitation energy dependence implies multiple laser lines; layer counts in paper | CC BY 4.0 (DOI 10.17632/jsmbyfmck2.1) | https://data.mendeley.com/datasets/jsmbyfmck2/1 ; zip pattern UNVERIFIED: https://data.mendeley.com/public-api/zip/jsmbyfmck2/download/1 | 4. Exactly the WS2 few-layer series with laser dependence, if the files exist; confirm file list |
| bjkct6pwx5 v4 "Raman Analysis of WS2 Modes in an Epoxy Matrix" (page checked) | WS2 filler in epoxy (powder composite, not flakes) | Raw and processed individual Raman spectra, combined plots, metadata file with acquisition parameters | Not listed on page; "Download All" button | Acquisition parameters file | CC BY 4.0 (DOI 10.17632/bjkct6pwx5.4, 10 Apr 2026) | https://data.mendeley.com/datasets/bjkct6pwx5/4 ; zip pattern UNVERIFIED: https://data.mendeley.com/public-api/zip/bjkct6pwx5/download/4 | 3. Raw spectra with acquisition metadata, but composite material, WS2 2LA(M)+E2g and A1g modes only |

## 3. University of Southampton ePrints (DOIs 10.5258/SOTON/...)

All pages checked. Southampton file URLs follow https://eprints.soton.ac.uk/<id>/<version>/<filename>. Version numbers seen: 446821/3, 416765/3, 441402/1, 449632/1. Data file versions not confirmed, so open the landing page and copy the link.

| Record | Material(s) | What is in it | Files and format | Metadata available | Licence | Direct URL | Suitability (1-5) and reason |
|---|---|---|---|---|---|---|---|
| D0371 "Data for Probing Excitons, Trions and Dark Excitons in Monolayer WS2 using Resonance Raman Spectroscopy" (eprints ID unconfirmed, see note below; Hewak group, 2018) | Monolayer WS2 | Resonance Raman spectra 4 K to 295 K, efficiency corrected | `RRS_Spectra.xlsx` ~5 MB, `Supp_Figures.xlsx` ~3 MB, `readme.txt` ~2 kB | Temperature, excitation energy | CC BY | https://doi.org/10.5258/SOTON/D0371 (resolve DOI; see note below) | 4. Monolayer WS2, temperature series, clean xlsx |
| D1314, eprints 446821 | MoSe2/WSe2 heterobilayers, WSe2 monolayer, hBN and graphite references | Reflectivity and resonance Raman at 4 K, excitation 2.05 to 2.25 eV, twist angles 57, 20, 6, 60 deg | `Reflectivity_Spectra.xlsx` 131 kB, `Resonance_Raman_Data.xlsx` 12 MB, `Readme_Supporting_Data.txt` 1 kB | Twist angle, excitation energy, T=4 K, SiO2/Si | Not stated on page | https://eprints.soton.ac.uk/446821 ; readme: https://eprints.soton.ac.uk/446821/3/Readme_Supporting_Data.txt | 3. Includes WSe2 monolayer, but resonance and heterobilayer focus |
| eprints 416765 (CC-BY) | MoS2 on silicon nanowire (black Si) | Raman (4 points, 77 rows), E2g/A1g peak positions for 7 samples, PL | One Excel workbook with 4 tabs (Fig 2, 3, 6, 7) | Peak positions with Gaussian fit errors, 7 samples | CC BY | https://eprints.soton.ac.uk/416765 ; readme: https://eprints.soton.ac.uk/416765/3/readme.txt | 3. Tiny, but MoS2 E2g/A1g and peak table are easy to use; substrate is unusual |
| eprints 441402, D1315 | hBN-encapsulated MoSe2 and WSe2 monolayers | PL, reflectivity and resonance Raman at 4 K | `readme_supp_data.txt`, `Reflectivity_and_Photoluminescence_Data_.xlsx`, `RRS_Data_MoSe2_.xlsx`, `RRS_Data_WSe2.xlsx` | 4 K, hBN encapsulated | CC BY (version not given) | https://eprints.soton.ac.uk/441402 ; readme: https://eprints.soton.ac.uk/441402/1/readme_supp_data.txt | 3. MoSe2 and WSe2 monolayers; resonance-focused |
| eprints 449632, D1747 | hBN-encapsulated MoSe2, WSe2 monolayers and heterostructures | Reflectivity and resonance Raman, 4 K | `Readme.txt`, `Reflectivity_Data.xlsx` 206 kB, `HS20_Data.xlsx` 4 MB, `HS57_Data.xlsx` 7 MB, `WSe2_Data.xlsx` 2 MB, `MoSe2_Data.xlsx` 7 MB | Twist angle in file names | CC BY 4.0 | https://eprints.soton.ac.uk/449632 ; readme: https://eprints.soton.ac.uk/449632/1/Readme.txt | 3. Same family as above |
| eprints 451441, D1734 | hBN-encapsulated MoSe2 and WSe2 monolayers | Resonance Raman, 4 K, hBN hyperbolic phonon polariton study | `MoSe2_hBN.xlsx`, `WSe2_hBN.xlsx`, `Readme.txt` | 4 K | CC BY | https://eprints.soton.ac.uk/451441 | 3. Includes hBN-related physics |

Note on D0371: one fetch of https://eprints.soton.ac.uk/416765 returned the D0371 WS2 page while another fetch of the same ID's readme described MoS2 on black Si, so the eprints ID for D0371 is NOT reliably known and the 416765 row above is also in doubt. Resolve https://doi.org/10.5258/SOTON/D0371 and the MoS2 black-Si DOI in a browser to get the true links.

## 4. Dryad

| Record | Material(s) | What is in it | Files and format | Metadata available | Licence | Direct URL | Suitability (1-5) and reason |
|---|---|---|---|---|---|---|---|
| doi:10.5061/dryad.5qfttdzm9 "Studies of the mechanically induced reactivity of graphene with water using a 2D-materials strain reactor" (page checked) | Strained graphene membranes with water | Excel spreadsheets of processed Raman data plus DFT outputs | `2DMSR.zip` 45.69 MB, `README.md` 7.54 KB (version of 3 Mar 2026) | Strain-dependent Raman; details in README | Page says reusable under Dryad terms (CC0 typical for Dryad, not confirmed) | https://datadryad.org/dataset/doi:10.5061/dryad.5qfttdzm9 | 4. Strained graphene Raman with the authors' interpretation; processed rather than raw |

## 5. Materials Cloud Archive, Figshare, NIMS MDR (checked, mostly out of scope)

| Record | Material(s) | What is in it | Files and format | Metadata | Licence | Direct URL | Suitability (1-5) and reason |
|---|---|---|---|---|---|---|---|
| Materials Cloud 2023.177 (record 2379), "High-throughput computation of ab initio Raman spectra for 2D materials" | 3,504 2D materials, computed | Calculated (not experimental) spectra | `data.zip` 4.2 MiB, `README.txt`, `files_description.md` | Material IDs | CC BY 4.0 | https://archive.materialscloud.org/record/2023.177 | 2. Not experimental, but a useful theory reference for peak assignment |
| Figshare 27284883 (same computed set) | as above | as above | No files listed on page fetched | - | Not shown | https://figshare.com/articles/dataset/High-throughput_computation_of_ab_initio_Raman_spectra_for_two-dimensional_materials/27284883 | 2. Same, theory only |
| NIMS MDR 7b2b69ae-d222-4c9e-9c1c-6fed97dc8b62, "Raman scattering excitation in monolayers of semiconducting TMDs" (npj 2D Mater. Appl. 2023) | hBN-encapsulated MoS2, MoSe2, WS2, WSe2 monolayers, 5 K | Only the article PDF is deposited | `s41699-023-00438-5.pdf` 1.6 MB | - | CC BY 4.0 | https://mdr.nims.go.jp/datasets/7b2b69ae-d222-4c9e-9c1c-6fed97dc8b62 | 2. No numeric data, but the paper is a digitization target (section 8) |

## 6. Bundled and curated collections

| Record | Material(s) | What is in it | Files and format | Metadata | Licence | Direct URL | Suitability (1-5) and reason |
|---|---|---|---|---|---|---|---|
| RamanSPy bundled datasets (page checked) | Bacteria, cells, COVID serum, adenine, wheat, RRUFF minerals | Seven datasets, none 2D materials | via `ramanspy.datasets.*` | - | varies | https://ramanspy.readthedocs.io/en/stable/datasets.html | 1. No graphene or TMD content, only usable as a loader template |
| RRUFF (via github.com/yjcyxky/raman-spectra-datasets, page checked) | Minerals, includes graphite and molybdenite (UNVERIFIED which entries have raw files) | Raman spectra of minerals, unoriented and oriented | txt downloads on rruff.info | Locality, orientation, laser | Free for research, terms on site | https://rruff.info | 3. Bulk graphite and MoS2 (molybdenite) reference spectra, not few-layer |

## 7. Negative results

- GitHub: searches for MoS2 or graphene Raman csv repos returned only generic collections (RRUFF, SOP, KnowItAll). No dedicated 2D-material experimental dataset found.
- Hugging Face and Kaggle: nothing specific found for experimental 2D Raman.
- arXiv 2312.01389 (deep learning Raman identification of 2D materials, DDPM augmentation): abstract does not state a data release. Check the paper body for a data availability statement.
- arXiv 2601.16107 (benchmarking deep learning for Raman across open-source datasets): surfaced in search; not checked. Worth reading for a list of open Raman sets.
- OSF, NOMAD, h-BN deposits: no confirmed raw h-BN Raman dataset found. h-BN appears only inside hBN-encapsulated samples above and in the Southampton D1734 record.

## Recommended first picks

Given what is verified, no record is a perfect "clean single spectra, csv/txt, permissive licence" match. Best three:

1. Mendeley jsmbyfmck2, few-layer WS2 excitation-energy dependence (CC BY 4.0). Likely the closest to a layer-series with laser metadata. Confirm file formats on download.
2. Southampton D0371, monolayer WS2 resonance Raman 4 K to 295 K (CC BY). Clean xlsx with temperature metadata; convert with pandas to csv.
3. Zenodo 14883846, graphene Raman `_Raman.txt` WITec exports (real txt files, plain two-column spectra after the header). Licence to confirm on the record page.

Fallbacks: Southampton eprints 416765 (MoS2, tiny xlsx with E2g/A1g peak table, CC BY), Dryad strained graphene (processed Raman, authors' strain interpretation).

## 8. Digitization-target papers (use if raw data stays unavailable)

| Paper | arXiv or ID | Material | Figure to digitize | Notes |
|---|---|---|---|---|
| Ferrari et al. 2006, Raman spectrum of graphene and graphene layers, PRL 97, 187401 | cond-mat/0606284 (UNVERIFIED id) | Graphene 1 to many layers | 2D band vs layer number | Canonical layer counting |
| Lee et al. 2010, Anomalous lattice vibrations of single- and few-layer MoS2, ACS Nano 4, 2695 | no arXiv id known | MoS2 1 to 6 layers | E2g and A1g spectra and peak spacing vs layers | Canonical MoS2 layer counting |
| Cancado et al. 2011, Quantifying defects in graphene via Raman spectroscopy at different excitation energies, Nano Lett. | arXiv:1105.0175 (seen in search) | Defected graphene | ID/IG vs defect density and laser energy | Defect quantification |
| Lee et al. 2012, Optical separation of mechanical strain from charge doping in graphene, Nat. Commun. 3, 1024 | arXiv id not confirmed | Graphene | G vs 2D peak position correlation plot | Strain and doping separation |
| Berkdemir et al. 2013, Identification of individual and few layers of WS2 using Raman spectroscopy, Sci. Rep. 3, 1755 | PDF at perso.uclouvain.be/jean-christophe.charlier/wp-content/papercite-data/pdf/berkdemir2013.pdf (seen in search) | WS2 1 to many layers | Raman vs layers at 514 and 325 nm | WS2 thickness series |
| Mueller et al. 2018, Evaluating arbitrary strain configurations and doping in graphene with Raman spectroscopy, 2D Mater. 5, 015016 | Open access PDF at refubium.fu-berlin.de/handle/fub188/20564 (CC BY 4.0) | Graphene | G and 2D shifts under strain and doping | No research data attached; figures are digitizable |
| Zhang et al. 2013, Raman spectroscopy of the interlayer shear mode in few-layer MoS2 | arXiv:1205.1916 (seen in search) | Few-layer MoS2 | Low-frequency shear and breathing modes | Layer count from low-frequency modes |
| Zhao et al. 2015, Mapping of low-frequency Raman modes in CVD-grown TMDs | arXiv:1508.00768 (seen in search) | MoS2, WS2, MoSe2, WSe2 | Low-frequency modes vs layer and stacking | Multi-material |
| Stress and charge transfer in uniaxially strained CVD graphene | arXiv:1801.05586 (seen in search) | CVD graphene | G and 2D vs strain | Strain series |
| Raman scattering excitation in monolayers of TMDs, npj 2D Mater. Appl. 2023 | doi:10.1038/s41699-023-00438-5 (CC BY 4.0, PDF in NIMS MDR) | MoS2, MoSe2, WS2, WSe2 in hBN | RSE profiles at 5 K | Open licence allows reuse of figures |

Tip: digitize with WebPlotDigitizer or the Python package `plotdigitizer`, and keep a provenance column (paper, figure, laser, layers) per extracted spectrum.

## 9. Download commands (Windows PowerShell)

Raw files go to `data\raw\spectra\<material>\`. File names that were not visible on landing pages are resolved at run time through the Zenodo and Mendeley endpoints; the PC can reach them even though my sandbox could not. Run from the repo root `osi-hackathon-2026`.

```powershell
# folders
New-Item -ItemType Directory -Force data\raw\spectra\graphene, data\raw\spectra\WS2, data\raw\spectra\MoS2, data\raw\spectra\TMD_other | Out-Null

# 1) Zenodo 14883846 graphene: list files through the API, then download all
$rec = Invoke-RestMethod "https://zenodo.org/api/records/14883846"
$rec.metadata.license
$rec.files | ForEach-Object {
  Write-Host $_.key $_.size
  Invoke-WebRequest $_.links.self -OutFile ("data\raw\spectra\graphene\" + ($_.key -replace '[\\/]', '_'))
}

# 2) VAMAS TWA 41 Project 11 (609 MB, optional, graphene interlab study)
curl.exe -L -o "data\raw\spectra\graphene\VAMAS_TWA41_P11.zip" "https://zenodo.org/records/10008276/files/VAMAS%20TWA%2041%20Project%2011.zip?download=1"

# 3) Mendeley jsmbyfmck2 few-layer WS2 (UNVERIFIED zip endpoint; fallback: click Download All on the landing page)
curl.exe -L -o "data\raw\spectra\WS2\jsmbyfmck2_v1.zip" "https://data.mendeley.com/public-api/zip/jsmbyfmck2/download/1"
Expand-Archive "data\raw\spectra\WS2\jsmbyfmck2_v1.zip" -DestinationPath "data\raw\spectra\WS2\jsmbyfmck2" -Force

# 4) Mendeley bjkct6pwx5 WS2 in epoxy (UNVERIFIED endpoint)
curl.exe -L -o "data\raw\spectra\WS2\bjkct6pwx5_v4.zip" "https://data.mendeley.com/public-api/zip/bjkct6pwx5/download/4"

# 5) Dryad strained graphene (Dryad downloads need the landing page link; the API below is the documented route)
curl.exe -L -o "data\raw\spectra\graphene\dryad_2DMSR.zip" "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.5qfttdzm9/download"

# 6) Southampton readmes (data file links must be copied from each landing page; versions vary)
curl.exe -L -o "data\raw\spectra\MoS2\soton_416765_readme.txt" "https://eprints.soton.ac.uk/416765/3/readme.txt"
curl.exe -L -o "data\raw\spectra\TMD_other\soton_446821_readme.txt" "https://eprints.soton.ac.uk/446821/3/Readme_Supporting_Data.txt"
# D0371 monolayer WS2: resolve the DOI in a browser, then save RRS_Spectra.xlsx into data\raw\spectra\WS2\
Start-Process "https://doi.org/10.5258/SOTON/D0371"

# 7) Zenodo sweep for more candidates (run once; lists id, title, license, file names)
foreach ($q in "Raman graphene","Raman MoS2 spectra","Raman WS2 dataset","Raman spectroscopy 2D materials dataset","Raman hBN boron nitride") {
  $r = Invoke-RestMethod ("https://zenodo.org/api/records?q=" + [uri]::EscapeDataString($q) + "&size=25&type=dataset")
  $r.hits.hits | ForEach-Object { "{0} | {1} | {2} | {3}" -f $_.id, $_.metadata.title, $_.metadata.license.id, (($_.files | ForEach-Object key) -join "; ") }
} | Out-File data\raw\spectra\zenodo_sweep.txt
```
