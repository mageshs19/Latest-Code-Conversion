# LOCATION: tools/run_label_probe.ps1
# ACTION: CREATE NEW FILE
#
# Runs the cursor key label probe and writes a timestamped transcript.
#
#   cd <project root>
#   powershell -ExecutionPolicy Bypass -File tools\run_label_probe.ps1
#
# Then share the transcript path printed at the end.

[CmdletBinding()]
param(
    [string]$InputDir = "",       # optional: override IDMS_INPUT_DIR
    [switch]$UseZoweWorkspace     # optional: point at mainframe\workspace
)

$ErrorActionPreference = "Continue"

# ---- locate project root (parent of tools\) -----------------------------
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host ""
Write-Host "=============================================================="
Write-Host " CURSOR KEY LABEL PROBE"
Write-Host "=============================================================="
Write-Host " Project root : $ProjectRoot"

# ---- environment --------------------------------------------------------
$env:PYTHONPATH   = "."
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONWARNINGS = "ignore:Unverified HTTPS request"

if ($UseZoweWorkspace) {
    $workspace = Join-Path $ProjectRoot "mainframe\workspace"
    $env:IDMS_INPUT_DIR = $workspace
    Write-Host " Mode         : ZOWE WORKSPACE"
}
elseif ($InputDir -ne "") {
    $env:IDMS_INPUT_DIR = $InputDir
    Write-Host " Mode         : EXPLICIT INPUT DIR"
}
else {
    Write-Host " Mode         : INHERITED (IDMS_INPUT_DIR not overridden)"
}

Write-Host " PYTHONPATH   : $env:PYTHONPATH"
Write-Host " IDMS_INPUT_DIR: $(if ($env:IDMS_INPUT_DIR) { $env:IDMS_INPUT_DIR } else { '(not set)' })"

# ---- resolve python -----------------------------------------------------
$python = "python"
$venv = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $venv) {
    $python = $venv
    Write-Host " Python       : $venv (venv)"
}
else {
    Write-Host " Python       : system python"
}

# ---- probe file present? ------------------------------------------------
$probe = Join-Path $ProjectRoot "tools\label_probe.py"
if (-not (Test-Path $probe)) {
    Write-Host ""
    Write-Host " ERROR: tools\label_probe.py not found." -ForegroundColor Red
    Write-Host " Create it first, then re-run this script."
    exit 2
}

# ---- transcript ---------------------------------------------------------
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$stamp      = Get-Date -Format "dd-MM-yyyy_HHmmss"
$transcript = Join-Path $logDir "label_probe_$stamp.log"

Write-Host " Transcript   : $transcript"
Write-Host "=============================================================="
Write-Host ""

# ---- run ----------------------------------------------------------------
& $python $probe 2>&1 | Tee-Object -FilePath $transcript
$code = $LASTEXITCODE

Write-Host ""
Write-Host "=============================================================="
Write-Host " Probe exit code : $code"
Write-Host " Transcript saved: $transcript"
Write-Host "=============================================================="
Write-Host ""
Write-Host " Share the contents of that file." -ForegroundColor Cyan
Write-Host ""

# ---- copy to clipboard for convenience ---------------------------------
try {
    Get-Content $transcript -Raw | Set-Clipboard
    Write-Host " (transcript copied to clipboard)" -ForegroundColor DarkGray
    Write-Host ""
}
catch {
    # clipboard is optional; never fail the run over it
}

exit $code