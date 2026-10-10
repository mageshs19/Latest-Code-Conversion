param(
    [Parameter(Mandatory = $true)][string]$Target
)

$root = (Get-Location).Path
if (-not (Test-Path $Target)) { Write-Host "Not found: $Target" -ForegroundColor Red; exit 1 }

$item     = Get-Item $Target
$isFolder = $item.PSIsContainer
$rel      = $item.FullName.Replace($root + '\', '')

Write-Host "`nREFERENCE SCAN : $rel" -ForegroundColor Cyan
Write-Host ("Type           : " + $(if ($isFolder) { 'FOLDER' } else { 'FILE' }))

# build literal needles
$needles = New-Object System.Collections.Generic.List[string]
$needles.Add(($rel -replace '\\','/'))
$needles.Add($rel)
if ($isFolder) {
    $needles.Add($item.Name + '/')
    $needles.Add($item.Name + '\')
    $needles.Add('.' + $item.Name)
} else {
    $stem = $item.BaseName
    $needles.Add($stem)
    $needles.Add($item.Name)
}

$files = Get-ChildItem -Path $root -Recurse -File `
            -Include *.py,*.md,*.txt,*.yaml,*.yml,*.toml,*.cfg,*.ini,*.json,*.bat,*.cmd,*.ps1,*.env |
         Where-Object {
             $p = $_.FullName
             ($p -notlike '*\.git\*') -and ($p -notlike '*__pycache__*') -and
             ($p -notlike '*\.venv\*') -and ($p -notlike '*\_quarantine_*') -and
             ($p -notlike ($item.FullName + '*'))
         }

Write-Host ("Scanned        : " + $files.Count + " files")
Write-Host "---------------------------------------------"

$hits = @()
foreach ($n in ($needles | Select-Object -Unique)) {
    $hits += $files | Select-String -SimpleMatch $n -CaseSensitive
}
$hits = $hits | Sort-Object Path, LineNumber -Unique

if (-not $hits) {
    Write-Host "`n  SAFE - no references found.`n" -ForegroundColor Green
    exit 0
}

Write-Host ("`n  REFERENCED - " + $hits.Count + " hit(s)`n") -ForegroundColor Red
foreach ($h in $hits) {
    $f = $h.Path.Replace($root + '\', '')
    $t = $h.Line.Trim()
    if ($t.Length -gt 95) { $t = $t.Substring(0, 92) + '...' }
    Write-Host ("    " + $f + ":" + $h.LineNumber) -ForegroundColor Gray
    Write-Host ("      " + $t) -ForegroundColor DarkGray
}
Write-Host "`n  DO NOT DELETE until these are resolved.`n" -ForegroundColor Red
exit 1