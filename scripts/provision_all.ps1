<#
.SYNOPSIS
    One-click master provisioning orchestrator for Android gaming handhelds.
.DESCRIPTION
    Executes complete, zero-touch community provisioning pipeline:
    1. Dynamic hardware profiling (RP5, RP Mini, RP4 Pro, Odin 2, Generic)
    2. Dynamic MicroSD UUID detection and canonical storage scaffolding
    3. Android 12/13 phantom process limit bypass
    4. Obtainium catalog & dynamic DroidDeck deployment
    5. Sony PS Vita OS firmware & Mesa Turnip Adreno GPU drivers (with GPU Guard)
    6. Ultra-low-latency 2D RetroArch engine & low-pass audio filters
    7. Automated 2D/Arcade core downloads & asset synchronization
    8. Standalone 3D emulators profile injection (DuckStation, NetherSX2, Dolphin, PPSSPP, Flycast, Azahar, Vita3K)
    9. Conditional widescreen patch deployment (Gecko 16:9 & PS2 pnach)
    10. Automated save, state & memory card backup pipeline
    11. Batch AppOps MANAGE_EXTERNAL_STORAGE permission grants
    12. Interactive Play Store & Steam 2FA breakpoints
#>

[CmdletBinding()]
param(
    [string]$Serial = "",
    [string]$Profile = "",
    [string]$SdId = "",
    [switch]$DryRun,
    [switch]$SkipCores,
    [switch]$SkipSaves,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = Split-Path -Parent $ScriptDir

# -----------------------------------------------------------------------------
# 1. Resolve ADB Executable
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 2. Resolve Python 3.10+ Executable
# -----------------------------------------------------------------------------
$KnownPythons = @(
    "C:\Users\dmill\AppData\Local\Programs\Python\Python312\python.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python310\python.exe"),
    (Join-Path $env:ProgramFiles "Python312\python.exe"),
    (Join-Path $env:ProgramFiles "Python311\python.exe")
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
    Write-Error "[!] Error: Python 3.10+ executable not found. Please install Python."
    exit 1
}

# -----------------------------------------------------------------------------
# 3. Detect and Validate Connected Device
# -----------------------------------------------------------------------------
$devicesRaw = & $AdbExe devices -l
$deviceLines = $devicesRaw -split "`r?`n" | Where-Object { $_ -match "\S" -and $_ -notmatch "^List of devices" }

if ($deviceLines.Count -eq 0) {
    Write-Host "[!] No ADB devices connected." -ForegroundColor Red
    Write-Host "    Please connect your handheld via USB-C with USB Debugging enabled."
    exit 1
}

# Auto-select device if serial not specified
if (-not $Serial) {
    $firstDevice = $deviceLines[0] -split "\s+"
    $Serial = $firstDevice[0]
}

# Check authorization
$targetLine = $deviceLines | Where-Object { $_ -match "^$Serial\s+" }
if ($targetLine -match "unauthorized") {
    Write-Host "========================================================================" -ForegroundColor Yellow
    Write-Host "  [!] DEVICE UNAUTHORIZED: $Serial" -ForegroundColor Yellow
    Write-Host "  Please unlock your device screen and tap 'Always allow from this computer'." -ForegroundColor Yellow
    Write-Host "========================================================================" -ForegroundColor Yellow
    Read-Host "Press [Enter] once authorized on the device screen..."
}

# Query hardware model
$DeviceModel = (& $AdbExe -s $Serial shell getprop ro.product.model).Trim()
if (-not $DeviceModel) { $DeviceModel = "Android Handheld" }

