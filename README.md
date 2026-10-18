# Retroid Pocket 5 Provisioning & Backup Toolkit

Automated ADB configuration, configuration snapshotting, save synchronization, native source port deployment, and verification toolkit tailored for the **Retroid Pocket 5 (RP5)** running Android 13 (Qualcomm Snapdragon 865 / Adreno 650).

---

## 🎯 Purpose & Scope

This repository serves as a deterministic backup, restore, snapshot, and provisioning repository for the Retroid Pocket 5. It automates device setup over ADB from a Windows host PC, eliminating manual emulator configuration, verifying settings against repo baselines, managing native Android source ports and static recompilations, and backing up irreplaceable game saves and memory cards.

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

### 4. Native Android Ports & Decompilations Ecosystem
- Manages 14+ native Android C/C++ source ports, static recompilations, and standalone fan projects launched directly from ES-DE via `/storage/<SD_ID>/ROMs/ports/*.app`:
  - **Zelda N64**: Ship of Harkinian (OOT) + 3DS Link/Young Link HD models, 2 Ship 2 Harkinian (MM)
  - **Retro 2D**: Zelda 3 (A Link to the Past), Apotris (Native GBA engine rewrite, 60fps), Sonic 3 A.I.R., Sonic Robo Blast 2 (SRB2)
  - **N64 Classics**: Mario Kart 64 (SpaghettiKart), Star Fox 64 (Starship), GoldenEye 007 (Recomp), Perfect Dark
  - **Fan Overhauls**: Mega Man X: Regenesis (SNES timeline), Mega Man X8 16-Bit Demake (Touch Mod v1.6 + 100% save)
  - **Modern Decomps**: Balatro (1080p 60fps AMOLED), Space Cadet 3D Pinball, PokeMMO (All 5 generations staged)

### 5. DroidDeck Steam PC Integration & Optimization
- Automates staging and configuration for DroidDeck (`com.droiddeck.launcher`):
  - Pre-seeds `/sdcard/DroidDeck/config.json` with 720p base rendering, 1080p AMD FSR upscaling, `DXVK_ASYNC=1`, `MESA_VK_WSI_PRESENT_MODE=mailbox`, and Turnip drivers.
  - Multi-mount VDF synchronizer maps `/mnt/bannerlator-sd`, `/storage/<SD_ID>/Games/Steam`, and `D:\`.
  - Stages verified Windows PC titles (e.g., **OutRun 2006: Coast 2 Coast** with widescreen, 60Hz physics fix, and `WINEDLLOVERRIDES="dinput8=n,b"`).

### 6. Deterministic Android UI Automator (`scripts/android_ui.py`)
- Eliminates visual coordinate guessing and blind tapping during setup:
  - Dumps live UIAutomator XML hierarchy directly from ADB.
  - Resolves elements by text, resource ID, or content description and computes true geometric centroids.
  - Automates complex Android Storage Access Framework (DocumentsUI) file pickers with search-and-select routines.

### 7. Upstream App Tracking via Obtainium (`configs/rp5_master_obtainium.json`)
- Manages open-source emulators and utilities directly from upstream GitHub releases and buildbots:
  - **ARM SX2** (Stable 2.8.3 arm64)
  - **NetherSX2** (Builder APK)
  - **Vita3K** (Continuous automatic CI builds)
  - **Azahar 3DS** (Vanilla build filter)
  - **Flycast** (Stable GitHub releases)
  - **RetroArch AArch64** (Libretro buildbot stable HTML scraper)
  - **Daijishō** (Frontend)
  - **Obtainium** (Clean arm64 release regex)

### 8. Automated RetroArch 2D Engine Provisioning (`scripts/download_retroarch_cores.py`)
- Downloads 11 designated 2D and arcade Libretro cores from the official Libretro buildbot.
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
│   ├── gba/                       # Full verified GBA library (.zip)
│   ├── gc/                        # GameCube games (.rvz)
│   ├── n64/                       # Full N64 Best Set (.n64.zip)
│   ├── nds/                       # Nintendo DS (.zip)
│   ├── ports/                     # Native Android port launchers (*.app)
│   ├── ps2/                       # PlayStation 2 (.chd)
│   ├── psx/                       # PlayStation 1 (.chd)
│   ├── snes/                      # Super Nintendo (.zip)
│   └── wii/                       # Nintendo Wii (.rvz)
├── ES-DE/                         # ES-DE themes, media, and gamelists
├── RetroArch/                     # RetroArch configs, cores, joypad profiles, shaders
├── Saves_Backup/                  # On-device latest and timestamped save archives
└── Games/Steam/                   # External DroidDeck Steam library
```

> [!IMPORTANT]
> Non-canonical folder variants (`Games/BIOS`, `BIOS/`, `roms/`, `/sdcard/ROMs`) are forbidden. ROMs live strictly on the MicroSD card under `/storage/<SD_ID>/ROMs/<system>/`.

---

## 🎮 Verified Working Titles & Baseline Settings

- **OutRun 2006: Coast 2 Coast (DroidDeck / Steam)**:
  - 1080p borderless, 2x MSAA, anisotropic filtering, 60fps physics fix, `dinput8` override.
- **Apotris (Native Port)**:
  - Standalone ARM64 APK running at native 60fps with full gamepad mapping; bypasses GBA emulation.
- **Mario Kart Wii (Dolphin)**:
  - Configured with `WiimoteProfile1 = Classic_Controller` in `RMC*.ini`.
  - Global `SIDevice0 = 6` (Standard GameCube Controller), `WiimoteSource0 = 1`, `WiimoteEnableGCControllers = True`.
- **Gran Turismo 4 Spec II (ARM SX2 / NetherSX2)**:
  - 16:9 widescreen rendering with CRT overscan crop (`Crop = 1`, `CropMode = Overscan`).
  - GS readbacks disabled (`HardwareDownloadMode = 1`) to eliminate slowdowns.
  - Active 16:9 widescreen patch (`646B2E29.pnach`) loaded via game CRC.

---

## 🛠️ Usage

### Prerequisites
1. Enable **Developer Options** and **USB Debugging** on the Retroid Pocket 5.
2. Connect the handheld via USB-C and authorize ADB debugging.
3. Ensure Python 3.10+ and ADB (provided in `platform-tools/`) are accessible.

### Running Master Provisioning Pipeline
```powershell
.\scripts\provision_all.ps1
```

### Running Verification & Audits
```powershell
# Verify hardware and emulator deployment against repository baselines
python scripts/verify_deployment.py
```

### UI Automation Helper
```powershell
# Inspect active screen hierarchy
python scripts/android_ui.py --dump

# Tap element deterministically
python scripts/android_ui.py --click-text "Play Steam"
```

---

## 🤝 Upstream Attributions

This repository integrates upstream configurations, shaders, and patches from:
- [Dolphin Emulator](https://dolphin-emu.org)
- [PCSX2 & NetherSX2 Community](https://pcsx2.net)
- [Libretro & RetroArch](https://www.retroarch.com)
- [ES-DE Frontend](https://gitlab.com/es-de/emulationstation-de)
- [DroidDeck](https://github.com/droiddeck)
- [HarbourMasters & Shipwright Teams](https://github.com/HarbourMasters)
- [Obtainium](https://github.com/ImranR98/Obtainium)

See [CREDITS.md](CREDITS.md) for full attributions and licenses.
