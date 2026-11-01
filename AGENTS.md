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
│   └── xbox/                     # Original Xbox trimmed XISO images (*.iso)
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
3. Android-managed folders (`Android/`, `Download/`, and stock media folders) are owned by the OS. Do not rely on them, and never delete `Android/`. `/sdcard/Download/` is used only to stage `rp5_master_obtainium.json`, Mesa Turnip drivers, and Vita firmware.
4. When pushing BIOS files, push to `/sdcard/bios/` and `/storage/<SD_ID>/bios/` only.

---

## 3. Workspace Directory Structure (host repo)

```text
AntigravityWorkingDir/
├── .agents/skills/          # Progressive skills (handheld-fork-governance, rom-and-port-staging, etc.)
├── configs/                 # Device profiles, ES-DE configs & Obtainium templates
├── patches/                 # GCN/Wii widescreen Gecko patches & PS2 pnach master cheats
├── scripts/                 # ADB automation, UI interaction & provisioning scripts
├── apks/                    # Staged offline APK installations (gitignored)
├── bios/                    # Staged system BIOS files (gitignored)
├── roms/                    # Local ROM staging (gitignored)
└── drivers/                 # Mesa Turnip Adreno 650 GPU drivers (gitignored)
```

---

## 4. Automation Protocols (`scripts/setup_rp5.py` and `scripts/provision_all.ps1`)

### A. Android 13 Phantom Process Killer Unlock
Android 12/13 enforce a maximum of 32 child processes per background app tree. Emulators and translation layers trigger silent `SIGKILL` termination. The script disables this limit:
```bash
adb shell "/system/bin/device_config set_sync_disabled_for_tests persistent"
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell "settings put global settings_enable_monitor_phantom_procs false"
```

### B. Directory Scaffolding (Canonical Layout Only)
- Creates `/sdcard/bios`.
- Automatically discovers the external MicroSD card under `/storage/XXXX-XXXX` and creates canonical directories.

### C. Staging Obtainium & DroidDeck Configuration
- Pushes `configs/rp5_master_obtainium.json` directly to `/sdcard/Download/rp5_master_obtainium.json`. Tracks RetroArch (AArch64) using Libretro's stable buildbot with a 2-level `intermediateLink` chain.
- Pushes `configs/droiddeck_config.json` (720p base rendering, FSR 1080p, `DXVK_ASYNC=1`, `MESA_VK_WSI_PRESENT_MODE=mailbox`, `TU_DEBUG=noconform`, Turnip driver) to `/sdcard/DroidDeck/config.json`.
- Deploys `configs/libraryfolders.vdf` mapping `/storage/<SD_ID>/Games/Steam` (drive `D:\\`).
- Stages Sony PS Vita OS Firmware `PSP2UPDAT.PUP` to `/sdcard/Download/vita3k/`.

### D. Ultra-Low-Latency 2D RetroArch Engine & Low-Pass Audio Filters
- Vulkan video backend, Ozone menu, frame delay 4, 48ms OpenSLES audio latency, run-ahead 1 frame.
- Genesis Model 1 low-pass filter (range 60, YM2612 MAME), SNES Gaussian audio interpolation (Snes9x), Gambatte Sinc audio resampler, GBA 5.5kHz IIR low-pass DSP filter (`gba_lowpass.dsp`) + `mGBA.slangp` LCD grid shader.

