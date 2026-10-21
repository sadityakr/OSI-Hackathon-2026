# Open experimental Raman spectra: semiconductors, carbons beyond graphene, oxides and perovskites

Compiled Oct 21, 2026 from the cloud sandbox. Scope: (a) group IV and III-V/II-VI semiconductors, (b) carbons beyond graphene, (c) oxides and perovskites. Raw numeric data only (csv, txt, xlsx, h5, mat, spc, wdf, rod, jdx); no figure images.

## How to read this catalog

- **Verified** means the record page (or the host's directory listing) was fetched and showed the file names or the data description cited here. Anything else is marked **UNVERIFIED**.
- The sandbox cannot reach Zenodo, Mendeley, Figshare or Dryad APIs, and curl is blocked (HTTP 403 from the proxy). Only page fetches worked. Mendeley Data record pages render their file list with JavaScript, so Mendeley file names were **not visible** for any Mendeley record. Those rows give the DOI and the record-level zip pattern `https://data.mendeley.com/public-api/zip/<id>/download/<version>` (UNVERIFIED pattern; if it fails, use the "Download all" button in a browser).
- Zenodo direct links use the standard pattern `https://zenodo.org/records/<id>/files/<name>?download=1`. File names in those rows were read from the record page, so the links are verified in name but not test-downloaded.
- Suitability: 5 = clean numeric spectra plus rich sample metadata or a real series, easy to ingest; 3 = usable but awkward format, thin metadata or unclear content; 1 = not usable.
- Hard finding: **no verified open raw dataset was found for GaN, AlN, GaAs, CdS/CdSe quantum dots, SiGe, SiC polytypes (outside RRUFF), carbon nanotube RBM series, nanodiamond, BaTiO3, SrTiO3 (outside substrate reference), PbTiO3, BiFeO3, CeO2, HfO2 (spectra), or halide perovskites (MAPbI3, CsPbBr3).** Several searches returned only papers with figures. For those materials the practical route is RRUFF (mineral analogues), the Raman Open Database, or digitizing figures from the papers. See "Gaps" at the end.

---

## 1. Cross-material reference collections (cover all three families)

| Record | Material(s) | What is in it (incl. series and conditions) | Files and format | Metadata | Licence | Direct URL | Suitability | Reason |
|---|---|---|---|---|---|---|---|---|
| RRUFF Raman project (rruff.info, mirrored at rruff.net) | Minerals. Relevant species expected: anatase, rutile, brookite, hematite, magnetite, baddeleyite (ZrO2), cerianite (CeO2), perovskite (CaTiO3), zincite (ZnO), greenockite (CdS), moissanite (SiC), diamond, graphite. Exact entries inside each zip are UNVERIFIED | Per site: 8,583 unoriented high-resolution spectra (4,166 samples), 5,852 oriented high-resolution spectra (551 samples), 7,764 unoriented low-resolution spectra (3,891 samples). Oriented sets carry crystal orientation and polarization, useful for symmetry reasoning | Verified directory listing (modified 2026-06-23): `LR-Raman.zip` 227M, `excellent_oriented.zip` 77M, `excellent_unoriented.zip` 229M, `fair_oriented.zip` 271K, `fair_unoriented.zip` 59M, `poor_unoriented.zip` 33M, `unrated_oriented.zip` 39M, `unrated_unoriented.zip` 12M. Inner format (text with header lines, then x,y) UNVERIFIED | Header per spectrum expected to carry RRUFF ID, wavelength, orientation, locality (UNVERIFIED). Mineral name and ID give a phase label; no temperature or pressure series | Terms of use not stated on pages fetched; project asks for citation (Lafuente et al. 2015). UNVERIFIED redistribution terms | https://www.rruff.net/zipped_data_files/raman/excellent_unoriented.zip (rruff.info redirects here with HTTP 302) | 5 | Largest curated experimental set with phase labels and an oriented subset; best single source for oxide, SiC, ZnO, CdS and diamond reference spectra |
| RRUFF Raman excellent, processed, unoriented (Spectragryph mirror, 2017 snapshot) | 1,677 minerals | 5,185 spectra at four laser wavelengths, status "excellent, processed, unoriented", retrieved 2017-06-13 | `RRUFF_Raman_DB_5185excellent_entries_2017_01.zip`, 89.6 MB. Also `RRUFF_Raman_DB_3087entries_02.zip`, 54.6 MB (2012 CrystalSleuth set). Inner format is Spectragryph-oriented (UNVERIFIED) | Wavelength per spectrum not named on the page | Not stated (RRUFF terms apply, UNVERIFIED) | https://effemm2.de/spectragryph/databases/RRUFF_Raman_DB_5185excellent_entries_2017_01.zip | 3 | Smaller fallback if rruff.net is slow; processed (baseline-corrected) so loses raw background |
| Raman Open Database (ROD, solsa.crystallography.net/rod) | 1,133 entries (latest deposit 2100051, 2025-10-30). Verified entries include rutile TiO2 (3500262), hematite (3500155 at 785 nm, 3500276 at 633 nm). Verona group (Kumar, Cassetta, El Mendili, Zanatta, Daldosso, Mariotto, Nazzareni) deposited a series of oxides | One spectrum per entry, linked to a COD crystal structure where available. Example 3500262: Horiba LabRAM HR800, 633 nm, 50x, 600 grating, silicon-wafer calibration, air, 300 K, no baseline correction | `.rod` (CIF-style two-column loop `_raman_spectrum.raman_shift` and `_raman_spectrum.intensity`), also `.jdx` (JCAMP-DX) for some entries | Strongest metadata of any open set: laser, objective, grating, calibration, space group and cell, COD cross-reference, instrument, temperature | CC0 1.0 (public domain; asks that original authors be acknowledged) | https://solsa.crystallography.net/rod/3500262.rod ; https://solsa.crystallography.net/rod/3500155.rod ; https://solsa.crystallography.net/rod/3500276.rod ; https://solsa.crystallography.net/rod/3500276.jdx | 4 | Small but richly annotated and CC0; bulk download method not found (SVN/rsync UNVERIFIED), so fetch IDs one by one |
| GEMS Raman Dataset (Hugging Face, JunhanCai/GEMS-Raman-Dataset) | RRUFF-derived subsets (RRUFF_CL, RRUFF_FT) plus bacteria, skin cancer, wheat, microplastic, QMe14S | Seven subdirectories, 8.86 GB total; every spectrum resampled to 3,500 points over 0 to 3,500 cm-1 and min-max normalized | Standard array formats for PyTorch/NumPy (exact file types UNVERIFIED); dataset viewer disabled | None per spectrum on the page | MIT | https://huggingface.co/datasets/JunhanCai/GEMS-Raman-Dataset | 2 | ML-ready but normalized and resampled, which destroys intensity and peak-position fidelity; use RRUFF directly |
| DTU Data: datasets for "Raman Spectrum Matching with Contrastive Representation Learning" | Mineral (RRUFF-derived) and Organic sets | Two datasets for reproducing an Analyst 2022 paper (doi 10.1039/d2an00403h); instructions are in the authors' GitHub repo | One download, 129.11 MB, internal file names UNVERIFIED | Not stated | Licence section present but text not shown | https://data.dtu.dk/articles/dataset/Datasets_for_replicating_the_paper_Raman_Spectrum_Matching_with_Contrastive_Representation_Learning_/20222331 | 2 | Preprocessed RRUFF subset; no advantage over the original zips |
| SSHADE: DRIMS (Database of Raman and Infrared Mineral Spectra) and BOREALIS | Elements, oxides and hydroxides, sulfides, silicates; example single entries for magnetite crystal and Fe oxides (e.g. SPECTRUM_BS_20250903_RAM_180_r) | DRIMS: 22 samples, 4 experiments, 81 spectra | Download format and login requirement UNVERIFIED | SSHADE sample and experiment metadata (rich in principle) | Not stated on page; see sshade.eu/credits (UNVERIFIED) | https://sshade.eu/db/drims | 2 | Too small to matter, but good metadata and includes MIR-FIR raw Raman of magnetite |
| IEEE DataPort "raman spectroscopy multiple" (doi 10.21227/4f00-0y53) | Not described | Heterogeneous multi-source Raman benchmark | No file list shown | None shown | Not stated; access (open or subscriber) UNVERIFIED | https://ieee-dataport.org/documents/raman-spectroscopy-multiple | 1 | Content unknown and possibly paywalled; skip |
| Wiley KnowItAll Raman collection (RMATX, RIX Sadtler inorganics) | Inorganics and organics, 23,830 spectra across 19 databases | Commercial libraries | Proprietary | Rich | Commercial | not applicable | 1 | Listed only so nobody wastes time on it; not open |

---

## 2. Group IV and III-V / II-VI semiconductors

| Record | Material(s) | What is in it (incl. series and conditions) | Files and format | Metadata | Licence | Direct URL | Suitability | Reason |
|---|---|---|---|---|---|---|---|---|
| Zenodo 15082447 (doi 10.5281/zenodo.15082448): "Highly strained Ge nanostructures and direct bandgap transition induced by femtosecond laser" (Liu, Aalto Univ.) | Ge, fs-laser-induced nanostructures with high strain | Raman at 50x (samples S6 to S27, grouped 1a to 1e) and 100x (line scans across structures, spectra Single_Secptrum_007 to 047), plus XRD, TEM, RTA data for strain interpretation | Single archive `10.5281zenodo.15082448.7z`, 270.5 MB (needs 7-Zip; Expand-Archive cannot open .7z). Inside: `Raman_50x/Raw.csv`, `Raman_100x/Raw.csv` with microscope images | Column 1 wavenumber, column 2 background to subtract, then one intensity column per sample; focus depth Z in file header; sample IDs map to figure panels. Laser wavelength not on the page (check paper) | CC BY 4.0 | https://zenodo.org/records/15082447/files/10.5281zenodo.15082448.7z?download=1 | 4 | Genuine strain-varied Ge spectra with raw csv and a spatial line scan; wavelength and strain values must be taken from the paper |
| Zenodo 13268476: "Fs-laser significantly enhances both above- and below-bandgap absorption in germanium" (Liu et al., Aalto) | Ge, fs-laser textured | Raw Raman results behind Table 1 in `Table1.csv` (50.7 kB); other csvs are absorption/reflectance figures | `Figure-1-b.csv` ... `Figure-4-d.csv`, `Table1.csv`, `SEM.zip` 45.6 MB | Whether Table1.csv holds full spectra or fitted parameters UNVERIFIED | CC BY 4.0 | https://zenodo.org/records/13268476/files/Table1.csv?download=1 | 3 | Small and tidy, but content of Table1.csv may be fit results rather than spectra |
| Southampton ePrints 386418 (doi 10.5258/SOTON/386418): Ge micro-disks on free-standing SiO2 beams, raw data | Ge under uniaxial and biaxial tensile strain | "Raman spectroscopy raw data for Ge disks on freestanding uniaxial and biaxial SiO2 beams with different lengths"; also PL data | File names not shown on page (UNVERIFIED) | Beam length series implies a strain series | Not stated (UNVERIFIED) | https://doi.org/10.5258/SOTON/386418 | 3 | Strain series is exactly the kind of data wanted, but files, format and licence are unconfirmed |
| Southampton ePrints 403064 (doi 10.5258/SOTON/403064): strain engineering in Ge membranes | Ge membranes | Spreadsheet only; whether it holds Raman is UNVERIFIED | `Raw_data.xlsx` 58 MB, `readme.txt` 547 B | UNVERIFIED | Not stated | https://doi.org/10.5258/SOTON/403064 | 2 | Might contain Raman strain data; check readme.txt first |
| Univ. Lorraine DOREL (doi 10.12763/VUVLSZ): "Raman spectrum of silicon sample from 50 to 4000 cm-1" (Kauffmann, LMOPS platform) | Single-crystal Si reference | One room-temperature raw spectrum 50 to 4000 cm-1 (first-order 520 cm-1 and second-order bands), plus microscope image | LabSpec6 `.ls6` plus `.txt` plus JPEG; sizes 530,248 / 723 / 86,365 / 170,440 bytes, not mapped to names | Room temperature, raw; laser and power not on the page | CC0 1.0 | https://doi.org/10.12763/VUVLSZ (mirror: https://b2find.dkrz.de/dataset/971438a6-1a34-5a1d-b276-0447e7f03e10) | 3 | Clean unprocessed Si reference including the 2TO band, but a single spectrum with no strain or doping |
| Southampton ePrints 488525 (doi 10.5258/SOTON/D2829): 2D-MoS2 on black silicon (ACS Appl. Energy Mater. 2024) | MoS2 on Si nanowires; bare Si reference | Fig. 2 sheet has raw Raman spectra at 4 points; Fig. 3 gives E2g and A1g positions for 7 samples; PL sheets | One xlsx workbook, 4 tabs (readme at https://eprints.soton.ac.uk/488525/2/README.txt) | Laser, power, temperature deferred to the manuscript | CC BY | https://eprints.soton.ac.uk/488525 | 2 | Mostly 2D-material content (other catalog), only a Si reference spectrum for this scope |
| Moissanite (SiC) entry in Mendeley jbr5237xxd | SiC (gem moissanite) | See carbon table, row "Diamond and simulant gemstones" | | | | | 3 | One SiC polytype spectrum at 532 nm; for polytype series use RRUFF |
| GaN, AlN, GaAs, SiGe, CdS/CdSe quantum dots, ZnO nanostructures | n/a | Searches (Zenodo, Mendeley, Figshare, Dryad, institutional) found papers only. Zenodo 6089198 (ZnO whiskers with Ga) contains XPS/TEM, no Raman | n/a | n/a | n/a | n/a | 1 | Nothing verified; use RRUFF (zincite, greenockite, moissanite) or digitize |

---

## 3. Carbons beyond graphene

| Record | Material(s) | What is in it (incl. series and conditions) | Files and format | Metadata | Licence | Direct URL | Suitability | Reason |
|---|---|---|---|---|---|---|---|---|
| Mendeley Data yyxsgk3nm3 (doi 10.17632/yyxsgk3nm3.1): soot Raman, mobility size and radiative emission data (Dasappa and Camacho, Data in Brief 2021) | Flame soot (disordered/amorphous carbon) | 18 premixed laminar stagnation flames; equivalence ratio 2.4, 2.5, 2.6; max flame temperature about 1950 to 2250 K; raw, baseline-corrected and deconvoluted first- and second-order Raman spectra | Supplementary workbooks per article: `Raman_Spectra.xlsx`, `SMPS_Data.xlsx`, `Color_ratio_Data.xlsx`. Mendeley file list not visible (UNVERIFIED) | Thermo DXR2, 532 nm, 1 mW, 50x, 100 to 3500 cm-1; flame temperature and equivalence ratio per spectrum | CC BY 4.0 | https://data.mendeley.com/public-api/zip/yyxsgk3nm3/download/1 (pattern UNVERIFIED); landing https://doi.org/10.17632/yyxsgk3nm3.1 | 5 | Disordered-carbon series against a real physical control (temperature, stoichiometry) with raw, baselined and fitted versions side by side |
| Mendeley Data 9smmfc9vb8 (doi 10.17632/9smmfc9vb8.1): Raman data for laser reduction of graphene oxide (Scardaci; Data in Brief, PMC8385394). A sibling record 8cyhhzmxtd/1 has the same title (UNVERIFIED) | Graphene oxide to laser-reduced GO | 20 spectra per sample at random locations (10 x 10 s accumulations); series over atmosphere (Ar, Ar + 5% H2), scan speed (1.2, 2.7, 5.9 mm/s), GO coverage (400, 850 ug/cm2), single or double laser pass | OriginPro projects `spettri_mend.opj`, `fit new_mend.opj`, `Spessore.opj`, `dati 2 pass.opj`, plus a Raman spectra folder of Origin files named like `Ar_266_400` and `_2P`. Needs Origin or a liborigin/originpro converter, no plain csv confirmed | Scribing 405 nm, 1.5 W; Raman 532 nm WITec alpha300 RS; D, G, 2D positions, ID/IG, D-peak width as fit outputs | CC BY 4.0 on the article; Mendeley record shows CC BY 4.0 | https://data.mendeley.com/public-api/zip/9smmfc9vb8/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/9smmfc9vb8/1 | 3 | Excellent processing-parameter series and 532 nm metadata, but locked in .opj files |
| Mendeley Data jbr5237xxd (doi 10.17632/jbr5237xxd.1): Raman and specular reflectance of diamond and diamond simulants | Single-crystal diamond, cubic zirconia, moissanite (SiC), quartz | Raman of four gemstones, Horiba Explora Plus, 532 nm; reflectance 200 to 1000 nm | Files not visible (UNVERIFIED) | 532 nm confocal; no series | CC0 1.0 on the record (site footer reserves text-and-data-mining rights, conflicting; check) | https://data.mendeley.com/public-api/zip/jbr5237xxd/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/jbr5237xxd/1 | 3 | Covers diamond, SiC and ZrO2 in one small clean set, but only four spectra |
| Mendeley Data czdwt595yp (doi 10.17632/czdwt595yp.1): Raman spectra of graphite (Sardinha, INPE) | Graphite powder | Single sample, 500 to 3500 cm-1 | Files not visible (UNVERIFIED) | LabRAM HR Evolution, 532 nm, 20 degrees C | CC BY 4.0 | https://data.mendeley.com/public-api/zip/czdwt595yp/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/czdwt595yp/1 | 3 | Clean graphite reference with instrument details but no series |
| Mendeley Data fw5t4fywjt (doi 10.17632/fw5t4fywjt.1): siderite sulfidation diamond synthesis (Bataleva et al., 2026) | Synthetic diamond with graphite, sulfide, carbonate-melt and sulfur-species inclusions | Raman of inclusions, IR of diamonds, PL at 80 K (395 and 532 nm excitation); synthesis at 6.3 GPa, 1550 C | Files not visible (UNVERIFIED) | Excitation for Raman not on the page | CC BY 4.0 (footer reserves TDM rights) | https://data.mendeley.com/public-api/zip/fw5t4fywjt/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/fw5t4fywjt | 3 | Diamond, graphite and sulfur-species spectra with high-pressure synthesis context; file format unknown |
| USGS ScienceBase data release (doi 10.5066/P13CBG7G): micro-Raman of biochar vs fusinite/semifusinite (Peterson et al., 2025) | 16 biochars from lignocellulosic feedstocks, one natural semifusinite | Pyrolysis temperature series, estimated internal heating temperature 326 to 825 C; Raman parameters for carbon stability and structural development | File names, formats, sizes not visible on page (UNVERIFIED); may be fit parameters rather than full spectra | Feedstock and temperature per sample | Public domain (USGS) | https://doi.org/10.5066/P13CBG7G | 3 | Ideal temperature series of disordered carbon if full spectra are included; check first |
| Zenodo 4771951 (doi 10.5281/zenodo.4771951): Raman data from carbonates, Haut Giffre (Kedar, Bond, Muirhead) | Carbonaceous material in thrust-stacked carbonates (Raman geothermometry) | Spectral parameters and calculated temperatures in strained samples | `Kedar_et_al_-_Raman_data.xlsx`, 133.4 kB | Whether it holds spectra or only fit parameters UNVERIFIED | CC BY 4.0 | https://zenodo.org/records/4771951/files/Kedar_et_al_-_Raman_data.xlsx?download=1 | 2 | Likely peak parameters, not spectra; still a geothermometry ground truth for D/G fits |
| Mendeley Data gzrbp6p929 (version 1): raw data for encapsulation methods for endohedral doping of single-wall carbon nanotubes | SWCNT (endohedral doping) | Absorption, Raman, fluorescence, EPR and TGA data per figure, with MATLAB R2025b analysis scripts (baseline, normalization, fit) | Described formats .DSW, .csv, .xlsx, .txt, .m3d, .mat, .DSC, .DTA; names and sizes not visible (UNVERIFIED) | Raman excitation and DOI not shown | Not stated (UNVERIFIED) | https://data.mendeley.com/public-api/zip/gzrbp6p929/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/gzrbp6p929/1 | 3 | The only open CNT Raman lead found; no chirality-resolved RBM series, and licence unconfirmed |
| Cardiff University (research-data.cardiff.ac.uk article 27053545): diamond growth on gallium oxide single crystal | Ga2O3 substrate, SiO2 and Al2O3 ALD layers, diamond film | Raman folder with three excitation wavelengths (noted in file names); two-column wavenumber, intensity | 484.1 kB total; file names not listed (UNVERIFIED) | Three wavelengths; zeta potential folder is not Raman | Not specified | https://research-data.cardiff.ac.uk/articles/dataset/Surface_zeta_potential_and_diamond_growth_on_gallium_oxide_single_crystal_-_data/27053545 | 3 | Diamond film vs substrate at multiple wavelengths, simple txt, but licence is blank |
| Cambridge Apollo handle 1810/369051 (doi 10.17863/CAM.109009): disorder-driven capacitance in nanoporous carbons | Nanoporous carbons | Raw Raman spectra, ID/IG and D-band FWHM, electrochemistry | `Research data supporting Raman paper.zip` 10.39 MB (.txt, .dat, .xlsx, .xls) | README files in subfolders | CC BY 4.0 but **embargoed until 2100-01-01**; only a request-a-copy form | https://www.repository.cam.ac.uk/handle/1810/369051 | 1 | Exactly the right content but not downloadable; email the authors if wanted |
| RRUFF (see section 1) | Diamond, graphite, moissanite and other carbon phases | Mineral-grade spectra | See section 1 | | | https://www.rruff.net/zipped_data_files/raman/excellent_unoriented.zip | 4 | Best source for reference diamond and graphite lines |
| Carbon nanotubes (RBM, chirality), nanodiamond, GO annealing series, carbon fibre | n/a | No verified open raw spectra beyond the rows above. Search hits were papers (e.g. arXiv cond-mat/0510427, 0506666) with figures only | n/a | n/a | n/a | n/a | 1 | Digitize from the cited papers or email authors |
| Leads not opened (UNVERIFIED): PANGAEA 10.1594/PANGAEA.930199 and .932772 (Pyrenees Raman carbonaceous-material Tmax), EarthChem ecl.earthchem.org/view.php?id=2994 (Catalina), EPOS-MSL Tauern Window carbonaceous matter | Carbonaceous material, metamorphic temperature series | Peak metamorphic temperature vs Raman parameters | Unknown (likely tables of fit parameters) | | | | | |

---

## 4. Oxides and perovskites

| Record | Material(s) | What is in it (incl. series and conditions) | Files and format | Metadata | Licence | Direct URL | Suitability | Reason |
|---|---|---|---|---|---|---|---|---|
| RRUFF and ROD | TiO2 polymorphs, ZrO2 (baddeleyite), CeO2 (cerianite), Fe2O3, Fe3O4, ZnO | See section 1. ROD entries 3500262 (rutile), 3500155 and 3500276 (hematite) verified | `.rod`, `.jdx`, RRUFF text | See section 1 | CC0 (ROD); RRUFF terms UNVERIFIED | https://solsa.crystallography.net/rod/3500262.rod | 4 | Phase-labeled references; the only way to get CeO2, ZrO2 and brookite quickly |
| Zenodo 7907659 (doi 10.5281/zenodo.7907659): Raman imaging of ZrO2 (Suchorab and Gawęda, NOMATEN) | ZrO2 tetragonal and monoclinic phases, samples Sa1 to Sa5 | Five WITec Raman images, K-means clustering and fits in the paper (doi 10.1016/j.saa.2023.122625) | `Raman data.zip`, 66.1 MB; five WITec project files inside, extensions UNVERIFIED | Requires WITec Control FIVE 5.2 PLUS; other fitting software works on exported K-means average spectra | ODbL 1.0 (Open Database License) | https://zenodo.org/records/7907659/files/Raman%20data.zip?download=1 | 3 | In-scope ZrO2 phase mixture, but proprietary WITec format needs conversion (WITio or export) |
| ASU Library Research Data Repository (doi 10.48349/asu/scxuiw): in situ Raman of microwave-synthesized TiO2, anatase to rutile | TiO2 | Proof-of-concept in situ Raman during microwave heating through the anatase-to-rutile transition (custom spectrometer) | 7 delimited files (.csv, .tab), 6 MATLAB live scripts (.mlx), README; names UNVERIFIED | Temperature values not on the page | Not named (site-wide rights notice) | https://doi.org/10.48349/asu/scxuiw (ASU Dataverse, UNVERIFIED path) | 4 | A phase-transition time/temperature series for TiO2, the best match to a "series" request; licence needs checking |
| Mendeley Data kd49tr4ddp (doi 10.17632/kd49tr4ddp.1): Raman mapping with MCR-ALS of TiO2-II (alpha-PbO2 type high-pressure polymorph) | TiO2-II grains from Archean spherule layers | 19 mapping datasets (15 high spectral resolution 20 x 20, 4 high spatial resolution 100 x 100); matrices of spectra by 70 to 1550 cm-1 in 0.5 cm-1 steps | Files not visible (UNVERIFIED) | Layers Carawine, Jeerinah, Monteville, Bee Gorge | CC BY 4.0 | https://data.mendeley.com/public-api/zip/kd49tr4ddp/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/kd49tr4ddp/1 | 3 | Rare high-pressure TiO2 polymorph spectra with mixing, good for unmixing tests |
| Mendeley Data pkxy842bmp (doi 10.17632/pkxy842bmp.1, Sep 2026): green-synthesised iron oxide, raw characterisation | Iron oxide nanoparticles (Fe3O4/Fe2O3 family) | Unprocessed data; 42 Raman files including a laser-power series at 1, 2, 5, 10 mW (laser heating changes iron oxide phase); five samples differing in wash cycles (unwashed, 2, 6, 10) | Raman 42 files; XRD, TGA, FTIR, UV-Vis, TEM also present; formats UNVERIFIED | README warns: power values are nominal, XRD has displacement offset, single batch, some files without provenance | CC BY 4.0 | https://data.mendeley.com/public-api/zip/pkxy842bmp/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/pkxy842bmp | 4 | Laser-power series on iron oxides is a classic Raman trap and an honest "what the spectrum cannot tell" test case |
| Zenodo 15316591 (doi 10.5281/zenodo.15316591): orbital angular momentum and phonon scattering, Bi4Ge3O12 (BGO), Pylypets et al., APL Photonics 2025 | Bi4Ge3O12 (cubic oxide, F2, A1, E modes) | Polarized Raman: Fig. 3 four spectra in different orientations and polarization configurations (VV, HV); Fig. 5 and 6 angle-dependent HV (360 degree rotation) without and with vortex filter; Fig. 7 fitted mode intensities vs angle; Fig. 8 forward and backward VV; IR reflectivity with fit (Fig. 2) | Verified list: `Fig.3_BGO(111)_0deg_vv.csv` 14.1 kB, `Fig.3_BGO001_HV.csv`, `Fig.3_BGO45_001_HV_I25_x20.csv`, `Fig.3_BGO_001_I25_x20_HV.csv`, `Fig.5_BGO_360_hv.csv` 995 kB, `Fig.6_BGO_360_VF_hv.csv` 995 kB, `Fig.7.csv`, Fig.8 csvs, `Fig.2_experiment.csv`, `README.txt`. Columns are wavenumber and counts | README documents offsets and multiplication factors in column names | CC BY 4.0 | https://zenodo.org/records/15316591/files/Fig.5_BGO_360_hv.csv?download=1 | 4 | Real polarization-resolved oxide spectra with an angular series; a CRD-style symmetry check is possible |
| Mendeley Data vnrjsvxrd6 (doi 10.17632/vnrjsvxrd6.1): VO2 metal-insulator transition modulated by H and oxygen-vacancy co-doping | VO2 films | R-T curves, Hall, cyclic R-T, Raman spectrum, SIMS, UV-Vis-NIR, XPS; whether the Raman is temperature-resolved is not stated | Files not visible (UNVERIFIED) | Doping/treatment series implied | CC BY 4.0 (footer reserves TDM rights) | https://data.mendeley.com/public-api/zip/vnrjsvxrd6/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/vnrjsvxrd6/1 | 3 | Only VO2 lead; probably room-temperature Raman across doping states |
| Mendeley Data zy57t3xrmg (doi 10.17632/zy57t3xrmg.1): second-order Raman in LiNbO3:Tb | LiNbO3 congruent vs Tb-doped (2.24 wt%) | Raman at 785 nm, BWS465-785H spectrometer; optical axis Z parallel or perpendicular to laser | Files not visible (UNVERIFIED) | No polarization setting stated, no temperature | CC BY 4.0 | https://data.mendeley.com/public-api/zip/zy57t3xrmg/download/1 (pattern UNVERIFIED); landing https://data.mendeley.com/datasets/zy57t3xrmg/1 | 3 | Doped vs pure LiNbO3 at two orientations; one of very few LiNbO3 sets |
| Cambridge Apollo item f4ac7ea8-d8ce-47be-97a3-e0e8c272a944: Raman optical response of 14 single-crystal substrates at 633 and 785 nm | LaAlO3, Al2O3, SrTiO3, Nb:SrTiO3, GdScO3, NdGaO3, MgO and others | Prominent peaks, relative intensities, backgrounds for each substrate; background subtracted and degree-2 polynomial baseline applied | Data files named after Figures 1 to 3 and S1 to S5, plus .txt exports of figure graphs; sizes and exact names not listed (UNVERIFIED) | Self-built setup with Python control; two excitation wavelengths | CC BY 4.0 | https://www.repository.cam.ac.uk/items/f4ac7ea8-d8ce-47be-97a3-e0e8c272a944 | 4 | Clean reference spectra for perovskite substrates (SrTiO3, LaAlO3) at two wavelengths; many agents will see these as substrate background in thin-film spectra |
| Cardiff Ga2O3 / diamond dataset (see carbon table) | Ga2O3 | Bare and coated Ga2O3 at three wavelengths | | | | | 3 | Wide-gap oxide reference |
| Dryad "An infrared, Raman, and X-ray database of battery interphase components" (arXiv 2310.13871) | Li2O, Li2CO3, LiH, LiPF6, MnF2, NiF2, LiOAc, PEO (Raman final data for 8 of 10) | One xlsx workbook per technique, one sheet per compound, raw and final data | Dryad URL not given in the paper; licence not stated (UNVERIFIED) | | | https://arxiv.org/pdf/2310.13871 (find Dryad DOI in data statement) | 2 | Only Li2O is in scope; interphase chemistry, not requested materials |
| Duisburg-Essen DuEPublico 74147: TiO2 thin-film Raman decomposition (anatase, rutile, brookite, amorphous on Si, fused silica, crown glass) | TiO2 thin films | Raman maps 30 x 30 um with 121 x 121 points | No data files shown on the page; DOI not listed | | CC BY 4.0 on the article | https://duepublico2.uni-due.de/receive/duepublico_mods_00074147 | 1 | Great content but no download found; email the authors |
| Hf1-xZrxO2 ferroelectrics (NIMS 10.48505/nims.5210; DataverseNL 10.34894/EIOXPT) | HfO2-based | NIMS: only a manuscript PDF. DataverseNL: STEM, XRD, electrical data, no Raman | PDF only | | In Copyright (NIMS); CC0 (DataverseNL) | n/a | 1 | No HfO2 Raman spectra deposited |
| BaTiO3, PbTiO3, BiFeO3, CeO2, halide perovskites (MAPbI3, CsPbBr3) | n/a | No verified open Raman raw data. Zenodo 14911318 and 5018380 (CsPbBr3 nanocrystals) hold absorption/PL/STEM only. The arXiv papers 2012.12669 (BaTiO3), 2208.05563, cond-mat/0507291 (BiFeO3) are candidates for digitizing | n/a | n/a | n/a | n/a | 1 | Gap |

---

## 5. Checked and rejected (so nobody repeats the search)

| Record | Why not |
|---|---|
| Zenodo 11246682 (Breitenfeld et al.): grain size vs Raman signal, forsterite, augite, diopside, labradorite, bytownite; `spectra_raman_grainsize.csv` 706 kB + `metadata_raman_grainsize.csv` 2.2 kB, CC BY 4.0 | Clean csv with a 10-bin particle-size series, but silicates, outside scope. Direct: https://zenodo.org/records/11246682/files/spectra_raman_grainsize.csv?download=1. Suitability 2 for this scope, 4 for a general ingestion test |
| Zenodo 7808302 (SilicH2O): silicate glass Raman and composition xlsx | Silicate glass for H2O quantification; file names not shown |
| Zenodo 8263236: GaS amorphous vs crystalline Raman (`Raman_amorph_GaS.txt`, `Raman_cryst_GaS.dat`, CC BY 4.0) | Layered III-VI chalcogenide, two spectra; useful only as a phase-change example |
| Zenodo 14503557 (mechanochemistry), 3572358 (SERS interlab, 3,516 spectra, CC BY 4.0), 6818608 (SERS on graphene, 1.6 GB), 17617324 (Raman EAD-coding) | Organic/SERS or graphene (other catalog), or content not described |
| Zenodo 6089198 (ZnO/Ga), 5018380 (CsPbBr3 nanoplatelets), 10677562 (atom probe Fe oxides), 11093050 (DAC pulser) | No Raman data |
| Mendeley vwd34rvphw (SWCNT dataset) | Molecular dynamics configurations, not spectra |
| NIMS 6ce1e386 / bd6db1cf (stress in CVD diamond by Raman and NV) | Only the paper PDF is deposited |
| TUdatalib (Raman TiC-CDC), QUT "Raman data.zip", Most Wiedzy open data | Blocked by a bot wall (Anubis) or not opened; UNVERIFIED. TiC-derived carbon (carbide-derived carbon, disordered carbon with graphitization series) would be in scope and is worth a browser check at https://tudatalib.ulb.tu-darmstadt.de/items/34233111-bf51-4e50-9aec-cff54eddaae4 |
| OSF rjg3c | Page returned no readable content |
| Materials Cloud 1981 / 2379 | Computed (DFPT) Raman spectra of 2D materials, not experimental |

---

## Recommended first picks (best 5 across scope)

1. **RRUFF excellent_unoriented.zip and excellent_oriented.zip** (306 MB together). Covers the most phases (anatase, rutile, brookite, hematite, magnetite, baddeleyite, cerianite, zincite, greenockite, moissanite, diamond, graphite). The oriented set carries orientation, which supports symmetry-based reasoning. Confirm usage terms and the inner file layout on first open.
2. **Raman Open Database CC0 entries** (3500262 rutile, 3500155 and 3500276 hematite, plus any other Verona oxide entries found via the ROD search page). Tiny, but the best-annotated spectra in the catalog (laser, objective, grating, calibration, space group) and they link to COD structures, which pairs with the CRD matcher.
3. **Zenodo 15082447, strained Ge** (270 MB 7z). Real strain-varied semiconductor spectra as raw csv with a spatial line scan; wavelength and strain need to be taken from the paper.
4. **Mendeley yyxsgk3nm3, flame soot Raman** (`Raman_Spectra.xlsx`). A disordered-carbon series against flame temperature (1950 to 2250 K) and equivalence ratio, with raw, baselined and deconvoluted spectra, 532 nm, 1 mW.
5. **Zenodo 15316591, polarized Raman of Bi4Ge3O12** (csv, CC BY 4.0). Verified file list, VV/HV configurations, 360 degree angle series with and without a vortex filter, and fitted mode intensities against angle (`Fig.7.csv`) as ground truth.

Runners-up worth a look after the five: Mendeley pkxy842bmp (iron-oxide laser-power series, 42 Raman files), ASU TiO2 anatase to rutile in situ series (check licence), Cambridge Apollo substrate Raman (SrTiO3, LaAlO3 at 633 and 785 nm), Mendeley 9smmfc9vb8 (GO laser reduction, needs Origin), USGS biochar series (check whether full spectra are included).

---

## PowerShell: download the recommended files

Run from the repo root on the PC (`C:\Users\sadit\Desktop\P_Projects\Hackathons\OSI Hackathon`). Mendeley zip links use an UNVERIFIED URL pattern; if one fails, use "Download all" in the browser and drop the zip into the same folder. The Ge archive is `.7z`, which `Expand-Archive` cannot open, so the script uses `7z` if it is on PATH.

```powershell
# ---- helpers -------------------------------------------------------------
$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Get-File {
    param([Parameter(Mandatory)][string]$url, [Parameter(Mandatory)][string]$out)
    if (Test-Path -LiteralPath $out) { Write-Host "skip (exists): $out"; return }
    $dir = Split-Path -Parent $out
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    try {
        Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing `
            -Headers @{ "User-Agent" = "Mozilla/5.0 (OSI-Hackathon RamanLens)" }
        Write-Host "ok: $out"
    } catch {
        Write-Warning "FAILED: $url  ($($_.Exception.Message))"
        if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Force }
    }
}

