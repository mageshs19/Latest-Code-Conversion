$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path

$files = Get-ChildItem -Path $root -Recurse -File `
            -Include *.py,*.md,*.txt,*.cfg,*.toml,*.ini,*.env,*.ps1,*.bat,*.yaml,*.yml |
         Where-Object { $_.FullName -notmatch '\$\.git|__pycache__|\.venv|venv|_quarantine_)\\' }

Write-Host "Rewriting $($files.Count) files...`n" -ForegroundColor Cyan

# ORDER MATTERS - longest / most specific first
$map = [ordered]@{
    # 1. runner paths (before the package rename eats them)
    'src/idms_db2_phase2/testing/run_retrieval\.py' = 'runners/convert_programs.py'
    'src/idms_db2_phase2/testing'                   = 'runners'
    'src\\\\idms_db2_phase2\\\\testing'             = 'runners'
    'code_review/runner'                            = 'review/runner'

    # 2. sub-package rename BEFORE the parent rename
    'idms_db2_phase2\.orchestration'                = 'converter.pipeline'
    'src\.idms_db2_phase2'                          = 'converter'

    # 3. package renames
    'idms_db2_phase2'                               = 'converter'
    'code_review'                                   = 'review'
    'from zowe\.'                                   = 'from mainframe.'
    'import zowe\.'                                 = 'import mainframe.'
    '\bzowe\.zowe_'                                 = 'mainframe.zowe_'
}

$changed = 0
foreach ($f in $files) {
    $text = Get-Content $f.FullName -Raw -Encoding UTF8
    $orig = $text
    foreach ($k in $map.Keys) { $text = $text -replace $k, $map[$k] }
    if ($text -ne $orig) {
        Set-Content $f.FullName -Value $text -NoNewline -Encoding UTF8
        $changed++
    }
}
Write-Host "Rewrote $changed file(s).`n" -ForegroundColor Green

# ---------------------------------------------------------------- patches
function Patch($path, $find, $replace, $label) {
    if (-not (Test-Path $path)) { Write-Host "  skip  $label" -ForegroundColor DarkGray; return }
    $t = Get-Content $path -Raw -Encoding UTF8
    if ($t -match $find) {
        Set-Content $path -Value ($t -replace $find, $replace) -NoNewline -Encoding UTF8
        Write-Host "  fixed $label" -ForegroundColor Green
    } else {
        Write-Host "  check $label (pattern not found)" -ForegroundColor Yellow
    }
}

Write-Host "Applying depth / path patches:" -ForegroundColor Cyan

# PYTHONPATH: two roots -> one
Patch ".\rules\test_runner_rules.py"   'PYTHONPATH_ENTRIES\s*=\s*\("src",\s*"\."$' 'PYTHONPATH_ENTRIES = (".",)' 'test_runner_rules PYTHONPATH'
Patch ".\rules\batch_console_rules.py" 'PYTHONPATH_ENTRIES\s*=\s*$"src",\s*"\."$' 'PYTHONPATH_ENTRIES = (".",)' 'batch_console_rules PYTHONPATH'

# runners/*/environment.py : was src/pkg/testing/<sub>/x.py  -> now runners/<sub>/x.py
Patch ".\runners\retrieval\retrieval_environment.py" 'parents$$2$$' 'parents[1]' 'retrieval_environment src_dir'
Patch ".\runners\retrieval\retrieval_environment.py" 'parents$$3$$' 'parents[2]' 'retrieval_environment project_root'
Patch ".\runners\update\update_environment.py"       'parents$$2$$' 'parents[1]' 'update_environment src_dir'
Patch ".\runners\update\update_environment.py"       'parents$$3$$' 'parents[2]' 'update_environment project_root'

# pytest_runner moved up two levels
Patch ".\runners\pytest_runner.py" 'parents$$3$$' 'parents[1]' 'pytest_runner project_root'

# workspace is now at the repo root, not inside the package
Patch ".\mainframe\zowe_workspace.py" 'return PACKAGE_DIR / WORKSPACE_DIR_NAME' 'return PROJECT_ROOT / WORKSPACE_DIR_NAME' 'workspace_root'

# web entry point moved
Patch ".\apps\web\main.py" 'SRC_DIR\s*=\s*CURRENT_FILE\s*\.\s*parents$$1$$' 'PROJECT_ROOT = CURRENT_FILE.parents[2]' 'web main SRC_DIR'

Write-Host "`nDone. Verify next." -ForegroundColor Cyan