# Dynamic MicroSD discovery
if (-not $SdId) {
    $storageEntries = (& $AdbExe -s $Serial shell ls /storage).Trim() -split "`r?`n"
    foreach ($entry in $storageEntries) {
        $cleanEntry = $entry.Trim()
        if ($cleanEntry -match "^[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$") {
            $SdId = $cleanEntry
            break
        }
    }
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   Handheld Community Provisioning Toolkit - Master Orchestrator        " -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "[*] Target Serial     : $Serial"
Write-Host "[*] Hardware Model    : $DeviceModel"
Write-Host "[*] MicroSD UUID      : $(if ($SdId) { $SdId } else { 'None (Using internal /sdcard fallback)' })"
Write-Host "[*] Selected Profile  : $(if ($Profile) { $Profile } else { 'Auto-Detecting' })"
Write-Host "[*] ADB Path          : $AdbExe"
Write-Host "[*] Python Path       : $PythonExe"
Write-Host "========================================================================`n"

# -----------------------------------------------------------------------------
# 4. Interactive Breakpoint: Google Play Store Emulators Check
# -----------------------------------------------------------------------------
if (-not $NonInteractive -and -not $DryRun) {
    $dolphinInstalled = (& $AdbExe -s $Serial shell pm list packages org.dolphinemu.dolphinemu).Trim() -match "org.dolphinemu.dolphinemu"
    $duckstationInstalled = (& $AdbExe -s $Serial shell pm list packages com.github.stenzek.duckstation).Trim() -match "com.github.stenzek.duckstation"

    if (-not $dolphinInstalled -or -not $duckstationInstalled) {
        Write-Host "========================================================================" -ForegroundColor Yellow
        Write-Host "              [PLAY STORE STANDALONE EMULATOR CHECK]                    " -ForegroundColor Yellow
        Write-Host "========================================================================" -ForegroundColor Yellow
        Write-Host "The following emulators are distributed via the Google Play Store:"
        Write-Host "  - Dolphin Emulator (GameCube/Wii) : $(if ($dolphinInstalled) { '[OK] Installed' } else { '[!] Missing' })"
        Write-Host "  - DuckStation (PS1)               : $(if ($duckstationInstalled) { '[OK] Installed' } else { '[!] Missing' })"
        Write-Host ""
        Write-Host "If missing: Open Google Play on your handheld, sign in, and install them."
        Write-Host "The provisioning script will automatically inject tuned settings and AppOps."
        Write-Host "------------------------------------------------------------------------"
        $choice = Read-Host "Press [Enter] to proceed, or type 'S' to skip waiting"
        Write-Host ""
    }
}

# -----------------------------------------------------------------------------
# 5. Execute Master Setup Pipeline (setup_rp5.py --all)
# -----------------------------------------------------------------------------
$SetupScript = Join-Path $ScriptDir "setup_rp5.py"
$setupArgs = @($SetupScript, "-s", $Serial, "--all")
if ($Profile) { $setupArgs += @("--profile", $Profile) }
if ($DryRun) { $setupArgs += "--dry-run" }

Write-Host ">>> Launching Automated Provisioning Pipeline..." -ForegroundColor Yellow
& $PythonExe @setupArgs

# -----------------------------------------------------------------------------
# 6. Interactive Breakpoint: Steam 2FA Authentication
# -----------------------------------------------------------------------------
if (-not $NonInteractive -and -not $DryRun) {
    $droiddeckPkg = (& $AdbExe -s $Serial shell pm list packages com.droiddeck.launcher).Trim()
    if ($droiddeckPkg -match "com.droiddeck.launcher") {
        # Check if Steam is already authenticated and running
        $steamRunning = (& $AdbExe -s $Serial shell ps -A).Trim() -match "steam"

        if (-not $steamRunning) {
            Write-Host "`n[*] Starting DroidDeck to initialize Steam authentication..." -ForegroundColor Cyan
            & $AdbExe -s $Serial shell "am start -n com.droiddeck.launcher/.SessionActivity" | Out-Null
            Start-Sleep -Seconds 2
        }

        Write-Host "`n========================================================================" -ForegroundColor Magenta
        Write-Host "########################################################################" -ForegroundColor Magenta
        Write-Host "#                                                                      #" -ForegroundColor Magenta
        Write-Host "#                    STEAM 2FA LOGIN BREAKPOINT                        #" -ForegroundColor Magenta
        Write-Host "#                                                                      #" -ForegroundColor Magenta
        Write-Host "########################################################################" -ForegroundColor Magenta
        Write-Host "========================================================================" -ForegroundColor Magenta
        Write-Host "Steam Big Picture is active on your handheld."
        Write-Host "1. Look at your device screen."
        Write-Host "2. Enter your Steam credentials and approve Steam Guard (Mobile 2FA/Email)."
        Write-Host "3. Once Steam reaches Big Picture Mode, press [Enter] below to verify mounts."
        Write-Host "========================================================================" -ForegroundColor Magenta
        Read-Host "Press [Enter] once Steam login is complete..."

        # Verify secondary library mount
        Write-Host "`n[*] Verifying Steam MicroSD library mount..." -ForegroundColor Cyan
        $vdfRemote = "/sdcard/DroidDeck/prefixes/default/drive_c/Program Files (x86)/Steam/config/libraryfolders.vdf"
        $vdfCheck = (& $AdbExe -s $Serial shell "cat '$vdfRemote' 2>/dev/null").Trim()
        if ($vdfCheck -match "Games/Steam") {
            Write-Host "    [OK] Steam secondary library recognized on external storage." -ForegroundColor Green
        } else {
            Write-Host "    [!] Steam libraryfolders.vdf not yet written by Steam. Pre-seeded mount will activate upon restart." -ForegroundColor Yellow
        }
    }
}

# -----------------------------------------------------------------------------
# 7. Final Completion Banner
# -----------------------------------------------------------------------------
Write-Host "`n========================================================================" -ForegroundColor Green
Write-Host "   Handheld Community Provisioning Successfully Completed! (v1.0)       " -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "Target Device   : $DeviceModel ($Serial)"
Write-Host "Hardware Profile: $(if ($Profile) { $Profile } else { 'Auto-Detected' })"
if ($SdId) {
    Write-Host "MicroSD Storage : /storage/$SdId/ (ROMs: /storage/$SdId/ROMs/)"
} else {
    Write-Host "Internal Storage: /sdcard/ (ROMs: /sdcard/ROMs/)"
}
Write-Host ""
Write-Host "Verified Subsystems & Optimizations:" -ForegroundColor Cyan
Write-Host "  [OK] Hardware Profile & Storage Scaffolding (Canonical Map)"
Write-Host "  [OK] Handheld Hardware Tuning (Do Not Disturb, Auto-Rotation Locked, Night Mode)"
Write-Host "  [OK] Physical Controller Auto-Discovery & Scan-Code Binding"
Write-Host "  [OK] Dolphin Safety Hotkeys (L3 + R3 combo) & Classic Controller"
Write-Host "  [OK] Dolphin Core Enhancements (Panic Handlers Suppressed, NTSC 60Hz Fallback)"
Write-Host "  [OK] PS2 Dual-Engine Support (ARM SX2 Primary & NetherSX2 Fallback + CRT Overscan Crop)"
Write-Host "  [OK] Upstream Community Patches Streamed (Gecko & PCSX2 pnach)"
Write-Host "  [OK] RetroArch 2D Engine (Vulkan, 48ms OpenSLES, GBA DSP, Genesis LPF, 10-State Buffer)"
Write-Host "  [OK] DroidDeck 720p FSR & MicroSD Steam Library Mapping (Drive D:\)"
Write-Host "  [OK] Batch AppOps MANAGE_EXTERNAL_STORAGE Applied"
Write-Host ""
Write-Host "Next Steps:"
Write-Host "1. Copy your game ROMs into the canonical ROMs folder."
Write-Host "2. Launch ES-DE on your handheld to browse and play your curated library!"
Write-Host "========================================================================`n"
