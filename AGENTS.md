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
    ├── apply_windows_optimizations.ps1 # Dell Precision 5560 Windows 11 workstation optimization suite
    ├── lock_audio_services.ps1         # MaxxAudio shield watchdog & Equalizer APO health verifier
    ├── register_audio_shield_task.ps1  # Automated SYSTEM boot/logon scheduled task registrar
    ├── rollback_services_and_optimizations.ps1 # Zero-loss rollback orchestrator for host optimizations
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
- **Dolphin (GameCube & Wii)**: 2.5x 1080p OpenSLES DSP audio, analog triggers (L=`Axis 22+`, R=`Axis 23+`). Global `SIDevice0 = 6`, `WiimoteSource0 = 1`, `WiimoteEnableGCControllers = True`. Global `GFX.ini` leaves `AspectRatio = 0` (Auto) so unpatched titles remain pillarboxed 4:3, while `[Wii] Widescreen = True` auto-scales 16:9 Wii games. Binds `WiimoteProfile1 = Classic_Controller` and `WiimoteSource0 = 1` in Mario Kart Wii (`RMC*.ini`) without conflicting `PadType0` dropdown indices.
- **PPSSPP (PSP)**: 4x 1080p 16x Anisotropic filtering.
- **Flycast (Dreamcast)**: 2x 1080p Widescreen.
- **Azahar (3DS)**: 3x 1080p Mesa Turnip driver, async shader compilation.
- **Vita3K (PS Vita)**: 2x 1080p Vulkan, `initial-setup: false`, `backend-renderer: Vulkan`, `pref-path: "/storage/emulated/0/Android/data/org.vita3k.emulator/files/vita"`, overlay opacity 0.

### F. Universal Community Patch Engine (`scripts/stage_community_patches.py`)
- **PS2 (NetherSX2 / PCSX2)**: Downloads and deploys 4,700+ `.pnach` master cheats to both `patches/` and `cheats/`.
- **GameCube & Wii (Dolphin)**: Staged 550 GameCube per-game profiles in `patches/gcn/` (323 verified Gecko widescreen codes and 225 native 16:9 configurations) assigning `[Video_Settings] AspectRatio = 1` and `wideScreenHack = False`. Upstream Dolphin GameSettings are smartly merged, preserving game bugfixes while layering widescreen codes across base and revision INIs. Global `GFX.ini` keeps `AspectRatio = 0` (Auto) to ensure unpatched 4:3 titles remain pillarboxed without distortion.
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
- **Performance Mode Invariant**: Maintain regular **Performance** mode (`settings put system performance_mode 1`) as the default baseline (or Standard `0` if user requests). NEVER autonomously switch or elevate the device to "High Performance" (Extreme) mode.
- **OLED Display Saturation & Color Calibration**: The RP5 AMOLED panel natively covers ~140-150% sRGB (DCI-P3 wide gamut). For authentic, non-neon retro rendering with 0 ms added latency:
  - System Property: `persist.sys.sf.color_saturation` (`0.90` default for punchy OLED pop without highlight clipping; `0.70` for mathematical 100% sRGB reference target).
  - Retroid OS Colors: Disable *Intelligent environment adaptation* (`automatic_button`) to prevent real-time ambient lux sensor drift; enforce white balance *nature* (neutral D65 reference).
  - OdinTools (`de.langerhans.odintools`): Uses `PServerBinder` to persist SurfaceFlinger saturation overrides (`service call SurfaceFlinger 1022 f <val>`) across reboots via `BootReceiver`.

### I. Granting AppOps
Android 11+ restricts storage access under Scoped Storage. The script invokes AppOps:
```bash
adb shell appops set <package.name> MANAGE_EXTERNAL_STORAGE allow
adb shell appops set dev.imranr.obtainium REQUEST_INSTALL_PACKAGES allow
adb shell appops set com.droiddeck.launcher REQUEST_INSTALL_PACKAGES allow
```

### J. Native Android Port Configurations (e.g., Perfect Dark)
- Deploys device-tuned INIs to `/sdcard/Android/data/<package>/files/` and `/sdcard/<port>/`.
- **Perfect Dark (`com.perfectdark.port`) XBLA "Duty Calls" Twin-Stick Formula**:
  - `StickCButtons = 0`: Outputs unquantized 360° analog pitch/yaw to `rstick_x` and `rstick_y`.
  - In-game Control Style must be **"Ext"** (Control Mode 8 in `libpd.so`). Selecting legacy N64 styles (e.g., 1.2 Solitaire) sets `w20 != 8`, bypassing the modern analog look path and reverting to discrete digital C-button stepping.
  - `MouseAimMode = 1`: Locks reticle dead-center on screen for modern FPS aim (eliminates floating cursor/crosshair bounding box delay).
  - `CrosshairSway = 0`: Eliminates reticle wobble while moving.
  - In-game `Lookspring = OFF`: Disables automatic camera leveling to the horizon when walking forward.
  - `UseKeyReloads = 1` + `X_BUTTON = JOY1_X`: Dedicated instant reload.
  - `CK_8000 = JOY1_B, JOY1_RSTICK`: Modern single-button/R3 toggle crouch.
  - `Z_TRIG = JOY1_RTRIGGER` (RT fire) & `R_TRIG = JOY1_LTRIGGER` (LT precision aim/zoom).
  - Profile maintained in `configs/ports/perfect_dark/pd.ini` and staged via `stage_port_configs()`.
- **Super Mario 64 ALO (`com.izzyagamer.sm64alo`)**:
  - Clean touchless binary (`sm64.alo.clean.apk`) deployed removing hardcoded touch overlays.
  - Multi-bound crouch/ground-pound/long-jump: `key_z` bound to ZL (`101a`) + L1 (`1009`) + L3 (`1007`); `key_b` to X and B; BetterCamera 360° analog stick look (`bettercam_analog true`, sensitivity 70); VSync locked to 60.0 FPS.
- **Sonic Mania Plus (`com.decomp.rsdkv5`)**:
  - Engine installed with `Data.rsdk` (208 MB) and `Settings.ini` staged to `/sdcard/RSDK/v5/` and app files. 1080p 60 FPS native rendering.
- **GoldenEye 007 Recomp (`com.sunjaycy.goldeneye`)**:
  - `default.xex` and game files must reside in root `/sdcard/Android/data/com.sunjaycy.goldeneye/files/` (never nested under `files/assets/`).
  - Injected custom James Bond gunbarrel 007 circular adaptive icon into APK mipmaps and mirrored to ES-DE covers.
  - Signature Migration Invariant: Always backup `/sdcard/Android/data/com.sunjaycy.goldeneye/files/` before any uninstall/reinstall cycle to preserve multi-track audio banks and player save profiles.
