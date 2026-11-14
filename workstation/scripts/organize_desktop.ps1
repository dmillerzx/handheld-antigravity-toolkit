$desktop = [System.Environment]::GetFolderPath('Desktop')

# Move screenshot/image
$img = Join-Path $desktop '8b05dc5a-5e8b-4e29-80a3-2f853a33a57e.jpg'
if (Test-Path $img) {
    Move-Item -LiteralPath $img -Destination (Join-Path $desktop 'Images_and_Screenshots') -Force
    Write-Host '[OK] Moved image to Desktop\Images_and_Screenshots'
}

# Move reg script
$reg = Join-Path $desktop 'tune_remote_60fps.reg'
if (Test-Path $reg) {
    Move-Item -LiteralPath $reg -Destination (Join-Path $desktop 'Scripts_and_Tools') -Force
    Write-Host '[OK] Moved reg script to Desktop\Scripts_and_Tools'
}

# Move Autani work documents
$workFiles = @(
    'ProductStatus_Oct30_updated.pptx  -  Repaired.pptx',
    'Open_Datasheet_Requests_2026-10-30 (002).xlsx'
)
foreach ($wf in $workFiles) {
    $p = Join-Path $desktop $wf
    if (Test-Path -LiteralPath $p) {
        Move-Item -LiteralPath $p -Destination (Join-Path $desktop 'Work_Autani_Keilton') -Force
        Write-Host "[OK] Moved $wf to Desktop\Work_Autani_Keilton"
    }
}

# Remove legacy 856MB DBZ Movie 01 copy from Desktop
$dbz01 = Join-Path $desktop 'Dragon Ball Z - Movie 01.mkv'
if (Test-Path -LiteralPath $dbz01) {
    Remove-Item -LiteralPath $dbz01 -Force
    Write-Host '[OK] Removed duplicate low-res Dragon Ball Z - Movie 01.mkv from Desktop'
}

Write-Host '[OK] Desktop cleanup and organization complete.'