function Expand-Once {
    param([string]$zip, [string]$dest)
    if (-not (Test-Path -LiteralPath $zip)) { return }
    if ((Test-Path -LiteralPath $dest) -and (Get-ChildItem -LiteralPath $dest -Force -ErrorAction SilentlyContinue | Select-Object -First 1)) {
        Write-Host "skip unzip (non-empty): $dest"; return
    }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force
    Write-Host "unzipped: $zip -> $dest"
}

function Get-ZenodoFile {   # builds the URL-encoded Zenodo file link
    param([string]$record, [string]$name, [string]$outDir)
    $enc = [Uri]::EscapeDataString($name)
    Get-File "https://zenodo.org/records/$record/files/${enc}?download=1" (Join-Path $outDir $name)
}

$root = "data\raw\spectra"

# ---- 1. RRUFF (verified directory listing, mirrored at rruff.net) ----------
$rruff = "$root\rruff"
Get-File "https://www.rruff.net/zipped_data_files/raman/excellent_unoriented.zip" "$rruff\excellent_unoriented.zip"
Get-File "https://www.rruff.net/zipped_data_files/raman/excellent_oriented.zip"   "$rruff\excellent_oriented.zip"
Expand-Once "$rruff\excellent_unoriented.zip" "$rruff\excellent_unoriented"
Expand-Once "$rruff\excellent_oriented.zip"   "$rruff\excellent_oriented"
# optional, smaller: fair_unoriented.zip (59M), unrated_oriented.zip (39M), LR-Raman.zip (227M)

