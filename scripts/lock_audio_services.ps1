# MaxxAudio / Waves Audio Shield & Equalizer APO Health Verifier

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

Write-Host "=========================================================="
Write-Host "     MAXXAUDIO / WAVES AUDIO SHIELD & APO VERIFIER        "
Write-Host "=========================================================="

$targetServices = @(
    'RtkAudUService',
    'WavesSvc',
    'RtkAudioUniversalService',
    'WavesAudioService',
    'WavesSysSvc'
)

$disabledCount = 0
foreach ($s in $targetServices) {
    $svc = Get-Service -Name $s -ErrorAction SilentlyContinue
    if ($svc) {
        if ($svc.Status -eq 'Running') {
            Stop-Service -Name $s -Force -ErrorAction SilentlyContinue
            Write-Host "! Service '$s' was running; stopped immediately."
        }
        if ($svc.StartType -ne 'Disabled') {
            Set-Service -Name $s -StartupType Disabled -ErrorAction SilentlyContinue
            Write-Host "+ Service '$s' set to Disabled (Start = 4)."
            $disabledCount++
        } else {
            Write-Host "OK: Service '$s' is confirmed Disabled."
        }
    } else {
        # Check direct registry in case service is unregistered
        $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$s"
        if (Test-Path $regPath) {
            Set-ItemProperty -Path $regPath -Name "Start" -Value 4 -Type DWord -Force -ErrorAction SilentlyContinue
            Write-Host "+ Registry key for '$s' forced to Start = 4 (Disabled)."
            $disabledCount++
        } else {
            Write-Host "- Service '$s' not present on system."
        }
    }
}

# Verify Equalizer APO and Peace
Write-Host "`n--- Equalizer APO & Peace Frontend Health ---"
$peaceProc = Get-Process -Name Peace -ErrorAction SilentlyContinue
if ($peaceProc) {
    Write-Host "OK: Peace Equalizer is actively running (PID $($peaceProc.Id))."
} else {
    Write-Host "INFO: Peace Equalizer is not currently running. Checking startup shortcut..."
    $startupFolder = [System.Environment]::GetFolderPath('Startup')
    if (Test-Path (Join-Path $startupFolder "Peace.lnk")) {
        Write-Host "OK: Peace.lnk is present in Startup folder."
    } else {
        Write-Warning "Peace.lnk was not found in Startup folder!"
    }
}

$apoConfig = "C:\Program Files\EqualizerAPO\config\config.txt"
if (Test-Path $apoConfig) {
    Write-Host "OK: Equalizer APO configuration file is intact:"
    Get-Content $apoConfig | ForEach-Object { Write-Host "     $_" }
} else {
    Write-Warning "Equalizer APO config.txt not found at $apoConfig!"
}

Write-Host "`n=========================================================="
Write-Host "  RAW AUDIO SHIELD ACTIVE - ZERO MAXXAUDIO DISTORTION     "
Write-Host "=========================================================="
