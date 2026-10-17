# Retroid Pocket 5 Provisioning & Backup Toolkit

Automated ADB configuration, configuration snapshotting, save synchronization, and verification toolkit tailored for the **Retroid Pocket 5 (RP5)** running Android 13 (Qualcomm Snapdragon 865 / Adreno 650).

---

## 🎯 Purpose & Scope

This repository serves as a deterministic backup, restore, snapshot, and provisioning repository for the Retroid Pocket 5. It automates device setup over ADB from a Windows host PC, eliminating manual emulator configuration, verifying settings against repo baselines, and backing up irreplaceable game saves and memory cards.

- **Target Device**: Retroid Pocket 5 (RP5)
- **SoC & GPU**: Qualcomm Snapdragon 865 (SM8250) / Adreno 650
- **Operating System**: Android 13 (AOSP Retroid OS)
- **Host Environment**: Windows (PowerShell 5.1/7+ and Python 3.10+) over ADB

---

## 📦 Core Capabilities

### 1. Configuration Snapshot & Restore Engine (`scripts/snapshot_device.py`)
- Force-stops all emulators and frontends before reading or writing.
- Captures active configurations from the device into timestamped archives under `snapshots/<YYYYMMDD_HHMMSS>/` and maintains a `snapshots/latest/` mirror.
- Covers Dolphin (`Config/`, `GameSettings/`), ARM SX2 (`inis/`, `gamesettings/`, `patches/`, `cheats/`), NetherSX2 (`inis/`, `gamesettings/`, `patches/`, `cheats/`), RetroArch (`retroarch.cfg`, core options, filters, SD config), ES-DE (`settings/`), Obtainium (`app_data/`), DuckStation, PPSSPP, Flycast, Azahar, and Vita3K.
- Supports bidirectional restoration:
  ```powershell
  python scripts/snapshot_device.py --restore snapshots/latest
  ```

### 2. Comprehensive Key-Value Verifier (`scripts/verify_deployment.py`)
- Performs semantic key-value comparisons across INI, XML, JSON, and Android system properties, accounting for unordered keys, trailing float formatting (`50.` vs `50.000000`), and unquoted tokens.
- Audits Dolphin controller bindings (`GCPadNew.ini`, `WiimoteNew.ini`, `Standard_Controller.ini`, `Classic_Controller.ini`), Mario Kart Wii GameSettings (`RMC*.ini`), ARM SX2 Gran Turismo 4 widescreen patches (`646B2E29.pnach`, `646B2E29.ini`), ES-DE `%ROM%` launch syntax, Obtainium tracked applications, RetroArch 48ms OpenSLES/Vulkan engine, and hardware trigger/overlay modes.

### 3. Bidirectional Save & Memory Card Pipeline (`scripts/sync_all_saves.py`)
- Automatically discovers the external MicroSD volume UUID at runtime.
- Systematically backs up Dolphin Wii saves, ARM SX2 virtual memory cards (`Mcd001.ps2`, `Mcd002.ps2`), NetherSX2 memory cards, Flycast VMUs, and RetroArch save folders to `/storage/<SD_ID>/Saves_Backup/latest/`, timestamped on-device archives, and local PC mirrors under `backups/saves/`.
- Provides full restore capabilities targeting individual emulators or the entire library:
  ```powershell
  python scripts/sync_all_saves.py --restore --restore-target all
  ```

### 4. Upstream App Tracking via Obtainium (`configs/rp5_master_obtainium.json`)
- Manages 8 open-source emulators and utilities directly from upstream GitHub releases and buildbots:
  - **ARM SX2** (Stable 2.8.3 arm64)
  - **NetherSX2** (Builder APK)
  - **Vita3K** (Continuous automatic CI builds)
  - **Azahar 3DS** (Vanilla build filter)
  - **Flycast** (Stable GitHub releases)
  - **RetroArch AArch64** (Libretro buildbot stable HTML scraper)
  - **Daijishō** (Kept for optional frontend configuration)
  - **Obtainium** (Clean arm64 release regex)

