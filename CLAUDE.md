# CLAUDE.md — Retroid Pocket 5 Automation & Active Troubleshooting Briefing

This repository is the **Retroid Pocket 5 (RP5) Automated Provisioning Workspace**. It contains ADB automation scripts, staging directories, configurations, patch definitions, and native port assets used to configure, optimize, provision, and maintain the Retroid Pocket 5 handheld gaming console.

---

## 1. Hardware & System Context

- **Device**: Retroid Pocket 5 (RP5)
- **Serial**: Dynamically read via `platform-tools/adb.exe devices` (always pass `-s <serial>` with ADB commands)
- **SoC**: Qualcomm Snapdragon 865 (SM8250)
- **GPU**: Adreno 650 (supports custom Turnip/Mesa drivers via Vulkan in supported emulators)
- **OS**: Android 13 (AOSP-based Retroid OS)
- **Display**: 5.5-inch 1080p AMOLED (1920x1080), 60Hz
- **Gamepad / Inputs**:
  - Integrated physical controls set to **Xbox Mode** (`persist.sys.gamepad.type 0`)
  - Trigger Mode set to **Both** (`persist.sys.trigger.mode 2` — analog axis + digital click)
  - Android Input Name: `Xbox Wireless Controller` (registered in Android `dumpsys input`)
- **Canonical Storage Layout**:
  - Internal: `/sdcard/bios/`
  - MicroSD: `/storage/<SD_ID>/` (UUID dynamically discovered, currently `EEEF-F762`)
    - `/storage/<SD_ID>/bios/` (Canonical BIOS shared by all emulators)
    - `/storage/<SD_ID>/ROMs/<system>/` (Canonical ROM root; NO ROMs on internal storage)
    - `/storage/<SD_ID>/ROMs/ports/` (Native Android port launchers `*.app`)
    - `/storage/<SD_ID>/ES-DE/` (Frontend data, gamelists, themes)
    - `/storage/<SD_ID>/RetroArch/` (Configs, cores, filters, shaders)
    - `/storage/<SD_ID>/Saves_Backup/latest/` (Save & memory card backup mirrors)
    - `/storage/<SD_ID>/Games/Steam/` (External DroidDeck Steam library)

> [!CAUTION]
> **Canonical Storage Rules**: Never create or push to `Games/BIOS`, `BIOS/`, `roms/` (lowercase), `Emulation/`, or `/sdcard/ROMs`. ROMs strictly reside in `/storage/<SD_ID>/ROMs/<system>/`.

---

## 2. Resolved Milestones (Verified on Hardware)

The following issues and components have been completely resolved and verified via live screen/logcat inspection:

1. **Gran Turismo 4 Spec II v1.10 (ARM SX2)**:
   - Full 16:9 widescreen rendering, circular HUD gauges, CRT overscan crop (`Crop = 1`, `CropMode = Overscan`), 2.0x Vulkan upscaling, and suppressed touch overlay.
2. **Mario Kart Wii (Dolphin)**:
   - Dual controller conflict resolved. Clean `GCPadNew.ini` mappings with direct tokens under active `Device` sections; GameCube port 1 native scheme active.
3. **OutRun 2006: Coast 2 Coast (DroidDeck Steam Integration)**:
   - Unnested canonical path to `/storage/EEEF-F762/Games/Steam/steamapps/common/OutRun 2006 Coast 2 Coast/`.
   - Updated `libraryfolders.vdf` in all three mount locations (`Games/Steam/`, `Games/Steam/steamapps/`, and DroidDeck rootfs `files/steam/steamapps/`) with App ID `"8960"`.
   - Verified live in DroidDeck: OutRun 2006 appears under the **Games** tab with the **Launch** button, launch settings, FSR 1080p upscaling, and `WINEDLLOVERRIDES="dinput8=n,b"` ready.
4. **Apotris Native Android Port**:
   - Upstream ARM64 build (`com.apotris.android`) installed with ES-DE launcher at `/storage/EEEF-F762/ROMs/ports/Apotris.app`.
   - Verified running at silky-smooth native 60fps with full controller support, rendering GBA emulation obsolete.
5. **PokeMMO 5-Region Staging**:
   - Clean retail ROMs for all 5 generations/regions (*Black*, *White*, *HeartGold*, *SoulSilver*, *Platinum*, plus *FireRed* & *Emerald*) extracted and staged to `/sdcard/Download/pokemmo_roms/` and internal sandbox `/sdcard/Android/data/eu.pokemmo.client/files/roms/`.
6. **Dreamcast Duplicate Cleanup**:
   - Confirmed single clean CDI format for *Arcade Racing Legends - Road Trip Edition*; duplicate CHD safely removed.
7. **GoldenEye 007 (Recomp)**:
   - Resolved asset path issue: `default.xex` and game files were previously placed in `files/assets/` rather than the root `files/` directory, causing "Game files not found (default.xex is missing)".
   - Relocated files directly to `/sdcard/Android/data/com.sunjaycy.goldeneye/files/` and verified on-device: game boots, loads full Twycross/Rare intro, and advances to the iconic James Bond gunbarrel animation.
