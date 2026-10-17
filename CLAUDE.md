# CLAUDE.md — Retroid Pocket 5 Automation & Active Troubleshooting Briefing

This repository is the **Retroid Pocket 5 (RP5) Automated Provisioning Workspace**. It contains ADB automation scripts, staging directories, configurations, and patch definitions used to configure, optimize, and provision the Retroid Pocket 5 handheld gaming console.

---

## 1. Hardware & System Context

- **Device**: Retroid Pocket 5 (RP5)
- **Serial**: `<SERIAL>` (Always pass `-s <serial>` with ADB at runtime)
- **SoC**: Qualcomm Snapdragon 865 (SM8250)
- **GPU**: Adreno 650 (supports custom Turnip/Mesa drivers via Vulkan)
- **OS**: Android 13 (Retroid OS, AOSP-based)
- **Display**: 5.5-inch 1080p AMOLED (1920x1080), 60Hz
- **Gamepad / Inputs**:
  - Integrated physical controls set to **Xbox Mode** (`persist.sys.gamepad.type 0`)
  - Trigger Mode set to **Both** (`persist.sys.trigger.mode 2` — analog axis + digital click)
  - Android Input Name: `Xbox Wireless Controller` (registered as Device 10 in Android `dumpsys input`)
- **Canonical Storage Layout**:
  - Internal: `/sdcard/bios/`
  - MicroSD: `/storage/<SD_ID>/`
    - `/storage/<SD_ID>/bios/` (Canonical BIOS shared by all emulators)
    - `/storage/<SD_ID>/ROMs/<system>/` (Canonical ROM root; NO ROMs on internal storage)
    - `/storage/<SD_ID>/ES-DE/` (Frontend data)
    - `/storage/<SD_ID>/RetroArch/` (Configs, cores, filters, shaders)
    - `/storage/<SD_ID>/Saves_Backup/latest/` (Save mirror)
    - `/storage/<SD_ID>/Games/Steam/` (DroidDeck Steam library)

> [!CAUTION]
> **Canonical Storage Rules**: Never create or push to `Games/BIOS`, `BIOS/`, `roms/` (lowercase), `Emulation/`, or `/sdcard/ROMs`. ROMs strictly reside in `/storage/<SD_ID>/ROMs/<system>/`.

---

## 2. Active Troubleshooting Status (Handoff from Antigravity/Gemini)

The previous agent sessions made major progress (ES-DE direct booting ARM SX2 with `%ROMSAF%`, Obtainium scraper fixes, RetroArch low-latency audio DSP pipelines), but ran into two major unresolved hurdles that currently require intervention:

### Issue A: Dolphin Controls in Mario Kart Wii (and Dolphin Wii controls)
1. **The Problem**:
   - Mario Kart Wii (`RMCE01` / `RMCEA2`) launches from ES-DE, but the physical controls on the handheld do not respond in game menus or races.
