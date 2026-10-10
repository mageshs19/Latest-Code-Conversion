$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path

Write-Host "STAGE 3 : testing -> runners`n" -ForegroundColor Cyan

# ---- guard: clean tree
$dirty = git status --porcelain
if ($dirty) {
    Write-Host "ABORT: working tree not clean. Commit or stash first." -ForegroundColor Red
    exit 1
}

# ---- 1. move the folder (two-step for Windows case safety)
git mv src/idms_db2_phase2/testing runners.__tmp
git mv runners.__tmp runners
Write-Host "moved  testing -> runners" -ForegroundColor Green

# ---- 2. rename the entry point
if (Test-Path .\runners\run_retrieval.py) {
    git mv runners/run_retrieval.py runners/convert_programs.py
    Write-Host "moved  run_retrieval.py -> convert_programs.py" -ForegroundColor Green
}

# ---- 3. rewrite references (LITERAL replace, no regex)
$pairs = @(
    @('src/idms_db2_phase2/testing/run_retrieval.py', 'runners/convert_programs.py'),
    @('src\idms_db2_phase2\testing\run_retrieval.py', 'runners\convert_programs.py'),
    @('src/idms_db2_phase2/testing',                  'runners'),
    @('src\idms_db2_phase2\testing',                  'runners'),
    @('idms_db2_phase2.testing',                      'runners'),
    @('idms_db2_phase2/testing',                      'runners'),
    @('idms_db2_phase2\testing',                      'runners')
)

$files = Get-ChildItem -Path $root -Recurse -File -Include *.py,*.md,*.txt,*.cfg,*.toml,*.env,*.bat,*.ps1 |
         Where-Object {
             $p = $_.FullName
             ($p -notlike '*\.git\*') -and
             ($p -notlike '*__pycache__*') -and
             ($p -notlike '*\.venv\*') -and
             ($p -notlike '*\_quarantine_*')
         }

$changed = 0
foreach ($f in $files) {
    $t = [IO.File]::ReadAllText($f.FullName)
    $o = $t
    foreach ($p in $pairs) { $t = $t.Replace($p[0], $p[1]) }
    if ($t -ne $o) { [IO.File]::WriteAllText($f.FullName, $t); $changed++ }
}
Write-Host "rewrote $changed file(s)" -ForegroundColor Green

# ---- 4. depth patches (folder lost two levels)
function Patch($path, $from, $to, $label) {
    if (-not (Test-Path $path)) { Write-Host "  skip  $label" -ForegroundColor DarkGray; return }
    $t = [IO.File]::ReadAllText($path)
    if ($t.Contains($from)) {
        [IO.File]::WriteAllText($path, $t.Replace($from, $to))
        Write-Host "  fixed $label" -ForegroundColor Green
    } else {
        Write-Host "  CHECK $label - '$from' not found" -ForegroundColor Yellow
    }
}

Write-Host "depth patches:"
Patch ".\runners\retrieval\retrieval_environment.py" "parents[2]" "parents[1]" "retrieval src_dir"
Patch ".\runners\retrieval\retrieval_environment.py" "parents[3]" "parents[2]" "retrieval project_root"
Patch ".\runners\update\update_environment.py"       "parents[2]" "parents[1]" "update src_dir"
Patch ".\runners\update\update_environment.py"       "parents[3]" "parents[2]" "update project_root"
Patch ".\runners\pytest_runner.py"                   "parents[3]" "parents[1]" "pytest_runner root"

Write-Host "`nNow run: .\tools\baseline.ps1" -ForegroundColor Cyan