# ---- 2. Raman Open Database, CC0 oxide entries -----------------------------
$rod = "$root\oxides_rod"
foreach ($id in 3500262, 3500155, 3500276) {
    Get-File "https://solsa.crystallography.net/rod/$id.rod" "$rod\$id.rod"
}
Get-File "https://solsa.crystallography.net/rod/3500276.jdx" "$rod\3500276.jdx"
# more oxide entries: browse http://solsa.crystallography.net/rod/ (Search) and add IDs above

# ---- 3. Zenodo 15082447: strained Ge (needs 7-Zip) --------------------------
$ge = "$root\germanium"
Get-ZenodoFile "15082447" "10.5281zenodo.15082448.7z" $ge
if ((Test-Path "$ge\10.5281zenodo.15082448.7z") -and -not (Test-Path "$ge\extracted")) {
    if (Get-Command 7z -ErrorAction SilentlyContinue) {
        7z x "$ge\10.5281zenodo.15082448.7z" "-o$ge\extracted" -y | Out-Null
    } else { Write-Warning "7z not found; install 7-Zip and extract $ge\10.5281zenodo.15082448.7z manually" }
}
# small companion: Aalto fs-laser Ge (Table1.csv may hold fitted parameters, UNVERIFIED)
Get-ZenodoFile "13268476" "Table1.csv" $ge