8. **Active Verified Native Ports (14 Titles Live on Device)**:
   - Super Mario 64 / Star Fox 64 (Starship) / Mario Kart 64 (SpaghettiKart) / Ocarina of Time (Ship of Harkinian) / Majora's Mask (2 Ship 2 Harkinian) / Zelda 3 (A Link to the Past) / GoldenEye 007 (Recomp) / Perfect Dark / Sonic 3 A.I.R. / Sonic Robo Blast 2 (SRB2) / Balatro / Space Cadet 3D Pinball / Mega Man X: Regenesis / Mega Man X8 16-Bit Demake (Touch Mod v1.6 + 100% save).

---

## 3. Active Blockers & Known Technical Bottlenecks

### Issue 1: The RT64 Adreno 650 Vulkan Pipeline Crash (DKR-R & Banjo Recomp)
- **Affected Packages**:
  - `io.github.thatguymcd.dkrr.preview` (Diddy Kong Racing Recomp v1.0.6)
  - `com.aure.banjorecomp` (Banjo-Kazooie Recomp v0.1.2)
- **Root Cause Verified via Logcat**:
  - Both ports use the `RT64` Vulkan backend (`recompui::renderer::RT64Context`).
  - DKR-R: Null pointer dereference (`SEGV_MAPERR`) inside `/vendor/lib64/hw/vulkan.adreno.so` at `qglinternal::vkCmdBindPipeline` when executing `RT64::DisplayList`.
  - Banjo Recomp: Crash inside `recompui::renderer::RT64Context::send_dummy_workload(unsigned int)+132` in `vulkan.adreno.so` (upstream GitHub issue #19: Adreno 650 driver incompatibility).
  - Standalone Android APKs cannot inject custom Turnip drivers because they bind directly to system `libvulkan.so`.
- **Recommended Action / Workaround**:
  - Do not attempt to rewrite the APK unless recompiling with an OpenGL ES fallback or custom Turnip loader hook.
  - Both titles run at a locked 60 FPS in 1080p with high-res texture packs via **Mupen64Plus FZ Standalone**.

### Issue 2: Paper Mario 64 Android Port Status
- **Current State**:
  - Decompilation is 100% complete (`pmret/papermario`).
  - HarbourMasters' official `PaperBoat` port currently targets Windows, Linux, and macOS only.
  - The community Android fork (`YlPorts/PaperBoat-android`) does not provide precompiled release APKs yet.
- **Recommended Action**:
  - Monitor `PaperBoat-android` for new release tags. In the meantime, route Paper Mario 64 through Mupen64Plus FZ Standalone in ES-DE.

---

## 4. Next Tasks on the Master Roster (Queued)

Consult [WORKQUEUE.md](WORKQUEUE.md) for the active 30-item task tracking table. The immediate next titles queued for deployment are:

1. **Super Mario 64 (`sm64ex-alo`)**: Deploy standalone APK with Render96 HD models/textures, 60fps interpolation, and 360° right-stick analog camera.
2. **Another Metroid 2 Remake (`AM2R`)**: Deploy v1.5.5+ Android build with uncompressed stereo audio and 16:9 widescreen canvas.
3. **Sonic Mania (`RSDKv5`)**: Deploy Retro Engine v5 native Android APK + `Data.rsdk` assets.
4. **Sonic 1, 2 & CD (`RSDKv3/v4`)**: Deploy widescreen 60fps decompilation APKs.
5. **CannonBall: OutRun**: Deploy 60fps widescreen C++ arcade rewrite.
6. **Hollow Knight & Celeste**: Deploy standalone native ARM64 Android ports.

---

## 5. UI Automation & Testing Protocol

To avoid coordinate guesswork and UI hangs:
- Use `scripts/android_ui.py` for deterministic UI element interaction via UIAutomator XML parsing and centroid calculation:
  ```powershell
  # Dump all visible elements
  python scripts/android_ui.py --dump

  # Click element by exact text or substring
  python scripts/android_ui.py --click-text "Play Steam"
  python scripts/android_ui.py --click-contains "OutRun"

  # Deterministically select files in Android DocumentsUI / SAF pickers
  python scripts/android_ui.py --select-file "oot.otr"
  ```
- Always verify running applications with `dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'` and logcat.
- When capturing screenshots, verify the file size before opening to prevent truncated image read errors.

---

## 6. Execution Guidance for Claude

1. **Working Directory**: `C:\Users\dmill\Documents\AntigravityWorkingDir`
2. **Local ADB Binary**: `.\platform-tools\adb.exe -s <SERIAL>`
3. **Local Python**: `python` (Python 3.12 at `C:\Users\dmill\AppData\Local\Programs\Python\Python312\python.exe`)
4. **Git Branch**: `main` (commit all changes cleanly before concluding sessions)
5. **Task Master**: Always read and update [WORKQUEUE.md](WORKQUEUE.md) when changing task status.
