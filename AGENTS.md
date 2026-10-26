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

### K. ROM Packaging & Compression Standards
- **Cartridge Systems (N64, SNES, Genesis, GBA, NES)**:
  - Standard Deflate `.zip` (level 9). Never push raw `.7z` archives to the device (Mupen64Plus FZ does not support `.7z`, and RetroArch experiences extraction lag on 64MB expanded ROMs).
  - N64 convention: `<Game Title>.n64.zip` containing exactly one clean `.z64` at the root of the archive (strip all nested subfolders, `.txt` documentation, and patch notes).
- **Disc Systems (PS1, PS2, PSP, Dreamcast, Sega CD)**:
  - Compressed `.chd` (CD-ROM/DVD MAME chdman format).
- **Nintendo Disc Systems (GameCube, Wii)**:
  - Compressed `.rvz` (Dolphin RVZ format with zstd/128KB chunking).

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

---

## 5. Operational Best Practices for Agents

1. **Master Runner**: Execute `.\scripts\provision_all.ps1 -Serial <SERIAL>` or `python scripts/setup_rp5.py --serial <SERIAL> --all`.
2. **Device State Verification**: Always check `adb devices` before executing device commands. If status is `unauthorized`, prompt the user to accept the USB debugging prompt on the device screen.
3. **Safe Storage Handling**: Do not write large binary files directly to version control. Validate paths before issuing `adb push` commands, and only push to the canonical paths in Section 2.
4. **Multiple Devices**: Multiple devices may be attached. Always query `adb devices` at runtime and pass `-s <serial>` explicitly.
5. **Markdown Clipboard Staging**: When generating markdown content for the user to post externally (GitHub PRs, issues, Discord), stage the raw text directly into the user's clipboard using PowerShell `.\scripts\stage_clipboard.ps1 -FilePath <path>` or `Get-Content <file> -Raw | Set-Clipboard` to prevent leading-space formatting corruption.
6. **OLED Display Sleep Invariant**: Whenever tasks conclude or when waiting on user feedback, power down the physical device display (`adb shell input keyevent 26`) and verify with `adb shell dumpsys power` (`mHoldingDisplaySuspendBlocker=false`) to eliminate AMOLED burn-in risk.
7. **Autonomous High-Confidence Proceed & Review Presentation Protocol**:
   - **High-Confidence Autonomous Execution**: When confidence in a recommendation, refinement, or `/learn` proposal is very high (validated against deterministic schema checks, live ADB tests, or verified source mappings), proceed with applying the improvement autonomously without halting to wait for user confirmation.
   - **Review Page Staging**: Continue generating the self-contained `.html` review page with clean styling, diff blocks, and visual hierarchy (e.g. `docs/review/<topic>.html`), and provide a clickable `file://` link for immediate visibility and audit trail.
   - **Anti-Hallucination Guardrails**: Always enforce the 5 Laws of Schema Verification (never guess INI keys/sections, use clean direct tokens under active device blocks, flatten extension syntax, and verify on live hardware logs/screenshots) before applying autonomous updates.
