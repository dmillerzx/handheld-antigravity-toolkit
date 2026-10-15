#!/usr/bin/env bash
# ==============================================================================
# Handheld Community Provisioning Toolkit - macOS & Linux Standalone Runner (v1.0)
# Dynamic Profiling • Controller Discovery • Upstream Widescreen • Steam
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "  Handheld Community Provisioning Toolkit - Standalone Runner (v1.0)"
echo "  macOS & Linux Edition • Zero CLI Experience Required"
echo "========================================================================"
echo ""

# 1. Check for Python 3
if ! command -v python3 &>/dev/null; then
    echo "[!] Python 3 was not found on your system."
    echo "    Please install Python 3:"
    echo "      - macOS: brew install python3 (or download from python.org)"
    echo "      - Debian/Ubuntu: sudo apt install python3"
    echo "      - Fedora: sudo dnf install python3"
    echo "      - Arch: sudo pacman -S python"
    exit 1
fi

# 2. Check for ADB / Platform-Tools (Auto-download if missing)
ADB_BIN=""
if [ -f "$SCRIPT_DIR/platform-tools/adb" ]; then
    ADB_BIN="$SCRIPT_DIR/platform-tools/adb"
    chmod +x "$ADB_BIN"
elif command -v adb &>/dev/null; then
    ADB_BIN="$(command -v adb)"
else
    echo "[*] Google Android platform-tools not found locally."
    OS_TYPE="$(uname -s)"
    DL_URL=""
    if [ "$OS_TYPE" = "Darwin" ]; then
        echo "[*] Detected macOS. Downloading official Google platform-tools for Darwin..."
        DL_URL="https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
    else
        echo "[*] Detected Linux. Downloading official Google platform-tools for Linux..."
        DL_URL="https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
    fi

    if command -v curl &>/dev/null; then
        curl -fsSL -o platform-tools.zip "$DL_URL"
    elif command -v wget &>/dev/null; then
        wget -q -O platform-tools.zip "$DL_URL"
    else
        echo "[ERROR] Neither curl nor wget was found. Please install one to auto-download adb."
        exit 1
    fi

    unzip -q platform-tools.zip
    rm -f platform-tools.zip
    ADB_BIN="$SCRIPT_DIR/platform-tools/adb"
    chmod +x "$ADB_BIN"
    echo "[*] Platform-tools successfully installed."
    echo ""
fi

# 3. Verify Android Handheld Connection
echo "[*] Checking connected Android devices..."
"$ADB_BIN" start-server >/dev/null 2>&1

DEVICES_OUTPUT="$("$ADB_BIN" devices | grep -E '^[a-zA-Z0-9]+' || true)"

if [ -z "$DEVICES_OUTPUT" ]; then
    echo ""
    echo "========================================================================"
    echo "  [!] NO ANDROID HANDHELD DETECTED VIA USB"
    echo "========================================================================"
    echo "  Troubleshooting Steps:"
    echo "   1. Connect your handheld (RP5, RP Mini, RP4 Pro, Odin 2) via USB-C."
    echo "   2. On your device, open: Settings -> System -> Developer options."
    echo "   3. Turn ON 'USB debugging'."
    echo "   4. When prompted on screen, tap 'Always allow from this computer'."
    echo "========================================================================"
    echo ""
    exit 1
fi

SERIAL="$(echo "$DEVICES_OUTPUT" | head -n1 | awk '{print $1}')"
STATUS="$(echo "$DEVICES_OUTPUT" | head -n1 | awk '{print $2}')"

if [ "$STATUS" = "unauthorized" ]; then
    echo ""
    echo "========================================================================"
    echo "  [!] DEVICE UNAUTHORIZED: $SERIAL"
    echo "  Look at your handheld screen and tap 'Always allow from this computer'."
    echo "========================================================================"
    read -rp "Press [Enter] after tapping Allow on the device screen..."
fi

# 4. Query Device Model
DEVICE_MODEL="$("$ADB_BIN" -s "$SERIAL" shell getprop ro.product.model | tr -d '\r')"
echo "[*] Device Connected : $DEVICE_MODEL (Serial: $SERIAL)"
echo ""

