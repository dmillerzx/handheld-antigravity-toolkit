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
  - External: `/storage/XXXX-XXXX/` (MicroSD FAT32/exFAT UUID; currently `EEEF-F762`)
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
└── ES-DE/                        # ES-DE frontend data (gamelists, media, settings)
```

### Layout rules for agents

1. **Do NOT create alternative folder variants.** Forbidden on the device, on both internal storage and the MicroSD card:
   - `Games/`, `Games/BIOS`, `BIOS/` (upper-case), `Bios/`
   - `roms/` (lower-case), `Emulation/`, `Emulation/roms`, `Emulation/bios`
   - `RetroArch/`, `Dolphin/` scaffolding folders created by scripts
   - Any other new top-level directory on `/storage/<SD_ID>/` besides `bios`, `ROMs`, `ES-DE`
2. **No internal ROM directories.** ROMs live only on the MicroSD card in `/storage/<SD_ID>/ROMs`. Never create `/sdcard/ROMs`, `/sdcard/roms` or `/sdcard/Emulation`.
3. Android-managed folders (`Android/`, `Download/`, and the stock media folders) are owned by the OS. Do not rely on them, and never delete `Android/`. `/sdcard/Download/` is used only to stage `rp5_master_obtainium.json`.
4. Do not add paths to scripts or docs without first updating this section.
5. When pushing BIOS files, push to `/sdcard/bios/` and `/storage/<SD_ID>/bios/` only.

---

## 3. Workspace Directory Structure (host repo)

```text
AntigravityWorkingDir/
├── .gitignore               # Excludes platform-tools/, logs, *.apk, bios/*, roms/**/* (keeps .gitkeep)
├── AGENTS.md                # Agent overview, canonical storage layout, workspace instructions
├── GEMINI.md                # Gemini-specific provisioning guidelines
├── README.md                # Hardware specs, pipeline docs, canonical storage map
├── platform-tools/          # Local Google Android SDK Platform-Tools (adb, fastboot) - not versioned
├── apks/                    # Staging directory for offline APK installations (not versioned)
├── bios/                    # Local staging copy of system BIOS files (not versioned)
├── roms/                    # Local ROM staging (not versioned)
├── patches/
│   ├── gcn/                 # GameCube widescreen/60fps/HD gecko patches & textures
│   └── ps2/                 # PS2 widescreen/60fps pnach patches
├── configs/                 # Device profiles & Obtainium import templates
│   └── rp5_master_obtainium.json
└── scripts/
    ├── setup_rp5.py         # Main automated ADB provisioning script
    └── run_setup.ps1        # PowerShell helper wrapper ensuring PATH resolution
```

---

## 4. Automation Protocols (`scripts/setup_rp5.py`)

The primary provisioning script handles the following Android 13 configuration routines:

### A. Android 13 Phantom Process Killer Unlock
Android 12 and 13 enforce a maximum of 32 child processes per background app tree. Emulators, background tasks, and translation environments can trigger silent `SIGKILL` termination. The script disables this limit:
```bash
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell "settings put global settings_enable_monitor_phantom_procs false"
```

### B. Directory Scaffolding (Canonical Layout Only)
- Creates `/sdcard/bios`.
- Automatically discovers the external MicroSD card under `/storage/XXXX-XXXX` and creates exactly `bios/`, `ROMs/` and `ES-DE/` there (see Section 2).

### C. Staging Obtainium Configuration
- Pushes `configs/rp5_master_obtainium.json` directly to `/sdcard/Download/rp5_master_obtainium.json`.
- Users can launch Obtainium on the device and select **Import/Export -> Obtainium Import** to batch-install and track all emulator releases directly from upstream GitHub releases.

### D. APK Installation (`--install-apks`)
Installs every `.apk` staged in `apks/` with `adb install -r -g`. Runs **before** the AppOps step so freshly installed packages are granted permissions in the same run.

### E. Granting AppOps
Android 11+ restricts storage access under Scoped Storage. Standard runtime permission requests fail for emulators reading ROMs from MicroSD. The script invokes AppOps:
```bash
adb shell appops set <package.name> MANAGE_EXTERNAL_STORAGE allow
adb shell appops set dev.imranr.obtainium REQUEST_INSTALL_PACKAGES allow
```
### F. Emulator Distribution Channels (Obtainium vs Google Play)
- **Google Play Store**: **Dolphin** (`org.dolphinemu.dolphinemu`) and **DuckStation** (`com.github.stenzek.duckstation`) do not publish standalone Android APK release assets on GitHub and are provisioned via Google Play. Once downloaded from Play Store, re-running `setup_rp5.py` immediately grants them `MANAGE_EXTERNAL_STORAGE`.
- **Obtainium**: All other emulators and frontends (**RetroArch**, **NetherSX2**, **PPSSPP**, **Azahar**, **Vita3K**, **Flycast**, **Daijisho**, and **ES-DE**) are provisioned and tracked directly from upstream GitHub releases using `configs/rp5_master_obtainium.json`.

---

## 5. Operational Best Practices for Agents

1. **Path Resolution**: When calling ADB or Python, prioritize local `platform-tools/adb.exe` if `adb` is missing from the global execution environment, or use `scripts/run_setup.ps1`.
2. **Device State Verification**: Always check `adb devices` before executing device commands. If status is `unauthorized`, prompt the user to accept the USB debugging prompt on the RP5 screen.
3. **Safe Storage Handling**: Do not write large binary files directly to version control. Validate paths before issuing `adb push` commands, and only push to the canonical paths in Section 2.
4. **Multiple Devices**: A Konkr Pocket Advance may also be attached. Always pass `-s <serial>` explicitly; the RP5 serial is `ff152647`.