- **CannonBall Arcade OutRun (`CannonBall - OutRun.game`)**:
  - Libretro CannonBall core (`cannonball_libretro_android.so`) deployed with 60 FPS 16:9 widescreen arcade ROMs, eliminating DX9 PC translation overhead.
- **LibUltraShip Decompilation Ports (SoH, 2S2H, Starship, PaperBoat)**:
  - Push authentic N64 ROM as `baserom.us.z64` into `/sdcard/Android/data/<package>/files/`.
  - Launch `<package>/.LauncherActivity` to execute internal C++ `Torch` extractor natively on-device, generating `*.o2r` (e.g. `pm64.o2r` 40.1 MB).
  - Disable on-screen touch overlays via `"gTouchControls": {"Enabled": 0}` and set backend ID `1` (OpenGL) in `<port>.cfg.json`.
  - Register standalone `.app` launcher pointing to `<package>` in `/storage/<SD_ID>/ROMs/ports/` dispatched via `<command label="Android App">%ANDROIDAPP%=%FILEINJECT%</command>`.

### K. ROM Packaging & Compression Standards (Retro Game Corps Best Practices)
- **Nintendo 64 (N64)**:
  - **Format**: Strictly uncompressed / extracted `.z64` (big-endian).
  - **Rule**: Never leave N64 games in `.zip` or `.7z` archives on the device. Standalone emulators (such as Mupen64Plus-FZ) and frontends (ES-DE) experience loading, parsing, or extraction delay issues with compressed N64 archives. Big-endian `.z64` is the native format of the Nintendo 64 hardware, ensuring maximum compatibility across standalone emulators and native recompilation ports without on-the-fly byte-swapping.
- **Nintendo DS (NDS)**:
  - **Format**: Uncompressed `.nds`. Eliminates redundant `.zip` duplicates and ensures instant loading in standalone DraStic and melonDS DS.
- **16-bit / 8-bit Cartridge Systems (SNES, Genesis, GBA, NES)**:
  - Standard Deflate `.zip` (level 9, exactly 1 game per archive). Never push `.7z` archives to the device.
- **Disc Systems (PS1, PS2, PSP, Dreamcast, Sega CD, Saturn)**:
  - Compressed `.chd` (CD-ROM/DVD MAME chdman format).
- **Nintendo Disc Systems (GameCube, Wii)**:
  - Compressed `.rvz` (Dolphin RVZ format with zstd/128KB chunking) or `.wbfs` for Wii.
- **Original Xbox (hakuX)**:
  - Sector-aligned trimmed XDVDFS `.iso` generated via `extract-xiso -c` (78.1% space savings, direct DMA streaming, zero decompression overhead).

### L. GPU Driver Architecture & Adreno 650 Governance
- **Device SoC**: Qualcomm Snapdragon 865 (SM8250 / Kona) with Adreno 650 GPU (`a6xx` architecture family).
- **Driver Hierarchy**:
  1. `turnip_v24.3.0_R9v2.zip` (K11MCH1): Gold-standard general-purpose Turnip driver for RP5 (Azahar 3DS, DroidDeck DXVK).
  2. `TurnipZ-0.3.0.zip` (AlexSanz0902): SD865-customized Mesa 27.0-devel branch (highest Switch/heavy Vulkan FPS, Unreal Engine color fixes).
  3. `Turnip-24.1.0.adpkg_R18.a6xx.zip`: Dedicated `a6xx` depth clearing & tessellation fix.
  4. Qualcomm Kona Stock Driver (`com.qualcomm.qti.gpudrivers.kona.api30`): Built-in system driver; default for PS2, Dolphin baseline, and native Android ports.
- **Architectural Boundary**: Native Android ports (Perfect Dark, SM64 ALO, Banjo, SoH, Sonic Mania, etc.) and direct OS bounded emulators (ARM SX2, NetherSX2, PPSSPP, Flycast, DuckStation) bind directly to `/system/lib64/libvulkan.so` and execute natively on Qualcomm hardware with zero translation overhead. Do not attempt to inject Turnip ZIPs into native ports.
- **Adreno 6xx Invariant**: Never stage Adreno 7xx-only (`vulkan.ad07xx.so`) driver archives as primary drivers on the RP5. Always verify `meta.json` inside driver ZIPs.

### M. Controller Configuration Preservation Invariant
Automated provisioning scripts (`setup_rp5.py`, `configure_standalones.py`, `provision_all.ps1`) must **never** unconditionally overwrite existing emulator controller mappings on the device:
1. **Dolphin Controller Guard**: Always check if `GCPadNew.ini` or `WiimoteNew.ini` exists on-device before pushing. If present, skip deploying controller templates to preserve user-calibrated physical button assignments and stick deadzones.
2. **RetroArch & Standalone Pads**: Input profiles in NetherSX2, ARM SX2, DuckStation, and PPSSPP must respect user-calibrated files once created.

### N. Architecture-Driven Platform Routing Heuristic
When a title exists across multiple platforms (e.g. PS2, GameCube, PSP, Native PC):
1. **Bespoke Console Titles**: Titles engineered natively for the PS2 architecture (e.g., *Gran Turismo 4*, *God of War*, *Devil May Cry 3*) run at a locked 60 FPS at 2.0x 1080p on the Snapdragon 865.
2. **PC/Xbox-Ported Outliers**: Titles originally engineered for PC/Xbox architectures (DirectX 8/9 with programmable shaders, e.g., *OutRun 2006: Coast 2 Coast*) fight the PS2 hardware, triggering excessive `autoFlush` stalls and single-threaded Emotion Engine bottlenecks.
3. **Preferred Routing**: For these outlier titles, prioritize:
   - **PSP (PPSSPP)**: Rendered at 4x Native (1080p) with emulated CPU clock unlocked to `444 MHz` for a locked 60 FPS presentation.
   - **GameCube (Dolphin)**: 2.5x 1080p with Gecko widescreen patches.
   - **Native PC (DroidDeck / Wine)**: Once 32-bit x86 DX9 translation stabilizes under FEX.