# ---- 4. Mendeley yyxsgk3nm3: flame soot Raman (pattern UNVERIFIED) ----------
$soot = "$root\carbon_soot"
Get-File "https://data.mendeley.com/public-api/zip/yyxsgk3nm3/download/1" "$soot\yyxsgk3nm3_v1.zip"
Expand-Once "$soot\yyxsgk3nm3_v1.zip" "$soot\extracted"

# ---- 5. Zenodo 15316591: polarized Raman of Bi4Ge3O12 (verified names) -------
$bgo = "$root\oxide_bgo_polarized"
$bgoFiles = @(
    "README.txt",
    "Fig.2_experiment.csv", "Fig.2_epsilon_and_fit.csv",
    "Fig.3_BGO(111)_0deg_vv.csv", "Fig.3_BGO001_HV.csv",
    "Fig.3_BGO45_001_HV_I25_x20.csv", "Fig.3_BGO_001_I25_x20_HV.csv",
    "Fig.5_BGO_360_hv.csv", "Fig.6_BGO_360_VF_hv.csv", "Fig.7.csv",
    "Fig.8_BGO_001_I100_x20_VF64_backward_VV.csv",
    "Fig.8_BGO_001_I25_x20_VF8_backward_VV.csv",
    "Fig.8_BGO_001_I25_x20_VV_nofilter.csv",
    "Fig.8_BGO_forward_VV_x20 vortex64.csv",
    "Fig.8_BGO_forward_VV_x20 vortex8.csv"
)
foreach ($f in $bgoFiles) { Get-ZenodoFile "15316591" $f $bgo }