### E. Standalone 3D Emulators Injection
- **ARM SX2 (PS2 Primary)**: Direct boot via `%EMULATOR_ARMSX2% %ACTION%=android.intent.action.VIEW %DATA%=%ROMSAF%`. 2.0x 1080p Vulkan, `AspectRatio = 16:9`, `Crop = 1`, `CropMode = Overscan`, `HardwareDownloadMode = 1` (Disable Readbacks), and `touchControllerOpacity = 0`.
- **NetherSX2 (PS2 Fallback)**: 2.25x 1080p SPU2 Catmull-Rom interpolation, `AspectRatio = 16:9`, `Crop = 1`, `CropMode = Overscan`.
- **DuckStation (PS1)**: 5x 1080p PGXP, Cubeb 20ms low latency audio.
- **Dolphin (GameCube & Wii)**: 2.5x 1080p OpenSLES DSP audio, analog triggers (L=`Axis 22+`, R=`Axis 23+`). Global `SIDevice0 = 6`, `WiimoteSource0 = 1`, `WiimoteEnableGCControllers = True`. Global `GFX.ini` leaves `AspectRatio = 0` (Auto) so unpatched titles remain pillarboxed 4:3, while `[Wii] Widescreen = True` auto-scales 16:9 Wii games.
- **PPSSPP (PSP)**: 4x 1080p 16x Anisotropic filtering.
- **Flycast (Dreamcast)**: 2x 1080p Widescreen.
- **Azahar (3DS)**: 3x 1080p Mesa Turnip driver, async shader compilation.
- **Vita3K (PS Vita)**: 2x 1080p Vulkan, `initial-setup: false`, `backend-renderer: Vulkan`, `pref-path: "/storage/emulated/0/Android/data/org.vita3k.emulator/files/vita"`, overlay opacity 0.

### F. Universal Community Patch Engine (`scripts/stage_community_patches.py`)
- **PS2**: Deploys 4,700+ `.pnach` master cheats to both `patches/` and `cheats/`.
- **GameCube & Wii**: Staged 550 GameCube per-game profiles in `patches/gcn/` (323 verified Gecko widescreen codes and 225 native 16:9 configurations) assigning `[Video_Settings] AspectRatio = 1` and `wideScreenHack = False`. Upstream Dolphin GameSettings are smartly merged. Global `GFX.ini` keeps `AspectRatio = 0` (Auto).

### G. Save & State Backup Pipeline
- Systematically mirrors saves, states, and virtual memory cards across all emulators to `/storage/<SD_ID>/Saves_Backup/latest/`.

### H. Retroid OS System & Hardware Tuning
- **Lockscreen**: Disabled (`locksettings set-disabled true`).
- **Floating Overlay**: Disabled (`settings put system is_show_floatingIcon 0`).
- **Auto-Rotate**: Disabled (`settings put system accelerometer_rotation 0`) to lock landscape orientation.
- **Controller Style**: Xbox mode (`persist.sys.gamepad.type 0`).
- **Trigger Mode**: Both analog axis + digital button click (`persist.sys.trigger.mode 2`).
- **Fan Profile**: Smart active cooling (`settings put system fan_mode 4`).
- **Performance Mode Invariant**: Maintain regular **Performance** mode (`settings put system performance_mode 1`) as the default baseline. NEVER autonomously switch or elevate the device to "High Performance" (Extreme) mode.
- **OLED Display Saturation & Color Calibration**: The RP5 AMOLED panel natively covers ~140-150% sRGB. Enforce `persist.sys.sf.color_saturation 0.90` default (`0.70` for mathematical 100% sRGB reference target). Disable *Intelligent environment adaptation* (`automatic_button`) and enforce neutral white balance (`nature`).

### I. Granting AppOps
Android 11+ restricts storage access under Scoped Storage:
```bash
adb shell appops set <package.name> MANAGE_EXTERNAL_STORAGE allow
adb shell appops set dev.imranr.obtainium REQUEST_INSTALL_PACKAGES allow
adb shell appops set com.droiddeck.launcher REQUEST_INSTALL_PACKAGES allow
```