### O. Android 13 Dynamic Linker Classloader Namespace Invariant (RetroArch Cores)
On Android 10+ and strictly on Android 13 (Retroid OS on RP5), the Android dynamic linker restricts native library loading via `classloader-namespace`:
- **Permitted Paths**: `permitted_paths="/data:/mnt/expand:/data/user/0/com.retroarch.aarch64"`.
- **External Storage Prohibition**: RetroArch cannot `dlopen()` any `.so` dynamic library located on `/sdcard/`, `/storage/emulated/0/`, or external MicroSD (`/storage/<SD_ID>/RetroArch/cores/`). Attempts to pass external core paths fail with:
  `dlopen failed: library "..." is not accessible for the namespace: [name="classloader-namespace"]`
- **Non-Root Write Boundary**: Unrooted ADB shell cannot write to `/data/user/0/com.retroarch.aarch64/cores/` (`Permission denied`), and `run-as` is unavailable on non-debuggable production builds.
- **Operational Requirement**:
  1. **Assets vs. Cores**: Frontend assets (Shaders, Joypad Autoconfig, Info files) can and should be staged to `/storage/<SD_ID>/RetroArch/`.
  2. **Core Acquisition**: Executable `.so` cores **must** be downloaded directly inside RetroArch via **Online Updater ➔ Core Downloader**. Provisioning scripts and agents must not assume pushing `.so` binaries to external storage provides a functional core.
  3. **Standalone N64 Routing**: If an in-app core download is not preferred, route N64 to standalone Mupen64Plus FZ (`org.mupen64plusae.v3.fzurita`) in `es_settings.xml`.

### P. Downstream Handheld Fork Governance & Android Target Boundary Law
1. **Continuous Upstream Synchronization**: When maintaining an orphaned or downstream handheld fork (e.g., DKR-R Android on `dmillerzx/DKR-R`), continuously track and rebase against `upstream/main` and upstream release tags. Downstream branches must never lag behind upstream bugfixes and engine enhancements (`ahead_by: N, behind_by: 0`).
2. **Community Standalone Release Obligation**: Handheld console users cannot compile C++ Android NDK code on-device. Whenever an upstream sync or downstream platform fix completes, package standalone signed APKs (`Package-Android-Preview.ps1`) and publish them to GitHub Releases with verified SHA-256 checksums and controller mapping instructions.
3. **Android CMake Library Target Boundary**: Never invoke default build targets in hybrid C++/Android projects. Default targets compile desktop host tests (e.g. `DKRMipmapLoadingTests`), which fail due to native window type mismatches. Always build the specific Android shared library target (e.g. `DKRPortGame` / `libDKR-R.so`).
4. **CI Host Test Flake Isolation**: Host test failures on unrelated platforms (e.g. WebRTC socket timing on GitHub Actions macOS VMs) must be recognized as platform-specific CI flakes and isolated from blocking Android release delivery.
5. **Downstream Fork Branch Protection Prohibition**: Never configure GitHub branch protection rules or require mandatory passing status checks on downstream maintenance forks (`dmillerzx/*`). Upstream test flakes on unrelated OS targets (e.g., macOS VM WebRTC socket timeouts) block handheld Android PR merges, and branch protection obstructs zero-friction fast-forward rebasing against upstream release tags.
6. **Pattern-Guard Baseline Indexing & Transition-Layer PR Invariant**: In repositories enforcing architectural pattern guards (e.g., `scripts/pattern_guard.py` rule `PG013`), newly staged dependency or platform patches must be sorted alphabetically into `architecture/pattern-guard-baseline.txt`. Accompanying pull requests must be explicitly tagged with the `transition-layer` label (`gh pr edit <PR> --add-label transition-layer`) so CI diff checks accept baseline expansion.
7. **Local Python Linter Preflight (`ruff`)**: Before pushing commits modifying Python contract tests, build tools, or packaging scripts in repos enforcing automated linting, always execute `ruff check` and `ruff format --check` locally to eliminate CI turnaround cycles.
8. **Homepage Release Prominence**: Standalone community APK releases must be promoted to the official latest release (`--latest`, `--prerelease=false`) so the download card and badge render prominently on the repository homepage sidebar rather than being collapsed under tags ("Create a new release").

### Q. Original Xbox Emulation (hakuX) & XDVDFS Sector Standards
1. **Package & Distribution**: `com.rfandango.haku_x` (tracked via Obtainium from `https://github.com/haku-x/hakux-emu` releases).
2. **Canonical ROM Storage**: `/storage/<SD_ID>/ROMs/xbox/`.
3. **ROM Image Standard (Trimmed XISO)**:
   - Original Xbox optical discs use a proprietary Cross-Title Virtual Disc File System (XDVDFS) layout with a standard DVD video partition in the lead-in and game data at sector 305,600.
   - Raw Redump DVD-9 images (7.05 GiB) waste up to 90% of their volume on zero-byte sector padding.
   - Extracting into loose folder structures breaks hakuX, which expects sector-accurate virtual disc geometry.
   - All Xbox titles must be packed into trimmed XISOs using `extract-xiso -c` (e.g. `scripts/deploy_xbox_roms.py`), yielding a 78.1% storage reduction while preserving exact XDVDFS sector offsets.
4. **Streaming Decompression Economics (XISO vs. CSO/ZSO)**:
   - While hakuX supports block compression (`.cso` / `.zso` via maxcso), community standards (Retro Game Corps / Russ) prioritize uncompressed trimmed `.iso`.
   - On the Snapdragon 865, streaming uncompressed XDVDFS images incurs 0% CPU decompression overhead via direct storage DMA, dedicating maximum CPU throughput to x86-to-ARM64 JIT dynamic translation and eliminating stutter during high-bandwidth asset streaming.
5. **GPU Driver**: Mesa Turnip Adreno 650 GPU driver (`turnip_v24.3.0_R9v2.zip`).
6. **ES-DE Launch Dispatch Syntax (`%DATA%=%ROMSAF%`)**:
   - In `configs/es_systems.xml` and `/sdcard/ES-DE/custom_systems/es_systems.xml`, hakuX must be launched via:
     `<command label="hakuX (Standalone)">%EMULATOR_HAKUX% %ACTION%=android.intent.action.VIEW %DATA%=%ROMSAF%</command>`
   - Standalone emulator launches in ES-DE must not use raw shell syntax (`am start -d %ROM%`) or raw POSIX paths (`%ROM%`), as Android 11+ Scoped Storage requires SAF Content URIs with granted permissions to access MicroSD storage.
