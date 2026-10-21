# Download block from data/catalog-series-quantum-magnetic.md. Run from anywhere: powershell -ExecutionPolicy Bypass -File data\scripts\get_series_quantum_magnetic.ps1
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot); Set-Location $repoRoot
# ---- setup and helpers (define first) ----
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
$OpenManual = $false          # set $true to open the manual landing pages in the browser
$root = "data\raw\spectra"
New-Item -ItemType Directory -Force $root | Out-Null
$manualFile = Join-Path $root "MANUAL_DOWNLOADS.txt"

function Get-File($url, $out) {
    if (Test-Path $out) { Write-Host "skip  $out"; return }
    New-Item -ItemType Directory -Force (Split-Path -Parent $out) | Out-Null
    Write-Host "get   $out"
    try { Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -TimeoutSec 900 }
    catch { Write-Warning "FAILED $url : $($_.Exception.Message)" }
}

function Expand-Zips($dir) {
    Get-ChildItem $dir -Filter *.zip -ErrorAction SilentlyContinue | ForEach-Object {
        $dest = Join-Path $dir $_.BaseName
        if (-not (Test-Path $dest)) { Expand-Archive $_.FullName -DestinationPath $dest -Force }
    }
}

function Get-ZenodoRecord($id, $dir) {     # resolves concept or version ids to the latest version
    New-Item -ItemType Directory -Force $dir | Out-Null
    try { $rec = Invoke-RestMethod "https://zenodo.org/api/records/$id/versions/latest" }
    catch { $rec = Invoke-RestMethod "https://zenodo.org/api/records/$id" }
    ("{0} | {1} | {2}" -f $rec.id, $rec.metadata.title, $rec.metadata.license.id) |
        Tee-Object -FilePath (Join-Path $dir "_record.txt") -Append | Write-Host
    foreach ($f in $rec.files) {
        $name = $f.key -replace '[\\/:*?"<>|]', '_'
        Get-File $f.links.self (Join-Path $dir $name)
    }
    Expand-Zips $dir
}

function Add-Manual($material, $url, $note) {
    New-Item -ItemType Directory -Force (Join-Path $root $material) | Out-Null
    "{0} | {1} | {2}" -f $material, $url, $note | Add-Content $manualFile
    Write-Host "manual: $material -> $url"
    if ($OpenManual) { Start-Process $url }
}

# ---- 1. NiPS3 and CoPS3 temperature series (Zenodo, CC BY 4.0) ----
Get-ZenodoRecord 23300631 "$root\NiPS3"
Get-ZenodoRecord 20449397 "$root\CoPS3"

# ---- 2. CrSBr: magneto-Raman zip (verified name) and Czech repository polarization sets (manual) ----
Get-File "https://zenodo.org/records/15048152/files/CrSBrPaper1.zip?download=1" "$root\CrSBr\CrSBrPaper1.zip"
Expand-Zips "$root\CrSBr"
Add-Manual "CrSBr" "https://datarepo.eosc.cz/doi/10.48700/datst.e94rx-q2q41" "Sahu et al. resonance Raman and anti-Stokes, CC BY 4.0, click Download"
Add-Manual "CrSBr" "https://datarepo.eosc.cz/doi/10.48700/c819g-kjx76" "CrSBr(1-x)Clx He+ irradiation, polarized, Excel about 3 MB, CC BY 4.0"
Add-Manual "CrSBr" "https://datarepo.eosc.cz/doi/10.48700/datst.bacck-32r88" "CrSBr(1-x)Clx phonon engineering, CC BY 4.0"
Add-Manual "CrSBr" "https://tudatalib.ulb.tu-darmstadt.de/handle/tudatalib/4929" "Markina et al. T and polarization series, solve bot check, read file list and licence (UNVERIFIED)"

# ---- 3. 2M-WS2 temperature and polarization (Harvard Dataverse, CC0; UNVERIFIED endpoint) ----
Get-File "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/I9UNL7" "$root\WS2_2M\dataverse_files.zip"
Expand-Zips "$root\WS2_2M"
Add-Manual "WS2_2M" "https://doi.org/10.7910/DVN/I9UNL7" "fallback if the API zip fails: Access Dataset, Download all"

