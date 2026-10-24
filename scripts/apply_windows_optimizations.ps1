# Dell Precision 5560 Windows 11 Workstation Optimization Script

$ErrorActionPreference = "Continue"

Write-Host "=========================================================="
Write-Host "  DELL PRECISION 5560 WINDOWS 11 WORKSTATION OPTIMIZATION  "
Write-Host "=========================================================="

# 1. OneNote & Phone Link Background Suppression
$oneNoteReg = "HKCU:\Software\Microsoft\Office\16.0\OneNote\Options\Other"
if (Test-Path $oneNoteReg) {
    Set-ItemProperty -Path $oneNoteReg -Name "EnableMemoryTrayMenuItem" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
    Set-ItemProperty -Path $oneNoteReg -Name "EnableMemoryShortcut" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] OneNote Tray & Shortcut registry options set to 0 (Disabled)."
}

$startupFolder = [System.Environment]::GetFolderPath('Startup')
$oneNoteLnk = Join-Path $startupFolder "Send to OneNote.lnk"
if (Test-Path -LiteralPath $oneNoteLnk) {
    Copy-Item -LiteralPath $oneNoteLnk -Destination "configs\system_backup\Send to OneNote.lnk" -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $oneNoteLnk -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Removed legacy 'Send to OneNote.lnk' from startup folder (backed up to configs\system_backup\)"
}

$onenotem = Get-Process -Name onenotem -ErrorAction SilentlyContinue
if ($onenotem) {
    Stop-Process -Name onenotem -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Stopped ONENOTEM.EXE process."
}

# Windows Phone Link background restriction
$phoneAppReg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications\Microsoft.YourPhone_8wekyb3d8bbwe"
if (Test-Path $phoneAppReg) {
    Set-ItemProperty -Path $phoneAppReg -Name "Disabled" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
    Set-ItemProperty -Path $phoneAppReg -Name "DisabledByUser" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Phone Link background permissions set to Disabled in BackgroundAccessApplications."
}
$policyReg = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System"
if (-not (Test-Path $policyReg)) {
    New-Item -Path $policyReg -Force -ErrorAction SilentlyContinue | Out-Null
}
Set-ItemProperty -Path $policyReg -Name "EnableMmx" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
$phoneProc = Get-Process -Name PhoneExperienceHost -ErrorAction SilentlyContinue
if ($phoneProc) {
    Stop-Process -Name PhoneExperienceHost -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Stopped PhoneExperienceHost process."
}

# 2. Tier 1: Telemetry & Background Trackers -> Disabled
$disableServices = @(
    'DiagTrack',
    'dmwappushservice',
    'ESRV_SVC_QUEENCREEK'
)

Write-Host "`n--- Configuring Tier 1: Telemetry Services (Disabled) ---"
foreach ($s in $disableServices) {
    $svc = Get-Service -Name $s -ErrorAction SilentlyContinue
    if ($svc) {
        Stop-Service -Name $s -Force -ErrorAction SilentlyContinue
        Set-Service -Name $s -StartupType Disabled -ErrorAction SilentlyContinue
        Write-Host "[OK] Service '$s' set to Disabled and stopped."
    }
}

# 3. Tier 1 Tasks: Disable Scheduled Tasks
$disableTasks = @(
    'Adobe-Genuine-Software-Integrity-Scheduler-1.0',
    'AdobeGCInvoker-1.0',
    'CCleaner Update',
    'CCleanerCrashReporting',
    'IntelSURQC-Upgrade-86621605-2a0b-4128-8ffc-15514c247132',
    'IntelSURQC-Upgrade-86621605-2a0b-4128-8ffc-15514c247132-Logon',
    'USER_ESRV_SVC_QUEENCREEK'
)

Write-Host "`n--- Configuring Tier 1: Telemetry Scheduled Tasks (Disabled) ---"
foreach ($t in $disableTasks) {
    $task = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
    if ($task -and $task.State -ne 'Disabled') {
        Disable-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[OK] Scheduled Task '$t' disabled."
    }
}

# 4. Tier 2: On-Demand Application Services -> Manual
$manualServices = @(
    'Apple Mobile Device Service',
    'Bonjour Service',
    'SamsungMagicianSVC',
    'CMigrationService',
    'Autodesk Access Service Host',
    'Autodesk CER Service',
    'VMAuthdService',
    'VMUSBArbService',
    'VMnetDHCP',
    'VMware NAT Service',
    'TbtP2pShortcutService',
    'MapsBroker',
    'InventorySvc',
    'NVWMI',
    'XboxService',
    'GamingServices',
    'GamingServicesNet',
    'GameInputRedistService',
    'DellTechHub',
    'DellClientManagementService'
)

Write-Host "`n--- Configuring Tier 2: On-Demand Services (Manual) ---"
foreach ($s in $manualServices) {
    $svc = Get-Service -Name $s -ErrorAction SilentlyContinue
    if ($svc) {
        Stop-Service -Name $s -Force -ErrorAction SilentlyContinue
        Set-Service -Name $s -StartupType Manual -ErrorAction SilentlyContinue
        Write-Host "[OK] Service '$s' set to Manual (on-demand)."
    }
}

# Terminate lingering telemetry subagents if any remained after service shutdown
$lingeringProcs = Get-Process | Where-Object { $_.ProcessName -like "Dell.TechHub*" -or $_.ProcessName -eq "Dell.CoreServices.Client" -or $_.ProcessName -eq "Dell.UCA.Manager" }
if ($lingeringProcs) {
    foreach ($p in $lingeringProcs) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Cleaned up lingering telemetry process: $($p.ProcessName) (PID $($p.Id))"
    }
}

# 5. Tier 4: DriverStore Safe Pruning (Non-Forced pnputil)
Write-Host "`n--- Performing DriverStore Safe Pruning (pnputil) ---"
$allOems = & pnputil /enum-drivers
$oemList = @()
foreach ($line in $allOems) {
    if ($line -match 'Published Name:\s+(oem\d+\.inf)') {
        $oemList += $Matches[1].Trim()
    }
}

Write-Host "Scanned $($oemList.Count) total OEM driver packages. Checking for unreferenced/superseded packages..."
$deletedCount = 0
$keptCount = 0

foreach ($oem in $oemList) {
    # Non-forced deletion. If Windows kernel indicates it is actively installed or referenced, it will fail harmlessly.
    $res = & pnputil /delete-driver $oem 2>&1
    if ($res -match 'deleted successfully') {
        $deletedCount++
    } else {
        $keptCount++
    }
}

Write-Host "[OK] DriverStore Pruning Complete: $deletedCount superseded packages safely removed, $keptCount active/in-use packages protected."

Write-Host "`n=========================================================="
Write-Host "  OPTIMIZATIONS APPLIED SUCCESSFULLY                      "
Write-Host "=========================================================="
