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

## 2. Items Resolved from Claude's Review (2026-10-16)

### Item A: ES-DE Dolphin Activity Find Rule
- **Resolution**: No change needed. Stock ES-DE's own `es_find_rules.xml` uses `org.dolphinemu.dolphinemu/.ui.main.TvMainActivity`. Verified valid.

### Item C: Mario Kart Wii Control Mode
- **Resolution**: Settled. Kept the exact working state from the device (`[Core] SIDevice0 = 6`, `[Controls] WiimoteSource0 = 0`, GameCube mode). Pulled and committed as source of truth.

### Item D: Single Source of Truth Cleanup
- **Resolution**: Completed in commit `4770a4d`.
  - Deleted `configs/templates/dolphin/` (all 9 files).
  - Deleted obsolete root `configs/GCPadNew.ini` and `configs/WiimoteNew.ini`.
  - Removed fallback inline `gcpad_ini` and `wiimote_ini` strings in `scripts/configure_standalones.py`; script now raises `FileNotFoundError` if repo files are missing.
  - Stopped regex rewriting `Device =` in profiles; captured profiles are deployed unchanged.
  - Removed unused `WiimoteSource0..3` from `dolphin_ini` `[Core]` section.

### Item E: Automated Verification Script (`verify_deployment.py`)
- **Resolution**: Completed in commit `e5b794a`.
  - Created `scripts/verify_deployment.py` to force-stop emulators, pull device configs, parse sections/keys/values, and compare key-value pairs (handling float formatting, backticks, comments, and repeated keys).
  - Live hardware test result: **100% PASS** across all 9 target files (7 Dolphin, 2 ARM SX2).

---

## 3. Remaining Low-Priority Tracking

### Item B: ARM SX2 Per-Game Settings File Naming Convention
- emulog.txt confirms ARM SX2 found `646B2E29.pnach` by CRC.
- Global `armsx2-settings.json` already sets 16:9, progressive scan, and `hardwareDownloadMode = 1`.
- Per-game settings lookup can be checked next time Doug opens GT4 per-game properties in ARM SX2 UI to see if ARM SX2 generates `<SERIAL>_<CRC>.ini` or `<CRC>.ini`. Low priority.