# ---- runners-up (uncomment as needed) ---------------------------------------
# Iron oxide laser-power series (Mendeley, pattern UNVERIFIED)
# Get-File "https://data.mendeley.com/public-api/zip/pkxy842bmp/download/1" "$root\iron_oxide\pkxy842bmp_v1.zip"
# Expand-Once "$root\iron_oxide\pkxy842bmp_v1.zip" "$root\iron_oxide\extracted"
# ZrO2 tetragonal/monoclinic WITec images (66 MB, WITec format)
# Get-ZenodoFile "7907659" "Raman data.zip" "$root\zro2"
# Expand-Once "$root\zro2\Raman data.zip" "$root\zro2\extracted"
# Diamond, moissanite, cubic zirconia, quartz gems (Mendeley CC0, pattern UNVERIFIED)
# Get-File "https://data.mendeley.com/public-api/zip/jbr5237xxd/download/1" "$root\diamond_sic\jbr5237xxd_v1.zip"
# Graphene oxide laser reduction, Origin .opj files (Mendeley, pattern UNVERIFIED)
# Get-File "https://data.mendeley.com/public-api/zip/9smmfc9vb8/download/1" "$root\graphene_oxide\9smmfc9vb8_v1.zip"
# Silicate grain-size series, clean csv for pipeline testing
# Get-ZenodoFile "11246682" "spectra_raman_grainsize.csv" "$root\test_silicates"
# Get-ZenodoFile "11246682" "metadata_raman_grainsize.csv" "$root\test_silicates"

