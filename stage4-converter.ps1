$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path

if (git status --porcelain) {
    Write-Host "ABORT: tree not clean. Commit Stage 3 first." -ForegroundColor Red
    exit 1
}

Write-Host "STAGE 4 : idms_db2_phase2 -> converter`n" -ForegroundColor Cyan

# ---- 1. move the package to the repo root
git mv src/idms_db2_phase2 converter.__tmp
git mv converter.__tmp converter
Write-Host "moved  src/idms_db2_phase2 -> converter" -ForegroundColor Green

# ---- 2. literal rewrites (specific first)
$pairs = @(
    @('src.idms_db2_phase2', 'converter'),
    @('src/idms_db2_phase2', 'converter'),
    @('src\idms_db2_phase2', 'converter'),
    @('idms_db2_phase2',     'converter')
)

$files = Get-ChildItem -Path $root -Recurse -File `
            -Include *.py,*.md,*.txt,*.cfg,*.toml,*.ini,*.env,*.bat,*.ps1,*.yaml,*.yml |
         Where-Object {
             $p = $_.FullName
             ($p -notlike '*\.git\*') -and ($p -notlike '*__pycache__*') -and
             ($p -notlike '*\.venv\*') -and ($p -notlike '*\_quarantine_*')
         }

$changed = 0
foreach ($f in $files) {
    $t = [IO.File]::ReadAllText($f.FullName); $o = $t
    foreach ($p in $pairs) { $t = $t.Replace($p[0], $p[1]) }
    if ($t -ne $o) { [IO.File]::WriteAllText($f.FullName, $t); $changed++ }
}
Write-Host "rewrote $changed file(s)" -ForegroundColor Green

# ---- 3. targeted patches
function Patch($path, $from, $to, $label) {
    if (-not (Test-Path $path)) { Write-Host "  skip  $label" -ForegroundColor DarkGray; return }
    $t = [IO.File]::ReadAllText($path)
    if ($t.Contains($from)) {
        [IO.File]::WriteAllText($path, $t.Replace($from, $to))
        Write-Host "  fixed $label" -ForegroundColor Green
    } else {
        Write-Host "  CHECK $label - not found" -ForegroundColor Yellow
    }
}

Write-Host "patches:"

# one import root now
Patch ".\rules\test_runner_rules.py"   'PYTHONPATH_ENTRIES = ("src", ".")' 'PYTHONPATH_ENTRIES = (".",)' 'test_runner PYTHONPATH'
Patch ".\rules\batch_console_rules.py" 'PYTHONPATH_ENTRIES = ("src", ".")' 'PYTHONPATH_ENTRIES = (".",)' 'batch PYTHONPATH'

# converter/app.py lost one level: parents[2] -> parents[1]
Patch ".\converter\app.py" 'parents[2]' 'parents[1]' 'app.py project root'

# baseline script now uses a single root
Patch ".\tools\baseline.ps1" '"src;."' '"."' 'baseline PYTHONPATH'

# ---- 4. drop the empty src shell
Remove-Item .\src -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "removed empty .\src" -ForegroundColor Green

Write-Host "`nNext:  `$env:PYTHONPATH = '.'  then  .\tools\baseline.ps1" -ForegroundColor Cyan