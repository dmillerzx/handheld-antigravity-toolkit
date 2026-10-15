@echo off
setlocal enabledelayedexpansion
title Handheld Community Provisioning Toolkit v1.0

cd /d "%~dp0"

echo ========================================================================
echo       Handheld Community Provisioning Toolkit - Standalone Runner
echo ========================================================================
echo.

:: 1. Check for platform-tools\adb.exe (Auto-download if missing)
if not exist "platform-tools\adb.exe" (
    echo [*] Google Android platform-tools not found locally.
    echo [*] Downloading official Google platform-tools archive...
    powershell -NoProfile -Command ^
        "$ProgressPreference = 'SilentlyContinue';" ^
        "Write-Host '    -> Fetching platform-tools-latest-windows.zip...';" ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
        "Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile 'platform-tools.zip';" ^
        "Write-Host '    -> Extracting archive...';" ^
        "Expand-Archive -Path 'platform-tools.zip' -DestinationPath '.' -Force;" ^
        "Remove-Item -Path 'platform-tools.zip' -Force;"
    if not exist "platform-tools\adb.exe" (
        echo [ERROR] Failed to download or extract platform-tools.
        echo Please manually extract platform-tools into: %~dp0platform-tools
        pause
        exit /b 1
    )
    echo [*] Platform-tools successfully installed.
    echo.
)

set "ADB_BIN=%~dp0platform-tools\adb.exe"

:: 2. Verify ADB Device Connectivity
echo [*] Checking connected Android devices...
"%ADB_BIN%" start-server >nul 2>&1

for /f "tokens=1,2" %%A in ('"%ADB_BIN%" devices ^| findstr /r "^[a-zA-Z0-9]"') do (
    if "%%B"=="device" (
        set "SERIAL=%%A"
        set "STATUS=authorized"
        goto :DeviceFound
    ) else if "%%B"=="unauthorized" (
        set "SERIAL=%%A"
        set "STATUS=unauthorized"
        goto :DeviceFound
    )
)

:DeviceNotFound
echo.
echo ========================================================================
echo  [!] NO ANDROID HANDHELD DETECTED VIA USB OR WI-FI
echo ========================================================================
echo  Troubleshooting:
echo   1. Connect your handheld (RP5, RP Mini, RP4 Pro, Odin 2) via USB-C.
echo   2. On your device, open: Settings -^> System -^> Developer options.
echo   3. Turn ON "USB debugging".
echo   4. When prompted on screen, tap "Always allow from this computer".
echo ========================================================================
echo.
pause
exit /b 1

:DeviceFound
if "!STATUS!"=="unauthorized" (
    echo.
    echo ========================================================================
    echo  [!] DEVICE UNAUTHORIZED: !SERIAL!
    echo  Look at your handheld screen and tap "Always allow from this computer".
    echo ========================================================================
    pause
)

:: 3. Query Device Model
for /f "usebackq delims=" %%M in (`"%ADB_BIN%" -s !SERIAL! shell getprop ro.product.model`) do set "DEVICE_MODEL=%%M"
echo [*] Device Connected : !DEVICE_MODEL! (Serial: !SERIAL!)
echo.

:: 4. Auto-detect Hardware Profile or Present Menu
set "PROFILE="

:: Check if override was provided as CLI argument (%1)
if not "%~1"=="" (
    set "PROFILE=%~1"
    goto :LaunchProvisioner
)

:: Auto-detection heuristics
echo !DEVICE_MODEL! | findstr /i "Pocket.5 RP5" >nul && set "PROFILE=rp5"
if not defined PROFILE (
    echo !DEVICE_MODEL! | findstr /i "Pocket.Mini RPMini" >nul && set "PROFILE=rp_mini"
)
if not defined PROFILE (
    echo !DEVICE_MODEL! | findstr /i "Pocket.4 RP4" >nul && set "PROFILE=rp4_pro"
)
if not defined PROFILE (
    echo !DEVICE_MODEL! | findstr /i "Odin.2 Odin2" >nul && set "PROFILE=odin2"
)

if defined PROFILE (
    echo [*] Automatically matched hardware profile: !PROFILE!
    echo.
    goto :LaunchProvisioner
)

:: If unrecognized, present interactive menu
:ProfileMenu
echo ========================================================================
echo              SELECT HARDWARE PROFILE FOR YOUR HANDHELD
echo ========================================================================
echo   [1] Retroid Pocket 5       (1080p 16:9 AMOLED, Snapdragon 865, Turnip)
echo   [2] Retroid Pocket Mini    (960p 4:3 OLED, Snapdragon 865, Turnip, 4:3)
echo   [3] Retroid Pocket 4 Pro   (720p 16:9 IPS, Dimensity 1100, Mali GPU)
echo   [4] AYN Odin 2             (1080p 16:9 IPS, Snapdragon 8 Gen 2, Turnip)
echo   [5] Generic Android Device (Safe standard baseline, 1080p 16:9)
echo ========================================================================
set /p "CHOICE=Enter choice [1-5] (Default: 1): "
if "!CHOICE!"=="" set "CHOICE=1"

if "!CHOICE!"=="1" set "PROFILE=rp5"
if "!CHOICE!"=="2" set "PROFILE=rp_mini"
if "!CHOICE!"=="3" set "PROFILE=rp4_pro"
if "!CHOICE!"=="4" set "PROFILE=odin2"
if "!CHOICE!"=="5" set "PROFILE=generic"

if not defined PROFILE (
    echo Invalid choice. Please enter 1, 2, 3, 4, or 5.
    goto :ProfileMenu
)

:LaunchProvisioner
echo [*] Active Profile Selected: !PROFILE!
echo [*] Executing master provisioning orchestrator...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\provision_all.ps1" -Serial "!SERIAL!" -Profile "!PROFILE!"

echo.
echo ========================================================================
echo   SETUP EXECUTION COMPLETE
echo ========================================================================
echo   - Emulators configured with optimal Vulkan and low-latency audio.
echo   - MicroSD and internal canonical storage folders scaffolded.
echo   - Steam Big Picture ready via DroidDeck launcher.
echo.
echo   Drop your ROMs into: /storage/^<SD_ID^>/ROMs/ (or /sdcard/ROMs/)
echo   and launch ES-DE on your handheld to begin gaming!
echo ========================================================================
echo.
pause
