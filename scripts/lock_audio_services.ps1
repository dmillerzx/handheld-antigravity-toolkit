# Backward-compatibility shim for scheduled task MaxxAudioShield_AntiDistortion
# Canonical script moved to workstation/scripts/lock_audio_services.ps1
$target = Join-Path $PSScriptRoot "..\workstation\scripts\lock_audio_services.ps1"
if (Test-Path $target) {
    & $target @args
} else {
    Write-Error "Target script not found: $target"
}