### J. Native Android Port Configurations
- **Perfect Dark (`com.perfectdark.port`)**: XBLA "Duty Calls" Twin-Stick formula (`StickCButtons = 0`, In-game Control Style "Ext" Mode 8, `MouseAimMode = 1`, `CrosshairSway = 0`, `Lookspring = OFF`, `CK_8000 = JOY1_B, JOY1_RSTICK`, `Z_TRIG = JOY1_RTRIGGER`, `R_TRIG = JOY1_LTRIGGER`).
- **Super Mario 64 ALO (`com.izzyagamer.sm64alo`)**: Clean touchless binary, BetterCamera 360° analog stick look, multi-bound crouch to ZL/L1/L3.
- **Sonic Mania Plus (`com.decomp.rsdkv5`)**: 1080p 60 FPS native rendering with `Data.rsdk` staged to `/sdcard/RSDK/v5/`.
- **GoldenEye 007 Recomp (`com.sunjaycy.goldeneye`)**: Game files in root `/sdcard/Android/data/com.sunjaycy.goldeneye/files/` (never `files/assets/`). Injected circular gunbarrel 007 adaptive icon. Always backup files before reinstall.
- **CannonBall Arcade OutRun (`CannonBall - OutRun.game`)**: Libretro CannonBall core with 60 FPS 16:9 widescreen arcade ROMs.
- **LibUltraShip Ports (SoH, 2S2H, Starship, PaperBoat)**: Extract authentic N64 ROM as `baserom.us.z64` via internal `Torch` extractor, generating `*.o2r`. Disable touch controls (`"Enabled": 0`), OpenGL backend ID 1. Register standalone `.app` launcher in ES-DE.

### K. ROM Packaging & Compression Standards (Summary)
- **N64**: Strictly uncompressed big-endian `.z64` (Russ/Retro Game Corps standard; never `.zip` or `.7z`).
- **NDS**: Strictly uncompressed `.nds`.
- **16-bit / 8-bit**: Standard Deflate `.zip` (level 9, exactly 1 game per archive; never `.7z`).
- **Disc Systems (PS1, PS2, PSP, Dreamcast, Saturn)**: Compressed `.chd`.
- **GameCube & Wii**: Compressed `.rvz` (zstd/128KB chunking) or `.wbfs` for Wii.
- **Xbox (hakuX)**: Sector-aligned trimmed XDVDFS `.iso` via `extract-xiso -c` (78.1% space savings, DMA streaming, zero CPU decompression).
*(Full runbook in `.agents/skills/rom-and-port-staging/SKILL.md`.)*

### L. GPU Driver Architecture & Adreno 650 Governance
- **Snapdragon 865 (SM8250 / Adreno 650)**: Gold standard driver is `turnip_v24.3.0_R9v2.zip` (K11MCH1), with `TurnipZ-0.3.0.zip` (AlexSanz0902) for heavy Vulkan.
- **Architectural Boundary**: Native Android ports and direct OS bounded emulators bind directly to `/system/lib64/libvulkan.so` with zero translation overhead. Never inject Turnip drivers into native ports. Never stage Adreno 7xx-only (`vulkan.ad07xx.so`) builds.
*(Full runbook in `.agents/skills/adreno-gpu-drivers/SKILL.md`.)*

### M. Controller Configuration Preservation Invariant
Automated provisioning scripts must **never** unconditionally overwrite existing emulator controller mappings on-device:
1. **Dolphin Guard**: Check if `GCPadNew.ini` or `WiimoteNew.ini` exists before pushing; skip if present to preserve user calibrations.
2. **RetroArch & Standalone Pads**: Input profiles in NetherSX2, ARM SX2, DuckStation, and PPSSPP must respect user-calibrated files once created.

### N. Architecture-Driven Platform Routing Heuristic
- **Bespoke Console Titles**: Native PS2 titles (*Gran Turismo 4*, *God of War*) run locked 60 FPS at 2.0x 1080p on SD865.
- **PC/Xbox-Ported Outliers**: DirectX 8/9 ported titles (*OutRun 2006*) fight PS2 hardware. Route to PSP (PPSSPP 4x 1080p 444 MHz locked 60 FPS), GameCube (Dolphin 2.5x 1080p), or Native PC (DroidDeck / Wine).

### O. Android 13 Dynamic Linker Classloader Namespace Invariant
On Android 13 (Retroid OS on RP5), the Android dynamic linker restricts native library loading via `classloader-namespace`:
- RetroArch cannot `dlopen()` any `.so` dynamic library located on external storage (`/sdcard/` or MicroSD).
- Non-root write boundary prevents writing to internal `/data/user/0/com.retroarch.aarch64/cores/`.
- Frontend assets (shaders, configs, joypads) stage to MicroSD, but executable `.so` cores **must** be downloaded inside RetroArch via **Online Updater ➔ Core Downloader**.

