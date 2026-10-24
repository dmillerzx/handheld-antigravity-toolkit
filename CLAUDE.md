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
  - MicroSD: `/storage/<SD_ID>/` (UUID dynamically discovered at runtime)
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
3. **OutRun 2006: Coast 2 Coast (DroidDeck Steam Integration & PR #1034)**:
   - Canonical path established at `/storage/<SD_ID>/Games/Steam/steamapps/common/OutRun 2006 Coast 2 Coast/`.
   - `libraryfolders.vdf` updated in all mount points with App ID `"8960"`.
   - DroidDeck updated in-app to PR #1034 test build (x86 Proton under FEX).
   - Diagnosed root causes of user's "No licenses" / exit code 2 errors: `steam://rungameid` shortcut mismatch and missing `appmanifest_8960.acf` in retail installs.
   - Reconfigured compatibility tool via evdev to `Proton Experimental` (x86 Proton under FEX). 32-bit DX9 translation under FEX remains experimental upstream.
   - Flawless 1080p 60fps alternatives verified on RP5: PPSSPP (4x 1080p) and ARM SX2 (2.0x 1080p Vulkan).
4. **Apotris Native Android Port**:
   - Upstream ARM64 build (`com.apotris.android`) installed with ES-DE launcher at `/storage/<SD_ID>/ROMs/ports/Apotris.app`.
   - Verified running at silky-smooth native 60fps with full controller support, rendering GBA emulation obsolete.
5. **PokeMMO 5-Region In-Game Setup (100% Verified)**:
   - Fixed Scoped Storage access by granting `READ_EXTERNAL_STORAGE` and `WRITE_EXTERNAL_STORAGE` permissions via `pm grant`.
   - Loaded all 5 regional ROMs through on-device Client Management SAF picker:
     - NDS Base: *Pokemon Black* (`pokemon_black.nds`)
     - GBA Regions: *Pokemon FireRed* (`Pokemon FireRed Version (USA) (Rev-A).gba`), *Pokemon Emerald* (`Pokemon Emerald Version (USA).gba`)
     - NDS Visual Overhauls: *Pokemon Platinum* (`pokemon_platinum.nds`), *Pokemon HeartGold* (`pokemon_heartgold.nds`)
   - Verified live in-game: Client Management confirms header `NDS: POKEMON B, POKEMON PL, POKEMON HG | GBA: BPRE v1.1, BPEE v1.0` and boots cleanly into the live animated cloud login screen (`pokemmo_login_form.png`).
6. **Dreamcast Duplicate Cleanup**:
   - Confirmed single clean CDI format for *Arcade Racing Legends - Road Trip Edition*; duplicate CHD safely removed.
7. **GoldenEye 007 (Recomp)**:
   - Resolved asset path issue: `default.xex` and game files were previously placed in `files/assets/` rather than the root `files/` directory, causing "Game files not found (default.xex is missing)".
   - Relocated files directly to `/sdcard/Android/data/com.sunjaycy.goldeneye/files/` and verified on-device: game boots, loads full Twycross/Rare intro, and advances to the iconic James Bond gunbarrel animation (`ge_live.png`).
8. **Active Verified Native Ports (19 Titles Live on Device)**:
   - Super Mario 64 (sm64ex-alo) / Another Metroid 2 Remake (AM2R) / Sonic Mania Plus / GoldenEye 007 (Recomp) / Ship of Harkinian (OOT) / 2 Ship 2 Harkinian (MM) / Mario Kart 64 (SpaghettiKart) / Star Fox 64 (Starship) / Zelda 3 (A Link to the Past) / Perfect Dark / Sonic 3 A.I.R. / Sonic Robo Blast 2 (SRB2) / Space Cadet 3D Pinball / Balatro / Mega Man X: Regenesis / Mega Man X8 16-Bit Demake (Touch Mod v1.6) / Apotris / PokeMMO (all 5 regions) / Paper Mario 64 (PaperBoat).
   - *ES-DE Ports Launcher Architecture*: ES-DE's default system for ports routes to RetroArch ECWolf. Resolved by deploying a custom `ports` system in `es_systems.xml` using `<command label="Android App">%ANDROIDAPP%=%FILEINJECT%</command>` and `<string name="AlternativeEmulator.ports" value="Android App" />` in `es_settings.xml`.
   - *Note on OutRun 2006*: Verified running at 1080p 60fps via PPSSPP (PSP) and ARM SX2 (PS2); DroidDeck PC execution remains investigated and pending upstream FEX 32-bit DX9 translation.
9. **Obtainium Emulation Pack Upstream Contribution (PR #195)**:
   - Responded to community feature request on RJNY/Obtainium-Emulation-Pack #187.
   - Identified root cause of Issue #183 (package ID mismatch between stable com.armsx2 and nightly com.armsx2.nightly).
   - Submitted PR #195 adding com.armsx2.nightly with prereleases enabled, filtered to Android-arm64.apk$, as a table-only entry.
10. **Public Toolkit Release (v1.0.0)**:
    - Formalized MIT License in root LICENSE file.
    - Streamlined README.md with a 3-step 60-second quick-start provisioning guide.

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

### Issue 2: Paper Mario 64 (PaperBoat) Android OpenGLES Shader Limitation
- **Affected Package**: `dev.net64.paperboat` (PaperBoat v1.0.3)
- **Current State**:
  - Deployed from official HarbourMasters CI artifact. `Torch` on-device ROM extraction successfully creates `pm64.o2r` (40.1 MB) from clean US ROM.
  - 3D world geometry, camera interpolation, and audio render cleanly at 60 FPS.
  - 2D billboard character sprites (Mario, NPCs) and theater curtain textures exhibit vertical striping and scrambled paletted noise under OpenGLES.
  - Root cause tracked to Fast3D GLES noise/dither shader logic in `external/libultraship` (PR #217 / PR #262).
  - High-res 1080p 60 FPS gameplay is immediately available via **Mupen64Plus FZ Standalone**.
### Issue 3: DroidDeck OutRun 2006 (Coast 2 Coast) & 32-bit x86 Proton DX9 Translation
- **Affected Pipeline**: `com.droiddeck.launcher` -> Steam Big Picture / PRoot / FEX -> `OR2006C2C.EXE`
- **Root Cause Verified**:
  - OutRun 2006 is a 32-bit x86 DirectX 9 Windows title.
  - Initial configuration was assigned to `Proton Experimental ARM64`, which immediately fails on 32-bit x86 binaries.
  - DroidDeck was updated via its in-app update UI to PR #1034 test build: *"fix: run x86 Proton under FEX in the Steam runtime it requires"* with active `Mesa_Turnip_v27.0.0-20261018-r2`.
  - Launching via `steam://rungameid/17844709432596889600` fails with "No licenses" (`Screenshot_20261018-142427.png`) because Steam queries its store backend for delisted App ID 8960 when unmapped in the active user's `shortcuts.vdf`.
  - Calling `droiddeck-proton-run --app 8960` returns exit code 2 (`steam_launch()` returns `None`) because retail PC installs lack Valve `appmanifest_8960.acf`.
  - When reconfigured inside Steam Big Picture to `Proton Experimental` (x86 Proton under FEX), Steam displays the launch spinner for ~4 seconds as FEX initializes, then silently returns to Big Picture without presenting a game surface. 32-bit Direct3D 9 / DXVK thunking under FEX remains experimental in PR #1034.
- **Recommended Action / Workaround**:
  - For immediate, flawless 1080p 60fps gameplay, play OutRun 2006 via **PPSSPP** (PSP at 4x resolution, full analog triggers) or **ARM SX2** (PS2 at 2.0x Vulkan).

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
- **Steam Big Picture & Gamescope Controller Evdev Injection**:
  - RP5 physical controller is registered at `/dev/input/event8` (`Xbox Wireless Controller`).
  - Button A (Select / South): `sendevent /dev/input/event8 1 304 1; sendevent /dev/input/event8 0 0 0; sleep 0.15; sendevent /dev/input/event8 1 304 0; sendevent /dev/input/event8 0 0 0`
  - Button B (Back / East): `sendevent /dev/input/event8 1 305 1; sendevent /dev/input/event8 0 0 0; sleep 0.15; sendevent /dev/input/event8 1 305 0; sendevent /dev/input/event8 0 0 0`
  - D-Pad Left: `sendevent /dev/input/event8 3 16 -1; sendevent /dev/input/event8 0 0 0; sleep 0.1; sendevent /dev/input/event8 3 16 0; sendevent /dev/input/event8 0 0 0`
  - D-Pad Right: `sendevent /dev/input/event8 3 16 1; sendevent /dev/input/event8 0 0 0; sleep 0.1; sendevent /dev/input/event8 3 16 0; sendevent /dev/input/event8 0 0 0`
  - D-Pad Down: `sendevent /dev/input/event8 3 17 1; sendevent /dev/input/event8 0 0 0; sleep 0.1; sendevent /dev/input/event8 3 17 0; sendevent /dev/input/event8 0 0 0`
  - D-Pad Up: `sendevent /dev/input/event8 3 17 -1; sendevent /dev/input/event8 0 0 0; sleep 0.1; sendevent /dev/input/event8 3 17 0; sendevent /dev/input/event8 0 0 0`

---

## 6. Execution Guidance for Claude

1. **Working Directory**: Workspace root directory (`<WORKSPACE_ROOT>`)
2. **Local ADB Binary**: `.\platform-tools\adb.exe -s <SERIAL>`
3. **Local Python**: `python` (Python 3.12)
4. **Git Branch**: `main` (commit all changes cleanly before concluding sessions)
5. **Task Master**: Always read and update [WORKQUEUE.md](WORKQUEUE.md) when changing task status.
6. **Markdown Clipboard Staging**: When providing markdown text intended for the user to copy/paste to external sites (GitHub comments, bug reports, forums), always stage the clean, unindented text directly into the user's Windows clipboard using PowerShell (`Get-Content <file> -Raw | Set-Clipboard`) to prevent accidental 4-space code block formatting.
7. **GitHub Issue & Bug Report Automation**: The host environment has an authenticated GitHub CLI (`gh` account `dmillerzx` with full `repo` scopes). Going forward, open bug reports, feature requests, and upstream issues directly via `gh issue create --repo <owner/repo> --title "<title>" --body-file "<file>"` rather than prompting the user to submit them manually.
