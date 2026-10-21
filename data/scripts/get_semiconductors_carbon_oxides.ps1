# Download block from data/catalog-semiconductors-carbon-oxides.md. Run from anywhere: powershell -ExecutionPolicy Bypass -File data\scripts\get_semiconductors_carbon_oxides.ps1
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot); Set-Location $repoRoot
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
