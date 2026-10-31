<#
.SYNOPSIS
  Reproducible, idempotent bootstrap for the video workspace (Windows / PowerShell 5.1+).
.DESCRIPTION
  Project-local only: no admin, no global config, no global installs. Safe to re-run:
  - uv sync --locked installs exactly uv.lock (no-op when already in sync, never upgrades)
  - models fetch skips weights that are already present
  - init creates only missing files
  Updating a dependency is a separate, explicit action (uv lock --upgrade-package X), not part of this script.
.PARAMETER CheckOnly
  Only report pending actions (read-only).
.PARAMETER SkipTests
  Skip the test suite.
.PARAMETER NoDownload
  Do not download model weights.
#>
param([switch]$CheckOnly, [switch]$SkipTests, [switch]$NoDownload)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$report = New-Object System.Collections.Generic.List[string]
function Step($text) { Write-Host "==> $text"; $report.Add("$(Get-Date -Format s) $text") }
function Need($name, $hint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { throw "missing prerequisite '$name': $hint" }
}

Step '1. Prerequisites'
Need 'uv' 'install uv: https://docs.astral.sh/uv/getting-started/installation/'
Need 'ffmpeg' 'winget install Gyan.FFmpeg  (needs approval: system-level install)'
Need 'ffprobe' 'comes with FFmpeg'
$report.Add("uv: $(uv --version)")
$report.Add("ffmpeg: $((ffmpeg -hide_banner -version | Select-Object -First 1))")

Step '2-3. Existing installation and pending actions (read-only)'
if (Test-Path .venv\Scripts\video-pipeline.exe) {
  & .venv\Scripts\video-pipeline.exe bootstrap-check
  $pendingExit = $LASTEXITCODE
} else {
  Write-Host 'PENDING: .venv not created yet'
  $pendingExit = 1
}
if ($CheckOnly) { exit $pendingExit }

Step '4/8. Install locked dependencies and the project package into .venv'
uv sync --locked
if ($LASTEXITCODE -ne 0) { throw 'uv sync --locked failed (lockfile out of date? run `uv lock` deliberately)' }

Step '6. Workspace skeleton (missing files only)'
uv run video-pipeline init
if ($LASTEXITCODE -ne 0) { throw 'init failed' }

Step '5. Approved model weights'
if ($NoDownload) { Write-Host 'skipped (-NoDownload)' } else {
  uv run video-pipeline models fetch faster-whisper-medium
  if ($LASTEXITCODE -ne 0) { throw 'model fetch failed' }
}

Step '7. Validate schemas, profiles and models'
uv run video-pipeline bootstrap-check
$checkExit = $LASTEXITCODE
uv run video-pipeline doctor

Step '9. Lint, types, tests and smoke test'
if ($SkipTests) { Write-Host 'skipped (-SkipTests)' } else {
  uv run ruff check src tests scripts; if ($LASTEXITCODE -ne 0) { throw 'ruff failed' }
  uv run mypy; if ($LASTEXITCODE -ne 0) { throw 'mypy failed' }
  uv run python scripts/sync_skills.py --check; if ($LASTEXITCODE -ne 0) { throw 'skill adapters out of sync' }
  uv run pytest -q; if ($LASTEXITCODE -ne 0) { throw 'tests failed' }
}

Step '10. Report'
New-Item -ItemType Directory -Force .local\state | Out-Null
$report.Add("bootstrap-check exit: $checkExit")
$report | Set-Content -Encoding utf8 .local\state\bootstrap-report.txt
Write-Host "report: .local\state\bootstrap-report.txt"
Write-Host 'next: uv run video-pipeline status'
exit $checkExit