7. **Aspect Ratio Architecture & EEPROM Screen Format Standards**:
   - Original Xbox geometry is determined by two layers: the console's virtual EEPROM `Screen Format` (`Normal` 4:3 vs. `Wide screen` 16:9 anamorphic) and game engine support.
   - Titles engineered exclusively for 4:3 (e.g., *Crazy Taxi 3: High Roller*, *Jet Set Radio Future* v1) lack widescreen code. When hakuX's global `Screen Format` is set to `Wide screen` and `Aspect Ratio` is set to `Auto`, hakuX assumes 16:9 output and horizontally stretches 4:3 games edge-to-edge.
   - **Pillarboxing Standard**: For pure 4:3 games, set hakuX's global **`Aspect Ratio` = `4:3`** (or toggle `Screen Format` to `Normal`). Setting `Aspect Ratio: 4:3` guarantees clean 1:1 circular pillarboxing (black sidebars) regardless of EEPROM settings.
   - **Per-Game Scope**: Decompiled binary inspection of `libhaku.so` confirms that `gameOverrides` currently only support `render_scale`, `upscale_filter`, and `driver` overrides; aspect ratio and screen format are global emulator settings in hakuX v1.2.x.

### R. ES-DE Custom Systems Architecture & XML Parser Invariant
1. **Canonical Custom Systems Location**: Custom systems live at `/sdcard/ES-DE/custom_systems/es_systems.xml` (internal storage) and `/storage/<SD_ID>/ES-DE/custom_systems/es_systems.xml` (MicroSD).
2. **Strict XML Parser Law**: ES-DE enforces strict XML schema validation on startup. Any unclosed tag, mismatched tag, or malformed entity causes a fatal modal crash on launch (`Failed to parse es_systems.xml`). Always validate custom XML trees using Python `xml.etree.ElementTree.parse()` prior to deployment.
3. **Intent Extra & Content URI Tokens**: ES-DE provides native tokens for Android intent dispatch: `%ACTION%`, `%DATA%=%ROMSAF%`, and `%EXTRA_*%`. Never attempt to chain ADB shell `am start` arguments into standalone `<command>` definitions.

### S. Retroid Pocket 5 Hall Effect Analog Stick Calibration & Deadband Invariant
1. **Hardware Characteristic**: The Retroid Pocket 5 features Hall effect magnetic analog joysticks. Unlike traditional potentiometers, Hall sensors eliminate physical wiper friction and mechanical wear.
2. **Center-Point Variance**: Hall effect sensors exhibit subtle resting magnetic variance (±3-5% around center). In emulators or native ports with zero deadband, this variance causes phantom micro-inputs, subtle camera creeping, or menu navigation jitter.
3. **Standard Calibration**: Always apply a 10% software deadband across primary emulators:
   - Dolphin: `Main Stick/Dead Zone = 10.0` and `C-Stick/Dead Zone = 10.0` in `GCPadNew.ini`.
   - ARM SX2: `Deadzone = 0.06` with `AxisScale = 1.33` in `RP5r.ini` for full outer circular reach.
   - RetroArch: `input_analog_deadzone = 0.10`.
   - Native Ports: `stick_deadzone = 6.0` to `10.0`.

### T. Reverse Engineer Anything (REA) Framework & MCP Integration
1. **Unified Reverse-Engineering Engine**: REA (`morluto/rea` v6.8.0) provides a unified agent-first framework for binary disassembly, headless JADX Android APK decompilation, ADB device telemetry, and Frida dynamic tracing without requiring original source code.
2. **Workstation Runtime & CLI**: Node.js LTS (`>=26.12.1`) is maintained on the host workstation. The `rea-agents` package is installed globally (`npm install --global rea-agents`), providing the standalone `rea` CLI command in PATH.
3. **Antigravity MCP Integration**: Configured in `~/.gemini/config/mcp_config.json` via direct Stdio execution (`node.exe .../scripts/rea.mjs mcp`) with `REA_ADB_PATH` explicitly pointing to the workspace `platform-tools/adb.exe`. Verified via `rea doctor --client antigravity` with `healthy: true` and `state: aligned`.
4. **Progressive Disclosure Skill**: Staged in `.agents/skills/reverse-engineer-anything/`. The skill activates autonomously whenever the task involves inspecting compiled binaries (ELF `.so`, DEX, APK, PE, IL2CPP, Dart AOT), missing source code, or live hardware hooks.
5. **Repository Boundary Law**: Agents MUST strictly observe REA's core rule: *"Skip REA for ordinary source-repository architecture analysis."* When analyzing or editing existing workspace source files, Python scripts, INI configs, or documentation, agents must use normal repository tools (`read_file`, `edit_file`) rather than REA to conserve tokens and speed.

### U. Extensibility Architecture & Zero-Marketplace Plugin Invariant
1. **Zero-Marketplace Plugin Invariant**: The Antigravity environment must maintain exactly **0** marketplace plugins (`agy plugin list` reports `No plugins installed`). Never install third-party marketplace plugins into this workspace. Third-party plugins package eager tool schemas, global rules, and lifecycle hooks that inject thousands of static tokens into every prompt turn and subagent call, exhausting the 5-hour rolling context quota.
2. **Progressive Disclosure Skill Standard**: All procedural workflows, automation patterns, and runbooks must be created as standalone skills in `.agents/skills/<name>/SKILL.md`. Under Antigravity's progressive disclosure architecture, only the skill name and brief description are loaded into the agent prompt (~50 tokens total), and full runbook text is loaded strictly on demand when activated.
3. **Personal Account Air-Gap & PII Boundary**: Maintain a complete air-gap between Antigravity and personal communication/calendar services. Never configure or request OAuth tokens or credentials for personal email (Gmail/Outlook) or calendar accounts in this provisioning workspace. If schedule or email text is required for a specific task, it must be provided as static, sanitized text or localized files (`.ics`, `.txt`) explicitly shared by the user in chat.
4. **Language Server Customization Inspection Protocol**: When programmatically inspecting installed plugins or extensions, query the local language server connect endpoint (`ANTIGRAVITY_LS_ADDRESS` + `ANTIGRAVITY_CSRF_TOKEN`) via `GetAllPlugins` or run `agy plugin list`. Never read `GetAllPlugins` unfiltered as it inlines the complete markdown text of every bundled skill; always filter down to names and paths.