### 5. Automated RetroArch 2D Engine Provisioning (`scripts/download_retroarch_cores.py`)
- Downloads 11 designated 2D and arcade Libretro cores (Mesen, Snes9x, Gambatte, mGBA, Genesis Plus GX, PicoDrive, Beetle PCE Fast, Beetle NeoPop, Beetle Cygne, FBNeo, Stella) from the official Libretro buildbot.
- Deploys Core Info files, Joypad autoconfigs, and Slang shaders headlessly over ADB.

---

## 📁 Canonical Storage Architecture

The toolkit strictly adheres to a clean device layout:

```text
Internal Storage   /sdcard/
└── bios/                          # Internal BIOS mirror

MicroSD Storage    /storage/<SD_ID>/
├── bios/                          # Canonical BIOS files (shared across emulators)
├── ROMs/                          # Game ROMs organized by system subfolder
│   ├── gba/
│   ├── gc/
│   ├── ps2/
│   ├── psx/
│   ├── snes/
│   └── wii/
├── ES-DE/                         # ES-DE themes, media, and gamelists
├── RetroArch/                     # RetroArch configs, cores, joypad profiles, shaders
├── Saves_Backup/                  # On-device latest and timestamped save archives
└── Games/Steam/                   # External DroidDeck Steam library
```

> [!IMPORTANT]
> Non-canonical folder variants (`Games/BIOS`, `BIOS/`, `roms/`, `/sdcard/ROMs`) are forbidden. ROMs live strictly on the MicroSD card under `/storage/<SD_ID>/ROMs/<system>/`.

---

## 🎮 Verified Working Titles & Baseline Settings

- **Mario Kart Wii (Dolphin)**:
  - Configured with `WiimoteProfile1 = Classic_Controller` in `RMC*.ini`.
  - Global `SIDevice0 = 6` (Standard GameCube Controller), `WiimoteSource0 = 1` (Emulated Wii Remote), `WiimoteEnableGCControllers = True`.
  - Direct token bindings (`Button A`, `Button B`, `Classic/Buttons/A`) under active `Device = ` sections.
- **Gran Turismo 4 Spec II (ARM SX2 / NetherSX2)**:
  - 16:9 widescreen rendering with CRT overscan crop (`Crop = 1`, `CropMode = Overscan`).
  - GS readbacks disabled (`HardwareDownloadMode = 1`) to eliminate tunnel and night-track slowdowns.
  - Active 16:9 widescreen patch (`646B2E29.pnach`) loaded via game CRC.

---

## 🛠️ Usage

### Prerequisites
1. Enable **Developer Options** and **USB Debugging** on the Retroid Pocket 5.
2. Connect the handheld via USB-C and authorize ADB debugging.
3. Ensure Python 3.10+ and ADB (provided in `platform-tools/`) are accessible.

### Running Verification & Audits
```powershell
# Verify hardware and emulator deployment against repository baselines
python scripts/verify_deployment.py
```

### Capturing a Configuration Snapshot
```powershell
# Create a timestamped configuration snapshot
python scripts/snapshot_device.py
```

### Backing Up Saves & Memory Cards
```powershell
# Synchronize device saves to MicroSD and host PC
python scripts/sync_all_saves.py
```

---

## 🤝 Upstream Attributions

This repository integrates upstream configurations, shaders, and patches from:
- [Dolphin Emulator](https://dolphin-emu.org)
- [PCSX2 & NetherSX2 Community](https://pcsx2.net)
- [Libretro & RetroArch](https://www.retroarch.com)
- [ES-DE Frontend](https://gitlab.com/es-de/emulationstation-de)
- [Obtainium](https://github.com/ImranR98/Obtainium)

See [CREDITS.md](CREDITS.md) for full attributions and licenses.
