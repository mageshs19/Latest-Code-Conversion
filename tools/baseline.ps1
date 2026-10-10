$env:PYTHONPATH = "src;."

python -m zowe.zowe_pipeline clean | Out-Null
$out = python -m zowe.zowe_pipeline convert 2>&1 | Out-String

$expect = @(
    @{ Key = 'Sheet Mapping rows'; Want = '840'  },
    @{ Key = 'DCLGEN columns';     Want = '187'  },
    @{ Key = 'Copybook fields';    Want = '1349' },
    @{ Key = 'LRF records';        Want = '3'    },
    @{ Key = 'Programs converted'; Want = '6'    }
)

$ok = $true
foreach ($e in $expect) {
    $line = ($out -split "`n") | Where-Object { $_ -like ("*" + $e.Key + "*:*") } | Select-Object -First 1
    if (-not $line) {
        Write-Host ("{0,-20} MISSING" -f $e.Key) -ForegroundColor Red
        $ok = $false
        continue
    }
    $got = ($line -split ':')[-1].Trim()
    $hit = ($got -eq $e.Want)
    if (-not $hit) { $ok = $false }
    Write-Host ("{0,-20} {1,6}   expect {2}" -f $e.Key, $got, $e.Want) `
        -ForegroundColor $(if ($hit) { 'Green' } else { 'Red' })
}

if ($out -notlike "*PIPELINE COMPLETED*") {
    Write-Host "PIPELINE did not complete" -ForegroundColor Red
    $ok = $false
}

Write-Host ""
if ($ok) { Write-Host "BASELINE OK"     -ForegroundColor Green; exit 0 }
else     { Write-Host "BASELINE BROKEN" -ForegroundColor Red;   exit 1 }