### V. Handheld Porting, Obtainium Asset Architecture & Driver Packaging Standards
1. **Obtainium Direct Download URL Standard**: All Obtainium manifest records in `rp5_master_obtainium.json` and on-device records (`/data/data/dev.imranr.obtainium/app_flutter/app_data/*.json`) must use public browser download URLs (`https://github.com/<owner>/<repo>/releases/download/<tag>/<filename>.apk`). Never use GitHub REST API asset endpoints (`api.github.com/repos/.../releases/assets/<id>`), which return JSON metadata on unauthenticated calls and trigger `"no APK found"` errors during batch updates.
2. **AdrenoTools Root Driver Packaging & `meta.json` Soname Resolution**: AdrenoTools driver loaders (e.g., in `BanjoSDLActivity.java` or emulator wrappers) must read `meta.json`'s `libraryName` (e.g. `libvulkan_freedreno.so`) and accept root-level `.so` entries rather than mandating an `arm64-v8a/` directory structure. Standard community Turnip ZIPs (`TurnipZ-0.3.0.zip`, `turnip_v24.3.0_R9v2.zip`) package files at the archive root.
3. **Android Recomp Handheld Profile Baseline**: N64 recompiled native Android ports (RT64 / RecompUI) must default on first boot to 60 FPS target refresh rate, 16:9 Expand aspect ratio, `Original 2x` (480p) internal rendering resolution, and dual-trigger crouch multi-binding (Z mapped to both ZL/axis 22 and L1/shoulder) with C-Down dedicated to the right analog stick. All handheld modern defaults must be strictly encapsulated inside `#if defined(__ANDROID__)`.
4. **GitHub Fork Actions Default Permission Boundary**: Community forks under `dmillerzx/*` default to read-only workflow permissions on GitHub Actions. CI release jobs attempting to attach APK artifacts will fail with HTTP 403 `Resource not accessible by integration` unless write permissions are explicitly granted at the repository level via `gh api -X PUT /repos/<owner>/<repo>/actions/permissions/workflow -f default_workflow_permissions=write`.
5. **RT64/Plume Vulkan Null-Pipeline Guard**: RT64 Plume Vulkan bindings trigger null pipeline dereferences in Qualcomm's Adreno 650 driver (`qglinternal::vkCmdBindPipeline`). Engine patches modifying submodule dependencies (`lib/rt64/src/contrib/plume`) must be applied in CI scripts targeting the specific submodule directory (`git -C "${PWD}/lib/rt64/src/contrib/plume" apply "$patch"`).
6. **Obtainium Tag-to-Manifest Divergence & Version Detection Standard**: When third-party APK releases on GitHub use a release tag (e.g. `v1.0.2`) that differs from the internal `versionName` compiled into `AndroidManifest.xml` (e.g., author forgot to bump `versionName "1.0.1"` in Gradle), Obtainium's `"versionDetection": true` ("Reconcile version string with version detected from OS") causes an endless pending update loop. Obtainium detects the OS version as `1.0.1`, compares it to `v1.0.2`, flags `"This app config may prevent updates"`, and persistently queues the app for update even after repeated installs. For any app exhibiting tag-to-manifest divergence, set `"versionDetection": false` in `configs/rp5_master_obtainium.json` and set both `installedVersion` and `latestVersion` to the canonical release tag (e.g. `v1.0.2`). This instructs Obtainium to track GitHub's canonical release tags directly, clearing the update loop while properly notifying on subsequent releases. In the Obtainium UI, clear lingering update indicators using `Additional options` ➔ `Mark updated` (`Yes, mark as updated`).
7. **Downstream CI Hot-Loop Optimization vs. Substring Contract Test Invariant**: When refactoring or patching downstream graphics pipelines (e.g., `plume_vulkan.cpp` in DKR-R) to eliminate hot-loop `stderr` logging or debug output, verify whether unit or contract test suites (e.g., `android_startup_contract_tests.py`) assert substrings or diagnostic stage tokens (`Stage::ComputePipeline`). If diagnostic strings are removed, update the contract test to assert the functional branch guard (e.g. `s_activeComputePipelineValid = false`) rather than the removed `fprintf` call.
8. **Platform-Agnostic Git Patch Streaming in Tests**: When invoking `git apply` inside Python contract or unit tests across multiple host platforms, never pass absolute filesystem paths with Windows drive letters (`C:\...`) to `git apply <path>`. MinGW/MSYS git misinterprets Windows drive prefixes. Always stream the patch bytes via standard input: `subprocess.run(["git", "-C", stage, "apply", "--recount", "--whitespace=error", "--ignore-space-change", "-"], input=patch_path.read_bytes(), check=True)`.



---


### W. Static Binary Recompilation ROM Version Invariant & Zero-Touch Hydration Law
1. **Static Recompilation Base ROM Dependency**: Static binary recompilations (e.g., N64Recomp, Banjo Recompiled, Zelda 64 Recompiled) statically recompile the machine instructions and RAM layout of one specific base ROM revision (e.g. NTSC-U v1.0 / Rev 0). Subsequent revisions (such as Rev A / v1.1 or European PAL) feature shifted code addresses and different data tables; feeding them to `librecomp` fails cryptographic hash checks (`RomValidationError::IncorrectVersion`).
2. **Silent Android Message Box Failure**: In RecompUI on Android, `recompui::message_box()` defaults to a console `printf("[ERROR]...")` because SDL's native message box path requires active Java Activity state. When an unsupported revision is selected, the document picker closes silently and reloads the launcher menu with "Load ROM", giving the false appearance that the game crashed or refused to open.
3. **Cartridge Header Version Inspection**: Android port wrappers must inspect the N64 cartridge header at bytes `0x3B–0x3F` on selection:
   - Offset `0x3B–0x3E`: Game ID (`NBKE` for Banjo-Kazooie)
   - Offset `0x3F`: Revision byte (`0x00` = v1.0 / Rev 0, `0x01` = Rev A / v1.1, `0x02` = Rev B / v1.2)
   - If an unsupported revision is selected, the application MUST present an explicit `AlertDialog` / `Toast` explaining that v1.0 is required.
4. **Zero-Touch Boot Hydration**: To eliminate friction with Android's DocumentsUI on controller-based handhelds, the startup activity (`onCreate`) must scan common storage locations (`/sdcard/Android/data/<package>/files/` and MicroSD `/storage/*/ROMs/n64/`) for authentic base ROMs (`*.z64`), verify the header signature, and automatically copy the verified ROM into internal storage (`data/<game_id>.z64`). On boot, `recomp::is_rom_valid()` evaluates to `true` immediately and the primary launcher button displays "Start Game" without requiring manual file navigation.
5. **Redundant Revision Pruning**: To prevent user selection errors and eliminate duplicate entries on ES-DE game wheels, incompatible cartridge revisions (e.g. `Banjo-Kazooie (USA) (Rev A).z64`) must be pruned from the MicroSD library once the working base ROM is verified.

