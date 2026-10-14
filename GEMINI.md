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
- When running commands in Windows PowerShell where PATH might not be reloaded in inherited subprocesses, ensure ADB and Python are referenced cleanly using environment refreshes or absolute fallbacks.

---

## 3. Provisioning Checklist

When executing or modifying `scripts/setup_rp5.py`, verify the following stages:

| Stage | Action | Verification Command |
|---|---|---|
| **Connectivity** | Confirm device is online and authorized | `adb devices` |
| **Phantom Process** | Disable Android 13 phantom process restrictions | `adb shell "/system/bin/device_config get activity_manager max_phantom_processes"` |
| **Storage Scaffolding** | Create directories on `/sdcard` and `/storage/*` | `adb shell "ls -la /sdcard/Emulation"` |
| **Obtainium Staging** | Push `rp5_master_obtainium.json` to `/sdcard/Download/` | `adb shell "ls -l /sdcard/Download/rp5_master_obtainium.json"` |
| **Permissions** | Grant `MANAGE_EXTERNAL_STORAGE` AppOps | `adb shell "appops get <package> MANAGE_EXTERNAL_STORAGE"` |

---

## 4. Emulator Package Reference

Key emulator packages targeted by this workspace:

- **Obtainium**: `dev.imranr.obtainium`
- **RetroArch**: `com.retroarch` / `com.retroarch.aarch64`
- **Dolphin (GameCube / Wii)**: `org.dolphinemu.dolphinemu`
- **AetherSX2 / NetherSX2 (PS2)**: `xyz.aethersx2.android`
- **DuckStation (PS1)**: `com.github.stenzek.duckstation`
- **PPSSPP (PSP)**: `org.ppsspp.ppsspp` / `org.ppsspp.ppssppgold`
- **Mupen64Plus FZ (N64)**: `org.mupen64plusae.v3.fzurita` / `org.mupen64plusae.v3.fzurita.pro`
- **Citra / Lime3DS (3DS)**: `io.github.lime3ds` / `org.citra.emu`
- **Vita3K (PS Vita)**: `org.vita3k.emulator`
- **Flycast (Dreamcast)**: `com.flyinghead.flycast`
- **Frontends**: `me.quack.daijisho` (Daijisho), `org.es_de.frontend` (ES-DE), `com.magneticstarlight.beacon` (Beacon)

---

## 5. Script Invocation

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
- `--skip-sync`: Skip pushing ROMs/BIOS/Obtainium files.
- `--skip-permissions`: Skip AppOps storage grant.
- `--serial <id>`: Target a specific device if multiple ADB instances exist.
