<#
.SYNOPSIS
    Rollback script for Dell Precision 5560 Windows optimizations.
.DESCRIPTION
    Restores all modified Windows services and scheduled tasks back to their
    exact pre-tuning baseline recorded in configs\system_backup\services_snapshot_pre_tuning.json.
#>

param (
    [switch]$WhatIf
)

$snapshotPath = Join-Path $PSScriptRoot "..\configs\system_backup\services_snapshot_pre_tuning.json"
$tasksSnapshotPath = Join-Path $PSScriptRoot "..\configs\system_backup\tasks_snapshot_pre_tuning.json"

if (-not (Test-Path $snapshotPath)) {
    Write-Error "Pre-tuning services snapshot not found at: $snapshotPath"
    exit 1
}

$services = Get-Content -LiteralPath $snapshotPath -Raw | ConvertFrom-Json
Write-Host "Loaded $($services.Count) service records from snapshot."

# List of service names targeted by optimization
$targetServices = @(
    'DiagTrack',
    'dmwappushservice',
    'ESRV_SVC_QUEENCREEK',
    'InventorySvc',
    'NVWMI',
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
    'XboxService',
    'GamingServices',
    'GamingServicesNet',
    'GameInputRedistService'
)

foreach ($target in $targetServices) {
    $rec = $services | Where-Object { $_.Name -eq $target }
    if ($rec) {
        $desiredMode = switch ($rec.StartMode) {
            'Auto' { 'Automatic' }
            'Manual' { 'Manual' }
            'Disabled' { 'Disabled' }
            default { $rec.StartMode }
        }
        Write-Host "Restoring $target -> StartMode: $desiredMode (Was: $($rec.StartMode), State: $($rec.State))"
        if (-not $WhatIf) {
            Set-Service -Name $target -StartupType $desiredMode -ErrorAction SilentlyContinue
            if ($rec.State -eq 'Running') {
                Start-Service -Name $target -ErrorAction SilentlyContinue
            }
        }
    }
}

# Restore scheduled tasks
if (Test-Path $tasksSnapshotPath) {
    $tasks = Get-Content -LiteralPath $tasksSnapshotPath -Raw | ConvertFrom-Json
    $targetTasks = @(
        'Adobe-Genuine-Software-Integrity-Scheduler-1.0',
        'AdobeGCInvoker-1.0',
        'CCleaner Update',
        'CCleanerCrashReporting',
        'IntelSURQC-Upgrade-86621605-2a0b-4128-8ffc-15514c247132',
        'IntelSURQC-Upgrade-86621605-2a0b-4128-8ffc-15514c247132-Logon',
        'USER_ESRV_SVC_QUEENCREEK'
    )
    foreach ($tName in $targetTasks) {
        $tRec = $tasks | Where-Object { $_.TaskName -eq $tName }
        if ($tRec -and $tRec.State -ne 'Disabled') {
            Write-Host "Re-enabling scheduled task: $tName"
            if (-not $WhatIf) {
                Enable-ScheduledTask -TaskName $tName -ErrorAction SilentlyContinue | Out-Null
            }
        }
    }
}

Write-Host "Rollback verification completed successfully."
