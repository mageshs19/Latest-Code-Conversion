$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path

if (git status --porcelain) {
    Write-Host "ABORT: tree not clean. Commit Stage 4 first." -ForegroundColor Red
    exit 1
}

Write-Host "STAGE 5 : review->review, zowe->mainframe, orchestration->pipeline`n" -ForegroundColor Cyan

git mv review review.__tmp
git mv review.__tmp review
Write-Host "moved  review -> review" -ForegroundColor Green

git mv zowe mainframe.__tmp
git mv mainframe.__tmp mainframe
Write-Host "moved  zowe -> mainframe" -ForegroundColor Green

git mv converter/pipeline converter/pipeline.__tmp
git mv converter/pipeline.__tmp converter/pipeline
Write-Host "moved  converter/pipeline -> converter/pipeline" -ForegroundColor Green

# literal rewrites - specific first
$pairs = @(
    @('converter.pipeline', 'converter.pipeline'),
    @('converter/pipeline', 'converter/pipeline'),
    @('converter\pipeline', 'converter\pipeline'),
    @('review',             'review'),
    @('from mainframe.',              'from mainframe.'),
    @('import mainframe.',            'import mainframe.'),
    @('mainframe.zowe_',              'mainframe.zowe_'),
    @('-m mainframe.',                '-m mainframe.')
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

Write-Host "`nNext: .\tools\baseline.ps1" -ForegroundColor Cyan