2. **The Root Causes Identified**:
   - **Invalid Section Header**: The script injected `[Controls]` into Dolphin's GameSettings (`/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings/RMCE01.ini`). **Dolphin GameSettings does not have a `[Controls]` section!** In Dolphin, game-specific overrides for controllers (`SIDevice0`, `WiimoteSource0`) MUST be placed under `[Core]`. Because `[Controls]` was ignored, Dolphin fell back to `Dolphin.ini`.
   - **Dual Port 1 Conflict**: In `Dolphin.ini`, both `SIDevice0 = 6` (Standard GameCube Controller connected to Port 1) AND `WiimoteSource0 = 1` (Emulated Wiimote enabled on Port 1) are active simultaneously. Mario Kart Wii natively supports both, creating conflicting or ignored input listeners.
   - **PowerShell Escaping Corruption**: Previous automation attempted to write INIs using inline PowerShell strings, accidentally escaping backticks into literal backslashes (e.g. `\Button X\` instead of `` `Button X` `` in `GCPadNew.ini`).
   - **Numeric vs Label Input Tokens**: Android Dolphin UI binds Xbox gamepad buttons as clean labels (e.g. `` `Button A` ``, `` `Button B` ``, `` `Button X` ``, `` `Button Y` ``) rather than numeric Android keycodes (`` `Button 96` ``).
3. **The Solution**:
   - **Recommended Approach (Native GameCube Controller Scheme)**: Mario Kart Wii has full native support for GameCube controllers. Setting Port 1 exclusively to GameCube avoids all Wiimote pointer / infrared emulation friction:
     In `RMCE01.ini` / `RMCEA2.ini`:
     ```ini
     [Core]
     SIDevice0 = 6
     WiimoteSource0 = 0
     ```
     Ensure `/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/GCPadNew.ini` contains valid Xbox controller mappings with proper backticks.
   - **Alternative (Classic Controller Extension)**:
     If using Wii Classic Controller:
     In `RMCE01.ini`:
     ```ini
     [Core]
     SIDevice0 = 0
     WiimoteSource0 = 1
     ```
     And in `WiimoteNew.ini`, configure `Extension = Classic` with verified UI tokens.

---

### Issue B: Gran Turismo 4 Spec II (ARMSX2) Widescreen Aspect Ratio
1. **The Problem**:
   - ES-DE now directly launches GT4 Spec II into ARM SX2 (resolved via custom `es_systems.xml` with `%EMULATOR_ARMSX2% %ACTION%=android.intent.action.VIEW %DATA%=%ROM%` and `es_find_rules.xml`).
   - However, the game displays in 4:3 with side pillarboxes rather than filling the 16:9 1080p AMOLED display.
2. **The Root Causes Identified**:
   - **In-Game Setting Requirement**: Gran Turismo 4 natively features an internal widescreen mode. By default, the game outputs 4:3 unless configured in its internal options: **Main Menu -> Option -> Picture Quality / Setup -> Aspect Ratio -> 16:9**.
   - **Widescreen Patch Staging (`.pnach`)**: The patch `patches/ps2/646B2E29.pnach` was pushed to `com.armsx2/files/cheats/` and `patches/`. In PCSX2/ARM SX2:
     - Widescreen patches loaded by `EnableWideScreenPatches = true` must reside in `cheats_ws/<CRC>.pnach` (or standard `cheats/<CRC>.pnach` when `EnableCheats = true`).
     - The pnach file contained RPCS3/Qt-style INI headers (`[Widescreen 16:9]`, `[No-Interlacing]`), which standard PCSX2 pnach parsers skip. Standard PCSX2 `.pnach` syntax requires `// comment` and `patch=1,EE,...`.
3. **The Solution**:
   - Deploy standard PCSX2 syntax `.pnach` to both `cheats/646B2E29.pnach` and `cheats_ws/646B2E29.pnach` under `/sdcard/Android/data/com.armsx2/files/`.
   - Ensure the user toggles in-game 16:9 mode in the GT4 Options menu, or verify the GS AspectRatio setting (`"aspectRatio": 1` in `armsx2-settings.json`).

---

## 3. Reference Files & Full Dossier

- **Complete Technical Briefing**: See [docs/RETROHANDHELD_CLAUDE_BRIEFING.md](docs/RETROHANDHELD_CLAUDE_BRIEFING.md)
- **Agent Directives & Storage Laws**: [AGENTS.md](AGENTS.md) and [GEMINI.md](GEMINI.md)
- **Quality Checklist**: [QA_CHECKLIST.md](QA_CHECKLIST.md)
- **Automation Scripts**:
  - `scripts/setup_rp5.py`: Master setup script (`--serial <SERIAL> --all`)
  - `scripts/configure_standalones.py`: Standalone 3D emulator config injector
  - `scripts/stage_community_patches.py`: PS2 & Dolphin patch engine

---

## 4. Execution Guidance for Claude

1. **Working Directory**: `C:\Users\dmill\Documents\AntigravityWorkingDir`
2. **Local ADB Binary**: `.\platform-tools\adb.exe -s <SERIAL>`
3. **Local Python**: `python` (Python 3.12)
4. **Git Remote**: `origin` -> `https://github.com/dmillerzx/handheld-antigravity-toolkit.git` (branch `main`)
5. **Always Verify with Live Hardware Inspections**: Test actual files on device with `adb shell cat` and verify input with `dumpsys input`.