### X. Handheld Repository Discoverability & Release Prominence Protocol
1. **Comprehensive Community Topics**: Community forks and provisioning toolkits under `dmillerzx/*` must configure rich GitHub repository topics (`gh repo edit --add-topic <topic>`) targeting the hardware SoC, GPU, architecture, and handheld model (e.g., `retroid-pocket-5`, `snapdragon-865`, `adreno-650`, `turnip`, `vulkan`, `recompilation`, `handheld-gaming`, `ayn-odin`, `adb-automation`).
2. **Action-Oriented Description**: Keep repository descriptions concise and focused on hardware-specific enhancements (e.g. Adreno 650 crash fix, Turnip GPU drivers, ZIP support, 60 FPS defaults).
3. **Homepage Release Prominence**: All standalone community APK releases must be promoted as the official latest release (`--latest`, `--prerelease=false`) so the release card and download badge render prominently on the repository homepage sidebar rather than being collapsed under tags.
4. **Master Toolkit Release Synchronization**: When significant automation scripts, port profiles, and driver configurations accumulate on the master provisioning repository, tag and publish formal community releases (e.g. `v1.1.0`) documenting the complete ecosystem progress.

---

## 5. Operational Best Practices for Agents

1. **Master Runner**: Execute `.\scripts\provision_all.ps1 -Serial <SERIAL>` or `python scripts/setup_rp5.py --serial <SERIAL> --all`.
2. **Device State Verification**: Always check `adb devices` before executing device commands. If status is `unauthorized`, prompt the user to accept the USB debugging prompt on the device screen.
3. **Safe Storage Handling**: Do not write large binary files directly to version control. Validate paths before issuing `adb push` commands, and only push to the canonical paths in Section 2.
4. **Multiple Devices**: Multiple devices may be attached. Always query `adb devices` at runtime and pass `-s <serial>` explicitly.
5. **Markdown Clipboard Staging**: When generating markdown content for the user to post externally (GitHub PRs, issues, Discord), stage the raw text directly into the user's clipboard using PowerShell `.\scripts\stage_clipboard.ps1 -FilePath <path>` or `Get-Content <file> -Raw | Set-Clipboard` to prevent leading-space formatting corruption.
6. **Strict Personal Privacy & PII Protection Invariant**: NEVER leak, publish, commit, or stage the user's real name, email, physical address, or any personally identifiable information (PII) into README files, commit messages, licenses, PRs, issues, or documentation. Strictly use the public GitHub handle (`dmillerzx`) or generic terms ("community contributor", "maintainer").
7. **Dynamic Hardware Identifier & Anti-Leak Invariant**: NEVER hardcode physical device serial numbers (e.g. `<SERIAL>`) or MicroSD filesystem UUIDs (e.g. `<SD_ID>`) into automation scripts, documentation, or commit history. Local `.git/hooks/pre-commit` enforces strict pattern rejection. Scripts must dynamically discover devices via `adb devices` (`detect_device()`) and MicroSD mount paths via `adb shell ls /storage/` (`detect_sd_id()`), providing `--serial` and `--sd-id` CLI overrides.
8. **OLED Display Sleep Invariant**: Whenever tasks conclude or when waiting on user feedback, ensure the physical device display is powered down to eliminate AMOLED burn-in risk. Since `input keyevent 26` is a toggle, first query `adb shell "dumpsys power | grep mWakefulness="`. Only execute `adb shell input keyevent 26` if `mWakefulness=Awake`. Verify with `adb shell "dumpsys power | grep -E 'mHoldingDisplay|mWakefulness'"` that `mHoldingDisplaySuspendBlocker=false` and `mWakefulness=Dozing`.
9. **Autonomous High-Confidence Proceed & Review Presentation Protocol**:
   - **High-Confidence Autonomous Execution**: When confidence in a recommendation, refinement, or `/learn` proposal is very high (validated against deterministic schema checks, live ADB tests, or verified source mappings), proceed with applying the improvement autonomously without halting to wait for user confirmation. For all `/learn` invocations with high conviction, implement the changes automatically and only ask for confirmation if genuinely unsure or facing ambiguous tradeoffs.
   - **Review Page Staging**: Continue generating the self-contained `.html` review page with clean styling, diff blocks, and visual hierarchy (e.g. `docs/review/<topic>.html`), and provide a clickable `file://` link for immediate visibility and audit trail.
   - **Anti-Hallucination Guardrails**: Always enforce the 5 Laws of Schema Verification (never guess INI keys/sections, use clean direct tokens under active device blocks, flatten extension syntax, and verify on live hardware logs/screenshots) before applying autonomous updates.
10. **GitHub Issue & Bug Report Governance (Human-in-the-Loop & Anti-AI Spam)**:
   - **No Autonomous Upstream Submissions**: NEVER autonomously submit issues, bug reports, or feature requests to third-party upstream repositories (e.g., `rt64/rt64`, `HarbourMasters/*`, etc.) via `gh issue create`. Autonomous creation is permitted ONLY on the user's personal forks and tracking repositories (`dmillerzx/*`).
   - **Upstream Submission Approval**: All reports or communications intended for external upstream maintainers must be drafted locally (e.g. in `docs/community_reports/`), presented to the user, and staged to clipboard (`.\scripts\stage_clipboard.ps1`) for explicit user review and manual posting.
   - **No AI-Generated Report Templates**: When drafting bug reports for external maintainers, NEVER use standard LLM templates (e.g. "Root Cause Analysis", "Suggested Fixes for Developers", bold didactic bullet lists). Keep reports concise, human, and focused purely on concrete reproduction steps, raw stack traces, and targeted context. Always verify whether upstream actually supports the target platform before raising platform-specific issues.
   - **Visual Asset Staging**: Never use local file paths or ephemeral URLs in bug reports. Stage screenshots into `docs/assets/screenshots/<name>.png`. Ensure `.gitignore` anchors `/assets/` at root so `docs/assets/` is tracked. Commit and push images to `origin main` *before* opening the issue, referencing permanent raw URLs (`https://raw.githubusercontent.com/<owner>/<repo>/main/docs/assets/screenshots/<name>.png`).
   - **Cross-Link Synchronization**: After an upstream issue is created, record the URL in `WORKQUEUE.md` and `CLAUDE.md`, and track it locally on fork issues to keep all agents and sessions aligned.
