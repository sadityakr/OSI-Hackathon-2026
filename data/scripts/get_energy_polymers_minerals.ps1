# Download block from data/catalog-energy-polymers-minerals.md. Run from anywhere: powershell -ExecutionPolicy Bypass -File data\scripts\get_energy_polymers_minerals.ps1
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot); Set-Location $repoRoot
# Helper: download only if the output file does not exist yet
function Get-File($url, $out) {
    if (Test-Path $out) { Write-Host "skip (exists): $out"; return }
    $dir = Split-Path -Parent $out
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Write-Host "get: $url"
    Invoke-WebRequest -Uri $url -OutFile $out -UserAgent "Mozilla/5.0" -MaximumRedirection 5
}

function Expand-Once($zip, $dest) {
    if (Test-Path $dest) { Write-Host "skip (extracted): $dest"; return }
    Expand-Archive -Path $zip -DestinationPath $dest
}

$root = "data\raw\spectra"

# 1. RRUFF Raman, excellent_oriented (77 MB). Host redirects rruff.info -> www.rruff.net.
$d = "$root\minerals-rruff"
Get-File "https://rruff.info/zipped_data_files/raman/excellent_oriented.zip" "$d\excellent_oriented.zip"
Expand-Once "$d\excellent_oriented.zip" "$d\excellent_oriented"
# Optional, 229 MB:
# Get-File "https://rruff.info/zipped_data_files/raman/excellent_unoriented.zip" "$d\excellent_unoriented.zip"
# Expand-Once "$d\excellent_unoriented.zip" "$d\excellent_unoriented"

# 2. API Raman spectra, Figshare 27931131 (file URLs from the Figshare API; UNVERIFIED from the sandbox)
$d = "$root\pharma-api"
New-Item -ItemType Directory -Force -Path $d | Out-Null
$meta = Invoke-RestMethod "https://api.figshare.com/v2/articles/27931131"
foreach ($f in $meta.files) { Get-File $f.download_url (Join-Path $d $f.name) }

# 3. Cambridge operando Raman, Li-ion electrolyte in hollow-core fibre (CC BY 4.0, 19 MB, URL from the record page)
$d = "$root\battery-operando-electrolyte"
Get-File "https://www.repository.cam.ac.uk/bitstreams/c0cc69be-4414-469c-a581-0947f47bb88f/download" "$d\Datasets.zip"
Expand-Once "$d\Datasets.zip" "$d\Datasets"

# 4. Dryad battery interphase database (whole dataset zip via Dryad API; UNVERIFIED, fall back to the browser if it returns 403)
$d = "$root\battery-interphase"
Get-File "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.v15dv421w/download" "$d\dryad_interphase.zip"
Expand-Once "$d\dryad_interphase.zip" "$d\dryad_interphase"

# 5. Microplastic Solution Library 1.1, TXT format (CC BY 4.0, 327 kB, URL from the record page)
$d = "$root\microplastics"
Get-File "https://zenodo.org/records/17710809/files/Microplastic%20Solution%20Library%201.1%20(.TXT%20format).zip?download=1" "$d\Microplastic_Solution_Library_1.1_TXT.zip"
Expand-Once "$d\Microplastic_Solution_Library_1.1_TXT.zip" "$d\Microplastic_Solution_Library_1.1_TXT"

# Extra A: low-wavenumber excipient Raman in spc format (CC BY 4.0, 0.9 MB total, URLs from the record page)
$d = "$root\pharma-excipients"
Get-File "https://zenodo.org/records/3614035/files/LF-785_spc_file_format.zip?download=1" "$d\LF-785_spc_file_format.zip"
Get-File "https://zenodo.org/records/3614035/files/FT-Raman_spc_file_format.zip?download=1" "$d\FT-Raman_spc_file_format.zip"
Expand-Once "$d\LF-785_spc_file_format.zip" "$d\LF-785_spc"
Expand-Once "$d\FT-Raman_spc_file_format.zip" "$d\FT-Raman_spc"

# Extra B: one ROD entry as JCAMP-DX (CC0), to check the format before crawling more IDs
Get-File "https://solsa.crystallography.net/rod/3500283.jdx" "$root\minerals-rod\3500283.jdx"