Write-Host "done"
```

## Gaps and suggested follow-ups

- **GaN, AlN, GaAs, SiGe, CdSe/CdS quantum dots, ZnO nanostructures, SiC polytypes, carbon nanotube RBM, nanodiamond, BaTiO3, SrTiO3 temperature series, PbTiO3, BiFeO3, CeO2, halide perovskites:** no verified open raw data. Options: (1) RRUFF species for ZnO, CdS, SiC, CeO2, ZrO2; (2) digitize from arXiv papers such as cond-mat/0510427 and cond-mat/0506666 (index-identified SWCNT RBM), 2012.12669 (BaTiO3), cond-mat/9905175 (SiGe strain), 1905.04186 and 1502.00072 (AlGaN/GaN strain), 2209.15423 (computed, for cross-checks); (3) email authors of papers whose data statements say "upon request".
- **Check in a browser from the PC** (blocked or JavaScript-only from the sandbox): file lists of every Mendeley row above, TUdatalib TiC-CDC Raman record, QUT "Raman data.zip", Cambridge Apollo f4ac7ea8 file names, ASU Dataverse record, Southampton 386418 file names, the USGS ScienceBase files, and which RRUFF species sit in each zip.
- **Licence caution:** Mendeley pages state CC BY 4.0 or CC0 on the record but add a site footer reserving text-and-data-mining and AI-training rights; follow the per-record licence and cite the DOI.