11. **Token Efficiency, Reasoning Effort & Quota Invariants**:
   - **Default to Medium Reasoning**: Routine automation, ADB execution, file patching, ROM staging, and documentation MUST run on `Medium` (or `Low`) reasoning effort. `High` reasoning is strictly reserved for deep binary reverse-engineering, elusive race-condition debugging, or explicit user instruction.
   - **Proactive Reasoning & Model Escalation Gate**: If a requested task (e.g., deep C++ NDK decompilation, complex multi-file architectural refactoring, elusive race conditions, or low-level SPIR-V/Vulkan shader debugging) would benefit significantly from `High` reasoning effort or a more capable model (e.g. `Claude 3.5 Sonnet` or `Gemini Pro`), the agent MUST pause immediately, explain the technical justification, and prompt the user to make the switch in the chat UI before proceeding with execution.
   - **Automated Turn-25 Compaction Alarm**: When a session reaches 25 turns, the agent must proactively prepend a high-visibility alert banner (`> [!IMPORTANT] Context Compaction Gate (Turn 25 Reached)`) advising the user to type `/compact` before sending their next prompt to reset quadratic transcript accumulation.
   - **Strict Compound One-Flow Execution**: Group related inspections, mutations, and verification into a single compound execution pass per turn (or unified PowerShell scratch scripts). Strictly eliminate serialized `thought -> tool -> thought -> tool` exploratory micro-turns.
   - **Output Silencing & Lean Receipts**: Never dump voluminous raw terminal/ADB outputs (e.g. `dumpsys`, full `logcat`, recursive directory trees, long test logs) directly into stdout, which permanently bloats `transcript.jsonl`. Pipe or filter outputs (`Select-Object -First 20`, `grep`), or redirect full logs to scratch files (`scratch/<name>.log`), reporting only concise exit codes and summaries.
   - **Multi-Pool Awareness**: Antigravity maintains independent quota buckets for Gemini, Claude/GPT, and Argon. When one bucket nears its 5-hour burst limiter, suggest balancing work across the other 100% available pools.
12. **Windows 11 Workstation Tuning & Shell Execution Invariants**:
   - **Dell Precision Service Boundary Law**: Always preserve `DPMService` (Dell Peripheral Manager / `DDPM.Subagent`) to protect external monitor input switching and USB-C hub peripheral controls. Set `DellTechHub` and `DellClientManagementService` to `Manual` (or `Disabled`) to eliminate 7 background telemetry subagents and prevent ~1.3 GB of idle memory bloat.
   - **Audio Shield Watchdog**: The scheduled task `MaxxAudioShield_AntiDistortion` locks Waves/Realtek services to `Start = 4` (Disabled) on boot and logon as `SYSTEM`, ensuring Peace Equalizer APO and RNNoise AI microphone filtering run with zero Realtek driver compression or distortion.
   - **OneNote Tray & Phone Link Suppression**: Office Click-to-Run must be prevented from restoring `Send to OneNote.lnk` on logon via `HKCU:\Software\Microsoft\Office\16.0\OneNote\Options\Other\EnableMemoryTrayMenuItem = 0`. Windows Phone Link background permissions must remain disabled (`Disabled = 1`, `EnableMmx = 0`).
   - **PowerShell Scratch File Execution Invariant**: When running complex PowerShell commands via agent CLI tools, never nest double-quoted script blocks or unescaped variables inside `-Command "..."`. Always stage multi-line scripts to `<appDataDir>\brain\<conversation-id>/scratch/<name>.ps1` and execute with `-File` for 100% deterministic, uncorrupted parsing.
13. **Community Project Orphan Takeover & Open-Source Forking Protocol**:
    - When an upstream maintainer announces departure or ends platform support (e.g., ThatGuyMcd on DKR-R Android), verify licensing (MIT/GPL).
    - Autonomously establish community continuity via `gh repo fork <owner>/<repo> --clone=false` under the user's account (`dmillerzx`).
    - Post empathetic, technically accurate feedback on the upstream issue explaining the hardware root cause (e.g. Qualcomm Vulkan SPIR-V compiler bugs vs mobile TBDR) and link to the community fork.
    - When multiple ports share the same underlying engine (e.g. N64Recomp + RT64 across DKR-R and Banjo Recomp), solve the bug on the orphaned project first, then backport or submit upstream PRs to active maintainers.
14. **Deep Engineering Session Boundary & Reasoning Elevation Invariant**:
    - Transitioning from high-level triage/planning to deep C++ Android NDK builds, CMake scripting, or Vulkan shader debugging MUST occur in a fresh session to eliminate transcript bloat and prevent quadratic token inflation.
    - Explicitly prompt the user to switch to a high-reasoning model (`Claude 3.5 Sonnet` or `Gemini Pro`) with `High` thinking effort before commencing native decompilation/patching work.
15. **REA Framework, MCP Integration & Autonomous Triggering**:
    - REA (`morluto/rea`) provides on-demand native reverse engineering, APK manifest analysis, and ADB telemetry via 229 MCP tools.
    - Antigravity triggers the `reverse-engineer-anything` skill autonomously when evaluating compiled targets, missing source code, or low-level runtime evidence.
    - For ordinary repository source and scripting, agents must use native tools (`read_file`, `edit_file`) to keep token usage lean.
16. **Extensibility Architecture, Zero-Marketplace Plugin & Personal Account Air-Gap Invariant**:
    - Keep installed marketplace plugins at 0 to eliminate eager tool schemas and rule bloat.
    - Implement all project runbooks as on-demand progressive disclosure skills in `.agents/skills/`.
    - Maintain a strict air-gap from personal email and calendar accounts; all imported data must be provided as explicit, sanitized local files or chat excerpts.
    - Always filter language server `GetAllPlugins` queries when inspecting extensions programmatically.
17. **Obtainium Direct Asset URLs & Handheld Recomp Invariants**:
    - Enforce direct release download URLs in Obtainium (`releases/download/<tag>/<filename>.apk`) to prevent `"no APK found"` batch update failures.
    - AdrenoTools loaders must parse `libraryName` from `meta.json` and accept root-level `.so` entries without enforcing `arm64-v8a/` directory nesting.
    - N64 recompilation ports must default to 60 FPS, 16:9 Expand, `Original 2x` (480p), and dual ZL+L1 crouch bindings under `#if defined(__ANDROID__)`.
    - Unblock GitHub Actions release attachments on downstream forks via `gh api -X PUT /repos/<owner>/<repo>/actions/permissions/workflow -f default_workflow_permissions=write`.


---

## 6. The 13 Laws of Schema Verification & Device Standards (Anti-Hallucination Guardrails)

