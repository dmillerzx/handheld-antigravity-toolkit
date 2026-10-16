# Outstanding Tasks & Claude Collaboration Hand-Off (2026-10-16)

## Overview
This document outlines the resolved fixes and the remaining outstanding items across the Retroid Pocket 5 automated provisioning workspace (`handheld-antigravity-toolkit`).

---

## 1. Resolved in This Session (Verified on Hardware)

1. **Dolphin Controller Bindings Resolved**:
   - Discovered root cause of non-responsive buttons: Dolphin on Android does **not** recognize numeric keycodes (`Button 96`, `Button 19`, etc.). It strictly registers human-readable key names (`Button A`, `Button B`, `Button X`, `Button Y`, `Button L1`, `Button R1`, `Start`, `Select`, `Mode`) and hat axes (`Axis 16`, `Axis 15`).
   - Device string confirmed as `Android/1/Xbox Wireless Controller`.
   - Both `GCPadNew.ini` and `WiimoteNew.ini` were captured directly from the user's manual mapping on hardware, deployed, and diff-verified via readback.

2. **Dolphin GameSettings Deduplication**:
   - Isolated Mario Kart Wii controls to `patches/wii/RMC.ini` (`[Core] SIDevice0 = 6`, `[Controls] WiimoteSource0 = 0`).
   - Removed conflicting controller lines from all four region files (`RMCE01.ini`, `RMCEA2.ini`, `RMCJ01.ini`, `RMCP01.ini`), preserving only their video and deflicker Gecko patches.

3. **ARM SX2 GT4 Spec II Widescreen**:
   - Mod CRC confirmed as `646B2E29`.
   - `646B2E29.pnach` loaded and verified active in `emulog.txt` (`Widescreen 16:9`, `No-Interlacing`, `480p progressive autoboot`, 60 FPS locked).
   - Display fills full 1920x1080 screen with 0 black bars.

4. **Pipeline Hardening**:
   - `configure_standalones.py` now issues `am force-stop` before pushing configs to prevent live emulators from overwriting INIs on exit.
   - Removed hardcoded inline string generation in favor of reading directly from repo config files (`configs/dolphin/`).

---

## 2. Outstanding Items for Claude Review & Assistance

### Item A: ES-DE Dolphin Activity Find Rule
- In `configs/es_systems.xml` / `es_find_rules.xml`, Claude noted:
  > *"The Dolphin find rule lists only `org.dolphinemu.dolphinemu/.ui.main.TvMainActivity` (the Android TV activity). Compare it against stock ES-DE's `es_find_rules.xml` for the handheld activity."*
- **Action Needed**: Check if ES-DE on Android handhelds should target `org.dolphinemu.dolphinemu/org.dolphinemu.dolphinemu.activities.EmulationActivity` or `.ui.main.MainActivity` rather than `.ui.main.TvMainActivity`.

### Item B: ARM SX2 Per-Game Settings File Naming Convention
- In PCSX2 source (`VMManager.cpp`, `GetGameSettingsPath`), per-game settings files are named `<SERIAL>_<CRC>.ini` (e.g. `SCUS-97436_646B2E29.ini`), whereas patches can use `<SERIAL>_<CRC>.pnach` or `<CRC>.pnach`.
- We currently push `646B2E29.ini` to `gamesettings/`.
- **Action Needed**: Verify if ARM SX2 reads `646B2E29.ini` or strictly requires `SCUS-97436_646B2E29.ini`. If the latter, rename `646B2E29.ini` and `646B2E29.pnach` to include the serial prefix.

### Item C: Mario Kart Wii Preferred Mode (GameCube vs. Classic Controller)
- Right now, `RMC.ini` sets `SIDevice0 = 6` (GameCube controller) and `WiimoteSource0 = 0` (Wii Remote off).
- Both the GameCube profile (`Standard_Controller.ini`) and the Classic Controller profile (`Classic_Controller.ini`) now have 100% identical physical hardware mappings.
- **Action Needed**: Confirm with Doug whether he prefers playing MKWii with GameCube mechanics (B = brake, R = drift) or Classic Controller mechanics (A = gas, B = drift, L/ZL = item). If Classic Controller is preferred, update `RMC.ini` to:
  ```ini
  [Controls]
  PadType0 = 0
  WiimoteSource0 = 1
  WiimoteProfile1 = Classic_Controller
  ```

### Item D: Single Source of Truth Cleanup (Claude Review Item 4)
- Remove duplicate/stale copies of configs in `configs/templates/dolphin/` and ensure all scripts deploy exclusively from `configs/dolphin/`.

### Item E: Automated Verification Script (`verify_deployment.py`)
- Formalize a standalone verification script that runs `am force-stop`, pulls all active emulator configs from the device, diffs them against repository templates, and prints a clean pass/fail audit table.
