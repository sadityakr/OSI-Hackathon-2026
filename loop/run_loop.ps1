# Headless build loop for RamanLens: one fresh `claude -p` session per backlog task.
#
# Each iteration starts with an empty context, reads loop/PROMPT.md, does the first open task in loop/TASKS.md,
# commits, and exits. State lives in files and git, so a crashed or killed iteration loses at most one task.
# Stop early by creating loop/STOP. Logs: loop/logs/iter-NN.jsonl (stream-json transcript) and loop/logs/status.txt.
#
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File loop\run_loop.ps1 -MaxIterations 12
param(
    [int]$MaxIterations = 12,
    [int]$TimeoutMinutes = 60,
    [string]$Model = "opus"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force "loop\logs" | Out-Null

for ($i = 1; $i -le $MaxIterations; $i++) {
    if (Test-Path "loop\STOP") { Write-Host "STOP file found, ending."; break }
    $open = Select-String -Path "loop\TASKS.md" -Pattern '^- \[ \]' -SimpleMatch:$false
    if (-not $open) { Write-Host "No open tasks left."; break }

    $tag = "{0:D2}" -f $i
    $log = "loop\logs\iter-$tag.jsonl"
    $err = "loop\logs\iter-$tag.err.txt"
    $head = (git rev-parse --short HEAD)
    Write-Host "[$(Get-Date -Format s)] iteration $tag, next: $($open[0].Line.Substring(0, [Math]::Min(70, $open[0].Line.Length)))"

    $claudeArgs = @("-p", "`"Read loop/PROMPT.md and follow it exactly.`"",
              "--settings", "loop/settings.json",
              "--permission-mode", "acceptEdits",
              "--model", $Model,
              "--output-format", "stream-json", "--verbose")
    $p = Start-Process -FilePath "claude" -ArgumentList $claudeArgs -NoNewWindow -PassThru `
         -RedirectStandardOutput $log -RedirectStandardError $err
    if (-not $p.WaitForExit($TimeoutMinutes * 60 * 1000)) {
        Write-Host "  timeout after $TimeoutMinutes min, killing iteration"
        $p.Kill()
    }

    $tests = & .venv\Scripts\python.exe -m pytest tests -q -m "not slow" 2>&1 | Select-Object -Last 1
    $now = (git rev-parse --short HEAD)
    $line = "$(Get-Date -Format s) iter $tag exit=$($p.ExitCode) commit $head -> $now | fast tests: $tests"
    Add-Content -Path "loop\logs\status.txt" -Value $line -Encoding utf8
    Write-Host "  $line"
    if ($now -eq $head) {
        Write-Host "  no commit this iteration; stopping so a human can look (see $log)."
        break
    }
}
