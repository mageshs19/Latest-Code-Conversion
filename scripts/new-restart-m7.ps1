Set-Location "C:\VSCode\Latest\Latest-Code_Conversion\IDMS-DB2-Code-Conversion"

$files = @(
    "tests\restart\_checklist.py",
    "tests\restart\test_m10c_golden_output.py"
)
foreach ($f in $files) {
    if (Test-Path $f) { Write-Host "skipped (exists) $f" }
    else { New-Item -ItemType File -Path $f -Force | Out-Null; Write-Host "created $f" }
}