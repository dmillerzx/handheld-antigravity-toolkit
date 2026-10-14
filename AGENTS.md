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
  - External: `/storage/XXXX-XXXX/` (MicroSD FAT32/exFAT UUID)
- **Connectivity**: USB-C with ADB debugging enabled

---

## 2. Workspace Directory Structure

```text
AntigravityWorkingDir/
├── .gitignore               # Excludes large binaries (*.apk, bios/*, roms/**/*)
├── AGENTS.md                # Agent overview and workspace instructions
├── GEMINI.md                # Gemini-specific provisioning guidelines
├── platform-tools/          # Local Google Android SDK Platform-Tools (adb, fastboot)
├── apks/                    # Staging directory for offline APK installations
├── bios/                    # Staging directory for system BIOS files (PS2, PS1, Saturn, etc.)
├── roms/
│   ├── gc/                  # GameCube ROMs (.iso, .rvz)
│   ├── ps2/                 # PlayStation 2 ROMs (.iso, .chd)
│   └── n64/                 # Nintendo 64 ROMs (.z64, .n64)
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

## 3. Automation Protocols (`scripts/setup_rp5.py`)

The primary provisioning script handles four key Android 13 configuration routines:

### A. Android 13 Phantom Process Killer Unlock
Android 12 and 13 enforce a maximum of 32 child processes per background app tree. Emulators, background tasks, and translation environments can trigger silent `SIGKILL` termination. The script disables this limit:
```bash
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell "settings put global settings_enable_monitor_phantom_procs false"
```

### B. Directory Scaffolding (Internal & SD Card)
- Scaffolds `/sdcard/Download`, `/sdcard/RetroArch`, `/sdcard/Dolphin`, and `/sdcard/Emulation/...`
- Automatically discovers external MicroSD card mount paths under `/storage/XXXX-XXXX` and establishes standard folder hierarchies (`bios/`, `roms/`, `saves/`, `states/`, `patches/`).

### C. Staging Obtainium Configuration
- Pushes `configs/rp5_master_obtainium.json` directly to `/sdcard/Download/rp5_master_obtainium.json`.
- Users can launch Obtainium on the device and select **Import/Export -> Obtainium Import** to batch-install and track all emulator releases directly from upstream GitHub releases.

### D. Granting `MANAGE_EXTERNAL_STORAGE`
Android 11+ restricts storage access under Scoped Storage. Standard runtime permission requests fail for emulators reading ROMs from MicroSD. The script invokes AppOps:
```bash
adb shell appops set <package.name> MANAGE_EXTERNAL_STORAGE allow
```
Applied across all detected emulator and frontend packages (RetroArch, Dolphin, NetherSX2, DuckStation, PPSSPP, Mupen64Plus FZ, Lime3DS, Vita3K, Daijisho, ES-DE, Obtainium, etc.).

---

## 4. Operational Best Practices for Agents

1. **Path Resolution**: When calling ADB or Python, prioritize local `platform-tools/adb.exe` if `adb` is missing from the global execution environment, or use `scripts/run_setup.ps1`.
2. **Device State Verification**: Always check `adb devices` before executing device commands. If status is `unauthorized`, prompt the user to accept the USB debugging prompt on the RP5 screen.
3. **Safe Storage Handling**: Do not write large binary files directly to version control. Validate paths before issuing `adb push` commands.
