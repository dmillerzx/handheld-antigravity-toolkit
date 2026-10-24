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

## ⚡ Quick Start (60-Second Provisioning)

Get a factory-fresh or reset Retroid Pocket 5 fully configured in minutes:

1. **Enable USB Debugging on your RP5**:
   - Go to **Settings** > **About handheld** and tap **Build number** 7 times to enable Developer options.
   - Go to **Settings** > **System** > **Developer options** and enable **USB debugging**.
2. **Connect Handheld to your Host PC**:
   - Plug the RP5 into your PC using USB-C. Authorize the USB debugging prompt on the device screen.
   - Verify connection in PowerShell:
     `powershell
     .\platform-tools\adb.exe devices
     `
3. **Run Zero-Touch Provisioning**:
   `powershell
   .\scripts\provision_all.ps1
   `
   *This automatically unlocks Android 13 phantom process restrictions, scaffolds the canonical MicroSD directories, tunes Retroid OS system flags (smart fan, Xbox controller mode, analog triggers), injects tuned 3D emulator profiles, configures low-latency 2D audio engines, and stages Obtainium app manifests.*

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
- Manages 19 native Android C/C++ source ports, static recompilations, and standalone fan projects launched directly from ES-DE via `/storage/<SD_ID>/ROMs/ports/*.app` using `%ANDROIDAPP%=%FILEINJECT%`:
  - **Super Mario 64 (sm64ex-alo)**: Native Snapdragon 865 60 FPS 1080p widescreen port with full 360° right-analog camera, ZL multi-bind, and clean touchless binary
  - **CannonBall: OutRun**: Standalone 60 FPS 16:9 widescreen arcade engine rewrite eliminating PC translation overhead
  - **Another Metroid 2 Remake (AM2R)**: Native 60 FPS 1080p AMOLED widescreen with HQ audio and physical gamepad mapping (`com.companyname.AM2RWrapper`)
  - **Sonic Mania Plus**: Retro Engine v5 native Android port (`com.decomp.rsdkv5`) running 1080p 60 FPS with full controller support and `Data.rsdk` assets
  - **Zelda N64**: Ship of Harkinian (OOT) + 3DS Link/Young Link HD models, 2 Ship 2 Harkinian (MM)
  - **Retro 2D**: Zelda 3 (A Link to the Past), Apotris (Native GBA engine rewrite, 60fps), Sonic 3 A.I.R., Sonic Robo Blast 2 (SRB2)
  - **N64 Classics**: Mario Kart 64 (SpaghettiKart), Star Fox 64 (Starship), GoldenEye 007 (Recomp), Perfect Dark, Paper Mario 64 (PaperBoat)
  - **Fan Overhauls**: Mega Man X: Regenesis (SNES timeline), Mega Man X8 16-Bit Demake (Touch Mod v1.6 + 100% save)
  - **Modern Decomps**: Balatro (1080p 60fps AMOLED), Space Cadet 3D Pinball, PokeMMO (All 5 generations staged)

