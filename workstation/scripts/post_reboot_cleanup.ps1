# Post-Reboot Servicing & Component Store Cleanup Script
# Run this script after completing the pending Windows Update reboot.

$ErrorActionPreference = "Continue"

Write-Host "=========================================================="
Write-Host "    POST-REBOOT COMPONENT CLEANUP & HEALTH VERIFIER       "
Write-Host "=========================================================="

# 1. Verify Reboot Completion
$rebootPending = Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired"
$cbsReboot = Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending"

if ($rebootPending -or $cbsReboot) {
    Write-Warning "A system reboot is still pending! Please complete the reboot before running component store cleanup."
    exit 1
}

Write-Host "[OK] System reboot verified. No pending reboot locks detected."

# 2. DISM Component Store Cleanup
Write-Host "`n--- Running DISM Component Store Cleanup ---"
Write-Host "Reclaiming superseded WinSxS manifests from recent Windows Updates..."
$dismResult = dism.exe /Online /Cleanup-Image /StartComponentCleanup
$dismResult | ForEach-Object { Write-Host "     $_" }

# 3. Clean Stale Temp Files
Write-Host "`n--- Cleaning Stale Temp Files (> 7 days) ---"
$staleDays = 7
$cutoff = (Get-Date).AddDays(-$staleDays)

$tempFiles = Get-ChildItem $env:TEMP -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff }
$reclaimedBytes = 0
foreach ($f in $tempFiles) {
    try {
        $reclaimedBytes += $f.Length
        Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue
    } catch {}
}
Write-Host ("[OK] Reclaimed {0:N2} MB of stale temporary files." -f ($reclaimedBytes / 1MB))

# 4. Re-verify Audio Shield & Workstation Invariants
Write-Host "`n--- Verifying Workstation Performance Invariants ---"
& "$PSScriptRoot\lock_audio_services.ps1"

$dpm = Get-Service -Name "DPMService" -ErrorAction SilentlyContinue
if ($dpm -and $dpm.Status -eq 'Running') {
    Write-Host "[OK] DPMService (Dell Peripheral Manager) is active and running."
} else {
    Write-Warning "DPMService is not running! External monitor presets may be affected."
}

$dellTelemetry = Get-Service -Name "DellTechHub", "DellClientManagementService" -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' }
if ($dellTelemetry) {
    Write-Warning "Dell telemetry services re-awakened after reboot. Stopping..."
    Stop-Service -Name "DellTechHub", "DellClientManagementService" -Force -ErrorAction SilentlyContinue
    Set-Service -Name "DellTechHub", "DellClientManagementService" -StartupType Manual -ErrorAction SilentlyContinue
} else {
    Write-Host "[OK] Dell telemetry services remain stopped (Manual)."
}

Write-Host "`n=========================================================="
Write-Host "         POST-REBOOT CLEANUP COMPLETED SUCCESSFULLY       "
Write-Host "=========================================================="
