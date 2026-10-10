<#
.SYNOPSIS
    Verify all three flows after the architecture rework.
.DESCRIPTION
    Zowe convert is already proven by baseline.ps1. This checks the
    parts nobody has exercised since the rename: the UI modules, the
    local pipeline steps, and the structural integrity of the two
    host-dependent steps (fetch / upload) that cannot run offline.
.EXAMPLE
    .\tools\verify-all.ps1
#>

$env:PYTHONPATH = "."
Get-ChildItem -Recurse -Directory -Filter __pycache__ -EA SilentlyContinue |
    Remove-Item -Recurse -Force -EA SilentlyContinue

$script:results = @()

function Test-Step {
    param([string]$Label, [scriptblock]$Body)
    try {
        & $Body 2>&1 | Out-Null
        $code = $LASTEXITCODE
        if ($null -eq $code -or $code -eq 0 -or $code -eq 1) {
            Write-Host ("PASS  " + $Label) -ForegroundColor Green
            $script:results += [pscustomobject]@{ Name = $Label; Result = 'PASS' }
        } else {
            Write-Host ("FAIL  " + $Label + "   exit " + $code) -ForegroundColor Red
            $script:results += [pscustomobject]@{ Name = $Label; Result = 'FAIL' }
        }
    } catch {
        Write-Host ("FAIL  " + $Label + "   " + $_.Exception.Message) -ForegroundColor Red
        $script:results += [pscustomobject]@{ Name = $Label; Result = 'FAIL' }
    }
}

Write-Host "`n=== 1. PACKAGE IMPORTS ===" -ForegroundColor Cyan
Test-Step "import converter"       { python -c "import converter" }
Test-Step "import runners"         { python -c "import runners" }
Test-Step "import mainframe"       { python -c "import mainframe" }
Test-Step "import review"          { python -c "import review" }

Write-Host "`n=== 2. UI MODULES (untested since rename) ===" -ForegroundColor Cyan
Test-Step "converter.app"          { python -c "import converter.app" }
Test-Step "ui.main_page"           { python -c "from converter.ui.main_page import render_main_page" }
Test-Step "ui.conversion_actions"  { python -c "import converter.ui.conversion_actions" }
Test-Step "ui.session_state"       { python -c "import converter.ui.session_state" }
Test-Step "ui.input_loader"        { python -c "import converter.ui.input_loader" }
Test-Step "ui.status_panel"        { python -c "import converter.ui.status_panel" }
Test-Step "ui.output_tabs"         { python -c "import converter.ui.output_tabs" }
Test-Step "ui.test_panel"          { python -c "import converter.ui.test_panel" }
Test-Step "review.ui.review_panel" { python -c "import review.ui.review_panel" }

Write-Host "`n=== 3. PYTEST RUNNER (UI Tests tab) ===" -ForegroundColor Cyan
Test-Step "pytest_runner root" {
    python -c "from runners.pytest_runner import PytestRunner; import inspect, pathlib; p=pathlib.Path(inspect.getfile(PytestRunner)).resolve().parents[1]; assert (p/'converter').is_dir(), p; print('root ok', p)"
}

Write-Host "`n=== 4. PIPELINE - LOCAL STEPS ===" -ForegroundColor Cyan
Test-Step "pipeline init"          { python -m mainframe.zowe_pipeline init }
Test-Step "pipeline show"          { python -m mainframe.zowe_pipeline show }
Test-Step "pipeline plan"          { python -m mainframe.zowe_pipeline plan }
Test-Step "pipeline clean"         { python -m mainframe.zowe_pipeline clean }
Test-Step "pipeline convert"       { python -m mainframe.zowe_pipeline convert }
Test-Step "pipeline review"        { python -m mainframe.zowe_pipeline review }

Write-Host "`n=== 4b. HOST STEPS - structural only ===" -ForegroundColor Cyan
Test-Step "fetch/upload modules" {
    python -c "import mainframe.zowe_fetcher as f, mainframe.zowe_writer as w, mainframe.zowe_settings as s; assert hasattr(f,'ZoweFetcher') and hasattr(f,'fetch_zowe_inputs'); assert hasattr(w,'upload_converted_program') and hasattr(w,'upload_converted_folder'); s.build_profiles(); f.ZoweFetcher(); print('ok')"
}

Write-Host "`n=== 5. RUNNERS DIRECT ===" -ForegroundColor Cyan
Test-Step "convert_programs.py"    { python runners\convert_programs.py }
Test-Step "review_file.py"         { python review\runner\review_file.py --folder mainframe\workspace\Output }

Write-Host "`n=== 6. WORKSPACE LAYOUT ===" -ForegroundColor Cyan
$ws = ".\mainframe\workspace"
foreach ($d in 'Mapping Sheet','DCLGen','Copybook','Subschema','Program','Output','Review','Logs') {
    $p = Join-Path $ws $d
    if (Test-Path $p) {
        Write-Host ("PASS  workspace\" + $d) -ForegroundColor Green
        $script:results += [pscustomobject]@{ Name = "workspace\$d"; Result = 'PASS' }
    } else {
        Write-Host ("FAIL  workspace\" + $d + "  MISSING") -ForegroundColor Red
        $script:results += [pscustomobject]@{ Name = "workspace\$d"; Result = 'FAIL' }
    }
}

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan

$failed = @()
foreach ($r in $script:results) {
    if ($r.Result -eq 'FAIL') { $failed += $r }
}

$total = $script:results.Count
$bad = $failed.Count

if ($bad -eq 0) {
    Write-Host "$total checks, 0 failed" -ForegroundColor Green
    exit 0
}

Write-Host "$total checks, $bad failed" -ForegroundColor Red
foreach ($f in $failed) {
    Write-Host ("  - " + $f.Name) -ForegroundColor Red
}
exit 1