To guarantee emulator stability and prevent input or configuration regressions:
1. **Never Guess INI Section Names or Key Syntaxes**: Always inspect Dolphin/emulator source code, upstream documentation, or native UI auto-mappings on the device before writing configurations. Never improvise section headers or property names.
2. **Clean Direct Tokens Under Active Device Sections**: Under an active `Device = <name>` section, bind buttons and axes using clean, direct tokens (e.g., `Button 96`, `Axis 1-`) rather than chained or device-prefixed expressions (e.g. `` `Device:Button 96` | ... ``), which fail to parse in Android UI builds.
3. **Flat Wiimote Extensions**: Dolphin Wiimote extensions (Classic, Nunchuk) live flat inside `[Wiimote1]` using extension prefixes (e.g., `Classic/Buttons/A = `Button 96``, `Nunchuk/Buttons/C = `Button 102``). Dolphin never recognizes standalone sections like `[Classic1]` or `[Wiimote1/Classic]`.
4. **Literal Plus/Minus Keys**: Dolphin keys for Plus and Minus buttons are literally `+` and `-` (e.g., `Buttons/+`, `Classic/Buttons/-`), never `Plus` or `Minus`.
5. **Always Verify with Live Hardware Logs & Screenshots**: Never declare input or emulator configuration complete without verifying via ADB dumps, live logcat output, or screen captures that in-game menus advance and inputs are cleanly captured without drawer/system popups.
6. **Strict ES-DE Custom Systems XML Schema & `%DATA%=%ROMSAF%` Law**: Custom systems reside at `/sdcard/ES-DE/custom_systems/es_systems.xml`. ES-DE enforces strict XML parsing on boot; malformed or unclosed tags crash ES-DE with a fatal error. Always preflight XML using `xml.etree.ElementTree`. Standalone Android emulators requiring SAF Content URIs must use `%DATA%=%ROMSAF%` rather than raw `-d %ROM%` shell arguments.
7. **Xbox Aspect Ratio & EEPROM Screen Format Standards**: Original Xbox display geometry is governed by emulated EEPROM `Screen Format` and game engine capabilities. 4:3-only titles (*Crazy Taxi 3*, *Jet Set Radio Future* v1) stretch horizontally when console format is `Wide screen` with `Auto` aspect ratio. For authentic geometry, force global `Aspect Ratio: 4:3` in hakuX (or toggle `Screen Format` to `Normal`). Decompiled `libhaku.so` confirms `gameOverrides` do not currently support aspect ratio overrides.
8. **Hall Effect Joystick Resting Deadband Invariant**: RP5 Hall effect magnetic analog sticks have subtle resting variance (±3-5%). Always enforce a 10% deadband across Dolphin (`Dead Zone = 10.0`), ARM SX2 (`Deadzone = 0.06`), and RetroArch (`input_analog_deadzone = 0.10`) to eliminate premature camera drift or sprint triggering.
9. **Obtainium Tag-to-Manifest Divergence & Version Detection Standard**: When upstream APK releases on GitHub use a release tag (e.g. `v1.0.2`) that differs from the internal `versionName` compiled into `AndroidManifest.xml` (e.g. author forgot to bump `versionName "1.0.1"` in Gradle), Obtainium's `"versionDetection": true` ("Reconcile version string with version detected from OS") causes an endless pending update loop. Obtainium detects the OS version as `1.0.1`, compares it to `v1.0.2`, flags `"This app config may prevent updates"`, and persistently queues the app for update even after repeated installs. For any app exhibiting tag-to-manifest divergence, set `"versionDetection": false` in `configs/rp5_master_obtainium.json` and set both `installedVersion` and `latestVersion` to the canonical release tag (e.g. `v1.0.2`). This instructs Obtainium to track GitHub's canonical release tags directly, clearing the update loop while properly notifying on subsequent releases. In the Obtainium UI, clear lingering update indicators using `Additional options` ➔ `Mark updated` (`Yes, mark as updated`).
10. **Downstream CI Hot-Loop Optimization vs. Substring Contract Test Invariant**: When refactoring or patching downstream graphics pipelines (e.g., `plume_vulkan.cpp` in DKR-R) to eliminate hot-loop `stderr` logging or debug output, verify whether unit or contract test suites (e.g., `android_startup_contract_tests.py`) assert substrings or diagnostic stage tokens (`Stage::ComputePipeline`). If diagnostic strings are removed, update the contract test to assert the functional branch guard (e.g. `s_activeComputePipelineValid = false`) rather than the removed `fprintf` call.
11. **Platform-Agnostic Git Patch Streaming in Tests**: When invoking `git apply` inside Python contract or unit tests across multiple host platforms, never pass absolute filesystem paths with Windows drive letters (`C:\...`) to `git apply <path>`. MinGW/MSYS git misinterprets Windows drive prefixes. Always stream the patch bytes via standard input: `subprocess.run(["git", "-C", stage, "apply", "--recount", "--whitespace=error", "--ignore-space-change", "-"], input=patch_path.read_bytes(), check=True)`.
12. **Android Component Resolution & UI Automation Focus Assertion Invariant**: When authoring or executing ADB UI automation scripts, never use shorthand dot notation (`am start -n <pkg>/.<Activity>`) assuming the activity name matches the application ID, particularly for preview or flavor packages where `applicationId` (e.g. `*.preview`) differs from the compiled Java class (e.g. `*.DkrActivity`). Always resolve the exact component string via `dumpsys package <pkg> | grep -i Activity`. Furthermore, all UI automation QA test scripts MUST query `dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'` immediately post-launch to assert that the target component is actively focused in the foreground before sending evdev/key events or capturing verification screenshots. If the target package is not focused, the script must fail fast with a fatal assertion error rather than capturing an unintended background app.
13. **Vulkan Mobile Scissor Rect & Viewport Clamping Invariant (`VUID-00282`)**: On mobile TBDR architectures (Qualcomm Adreno 6xx/7xx), negative scissor offsets (`left < 0` or `top < 0`) violate Vulkan specification `VUID-VkRect2D-offset-00282` and cause mobile hardware drivers to discard draw calls entirely. When rendering 2D/3D mixed projection viewports or widescreen letterboxes, all scissor coordinates must be clamped strictly against target framebuffer boundaries (`[0, fbWidth]`, `[0, fbHeight]`) before submitting to `vkCmdSetScissor`. Zero-area or inverted rects must fall back to `VkRect2D{ {0, 0}, {0, 0} }`.

