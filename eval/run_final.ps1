# Final held-out comparison, all arms, resumable. Run in its own PowerShell window from the repo root:
#   powershell -ExecutionPolicy Bypass -File eval\run_final.ps1
# Each step skips cases that already have a report, so rerunning after any interruption continues where it stopped.
# Skill-arm cases run one at a time: each starts an iopic-bond MCP server that loads PyTorch (memory).
# Output: eval/runs/final-*/ ; log: eval/runs/final-chain.log ; then figure, comparisons and results/ export.

$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
$py = ".venv\Scripts\python.exe"
$log = "eval\runs\final-chain.log"
function Step($label, [string[]]$cmd) {
    Add-Content $log "[$(Get-Date -Format s)] $label"
    Write-Host "[$(Get-Date -Format s)] $label"
    & $py @cmd 2>&1 | Tee-Object -FilePath $log -Append
}
$R = "eval\run_claude_code.py"

# 1. interpretation (7 held-out cases)
Step "int haiku bare"   @($R, "--split", "heldout", "--kind", "interpret", "--arm", "bare",  "--run-name", "final-int", "--model", "claude-haiku-5-5", "--parallel", "2", "--timeout-min", "30")
Step "int haiku skill"  @($R, "--split", "heldout", "--kind", "interpret", "--arm", "skill", "--run-name", "final-int", "--model", "claude-haiku-5-5", "--parallel", "1", "--timeout-min", "30")
Step "int sonnet bare"  @($R, "--split", "heldout", "--kind", "interpret", "--arm", "bare",  "--run-name", "final-int-sonnet", "--parallel", "2", "--timeout-min", "30")
Step "int sonnet skill" @($R, "--split", "heldout", "--kind", "interpret", "--arm", "skill", "--run-name", "final-int-sonnet", "--parallel", "1", "--timeout-min", "30")
Step "int pipeline"     @("eval\baselines.py", "--arm", "pipeline", "--split", "heldout", "--run-name", "final-int", "--kind", "interpret")

# 2. identification (37 held-out cases)
Step "id haiku bare"    @($R, "--split", "heldout", "--kind", "identify", "--arm", "bare",  "--run-name", "final-id", "--model", "claude-haiku-5-5", "--parallel", "2", "--timeout-min", "20")
Step "id haiku skill"   @($R, "--split", "heldout", "--kind", "identify", "--arm", "skill", "--run-name", "final-id", "--model", "claude-haiku-5-5", "--parallel", "1", "--timeout-min", "20")
Step "id sonnet bare"   @($R, "--split", "heldout", "--kind", "identify", "--arm", "bare",  "--run-name", "final-id-sonnet", "--parallel", "2", "--timeout-min", "20")
Step "id sonnet skill"  @($R, "--split", "heldout", "--kind", "identify", "--arm", "skill", "--run-name", "final-id-sonnet", "--parallel", "1", "--timeout-min", "20")
Step "id libsearch"     @("eval\baselines.py", "--arm", "libsearch", "--split", "heldout", "--run-name", "final-id", "--kind", "identify")

# 3. grading, comparisons, export
Step "judge int"        @("eval\judge.py", "eval\runs\final-int", "--parallel", "2")
Step "judge int sonnet" @("eval\judge.py", "eval\runs\final-int-sonnet", "--parallel", "2")
Step "score id"         @("eval\score.py", "eval\runs\final-id")
Step "score id sonnet"  @("eval\score.py", "eval\runs\final-id-sonnet")
foreach ($r in "final-int", "final-int-sonnet", "final-id", "final-id-sonnet") { Step "compare $r" @("eval\compare_arms.py", $r) }
Step "compare pipeline" @("eval\compare_arms.py", "final-int", "--arms", "pipeline", "skill")
Step "export"           @("eval\export_results.py")
Write-Host "Done. If a step printed USAGE LIMIT, rerun this script after the reset."
