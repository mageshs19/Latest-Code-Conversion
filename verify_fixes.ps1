param([datetime]$Since = (Get-Date).AddMinutes(-15))

$root = "C:\VSCode\Latest\Latest-Code_Conversion\IDMS-DB2-Code-Conversion"
$out  = Join-Path $root "mainframe\workspace\Output"

$new = @(Get-ChildItem $out -Recurse -Include *.cbl -ErrorAction SilentlyContinue |
         Where-Object { $_.LastWriteTime -gt $Since })

if ($new.Count -eq 0) {
    Write-Host "No member written since $Since - run the conversion first." -ForegroundColor Yellow
    return
}

$rows = foreach ($f in $new) {
    $l = Get-Content $f.FullName

    $sentinel = @($l | Select-String "IF DA-CCYYMMDD = ZERO").Count
    $parmMove = @($l | Select-String "MOVE DATE-YMD8").Count
    $init     = @($l | Select-String "INITIALIZE\s+DCLDZ").Count
    $bad      = @($l | Where-Object { $_.Length -ne 80 }).Count

    $moveNested = $false
    for ($i = 0; $i -lt $l.Count - 2; $i++) {
        if ($l[$i] -match "PERFORM READ-FLAT-FILE") {
            $upper = [Math]::Min($i + 4, $l.Count - 1)
            $window = ($l[($i+1)..$upper] -join " ")
            if ($window -match "MOVE NB-READ" -and $window -match "END-PERFORM") {
                if ($window.IndexOf("MOVE NB-READ") -lt $window.IndexOf("END-PERFORM")) {
                    $moveNested = $true
                }
            }
        }
    }

    [PSCustomObject]@{
        Member        = $f.Name
        I1_Sentinels  = $sentinel
        I1_ParmMoves  = $parmMove
        I2_MoveNested = $moveNested
        I3_Initialize = $init
        BadWidth      = $bad
    }
}

$rows | Format-Table -AutoSize

$m = $new | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($m) {
    Write-Host ""
    Write-Host "=== $($m.Name) ===" -ForegroundColor Cyan
    Select-String -Path $m.FullName -Pattern "MOVE DATE-YMD8"           -Context 1,4
    Select-String -Path $m.FullName -Pattern "JOB-IS-RESTART\."         -Context 0,13
    Select-String -Path $m.FullName -Pattern "^\s*\d{6}\s+VERWERKING\." -Context 0,4
}
