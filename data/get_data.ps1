# RamanLens data setup. Run from the repo root on the PC:
#     powershell -ExecutionPolicy Bypass -File data\get_data.ps1
# Idempotent: skips files that already exist. Sources and licences: data\README.md and the two catalogs.

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"   # makes Invoke-WebRequest much faster
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$dirs = "data\raw\crd", "data\raw\pdfs", "data\raw\parsed",
        "data\raw\spectra\WS2", "data\raw\spectra\MoS2", "data\raw\spectra\graphene",
        "data\raw\spectra\CrSBr", "data\raw\spectra\rruff", "data\raw\zenodo_search",
        "data\test_set", "data\build_set"
foreach ($d in $dirs) { New-Item -ItemType Directory -Force $d | Out-Null }

function Get-File($url, $out) {
    if (Test-Path $out) { Write-Host "skip  $out"; return }
    Write-Host "get   $out"
    try { Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -TimeoutSec 600 }
    catch { Write-Warning "FAILED $url : $($_.Exception.Message)" }
}

# 1. CRD: move the zip from data\ into data\raw\crd\ and unzip
$crdZip = "data\raw\crd\Computational_Raman_Database_v1.0.1.zip"
if ((Test-Path "data\Computational_Raman_Database_v1.0.1.zip") -and -not (Test-Path $crdZip)) {
    Move-Item "data\Computational_Raman_Database_v1.0.1.zip" $crdZip
}
Get-File "https://archive.materialscloud.org/records/0m9r0-g3486/files/Computational_Raman_Database_v1.0.1.zip?download=1" $crdZip
if (-not (Test-Path "data\raw\crd\crd.json")) { Expand-Archive $crdZip -DestinationPath "data\raw\crd" -Force }
Write-Host "CRD md5 (expect E2AAEA03DF70FDA95DBD970C60456882):" (Get-FileHash $crdZip -Algorithm MD5).Hash

# 2. CrSBr magneto-Raman deposit, Zenodo 15048152, CC BY 4.0
$z = "data\raw\spectra\CrSBr\CrSBrPaper1.zip"
Get-File "https://zenodo.org/records/15048152/files/CrSBrPaper1.zip?download=1" $z
if ((Test-Path $z) -and -not (Test-Path "data\raw\spectra\CrSBr\CrSBrPaper1")) {
    Expand-Archive $z -DestinationPath "data\raw\spectra\CrSBr\CrSBrPaper1" -Force }

# 3. Graphene WITec txt exports, Zenodo 14883846 (licence printed, check before publishing derived data)
try {
    $rec = Invoke-RestMethod "https://zenodo.org/api/records/14883846"
    Write-Host "Zenodo 14883846 licence:" $rec.metadata.license.id
    foreach ($f in $rec.files) { Get-File $f.links.self ("data\raw\spectra\graphene\" + ($f.key -replace '[\\/]', '_')) }
} catch { Write-Warning "Zenodo 14883846 listing failed: $($_.Exception.Message)" }

# 4. WS2 sets on Mendeley Data (CC BY 4.0): all files of the latest version via the public API
foreach ($id in "jsmbyfmck2", "bjkct6pwx5") {
    try {
        $ds = Invoke-RestMethod "https://data.mendeley.com/public-api/datasets/$id"
        $ver = $ds.version
        $files = Invoke-RestMethod "https://data.mendeley.com/public-api/datasets/$id/files?folder_id=root&version=$ver"
        foreach ($f in $files) {
            $url = $f.content_details.download_url
            if ($url) { Get-File $url ("data\raw\spectra\WS2\${id}_" + $f.filename) }
        }
    } catch { Write-Warning "Mendeley $id failed (download manually from https://data.mendeley.com/datasets/$id): $($_.Exception.Message)" }
}

# 5. RRUFF oriented minerals (general library, 77 MB)
$r = "data\raw\spectra\rruff\excellent_oriented.zip"
Get-File "https://rruff.net/zipped_data_files/raman/excellent_oriented.zip" $r
if ((Test-Path $r) -and -not (Test-Path "data\raw\spectra\rruff\excellent_oriented")) {
    Expand-Archive $r -DestinationPath "data\raw\spectra\rruff\excellent_oriented" -Force }

# 6. Key arXiv papers for figure grounding (PDF cache used by ramanlens.literature)
$papers = "2211.12939", "2212.01754", "2410.22164", "2502.01794", "2405.07853",   # CrSBr Raman
          "1005.2509", "1212.6796", "1308.3835",                                   # MoS2
          "1105.0175", "1207.2058", "1405.4264"                                    # graphene defects/doping
foreach ($p in $papers) { Get-File "https://arxiv.org/pdf/$p" "data\raw\pdfs\$p.pdf"; Start-Sleep -Seconds 3 }

# 7. Zenodo searches the sandbox could not run; JSON hit lists for manual triage
foreach ($q in "Raman WS2", "Raman MoS2", "Raman graphene spectra", "CrSBr Raman",
               "polarized Raman 2D", "angle-resolved Raman", "Raman spectroscopy 2D materials dataset") {
    $fn = "data\raw\zenodo_search\" + ($q -replace '\s', '_') + ".json"
    try { Invoke-RestMethod "https://zenodo.org/api/records?q=$([uri]::EscapeDataString($q))&size=25" |
          ConvertTo-Json -Depth 8 | Out-File $fn -Encoding utf8 }
    catch { Write-Warning "search '$q' failed" }
}

# 8. Broader material coverage (optional, larger): pass -All to run the three extra catalog scripts
if ($args -contains "-All") {
    foreach ($s in "get_series_quantum_magnetic.ps1", "get_semiconductors_carbon_oxides.ps1", "get_energy_polymers_minerals.ps1") {
        Write-Host "`n=== $s ==="
        & (Join-Path $PSScriptRoot "scripts\$s")
        Set-Location $root
    }
} else { Write-Host "`nTip: run with -All to also fetch series, semiconductor/carbon/oxide and energy/polymer/mineral sets (data\scripts\)." }

Write-Host "`nDone. Not automated (manual): Southampton ePrints xlsx (WS2 D0371, MoS2 416765), Dryad 5qfttdzm9, VAMAS Zenodo 10008276 (609 MB), TUdatalib 4928/4929 (bot check)."
Get-ChildItem data\raw -Recurse -File | Measure-Object -Property Length -Sum |
    ForEach-Object { "{0} files, {1:N1} MB in data\raw" -f $_.Count, ($_.Sum / 1MB) }
