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

When executing or modifying `scripts/setup_rp5.py` and `scripts/provision_all.ps1`, verify the following stages:

| Stage | Action | Verification Command |
|---|---|---|
| **Connectivity** | Confirm device is online and authorized | `adb devices` |
| **Phantom Process** | Disable Android 13 phantom process restrictions | `adb shell "/system/bin/device_config get activity_manager max_phantom_processes"` |
| **Storage Scaffolding** | Create canonical directories | `adb shell "ls -la /sdcard/bios /storage/<SD_ID>"` |
| **Obtainium Staging** | Push `rp5_master_obtainium.json` to `/sdcard/Download/` (Libretro buildbot intermediateLink array for RetroArch) | `adb shell "ls -l /sdcard/Download/rp5_master_obtainium.json"` |
| **ES-DE Pre-Config** | Push `es_settings.xml` configured with MicroSD ROM path & direct ARMSX2 .Main launch | `adb shell "cat /sdcard/ES-DE/settings/es_settings.xml"` |
| **Turnip Drivers** | Stage Mesa Turnip GPU drivers in `/sdcard/Download/drivers/` | `adb shell "ls -la /sdcard/Download/drivers"` |
| **Hardware Tuning** | Lockscreen disabled, overlay hidden, auto-rotate disabled (`accelerometer_rotation 0`), Xbox layout, Both triggers (`persist.sys.trigger.mode 2`) | `adb shell "getprop persist.sys.trigger.mode; settings get system accelerometer_rotation"` |
| **DroidDeck & Steam** | Stage DroidDeck 720p/FSR profile, env overrides, libraryfolders.vdf, and Sony Vita firmware | `adb shell "cat /sdcard/DroidDeck/config.json"` |
| **RetroArch 2D Engine** | Deploy Vulkan, Ozone, 48ms OpenSLES, Genesis Model 1 LPF, GBA 5.5kHz DSP, mGBA LCD grid | `adb shell "ls -la /storage/<SD_ID>/RetroArch/filters/audio"` |
| **2D/Arcade Cores** | Fetch & stage 11 designated cores and frontend assets | `adb shell "ls -la /storage/<SD_ID>/RetroArch/cores"` |
| **Standalone 3D Profiles** | Inject tuned Vulkan/audio profiles into DuckStation, NetherSX2 (16:9 Overscan), ARM SX2 (16:9 Overscan, Disable Readbacks, direct boot), Dolphin (global SIDevice0=6 standard GC controller, WiimoteSource0=1, no broken PadType0 overrides), PPSSPP, Flycast, Azahar, Vita3K (initial-setup: false, Vulkan backend, pref-path) | `adb shell "cat /sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Dolphin.ini"` |
| **Universal Patches** | Stage 4,700+ PS2 pnach cheats & 1,891 curated Dolphin GameSettings with 16:9 Gecko codes | `adb shell "ls /sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings"` |
| **Save Backup Sync** | Mirror saves, savestates, and memory cards to `/storage/<SD_ID>/Saves_Backup/latest/` | `adb shell "ls -la /storage/<SD_ID>/Saves_Backup/latest"` |
| **Permissions** | Grant `MANAGE_EXTERNAL_STORAGE` across all emulators and frontends | `adb shell "appops get <package> MANAGE_EXTERNAL_STORAGE"` |

---

## 5. Emulator Package Reference & Distribution Channels

### A. Google Play Store (Manual install / no standalone GitHub APKs)
- **Dolphin (GameCube / Wii)**: `org.dolphinemu.dolphinemu`
- **DuckStation (PS1)**: `com.github.stenzek.duckstation`
*(Once downloaded from Play Store, re-run setup_rp5.py to apply MANAGE_EXTERNAL_STORAGE AppOps automatically.)*

