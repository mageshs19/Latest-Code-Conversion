$ErrorActionPreference = 'Stop'
if (git status --porcelain) { Write-Host "ABORT: tree not clean." -ForegroundColor Red; exit 1 }

$groupA = @(
    'rules\COMPLETE_DOCUMENTATION_INDEX.py',
    'converter\generators\CODE_BUCKET_INTEGRATION_GUIDE.py',
    'converter\generators\CODE_BUCKET_QUICK_REFERENCE.py',
    'converter\generators\CODE_FLOW_ORCHESTRATOR_GUIDE.py',
    'Prompt'
)
$groupB = @(
    'converter\services\conversion_service.py',
    'converter\services\metadata_service.py'
)
$groupC = @(
    'runners\batch_execution.py',
    'runners\batch_console.py',
    'runners\console',
    'runners\execution',
    'rules\batch_console_rules.py',
    'patterns\batch_console_patterns.py',
    'review\runner\review_retrieval.py',
    'review\runner\review_update.py'
)

function Kill($list, $label) {
    Write-Host "`n--- $label ---" -ForegroundColor Cyan
    foreach ($p in $list) {
        if (Test-Path $p) {
            git rm -r --quiet -- $p
            Write-Host "  removed $p" -ForegroundColor Green
        } else {
            Write-Host "  missing $p" -ForegroundColor DarkGray
        }
    }
}

Remove-Group $groupA "GROUP A - documentation"
Remove-Group $groupB "GROUP B - shims"
Remove-Group $groupC "GROUP C - batch CLI cluster"

Write-Host "`nNow run: .\tools\baseline.ps1" -ForegroundColor Cyan