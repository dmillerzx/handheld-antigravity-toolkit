# AGENTS.md — Retroid Pocket 5 Workspace Agent Guidance

Welcome to the **Retroid Pocket 5 (RP5) Automated Provisioning Workspace**. This repository contains ADB automation scripts, staging directories, configurations, and patch definitions used to configure, optimize, and provision the Retroid Pocket 5 handheld gaming console.

---

## 1. Hardware & System Context

- **Device**: Retroid Pocket 5 (RP5)
- **SoC**: Qualcomm Snapdragon 865 (SM8250)
- **GPU**: Adreno 650 (supports custom Turnip/Mesa drivers via Vulkan in supported emulators)
- **OS**: Android 13 (AOSP-based Retroid OS)
- **Display**: 5.5-inch 1080p AMOLED (1920x1080), 60Hz
- **Storage**:
  - Internal: `/sdcard` or `/storage/emulated/0`
  - External: `/storage/<SD_ID>/` (MicroSD FAT32/exFAT UUID)
- **Connectivity**: USB-C with ADB debugging enabled

---

## 2. CANONICAL DEVICE STORAGE LAYOUT (STRICT)

This is the **only** permitted on-device layout. It is hardcoded in `scripts/setup_rp5.py` (`INTERNAL_DIRS`, `SD_DIRS`).

```text
Internal storage   /sdcard/
└── bios/                         # BIOS copy (internal)

MicroSD            /storage/<SD_ID>/
├── bios/                         # BIOS files (canonical, shared by all emulators)
├── ROMs/                         # All ROMs (one subfolder per system, managed by ES-DE)
├── ES-DE/                        # ES-DE frontend data (gamelists, media, settings)
├── RetroArch/                    # RetroArch configs, cores, joypad autoconfig, shaders
├── Saves_Backup/                 # Canonical save, savestate & memory card backup mirrors
└── Games/Steam/                  # External DroidDeck Steam library (MicroSD)
```

### Layout rules for agents

1. **Do NOT create alternative ROM folder variants.** Forbidden on the device, on both internal storage and the MicroSD card:
   - `Games/BIOS`, `BIOS/` (upper-case), `Bios/`
   - `roms/` (lower-case), `Emulation/`, `Emulation/roms`, `Emulation/bios`
   - `/sdcard/ROMs`, `/sdcard/roms`, `/sdcard/Emulation` (ROMs live only on MicroSD in `/storage/<SD_ID>/ROMs`)
2. **Canonical ROM storage.** ROMs live strictly on the MicroSD card in `/storage/<SD_ID>/ROMs/<system>/`.
3. Android-managed folders (`Android/`, `Download/`, and the stock media folders) are owned by the OS. Do not rely on them, and never delete `Android/`. `/sdcard/Download/` is used only to stage `rp5_master_obtainium.json`, Mesa Turnip drivers, and Vita firmware.
4. When pushing BIOS files, push to `/sdcard/bios/` and `/storage/<SD_ID>/bios/` only.

---

## 3. Workspace Directory Structure (host repo)

```text
AntigravityWorkingDir/
├── .gitignore               # Excludes platform-tools/, logs, *.apk, bios/*, roms/**/*, *.pnach
├── AGENTS.md                # Agent overview, canonical storage layout, workspace instructions
├── CLAUDE.md                # Claude handoff dossier, active troubleshooting & hardware briefing
├── GEMINI.md                # Gemini-specific provisioning guidelines
├── README.md                # Hardware specs, pipeline docs, ecosystem matrix
├── WORKQUEUE.md             # Persistent 30-item master workqueue across all emulators & ports
├── platform-tools/          # Local Google Android SDK Platform-Tools (adb, fastboot) - not versioned
├── apks/                    # Staging directory for offline APK installations (not versioned)
├── bios/                    # Local staging copy of system BIOS files (not versioned)
├── roms/                    # Local ROM staging (not versioned)
├── patches/
│   ├── gcn/                 # GameCube widescreen/60fps Gecko patches
│   ├── wii/                 # Wii widescreen/deflicker/bloom Gecko patches
│   └── ps2/                 # PS2 PCSX2 master pnach cheats (.gitkeep)
├── configs/                 # Device profiles, ES-DE configs & Obtainium templates
│   ├── rp5_master_obtainium.json
│   ├── es_systems.xml       # Custom systems forcing standalone 3D emulator priority
│   ├── es_settings.xml
│   ├── droiddeck_config.json
│   ├── libraryfolders.vdf   # Pre-seeded Steam MicroSD library mapping
│   └── retroarch/           # Low-latency configs, core options, GBA low-pass filter & shader
├── drivers/                 # Mesa Turnip Adreno 650 GPU drivers (not versioned)
└── scripts/
    ├── provision_all.ps1    # Master PowerShell provisioning orchestrator
    ├── setup_rp5.py         # Main automated ADB provisioning script (--all)
    ├── android_ui.py        # Deterministic UIAutomator XML element interaction utility
    ├── stage_community_patches.py # Universal PS2 & GameCube/Wii patch engine
    ├── configure_standalones.py # Standalone 3D emulator profile injector
    ├── download_retroarch_cores.py # Automated Libretro 2D/Arcade core & asset deployer
    ├── sync_all_saves.py    # Save, savestate & memory card backup sync
    ├── fetch_youtube.py     # YouTube metadata, chapter & timestamped transcript extractor
    └── run_setup.ps1        # PowerShell helper wrapper ensuring PATH resolution
```

