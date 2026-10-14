# GEMINI.md — Gemini Directives for Retroid Pocket 5 Automation

This file provides system context and operational instructions for Google Gemini models interacting with this Retroid Pocket 5 (RP5) workspace.

---

## 1. Persona & Context

You are assisting with the automated provisioning and maintenance of a **Retroid Pocket 5** retro gaming handheld running **Android 13** on the **Snapdragon 865** chipset.

Your primary interface to the device is **ADB (Android Debug Bridge)** over USB or local Wi-Fi pairing.

---

## 2. Environment Invariants

- **Workspace Root**: `C:\Users\dmill\Documents\AntigravityWorkingDir`
- **Local Platform Tools**: `C:\Users\dmill\Documents\AntigravityWorkingDir\platform-tools\adb.exe`
- **Installed Python**: `C:\Users\dmill\AppData\Local\Programs\Python\Python312\python.exe`
- **Git Binary**: `C:\Program Files\Git\cmd\git.exe`
- **RP5 serial**: `ff152647` (a second device, the Konkr Pocket Advance, may also be attached - always use `adb -s <serial>`)
- When running commands in Windows PowerShell where PATH might not be reloaded in inherited subprocesses, ensure ADB and Python are referenced cleanly using environment refreshes or absolute fallbacks.

---

## 3. CANONICAL STORAGE LAYOUT (STRICT - DO NOT DEVIATE)

```text
Internal storage   /sdcard/bios
MicroSD            /storage/<SD_ID>/bios
                   /storage/<SD_ID>/ROMs
                   /storage/<SD_ID>/ES-DE
```

**Forbidden - never create, push to, or document these on the device:**

- `Games/`, `Games/BIOS`, `BIOS/`, `Bios/`
- `roms/` (lower-case), `Emulation/`, `Emulation/roms`, `Emulation/bios`
- `/sdcard/ROMs`, `/sdcard/roms`, `/sdcard/Emulation` (no ROM directories on internal storage)
- Any other new top-level directory on `/storage/<SD_ID>/` besides `bios`, `ROMs`, `ES-DE`

If a task seems to require a different path, stop and ask the user instead of creating a new folder variant. `AGENTS.md` Section 2 is the source of truth.

---

## 4. Provisioning Checklist

When executing or modifying `scripts/setup_rp5.py`, verify the following stages:

| Stage | Action | Verification Command |
|---|---|---|
| **Connectivity** | Confirm device is online and authorized | `adb devices` |
| **Phantom Process** | Disable Android 13 phantom process restrictions | `adb shell "/system/bin/device_config get activity_manager max_phantom_processes"` |
| **Storage Scaffolding** | Create the canonical directories only | `adb shell "ls -la /sdcard/bios /storage/<SD_ID>"` |
| **Obtainium Staging** | Push `rp5_master_obtainium.json` to `/sdcard/Download/` | `adb shell "ls -l /sdcard/Download/rp5_master_obtainium.json"` |
| **APK Install** | Install staged APKs from `apks/` | `adb shell "pm list packages \| grep -E 'obtainium\|es_de'"` |
| **Permissions** | Grant `MANAGE_EXTERNAL_STORAGE` (all targets) and `REQUEST_INSTALL_PACKAGES` (Obtainium) AppOps | `adb shell "appops get <package> MANAGE_EXTERNAL_STORAGE"` |

---

## 5. Emulator Package Reference & Distribution Channels

### A. Google Play Store (Manual install / no standalone GitHub APKs)
- **Dolphin (GameCube / Wii)**: `org.dolphinemu.dolphinemu`
- **DuckStation (PS1)**: `com.github.stenzek.duckstation`
*(Once downloaded from Play Store, re-run setup_rp5.py to apply MANAGE_EXTERNAL_STORAGE AppOps automatically.)*

### B. Tracked via Obtainium (`rp5_master_obtainium.json`)
- **Obtainium App Updater**: `dev.imranr.obtainium`
- **ES-DE Frontend**: `org.es_de.frontend`
- **RetroArch (64-bit)**: `com.retroarch.aarch64`
- **NetherSX2 (PS2)**: `xyz.aethersx2.android`
- **PPSSPP (PSP)**: `org.ppsspp.ppsspp`
- **Azahar (3DS)**: `org.azahar_emu.azahar`
- **Vita3K (PS Vita)**: `org.vita3k.emulator`
- **Flycast (Dreamcast)**: `com.flycast.emulator`
- **Daijisho (Frontend)**: `com.magneticchen.daijishou`
- **Additional Frontends / Tools**: `com.magneticstarlight.beacon` (Beacon), `org.mupen64plusae.v3.fzurita` (Mupen64Plus FZ)

---

## 6. Script Invocation

To run the provisioning pipeline:
```powershell
python scripts/setup_rp5.py
```
Or via the PowerShell launcher:
```powershell
.\scripts\run_setup.ps1
```
Options available:
- `--dry-run`: Preview ADB commands without applying them.
- `--status`: Check device connection and print hardware specs, then exit.
- `--serial <id>` / `-s <id>`: Target a specific device if multiple ADB instances exist.
- `--install-apks`: Install every `.apk` staged in `apks/` (runs before the AppOps step).
- `--skip-phantom`: Skip the Phantom Process Killer unlock.
- `--skip-scaffold`: Skip canonical directory scaffolding.
- `--skip-obtainium`: Skip pushing `rp5_master_obtainium.json`.
- `--skip-permissions`: Skip the AppOps grants.
- `--adb <path>`: Explicit path to the adb binary.