### B. Tracked via Obtainium (`rp5_master_obtainium.json`) & Staged APKs
- **Obtainium App Updater**: `dev.imranr.obtainium`
- **ES-DE Frontend**: `org.es_de.frontend`
- **RetroArch (64-bit)**: `com.retroarch.aarch64`
- **ARM SX2 (PS2 Primary)**: `com.armsx2`
- **NetherSX2 (PS2 Fallback)**: `xyz.aethersx2.android`
- **PPSSPP (PSP)**: `org.ppsspp.ppsspp`
- **Azahar (3DS)**: `org.azahar_emu.azahar`
- **Vita3K (PS Vita)**: `org.vita3k.emulator`
- **Flycast (Dreamcast)**: `com.flycast.emulator`
- **Daijisho (Frontend)**: `com.magneticchen.daijishou`
- **DroidDeck (Steam Launcher)**: `com.droiddeck.launcher`
- **Additional Frontends / Tools**: `com.magneticstarlight.beacon` (Beacon), `org.mupen64plusae.v3.fzurita` (Mupen64Plus FZ)

---

## 6. Script Invocation

To run the complete zero-touch provisioning pipeline:
```powershell
.\scripts\provision_all.ps1 -Serial ff152647
```
Or directly via Python:
```powershell
python scripts/setup_rp5.py --serial ff152647 --all
```
Options available:
- `--all`: Execute complete community provisioning pipeline (hardware tuning, storage, Obtainium, DroidDeck, Vita firmware, RetroArch low-pass engine, standalone 3D profiles, widescreen patches, and save backup sync).
- `--dry-run`: Preview ADB commands without applying them.
- `--status`: Check device connection and print hardware specs, then exit.
- `--serial <id>` / `-s <id>`: Target a specific device if multiple ADB instances exist.
- `--install-apks`: Install every `.apk` staged in `apks/`.
- `--skip-phantom`: Skip the Phantom Process Killer unlock.
- `--skip-scaffold`: Skip canonical directory scaffolding.
- `--skip-obtainium`: Skip pushing `rp5_master_obtainium.json`.
- `--skip-esde`: Skip staging headless ES-DE `es_settings.xml`.
- `--skip-drivers`: Skip staging Mesa Turnip GPU drivers.
- `--skip-tuning`: Skip Retroid OS hardware & system tuning.
- `--skip-permissions`: Skip the AppOps grants.
- `--adb <path>`: Explicit path to the adb binary.

---

## 7. YouTube Tutorial & Community Research

To extract metadata, chapters, links, and complete timestamped transcripts from YouTube setup guides (e.g., Retro Game Corps, Joey's Retro Handhelds):
```powershell
python scripts/fetch_youtube.py "<url_or_video_id>"
python scripts/fetch_youtube.py "<url_or_video_id>" -o notes/guide.md
```
Powered by `youtube-transcript-api` and `yt-dlp`. Structured skill definition available at `.agents/skills/youtube-research/SKILL.md`.

---

## 8. The 5 Laws of Schema Verification (Anti-Hallucination Guardrails)

To guarantee emulator stability and prevent input or configuration regressions:
1. **Never Guess INI Section Names or Key Syntaxes**: Always inspect Dolphin/emulator source code, upstream documentation, or native UI auto-mappings on the device before writing configurations. Never improvise section headers or property names.
2. **Clean Direct Tokens Under Active Device Sections**: Under an active `Device = <name>` section, bind buttons and axes using clean, direct tokens (e.g., `Button 96`, `Axis 1-`) rather than chained or device-prefixed expressions (e.g. `` `Device:Button 96` | ... ``), which fail to parse in Android UI builds.
3. **Flat Wiimote Extensions**: Dolphin Wiimote extensions (Classic, Nunchuk) live flat inside `[Wiimote1]` using extension prefixes (e.g., `Classic/Buttons/A = `Button 96``, `Nunchuk/Buttons/C = `Button 102``). Dolphin never recognizes standalone sections like `[Classic1]` or `[Wiimote1/Classic]`.
4. **Literal Plus/Minus Keys**: Dolphin keys for Plus and Minus buttons are literally `+` and `-` (e.g., `Buttons/+`, `Classic/Buttons/-`), never `Plus` or `Minus`.
5. **Always Verify with Live Hardware Logs & Screenshots**: Never declare input or emulator configuration complete without verifying via ADB dumps, live logcat output, or screen captures that in-game menus advance and inputs are cleanly captured without drawer/system popups.

