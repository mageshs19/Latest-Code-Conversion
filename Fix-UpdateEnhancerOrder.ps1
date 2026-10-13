#requires -Version 5.1
# ============================================================================
#  Fix-UpdateEnhancerOrder.ps1
#  Root-cause fix: single restart generator, audit MOVEs written last.
# ============================================================================

$Root   = "C:\VSCode\Latest\Latest-Code_Conversion\IDMS-DB2-Code-Conversion"
$DryRun = $true          # <-- set to $false to actually write

$Enh  = Join-Path $Root "converter\postprocess\update_program_enhancer.py"
$Dead = @(
    "converter\generators\control_paragraph_generator.py",
    "converter\generators\restart_infrastructure_fixer.py"
)

$Stamp  = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $Root "_backup_$Stamp"

function Write-Head($t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Write-Ok($t)   { Write-Host "  [ok]   $t" -ForegroundColor Green }
function Write-Warn($t) { Write-Host "  [warn] $t" -ForegroundColor Yellow }
function Write-Err($t)  { Write-Host "  [ERR]  $t" -ForegroundColor Red }

function Save-Utf8NoBom([string]$Path, [string[]]$Lines) {
    $enc = New-Object System.Text.UTF8Encoding $false
    [IO.File]::WriteAllLines($Path, $Lines, $enc)
}

# Returns the 0-based index of the line that closes the statement
# beginning at $start, by parenthesis balance.
function Get-BlockEnd([string[]]$L, [int]$start) {
    $depth = 0
    for ($i = $start; $i -lt $L.Count; $i++) {
        $line = $L[$i]
        foreach ($c in $line.ToCharArray()) {
            if ($c -eq '(') { $depth++ }
            elseif ($c -eq ')') { $depth-- }
        }
        if ($depth -le 0) { return $i }
    }
    return $start
}

# Walks backwards from $start collecting contiguous comment / blank lines
function Get-BlockStartWithComments([string[]]$L, [int]$start) {
    $i = $start - 1
    while ($i -ge 0) {
        $t = $L[$i].Trim()
        if ($t -eq '' -or $t.StartsWith('#')) { $i-- } else { break }
    }
    return $i + 1
}

# ---------------------------------------------------------------------------
Write-Head "0. Preconditions"
# ---------------------------------------------------------------------------
if (-not (Test-Path $Enh)) { Write-Err "Not found: $Enh"; return }
Write-Ok "enhancer found"

$lines = [string[]](Get-Content $Enh)
Write-Ok "$($lines.Count) line(s) read"

$iParas = ($lines | Select-String -Pattern 'output\s*=\s*self\.restart_paragraph_manager\.ensure_restart_paragraphs' | Select-Object -First 1).LineNumber
$iStd   = ($lines | Select-String -Pattern 'output\s*=\s*self\.business_sql_standardizer\.standardize'              | Select-Object -First 1).LineNumber
$iGen   = ($lines | Select-String -Pattern 'output\s*=\s*self\._apply_generic_restart_logic'                        | Select-Object -First 1).LineNumber

if (-not $iParas -or -not $iStd -or -not $iGen) {
    Write-Err "Could not locate all three call sites. Aborting."
    "  ensure_restart_paragraphs : $iParas"
    "  standardize               : $iStd"
    "  _apply_generic_restart    : $iGen"
    return
}

# Select-String LineNumber is 1-based -> convert
$iParas--; $iStd--; $iGen--

if (-not ($iParas -lt $iStd -and $iStd -lt $iGen)) {
    Write-Warn "Order is not the expected 297 < 301 < 305 pattern. Already fixed? Aborting."
    return
}
Write-Ok "call order confirmed: ensure_restart_paragraphs -> standardize -> _apply_generic_restart_logic"

# ---------------------------------------------------------------------------
Write-Head "1. Backup"
# ---------------------------------------------------------------------------
if (-not $DryRun) { New-Item -ItemType Directory -Path $Backup -Force | Out-Null }
foreach ($rel in @((Split-Path $Enh -Leaf)) + $Dead) {
    $src = if ($rel -like '*\*') { Join-Path $Root $rel } else { $Enh }
    if (Test-Path $src) {
        $dst = Join-Path $Backup (Split-Path $src -Leaf)
        if ($DryRun) { Write-Warn "would back up $src" }
        else { Copy-Item $src $dst -Force; Write-Ok "backed up $(Split-Path $src -Leaf)" }
    }
}

# ---------------------------------------------------------------------------
Write-Head "2. Delete dead modules (guarded)"
# ---------------------------------------------------------------------------
foreach ($rel in $Dead) {
    $path = Join-Path $Root $rel
    if (-not (Test-Path $path)) { Write-Warn "already gone: $rel"; continue }

    $leaf  = [IO.Path]::GetFileNameWithoutExtension($path)
    $class = ($leaf -split '_' | ForEach-Object { $_.Substring(0,1).ToUpper() + $_.Substring(1) }) -join ''

    $refs = Get-ChildItem $Root -Recurse -Filter *.py |
            Where-Object { $_.FullName -ne $path } |
            Select-String -Pattern $leaf, $class -SimpleMatch

    if ($refs) {
        Write-Err "REFUSED to delete $rel - still referenced:"
        $refs | ForEach-Object { "        {0}:{1}" -f $_.Path.Substring($Root.Length+1), $_.LineNumber }
    }
    else {
        if ($DryRun) { Write-Warn "would delete $rel (0 references)" }
        else { Remove-Item $path -Force; Write-Ok "deleted $rel" }
    }
}

# ---------------------------------------------------------------------------
Write-Head "3. Patch enhance(): drop generator 1, move generator 2 ahead of standardize"
# ---------------------------------------------------------------------------
$pStart = Get-BlockStartWithComments $lines $iParas
$pEnd   = Get-BlockEnd $lines $iParas

$sStart = Get-BlockStartWithComments $lines $iStd
$sEnd   = Get-BlockEnd $lines $iStd

$gStart = Get-BlockStartWithComments $lines $iGen
$gEnd   = Get-BlockEnd $lines $iGen

"  generator-1 block : lines $($pStart+1)..$($pEnd+1)   (DELETE)"
"  standardize block : lines $($sStart+1)..$($sEnd+1)"
"  generator-2 block : lines $($gStart+1)..$($gEnd+1)   (MOVE before standardize)"

$stdBlock = $lines[$sStart..$sEnd]
$genBlock = $lines[$gStart..$gEnd]

$note = @(
    "        # ROOT-CAUSE FIX ($Stamp):",
    "        # The restart family OWNS the business paragraph: it rebuilds it",
    "        # from a repaired span. It must therefore run BEFORE the business",
    "        # SQL standardizer, otherwise the audit MOVEs the standardizer",
    "        # inserts are destroyed by the rebuild. The duplicate legacy call",
    "        # to ensure_restart_paragraphs was removed: its output was",
    "        # regenerated by this pass on every run."
)

$new = @()
$new += $lines[0..($pStart-1)]            # everything before generator 1
$new += $note
$new += $genBlock                          # generator 2 first
$new += ""
$new += $stdBlock                          # standardizer last
$new += $lines[($gEnd+1)..($lines.Count-1)]  # everything after generator 2

if ($DryRun) {
    Write-Warn "DRY RUN - no file written. Preview of the new sequence:"
    $new | Select-String -Pattern '^\s*(def |output = self\.)' |
      ForEach-Object { "      {0}" -f $_.Line.TrimEnd() }
}
else {
    Save-Utf8NoBom $Enh $new
    Write-Ok "patched $(Split-Path $Enh -Leaf)  ($($lines.Count) -> $($new.Count) lines)"
}

# ---------------------------------------------------------------------------
Write-Head "4. Syntax check"
# ---------------------------------------------------------------------------
if ($DryRun) { Write-Warn "skipped in dry run" }
else {
    $check = & python -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read()); print('OK')" $Enh 2>&1
    if ($check -match 'OK') { Write-Ok "python ast.parse OK" }
    else { Write-Err "SYNTAX ERROR - restore from $Backup"; $check }
}

# ---------------------------------------------------------------------------
Write-Head "5. New call order"
# ---------------------------------------------------------------------------
Select-String -Path $Enh -Pattern '^\s*(def enhance|output = self\.)' |
  ForEach-Object { "{0,5}: {1}" -f $_.LineNumber, $_.Line.TrimEnd() }

Write-Host "`nDone. DryRun = $DryRun" -ForegroundColor Cyan
if (-not $DryRun) { Write-Host "Backup: $Backup" -ForegroundColor Cyan }