# ---- 4. MnSi2Te4 temperature and angle (SciDB, CC BY-NC-ND, keep out of the public repo) ----
Add-Manual "MnSi2Te4" "https://www.scidb.cn/detail?dataSetId=40975ed27e9c4da8af7c94559fbc4b88" "52 files, 636 kB, Raman T and polarization angle, CC BY-NC-ND 4.0"

# ---- 5. WSe2/WS2 moire: gate, field, temperature, polarization (Dryad, CC0; UNVERIFIED endpoint) ----
Get-File "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.dr7sqvb8n/download" "$root\WSe2_WS2_moire\dryad_dr7sqvb8n.zip"
Expand-Zips "$root\WSe2_WS2_moire"
Add-Manual "WSe2_WS2_moire" "https://doi.org/10.5061/dryad.dr7sqvb8n" "fallback: Download dataset button on the Dryad page"

# ---- runners-up ----
Get-ZenodoRecord 23040882 "$root\graphene_AGNR"                         # temperature, anharmonic, CC BY 4.0
Get-ZenodoRecord 20604906 "$root\NbIrTe4_pressure"                      # pressure, IR plus Raman
Get-ZenodoRecord 11493104 "$root\MoS2_magneto_phonon_moment"            # field series, monolayer MoS2
Get-ZenodoRecord 17537553 "$root\graphite_isotope_Landau"               # field series
Get-File "https://figshare.com/ndownloader/articles/11774793/versions/1" "$root\RuCl3\figshare_11774793.zip"   # UNVERIFIED pattern
Expand-Zips "$root\RuCl3"
Get-File "https://researchdata.bath.ac.uk/521/5/Figure_1b_Raman_data.xls" "$root\ReSe2\Figure_1b_Raman_data.xls"  # verified URL

Add-Manual "ScV6Sn6" "https://hdl.handle.net/11299/254842" "DRUM, folder TdepRaman_ScVSn, T 5.5 to 300 K, CC BY-NC 3.0 US"
Add-Manual "Bi2212" "https://www.fdr.uni-hamburg.de/record/14833" "Glier et al. NEARS spectra A1g and B1g, CC BY 4.0, data_summary.pdf"
Add-Manual "SrIrO3" "https://radar.kit.edu/radar/en/dataset/xxQRiaiTyRNskhik" "KIT RADAR, 21.2 MB tar, CC BY 4.0"
Add-Manual "FePS3" "https://yareta.unige.ch/archives/de9f3f78-a7a5-4a2d-b018-676aa495ed69" "Geneva Open Data FePS3, check access level"
Add-Manual "FePO4_pressure" "https://www.scidb.cn/detail?dataSetId=4f41765c821342c7a2993a6f5eda8a44" "DAC 0.2 to 27.35 GPa, 296 MB, CC BY-NC-ND 4.0"
Add-Manual "BaTiGeO3_pressure" "https://www.scidb.cn/detail?dataSetId=670b762ff4cd465c86890f8eddedfde5" "DAC to 30 GPa, 4 MB, CC BY-NC 4.0"
Add-Manual "graphene_strain" "https://databank.illinois.edu/datasets/IDB-6434046" "Figure2c_progressive_allspectra.csv, CC BY"
Add-Manual "graphene_gating" "https://datarepo.eosc.cz/doi/10.48700/crkdk-9n012" "spectroelectrochemistry, Excel/Origin/Igor, CC BY 4.0"
Add-Manual "Sb2Se3" "http://datacat.liverpool.ac.uk/id/eprint/1062" "angle-resolved polarised Raman, Full Archive, CC BY 3.0"
Add-Manual "organic_facets" "https://data.mendeley.com/datasets/rb7w2ws48r/1" "angle-resolved polarised Raman of organic crystals, CC BY 4.0"
Add-Manual "manganites" "https://redu.unicamp.br/citation?persistentId=doi:10.25824/redu/2YRTO3" "Raman 15 to 300 K, 4 zips, CC BY-NC 4.0"

Write-Host "Done. Manual items listed in $manualFile"