8. **GitHub Issue & Bug Report Automation**: The host environment has an authenticated GitHub CLI (`gh` account `dmillerzx` with full `repo` scopes). Going forward, open bug reports, feature requests, and upstream issues directly via `gh issue create --repo <owner/repo> --title "<title>" --body-file "<file>"` rather than prompting the user to submit them manually.
   - **Visual Asset Staging**: Never use local file paths or ephemeral URLs in bug reports. Stage screenshots into `docs/assets/screenshots/<name>.png`. Ensure `.gitignore` anchors `/assets/` at root so `docs/assets/` is tracked. Commit and push images to `origin main` *before* opening the issue, referencing permanent raw URLs (`https://raw.githubusercontent.com/<owner>/<repo>/main/docs/assets/screenshots/<name>.png`).
   - **Cross-Link Synchronization**: After creating an upstream issue, immediately record the returned URL in `WORKQUEUE.md` and `CLAUDE.md`, and post a synchronization comment to local repository tracking threads (e.g., Issue #1) to keep all agents and sessions aligned.
9. **Token Efficiency, Reasoning Effort & Quota Invariants**:
   - **Default to Medium Reasoning**: Routine automation, ADB execution, file patching, ROM staging, and documentation MUST run on `Medium` (or `Low`) reasoning effort. `High` reasoning is strictly reserved for deep binary reverse-engineering, elusive race-condition debugging, or explicit user instruction.
   - **Proactive Reasoning & Model Escalation Gate**: If a requested task (e.g., deep C++ NDK decompilation, complex multi-file architectural refactoring, elusive race conditions, or low-level SPIR-V/Vulkan shader debugging) would benefit significantly from `High` reasoning effort or a more capable model (e.g. `Claude 3.5 Sonnet` or `Gemini Pro`), the agent MUST pause immediately, explain the technical justification, and prompt the user to make the switch in the chat UI before proceeding with execution.
   - **Automated Turn-25 Compaction Alarm**: When a session reaches 25 turns, the agent must proactively prepend a high-visibility alert banner (`> [!IMPORTANT] Context Compaction Gate (Turn 25 Reached)`) advising the user to type `/compact` before sending their next prompt to reset quadratic transcript accumulation.
   - **Strict Compound One-Flow Execution**: Group related inspections, mutations, and verification into a single compound execution pass per turn (or unified PowerShell scratch scripts). Strictly eliminate serialized `thought -> tool -> thought -> tool` exploratory micro-turns.
   - **Output Silencing & Lean Receipts**: Never dump voluminous raw terminal/ADB outputs (e.g. `dumpsys`, full `logcat`, recursive directory trees, long test logs) directly into stdout, which permanently bloats `transcript.jsonl`. Pipe or filter outputs (`Select-Object -First 20`, `grep`), or redirect full logs to scratch files (`scratch/<name>.log`), reporting only concise exit codes and summaries.
   - **Multi-Pool Awareness**: Antigravity maintains independent quota buckets for Gemini, Claude/GPT, and Argon. When one bucket nears its 5-hour burst limiter, suggest balancing work across the other 100% available pools.
10. **Windows 11 Workstation Tuning & Shell Execution Invariants**:
   - **Dell Precision Service Boundary Law**: Always preserve `DPMService` (Dell Peripheral Manager / `DDPM.Subagent`) to protect external monitor input switching and USB-C hub peripheral controls. Set `DellTechHub` and `DellClientManagementService` to `Manual` (or `Disabled`) to eliminate 7 background telemetry subagents and prevent ~1.3 GB of idle memory bloat.
   - **Audio Shield Watchdog**: The scheduled task `MaxxAudioShield_AntiDistortion` locks Waves/Realtek services to `Start = 4` (Disabled) on boot and logon as `SYSTEM`, ensuring Peace Equalizer APO and RNNoise AI microphone filtering run with zero Realtek driver compression or distortion.
   - **OneNote Tray & Phone Link Suppression**: Office Click-to-Run must be prevented from restoring `Send to OneNote.lnk` on logon via `HKCU:\Software\Microsoft\Office\16.0\OneNote\Options\Other\EnableMemoryTrayMenuItem = 0`. Windows Phone Link background permissions must remain disabled (`Disabled = 1`, `EnableMmx = 0`).
   - **PowerShell Scratch File Execution Invariant**: When running complex PowerShell commands via agent CLI tools, never nest double-quoted script blocks or unescaped variables inside `-Command "..."`. Always stage multi-line scripts to `<appDataDir>\brain\<conversation-id>/scratch/<name>.ps1` and execute with `-File` for 100% deterministic, uncorrupted parsing.
11. **Community Project Orphan Takeover & Open-Source Forking Protocol**:
    - When an upstream maintainer announces departure or ends platform support (e.g., ThatGuyMcd on DKR-R Android), verify licensing (MIT/GPL).
    - Autonomously establish community continuity via `gh repo fork <owner>/<repo> --clone=false` under the user's account (`dmillerzx`).
    - Post empathetic, technically accurate feedback on the upstream issue explaining the hardware root cause (e.g. Qualcomm Vulkan SPIR-V compiler bugs vs mobile TBDR) and link to the community fork.
    - When multiple ports share the same underlying engine (e.g. N64Recomp + RT64 across DKR-R and Banjo Recomp), solve the bug on the orphaned project first, then backport or submit upstream PRs to active maintainers.
12. **Deep Engineering Session Boundary & Reasoning Elevation Invariant**:
    - Transitioning from high-level triage/planning to deep C++ Android NDK builds, CMake scripting, or Vulkan shader debugging MUST occur in a fresh session to eliminate transcript bloat and prevent quadratic token inflation.
    - Explicitly prompt the user to switch to a high-reasoning model (`Claude 3.5 Sonnet` or `Gemini Pro`) with `High` thinking effort before commencing native decompilation/patching work.

---

## 6. The 5 Laws of Schema Verification (Anti-Hallucination Guardrails)

To guarantee emulator stability and prevent input or configuration regressions:
1. **Never Guess INI Section Names or Key Syntaxes**: Always inspect Dolphin/emulator source code, upstream documentation, or native UI auto-mappings on the device before writing configurations. Never improvise section headers or property names.
2. **Clean Direct Tokens Under Active Device Sections**: Under an active `Device = <name>` section, bind buttons and axes using clean, direct tokens (e.g., `Button 96`, `Axis 1-`) rather than chained or device-prefixed expressions (e.g. `` `Device:Button 96` | ... ``), which fail to parse in Android UI builds.
3. **Flat Wiimote Extensions**: Dolphin Wiimote extensions (Classic, Nunchuk) live flat inside `[Wiimote1]` using extension prefixes (e.g., `Classic/Buttons/A = `Button 96``, `Nunchuk/Buttons/C = `Button 102``). Dolphin never recognizes standalone sections like `[Classic1]` or `[Wiimote1/Classic]`.
4. **Literal Plus/Minus Keys**: Dolphin keys for Plus and Minus buttons are literally `+` and `-` (e.g., `Buttons/+`, `Classic/Buttons/-`), never `Plus` or `Minus`.
5. **Always Verify with Live Hardware Logs & Screenshots**: Never declare input or emulator configuration complete without verifying via ADB dumps, live logcat output, or screen captures that in-game menus advance and inputs are cleanly captured without drawer/system popups.

