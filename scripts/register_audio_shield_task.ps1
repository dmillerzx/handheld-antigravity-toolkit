# Register MaxxAudio Shield Scheduled Task to run automatically on system boot and logon

$taskName = "MaxxAudioShield_AntiDistortion"
$scriptPath = Join-Path $PSScriptRoot "lock_audio_services.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""
$triggerBoot = New-ScheduledTaskTrigger -AtStartup
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($triggerBoot, $triggerLogon) -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "Scheduled task '$taskName' successfully registered to run at startup and logon as SYSTEM."