---

## 4. Automation Protocols (`scripts/setup_rp5.py` and `scripts/provision_all.ps1`)

The provisioning pipeline handles the following Android 13 configuration routines:

### A. Android 13 Phantom Process Killer Unlock
Android 12 and 13 enforce a maximum of 32 child processes per background app tree. Emulators, background tasks, and translation environments can trigger silent `SIGKILL` termination. The script disables this limit:
```bash
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell "settings put global settings_enable_monitor_phantom_procs false"
```

### B. Directory Scaffolding (Canonical Layout Only)
- Creates `/sdcard/bios`.
- Automatically discovers the external MicroSD card under `/storage/XXXX-XXXX` and creates canonical directories.

### C. Staging Obtainium & DroidDeck Configuration
- Pushes `configs/rp5_master_obtainium.json` directly to `/sdcard/Download/rp5_master_obtainium.json`. Tracks RetroArch (AArch64) using Libretro's stable buildbot (`https://buildbot.libretro.com/stable`) with a 2-level `intermediateLink` chain (`\d+\.\d+\.\d+` -> `android`) and `aarch64` APK regex, avoiding missing release asset errors.
- Pushes `configs/droiddeck_config.json` (720p base rendering, FSR 1080p, `DXVK_ASYNC=1`, `MESA_VK_WSI_PRESENT_MODE=mailbox`, `TU_DEBUG=noconform`, Turnip driver) to `/sdcard/DroidDeck/config.json`.
- Deploys `configs/libraryfolders.vdf` mapping `/mnt/bannerlator-sd` and `/storage/<SD_ID>/Games/Steam` (drive `D:\`).
- Stages Sony PS Vita OS Firmware `PSP2UPDAT.PUP` to `/sdcard/Download/vita3k/`.

### D. Ultra-Low-Latency 2D RetroArch Engine & Low-Pass Audio Filters
- Vulkan video backend, Ozone menu, frame delay 4, 48ms OpenSLES audio latency, run-ahead 1 frame.
- Genesis Model 1 low-pass filter (range 60, YM2612 MAME).
- Super Nintendo Gaussian audio interpolation (Snes9x).
- Game Boy / Game Boy Color Sinc audio resampler (Gambatte).
- Game Boy Advance 5.5kHz IIR low-pass DSP filter (`gba_lowpass.dsp`) + `mGBA.slangp` GBA color & LCD grid shader.
- Automated fetching of 11 designated 2D/Arcade cores and frontend assets.

### E. Standalone 3D Emulators Injection
- **ARM SX2 (PS2 Primary)**: Direct boot via `%EMULATOR_ARMSX2% %ACTION%=android.intent.action.VIEW %DATA%=%ROMSAF%`. 2.0x 1080p Vulkan, string `AspectRatio = 16:9` (`"aspectRatio": 1` in UI JSON), `Crop = 1`, `CropMode = Overscan`, `HardwareDownloadMode = 1` (Disable Readbacks), and `touchControllerOpacity = 0`.
- **NetherSX2 (PS2 Fallback)**: 2.25x 1080p SPU2 Catmull-Rom interpolation, `AspectRatio = 16:9`, `Crop = 1`, `CropMode = Overscan`.
- **DuckStation (PS1)**: 5x 1080p PGXP, Cubeb 20ms low latency audio.
- **Dolphin (GameCube & Wii)**: 2.5x 1080p OpenSLES DSP audio, analog triggers (L=`Axis 22+`, R=`Axis 23+`). Global `SIDevice0 = 6`, `WiimoteSource0 = 1`, `WiimoteEnableGCControllers = True`. Binds `WiimoteProfile1 = Classic_Controller` and `WiimoteSource0 = 1` in Mario Kart Wii (`RMC*.ini`) without conflicting `PadType0` dropdown indices.
- **PPSSPP (PSP)**: 4x 1080p 16x Anisotropic filtering.
- **Flycast (Dreamcast)**: 2x 1080p Widescreen.
- **Azahar (3DS)**: 3x 1080p Mesa Turnip driver, async shader compilation.
- **Vita3K (PS Vita)**: 2x 1080p Vulkan, `initial-setup: false`, `backend-renderer: Vulkan`, `pref-path: "/storage/emulated/0/Android/data/org.vita3k.emulator/files/vita"`, overlay opacity 0.

### F. Universal Community Patch Engine (`scripts/stage_community_patches.py`)
- **PS2 (NetherSX2 / PCSX2)**: Downloads and deploys 4,700+ `.pnach` master cheats to both `patches/` and `cheats/`.
- **GameCube & Wii (Dolphin)**: Parses 1,891 upstream GameSettings INIs, injects 16:9 widescreen Gecko codes under `[Gecko_Enabled]`, sets `[Video_Settings] AspectRatio = 1`, and merges custom Gecko patches.
- Headless `es_settings.xml` pre-routes all 3D systems to standalone emulators while routing 2D/Arcade systems to RetroArch.

### G. Save & State Backup Pipeline
- Systematically mirrors saves, states, and virtual memory cards across all emulators to `/storage/<SD_ID>/Saves_Backup/latest/`.

### H. Retroid OS System & Hardware Tuning
- **Lockscreen**: Disabled (`locksettings set-disabled true`).
- **Floating Overlay**: Disabled (`settings put system is_show_floatingIcon 0`).
- **Auto-Rotate**: Disabled (`settings put system accelerometer_rotation 0`) to lock landscape display orientation.
- **Controller Style**: Xbox mode (`persist.sys.gamepad.type 0`).
- **Trigger Mode**: Both analog axis + digital button click (`persist.sys.trigger.mode 2`).
- **Fan Profile**: Smart active cooling (`settings put system fan_mode 4`).

### I. Granting AppOps
Android 11+ restricts storage access under Scoped Storage. The script invokes AppOps:
```bash
adb shell appops set <package.name> MANAGE_EXTERNAL_STORAGE allow
adb shell appops set dev.imranr.obtainium REQUEST_INSTALL_PACKAGES allow
adb shell appops set com.droiddeck.launcher REQUEST_INSTALL_PACKAGES allow
```

---

## 5. Operational Best Practices for Agents

1. **Master Runner**: Execute `.\scripts\provision_all.ps1 -Serial <SERIAL>` or `python scripts/setup_rp5.py --serial <SERIAL> --all`.
2. **Device State Verification**: Always check `adb devices` before executing device commands. If status is `unauthorized`, prompt the user to accept the USB debugging prompt on the device screen.
3. **Safe Storage Handling**: Do not write large binary files directly to version control. Validate paths before issuing `adb push` commands, and only push to the canonical paths in Section 2.
4. **Multiple Devices**: Multiple devices may be attached. Always query `adb devices` at runtime and pass `-s <serial>` explicitly.
5. **Markdown Clipboard Staging**: When generating markdown content for the user to post externally (GitHub PRs, issues, Discord), stage the raw text directly into the user's clipboard using PowerShell `.\scripts\stage_clipboard.ps1 -FilePath <path>` or `Get-Content <file> -Raw | Set-Clipboard` to prevent leading-space formatting corruption.
6. **OLED Display Sleep Invariant**: Whenever tasks conclude or when waiting on user feedback, power down the physical device display (`adb shell input keyevent 26`) and verify with `adb shell dumpsys power` (`mHoldingDisplaySuspendBlocker=false`) to eliminate AMOLED burn-in risk.

---

## 6. The 5 Laws of Schema Verification (Anti-Hallucination Guardrails)

To guarantee emulator stability and prevent input or configuration regressions:
1. **Never Guess INI Section Names or Key Syntaxes**: Always inspect Dolphin/emulator source code, upstream documentation, or native UI auto-mappings on the device before writing configurations. Never improvise section headers or property names.
2. **Clean Direct Tokens Under Active Device Sections**: Under an active `Device = <name>` section, bind buttons and axes using clean, direct tokens (e.g., `Button 96`, `Axis 1-`) rather than chained or device-prefixed expressions (e.g. `` `Device:Button 96` | ... ``), which fail to parse in Android UI builds.
3. **Flat Wiimote Extensions**: Dolphin Wiimote extensions (Classic, Nunchuk) live flat inside `[Wiimote1]` using extension prefixes (e.g., `Classic/Buttons/A = `Button 96``, `Nunchuk/Buttons/C = `Button 102``). Dolphin never recognizes standalone sections like `[Classic1]` or `[Wiimote1/Classic]`.
4. **Literal Plus/Minus Keys**: Dolphin keys for Plus and Minus buttons are literally `+` and `-` (e.g., `Buttons/+`, `Classic/Buttons/-`), never `Plus` or `Minus`.
5. **Always Verify with Live Hardware Logs & Screenshots**: Never declare input or emulator configuration complete without verifying via ADB dumps, live logcat output, or screen captures that in-game menus advance and inputs are cleanly captured without drawer/system popups.