### 5. DroidDeck Steam PC Integration & Optimization
- Automates staging and configuration for DroidDeck (`com.droiddeck.launcher`):
  - Pre-seeds `/sdcard/DroidDeck/config.json` with 720p base rendering, 1080p AMD FSR upscaling, `DXVK_ASYNC=1`, `MESA_VK_WSI_PRESENT_MODE=mailbox`, and Turnip drivers.
  - Multi-mount VDF synchronizer maps `/mnt/bannerlator-sd`, `/storage/<SD_ID>/Games/Steam`, and `D:\`.
  - Maps Steam Big Picture controller input and manages PC translation environments (x86 Proton under FEX tested; 32-bit DX9 translation remains experimental upstream in PR #1034).

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

### 9. Universal Community Patch Engine & Dolphin Widescreen Architecture (`scripts/stage_community_patches.py`)
- **PS2 Master `.pnach` Cheats**: Streams and deploys 4,700+ PCSX2 master cheats directly into NetherSX2 and ARM SX2 `patches/` and `cheats/` directories.
- **Dolphin Aspect Ratio Decoupling**: Global Dolphin graphics setting remains strictly on `Auto` (`AspectRatio = 0` in `GFX.ini`). Unpatched 4:3 titles maintain pure pillarboxing without horizontal distortion, while native 16:9 Wii games automatically scale via `[Wii] Widescreen = True`.
- **550 GameCube Per-Game Profiles (`patches/gcn/`)**:
  - **323 Gecko-Patched Games**: Injects clean engine-level camera patches under `[Gecko_Enabled]` with `[Video_Settings] AspectRatio = 1` and `wideScreenHack = False` (*Super Smash Bros. Melee*, *Super Mario Sunshine*, *The Legend of Zelda: The Wind Waker*, *Mario Kart: Double Dash!!*, *Luigi's Mansion*, *Paper Mario: TTYD*, etc.).
  - **225 Native 16:9 Games**: Configures `[Video_Settings] AspectRatio = 1` and `wideScreenHack = False` without Gecko hacks (*F-Zero GX*, *007: Nightfire*, *Red Faction II*, *Tony Hawk*, *Burnout*, *TimeSplitters*, etc.).
- **Smart Non-Destructive INI Merging**: Layers widescreen codes and video overrides on top of upstream Dolphin GameSettings without overwriting upstream bugfixes (MMU, dual-core, fastmem workarounds), and automatically propagates widescreen settings across all game revisions (`GALE01r*.ini`).

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

- **Gran Turismo 4 Spec II (ARM SX2 / NetherSX2)**:
  - 16:9 widescreen rendering with CRT overscan crop (`Crop = 1`, `CropMode = Overscan`).
  - GS readbacks disabled (`HardwareDownloadMode = 1`) to eliminate slowdowns.
  - Active 16:9 widescreen patch (`646B2E29.pnach`) loaded via game CRC.
- **Dolphin (GameCube & Wii Standalone)**:
  - **Global Aspect Ratio Auto**: `AspectRatio = 0` in `GFX.ini` preserves true 4:3 pillarboxing for unpatched retro games without manual toggling; native 16:9 Wii games automatically scale via `[Wii] Widescreen = True`.
  - **550 GameCube Per-Game Widescreen Profiles**: Staged in `patches/gcn/*.ini` (323 with active `$Widescreen Hack` Gecko codes and 225 with native 16:9 `[Video_Settings] AspectRatio = 1`).
  - **Hardware Analog Triggers**: Binds hardware triggers to true analog axes (L=`Axis 22+`, R=`Axis 23+`).
  - **Mario Kart Wii**: Configured with `WiimoteProfile1 = Classic_Controller` and `WiimoteSource0 = 1` in `RMC*.ini` without conflicting `PadType0` dropdown indices.

- **OutRun 2006: Coast 2 Coast (PPSSPP & ARM SX2)**:
  - **PPSSPP (PSP)**: 4x 1080p, locked 60 FPS, full analog trigger acceleration.
  - **ARM SX2 (PS2)**: 2.0x 1080p Vulkan, locked 60 FPS, uncompressed arcade audio and high-polygon car models.
  - *(Note: Windows PC execution under DroidDeck / FEX x86 Proton is blocked pending upstream 32-bit DX9 translation stability; play via PPSSPP or ARM SX2 on RP5).*
- **Apotris (Native Port)**:
  - Standalone ARM64 APK running at native 60fps with full gamepad mapping; bypasses GBA emulation.
- **GoldenEye 007 (Native Android Recomp)**:
  - Native 60 FPS execution on physical RP5 hardware with full dual-analog camera controls; Rareware intro and 007 gunbarrel sequence verified in-game.
- **Perfect Dark (Native Android Port)**:
  - Modern dual-analog twin-stick FPS mapping deployed via `configs/ports/perfect_dark/pd.ini` achieving 1:1 parity with Xbox Live Arcade (XBLA) "Duty Calls" preset.
  - Right analog stick controls true pitch/yaw (`StickCButtons=0`), reticle locked dead-center (`MouseAimMode=1`, `CrosshairSway=0`), modern trigger shooting (RT=Fire, LT=Aim, RB/LB=Alt-Fire, X=Reload, Y=Weapon Cycle, B/R3=Crouch).
  - In-game Control Style must be set to **"Ext"** (Mode 8: native PC Port layout).

- **Ship of Harkinian & 2 Ship 2 Harkinian (Zelda N64 Decompilations)**:
  - Native 60 FPS 1080p widescreen with 3DS Link & Young Link HD character models.
- **PokeMMO (Native MMO Client)**:
  - All 5 regions (Black, White, HeartGold, Platinum, FireRed, Emerald) loaded and verified in-game at 1080p 60fps.

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


---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the [LICENSE](LICENSE) file for details.
