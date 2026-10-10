<#
.SYNOPSIS
    The refactoring contract. Six numbers plus three guards.
.DESCRIPTION
    Row counts prove the pipeline RAN. They do not prove every pass
    PARTICIPATED. Two silent regressions were missed by counts alone:
      1. deleting a try:-wrapped import (flow_bucket_..._v2)
      2. a migrated stage left disabled in registry.py
    Hence the extra guards below.
.EXAMPLE
    .\tools\baseline.ps1
#>

$env:PYTHONPATH = "."

python -m mainframe.zowe_pipeline clean | Out-Null
$out = python -m mainframe.zowe_pipeline convert 2>&1 | Out-String

$ok = $true

# ---------------------------------------------------------------- metrics
$expect = @(
    @{ Key = 'Sheet Mapping rows'; Want = '840'  },
    @{ Key = 'DCLGEN columns';     Want = '187'  },
    @{ Key = 'Copybook fields';    Want = '1349' },
    @{ Key = 'LRF records';        Want = '3'    },
    @{ Key = 'Programs converted'; Want = '6'    }
)

foreach ($e in $expect) {
    $line = ($out -split "`n") |
            Where-Object { $_ -like ("*" + $e.Key + "*:*") } |
            Select-Object -First 1

    if (-not $line) {
        Write-Host ("{0,-24} MISSING" -f $e.Key) -ForegroundColor Red
        $ok = $false
        continue
    }

    $got = ($line -split ':')[-1].Trim()
    $hit = ($got -eq $e.Want)
    if (-not $hit) { $ok = $false }
    Write-Host ("{0,-24} {1,6}   expect {2}" -f $e.Key, $got, $e.Want) `
        -ForegroundColor $(if ($hit) { 'Green' } else { 'Red' })
}

# ---------------------------------------------------------------- verdict
if (-not $out.Contains("PIPELINE COMPLETED")) {
    Write-Host "PIPELINE did not complete" -ForegroundColor Red
    $ok = $false
}

# ------------------------------------------------- guard 1: silent failure
foreach ($token in @('[ERROR]', 'ModuleNotFoundError', 'Orchestration Error', 'unknown pipeline stage')) {
    if ($out.Contains($token)) {
        Write-Host ("Silent stage failure: '{0}' in conversion output" -f $token) -ForegroundColor Red
        $ok = $false
    }
}

# -------------------------------------------------- guard 2: output volume
$cbl = Get-ChildItem .\mainframe\workspace\Output -Filter *.cbl -ErrorAction SilentlyContinue |
       Sort-Object Length -Descending | Select-Object -First 1

if (-not $cbl) {
    Write-Host ("{0,-24} NONE FOUND" -f 'Largest output') -ForegroundColor Red
    $ok = $false
} else {
    $lines = (Get-Content $cbl.FullName).Count
    $hit = ($lines -ge 400)
    if (-not $hit) { $ok = $false }
    Write-Host ("{0,-24} {1,6}   expect >= 400" -f 'Largest output lines', $lines) `
        -ForegroundColor $(if ($hit) { 'Green' } else { 'Red' })
}

# ----------------------------------------- guard 3: migrated passes ran
$log = Get-ChildItem .\logs -Filter *.log -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime | Select-Object -Last 1

if (-not $log) {
    Write-Host ("{0,-24} NO LOG" -f 'Pass evidence') -ForegroundColor Yellow
} else {
    $text = Get-Content $log.FullName -Raw

    $passes = @(
        @{ Name = 'normalise_procedure_indent'; Token = 'Procedure indent:' },
        @{ Name = 'declare_counters';           Token = 'Counters:'         }
    )

    foreach ($p in $passes) {
        $hit = $text.Contains($p.Token)
        if (-not $hit) { $ok = $false }
        Write-Host ("{0,-24} {1,6}   token '{2}'" -f $p.Name, $(if ($hit) { 'RAN' } else { 'SILENT' }), $p.Token) `
            -ForegroundColor $(if ($hit) { 'Green' } else { 'Red' })
    }
}

# ---------------------------------------------------------------- result
Write-Host ""
if ($ok) {
    Write-Host "BASELINE OK" -ForegroundColor Green
    exit 0
} else {
    Write-Host "BASELINE BROKEN" -ForegroundColor Red
    exit 1
}

foreach ($token in @('[ERROR]', 'ModuleNotFoundError', 'Enhancement pipeline FAILED', 'unknown pipeline stage')) {