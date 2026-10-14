# rp5-antigravity-toolkit

ADB automation for provisioning a **Retroid Pocket 5** handheld: Android 13 tweaks, a strict on-device storage layout, Obtainium bootstrap, and storage AppOps.

## Hardware

| Item | Spec |
|---|---|
| Device | Retroid Pocket 5 (RP5) |
| SoC | Qualcomm Snapdragon 865 (SM8250) |
| GPU | Adreno 650 (custom Turnip/Mesa Vulkan drivers supported in some emulators) |
| OS | Android 13 (SDK 33), AOSP-based Retroid OS |
| Display | 5.5" 1080p AMOLED (1920x1080), 60 Hz |
| Storage | Internal (`/sdcard`) + MicroSD (`/storage/<SD_ID>/`, exFAT/FAT32) |
| Connectivity | USB-C, ADB debugging |

## Canonical storage map

This is the only supported on-device layout. It is hardcoded in [`scripts/setup_rp5.py`](scripts/setup_rp5.py) (`INTERNAL_DIRS`, `SD_DIRS`).

```text
Internal storage   /sdcard/
└── bios/                  # BIOS copy

MicroSD            /storage/<SD_ID>/
├── bios/                  # BIOS files (shared by all emulators)
├── ROMs/                  # ROMs, one subfolder per system
└── ES-DE/                 # ES-DE frontend data
```

Not supported (never created): `Games/`, `Games/BIOS`, `BIOS/`, `roms/`, `Emulation/`, or any ROM directory on internal storage. See [`AGENTS.md`](AGENTS.md) for the full rules.

## Provisioning pipeline

Run from the repo root (PowerShell):

```powershell
.\scripts\run_setup.ps1 --serial <RP5_SERIAL> --install-apks
```

or directly: `python scripts/setup_rp5.py --serial <RP5_SERIAL> --install-apks`

The pipeline runs these stages in order:

1. **Connectivity check** - verifies the device is online and authorized (`adb devices -l`) and prints model/SoC/Android version.
2. **Phantom Process Killer unlock** - sets `max_phantom_processes` to `2147483647` and disables phantom process monitoring so emulators are not silently killed.
3. **Canonical directory scaffolding** - creates `/sdcard/bios` and `/storage/<SD_ID>/{bios,ROMs,ES-DE}` and nothing else.
4. **Obtainium config staging** - pushes `configs/rp5_master_obtainium.json` to `/sdcard/Download/` for **Import/Export -> Obtainium Import**.
5. **Headless ES-DE config staging** - pushes `configs/es_settings.xml` configured for `/storage/<SD_ID>/ROMs` to `/sdcard/ES-DE/settings/` and `/storage/<SD_ID>/ES-DE/settings/` to bypass first-launch folder wizards.
6. **Mesa Turnip GPU driver staging** - pushes Adreno 650 Turnip Vulkan driver archives from `drivers/` to `/sdcard/Download/drivers/`.
7. **Retroid OS hardware & system tuning** - disables the lock screen, hides the floating game assistant overlay, and sets gamepad controller style to Xbox mode (`persist.sys.gamepad.type=0`).
8. **APK install** (`--install-apks`) - installs every `.apk` in `apks/` with `adb install -r -g`.
9. **AppOps** - grants `MANAGE_EXTERNAL_STORAGE` to every installed emulator/frontend package, plus `REQUEST_INSTALL_PACKAGES` to Obtainium.

### Options

| Flag | Effect |
|---|---|
| `--serial`, `-s <id>` | Target a specific device (always use this when more than one device is attached) |
| `--dry-run` | Print ADB commands without applying them |
| `--status` | Print connection and hardware info, then exit |
| `--install-apks` | Install APKs staged in `apks/` |
| `--skip-phantom` | Skip Android 13 phantom process killer unlocks |
| `--skip-scaffold` | Skip canonical directory scaffolding on storage |
| `--skip-obtainium` | Skip pushing `rp5_master_obtainium.json` |
| `--skip-esde` | Skip staging headless ES-DE `es_settings.xml` |
| `--skip-drivers` | Skip staging Mesa Turnip GPU drivers |
| `--skip-tuning` | Skip Retroid OS hardware & system tuning |
| `--skip-permissions` | Skip granting `MANAGE_EXTERNAL_STORAGE` AppOps |
| `--adb <path>` | Explicit adb binary path |

