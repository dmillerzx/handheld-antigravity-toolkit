<#
.SYNOPSIS
    One-click master provisioning orchestrator for Retroid Pocket 5 (RP5).
.DESCRIPTION
    Executes complete, zero-touch community provisioning pipeline for RP5:
    1. Retroid hardware profiles & trigger mode (Both: Analog + Digital click)
    2. Android 13 phantom process limit unlock
    3. Canonical storage layout scaffolding
    4. Obtainium catalog & DroidDeck deployment
    5. Sony PS Vita OS firmware (PSP2UPDAT.PUP) & Mesa Turnip Adreno 650 GPU drivers
    6. Ultra-low-latency 2D RetroArch engine & low-pass audio filters (Genesis Model 1, GBA 5.5kHz DSP, mGBA shaders)
    7. Automated 2D/Arcade core downloads & asset synchronization
    8. Standalone 3D emulators configuration (DuckStation, NetherSX2, Dolphin, PPSSPP, Flycast, Azahar, Vita3K)
    9. Widescreen patches (GCN Gecko, PS2 pnach) & ES-DE alternative emulator routing
    10. Automated save, state & memory card backup pipeline
    11. AppOps MANAGE_EXTERNAL_STORAGE permission grants across all emulators
#>

[CmdletBinding()]
param(
    [string]$Serial = "ff152647",
    [string]$SdId = "EEEF-F762",
    [switch]$DryRun,
    [switch]$SkipCores,
    [switch]$SkipSaves
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = Split-Path -Parent $ScriptDir

# 1. Resolve ADB
$PlatformTools = Join-Path $WorkspaceRoot "platform-tools"
if ((Test-Path $PlatformTools) -and ($env:Path -notlike "*$PlatformTools*")) {
    $env:Path = "$PlatformTools;$env:Path"
}

$AdbExe = Join-Path $PlatformTools "adb.exe"
if (-not (Test-Path $AdbExe)) {
    $AdbExe = (Get-Command adb -ErrorAction SilentlyContinue).Source
}

if (-not $AdbExe) {
    Write-Error "[!] Error: adb executable not found in platform-tools or PATH."
    exit 1
}

# 2. Resolve Python 3.12+
$KnownPythons = @(
    "C:\Users\dmill\AppData\Local\Programs\Python\Python312\python.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
    (Join-Path $env:ProgramFiles "Python312\python.exe")
)

$PythonExe = $null
foreach ($cand in $KnownPythons) {
    if (Test-Path $cand) {
        $PythonExe = $cand
        break
    }
}

if (-not $PythonExe) {
    $cmdPy = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($cmdPy -and ($cmdPy -notmatch "WindowsApps")) {
        $PythonExe = $cmdPy
    }
}

if (-not $PythonExe) {
    Write-Error "[!] Error: Python 3.12 executable not found."
    exit 1
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   Retroid Pocket 5 (RP5) - Complete Community Master Provisioner       " -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "[*] Target Serial : $Serial"
Write-Host "[*] MicroSD UUID  : $SdId"
Write-Host "[*] ADB Path      : $AdbExe"
Write-Host "[*] Python Path   : $PythonExe"

# Verify device connectivity
$devicesOut = & $AdbExe devices
if ($devicesOut -notmatch "$Serial\s+device") {
    Write-Warning "[!] Device $Serial is not authorized or not connected."
    Write-Host "    Current devices status:"
    Write-Host $devicesOut
    exit 1
}

# Execute Master Setup Script with --all
$SetupScript = Join-Path $ScriptDir "setup_rp5.py"
$setupArgs = @($SetupScript, "-s", $Serial, "--all")
if ($DryRun) { $setupArgs += "--dry-run" }

Write-Host "`n>>> Running Master Provisioning Pipeline (setup_rp5.py --all)..." -ForegroundColor Yellow
& $PythonExe @setupArgs

Write-Host "`n========================================================================" -ForegroundColor Green
Write-Host "   RP5 Community Provisioning Successfully Completed!                  " -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "Your Retroid Pocket 5 is fully configured and ready for gaming."
Write-Host "Next step: Copy your game ROMs into /storage/$SdId/ROMs/ and launch ES-DE!"