# 5. Auto-detect Hardware Profile or Present Menu
PROFILE="${1:-}"

if [ -z "$PROFILE" ]; then
    case "$DEVICE_MODEL" in
        *Pocket*5*|*RP5*)
            PROFILE="rp5"
            ;;
        *Pocket*Mini*|*RPMini*)
            PROFILE="rp_mini"
            ;;
        *Pocket*4*|*RP4*)
            PROFILE="rp4_pro"
            ;;
        *Odin*2*|*Odin2*)
            PROFILE="odin2"
            ;;
    esac
fi

if [ -n "$PROFILE" ]; then
    echo "[*] Automatically matched hardware profile: $PROFILE"
    echo ""
else
    echo "========================================================================"
    echo "              SELECT HARDWARE PROFILE FOR YOUR HANDHELD"
    echo "========================================================================"
    echo "  [1] Retroid Pocket 5       (1080p 16:9 AMOLED, Snapdragon 865, Turnip)"
    echo "  [2] Retroid Pocket Mini    (960p 4:3 OLED, Snapdragon 865, Turnip, 4:3)"
    echo "  [3] Retroid Pocket 4 Pro   (720p 16:9 IPS, Dimensity 1100, Mali GPU)"
    echo "  [4] AYN Odin 2             (1080p 16:9 IPS, Snapdragon 8 Gen 2, Turnip)"
    echo "  [5] Generic Android Device (Safe standard baseline, 1080p 16:9)"
    echo "========================================================================"
    read -rp "Enter choice [1-5] (Default: 1): " CHOICE
    CHOICE="${CHOICE:-1}"
    case "$CHOICE" in
        1) PROFILE="rp5" ;;
        2) PROFILE="rp_mini" ;;
        3) PROFILE="rp4_pro" ;;
        4) PROFILE="odin2" ;;
        5) PROFILE="generic" ;;
        *) PROFILE="rp5" ;;
    esac
fi

echo "[*] Active Profile Selected: $PROFILE"
echo "[*] Executing master provisioning pipeline via Python 3..."
echo ""

python3 "$SCRIPT_DIR/scripts/setup_rp5.py" --serial "$SERIAL" --profile "$PROFILE" --all

echo ""
echo "========================================================================"
echo "  SETUP EXECUTION COMPLETE - v1.0 BASELINE"
echo "========================================================================"
echo "  [OK] Hardware Profile Applied   : $PROFILE"
echo "  [OK] Controller Auto-Bound      : Dynamic input node discovery (Dolphin GC/Classic & PS2)"
echo "  [OK] Dolphin Safety Hotkeys     : L3 + R3 toggle pause (Button B back-action isolated)"
echo "  [OK] Dolphin Core Enhancements  : Panic handlers suppressed, NTSC fallback forced"
echo "  [OK] PS2 Dual-Engine Support    : ARM SX2 (Primary) & NetherSX2 (Fallback) + CRT Overscan Crop"
echo "  [OK] Upstream Community Patches : Streamed live (Gecko widescreen & PCSX2 pnach)"
echo "  [OK] 2D Low-Latency Audio/Video : Vulkan, 48ms OpenSLES, GBA DSP, Genesis LPF"
echo "  [OK] RetroArch Community Polish : Instant hotkey quit, 10-state safety buffer, overlay disabled"
echo "  [OK] Handheld Hardware Tuning   : Do Not Disturb, auto-rotation locked, dark theme, click sounds muted"
echo "  [OK] Canonical Storage Ready    : Internal /sdcard/ and MicroSD /storage/<SD_ID>/"
echo "  [OK] Steam PC Gaming Ready      : 720p FSR, DroidDeck & MicroSD secondary library"
echo ""
echo "  Drop your ROMs into: /storage/<SD_ID>/ROMs/<system>/ on your MicroSD card"
echo "  and launch ES-DE on your handheld to begin gaming!"
echo "========================================================================"