### Emulator Ecosystem & Distribution Channels

- **Google Play Store**: **Dolphin** (`org.dolphinemu.dolphinemu`) and **DuckStation** (`com.github.stenzek.duckstation`) do not publish standalone Android APK releases on GitHub and are provisioned directly from Google Play. Once installed from the Play Store, re-running `setup_rp5.py` automatically grants them `MANAGE_EXTERNAL_STORAGE` permissions.
- **Obtainium**: All other emulators and frontends (**RetroArch**, **NetherSX2**, **PPSSPP**, **Azahar**, **Vita3K**, **Flycast**, **Daijisho**, and **ES-DE**) are tracked and updated directly from upstream GitHub releases via `configs/rp5_master_obtainium.json`.

### Mesa Turnip GPU Drivers (Adreno 650)

Custom Mesa Turnip drivers (from [`K11MCH1/AdrenoToolsDrivers`](https://github.com/K11MCH1/AdrenoToolsDrivers)) are staged in `drivers/` and pushed to `/sdcard/Download/drivers/`. Emulators supporting AdrenoTools custom drivers (such as Azahar / 3DS and Vita3K / PS Vita) can load them directly via their in-app GPU driver settings to maximize Vulkan performance and fix rendering glitches.

### Headless ES-DE Setup

[`configs/es_settings.xml`](configs/es_settings.xml) pre-defines:
```xml
<string name="ROMDirectory" value="/storage/EEEF-F762/ROMs" />
```
Pushed to both `/sdcard/ES-DE/settings/` and `/storage/<SD_ID>/ES-DE/settings/`. Once SAF document tree permissions are granted on first launch, ES-DE directly indexes the MicroSD card ROM tree without further configuration.

### Retroid OS Hardware Tuning

The provisioning pipeline configures the following low-level settings via ADB:
- **Lock screen**: Disabled (`locksettings set-disabled true`) for instant boot to frontend and headless reliability.
- **Floating overlay**: Game assistant icon disabled (`settings put system is_show_floatingIcon 0`).
- **Controller style**: Standard Xbox mode (`persist.sys.gamepad.type=0`).

### Bootstrapping Obtainium

Download the arm64 build into `apks/` and verify it against the published checksum, then run the pipeline with `--install-apks`:

```powershell
curl.exe -L -o apks\app-arm64-v8a-release.apk https://github.com/ImranR98/Obtainium/releases/latest/download/app-arm64-v8a-release.apk
```

### Pushing BIOS files

BIOS files are staged locally in `bios/` (git-ignored). Push only to the canonical paths:

```powershell
.\platform-tools\adb.exe -s <RP5_SERIAL> push bios/. /sdcard/bios/
.\platform-tools\adb.exe -s <RP5_SERIAL> push bios/. /storage/<SD_ID>/bios/
```

## Repository layout

```text
.
├── scripts/        setup_rp5.py (provisioning) and run_setup.ps1 (PATH-resolving wrapper)
├── configs/        rp5_master_obtainium.json, es_settings.xml
├── drivers/        Mesa Turnip GPU drivers (contents git-ignored)
├── patches/        gcn/ and ps2/ widescreen / 60fps patches
├── apks/           local APK staging       (contents git-ignored)
├── bios/           local BIOS staging      (contents git-ignored)
├── roms/           local ROM staging       (contents git-ignored)
├── AGENTS.md       agent guidance + canonical layout rules
└── GEMINI.md       Gemini-specific directives
```

`platform-tools/`, logs, APKs, driver archives, BIOS files and ROMs are never committed.

## Requirements

- Windows with PowerShell, Python 3.12, and Google platform-tools (placed in `platform-tools/` or on `PATH`)
- USB debugging enabled on the RP5 and the computer authorized on-device