### P. Downstream Handheld Fork Governance & Release Protocols
Detailed runbook in [`.agents/skills/handheld-fork-governance/SKILL.md`](.agents/skills/handheld-fork-governance/SKILL.md):
1. **Continuous Upstream Sync**: Rebase downstream branches against `upstream/main` (`ahead_by: N, behind_by: 0`).
2. **Community Release Obligation**: Package standalone signed preview APKs (`Package-Android-Preview.ps1`) and publish to GitHub Releases with SHA-256 checksums and controller mappings.
3. **Android Target Boundary**: Compile specific Android shared library targets (`DKRPortGame` / `libDKR-R.so`), never default desktop test targets.
4. **CI Flake Isolation**: Do not let host test flakes on unrelated OS targets (e.g. macOS WebRTC socket timeouts) block Android releases.
5. **Branch Protection Prohibition**: Never enforce branch protection or required passing checks on downstream maintenance forks (`dmillerzx/*`).
6. **Pattern-Guard Indexing**: Sort new patches alphabetically into `architecture/pattern-guard-baseline.txt` and tag PRs with `transition-layer`.
7. **Local Ruff Preflight**: Execute `ruff check` and `ruff format --check` locally before pushing python test/tooling changes.
8. **Homepage Release Prominence**: Standalone APK releases must be promoted to `--latest` (`--prerelease=false`).
9. **Law 16 (Release Metadata Atomic Sync)**: Bumping `VERSION` must atomically register the release in `packaging/linux/*.appdata.xml`. Verify with `python scripts/check.py --suite tooling`.
10. **Law 17 (Upstream pull_request_target CI Triage)**: Upstream `validate-external` failures from `actions/checkout@v4` on `pull_request_target` are expected upstream security guardrails, not fork PR defects. Maintain verification on fork workflows (`Android APK`).

### Q. Original Xbox Emulation (hakuX) & XDVDFS Sector Standards
1. **Package**: `com.rfandango.haku_x` staged via Obtainium. ROMs in `/storage/<SD_ID>/ROMs/xbox/`.
2. **Trimmed XISO Standard**: Pack titles with `extract-xiso -c` (78.1% space savings, DMA streaming, zero CPU decompression).
3. **ES-DE Dispatch**: `%EMULATOR_HAKUX% %ACTION%=android.intent.action.VIEW %DATA%=%ROMSAF%`.
4. **Geometry**: Original Xbox geometry is governed by emulated EEPROM `Screen Format` (`Normal` 4:3 vs. `Wide screen` 16:9) and game engine support. Force global `Aspect Ratio: 4:3` in hakuX for 4:3-only titles (*Crazy Taxi 3*, *JSRF* v1).

---

## 5. Specialized Skills Reference Directory

For domain-specific procedures, refer directly to the corresponding skills:
- **Downstream Fork Governance & Releases**: [`.agents/skills/handheld-fork-governance/SKILL.md`](.agents/skills/handheld-fork-governance/SKILL.md)
- **ROM Packaging & Port Profiles**: [`.agents/skills/rom-and-port-staging/SKILL.md`](.agents/skills/rom-and-port-staging/SKILL.md)
- **Qualcomm Adreno 650 Drivers**: [`.agents/skills/adreno-gpu-drivers/SKILL.md`](.agents/skills/adreno-gpu-drivers/SKILL.md)
- **RP5 Hardware & OLED Display Sleep**: [`.agents/skills/rp5-device-control/SKILL.md`](.agents/skills/rp5-device-control/SKILL.md)
- **Workstation Tuning & Audio Shield**: [`.agents/skills/workstation-tuning/SKILL.md`](.agents/skills/workstation-tuning/SKILL.md)
- **YouTube Research & Setup Guides**: [`.agents/skills/youtube-research/SKILL.md`](.agents/skills/youtube-research/SKILL.md)
- **Binary Reverse Engineering (REA)**: [`.agents/skills/reverse-engineer-anything/SKILL.md`](.agents/skills/reverse-engineer-anything/SKILL.md)
