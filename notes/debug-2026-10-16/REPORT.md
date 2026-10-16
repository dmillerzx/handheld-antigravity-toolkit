# Hardware-Antigravity Provisioning Status Report (2026-10-16)

## Executive Summary
This report summarizes the ground-truth hardware state, controller mappings, GameSettings overrides, and widescreen status for the Retroid Pocket 5 handheld (`serial: ff152647`).

---

## 1. Dolphin Controller Configuration

### A. Device String
Ground-truth device string verified directly from Dolphin on Android:
```ini
Device = Android/1/Xbox Wireless Controller
```

### B. Input Token Names
Dolphin on Android does **not** recognize numeric Android keycodes (e.g. `Button 96`, `Button 19`). It registers and parses human-readable token names defined in `Source/Core/InputCommon/ControllerInterface/Android/Android.cpp` (`KEYCODE_NAMES`):
- Face buttons: `Button A`, `Button B`, `Button X`, `Button Y`
- Bumpers: `Button L1`, `Button R1`
- Triggers: `Axis 17+`&`Axis 23+` (L), `Axis 18+`&`Axis 22+` (R)
- D-Pad: `Axis 16-` (Up), `Axis 16+` (Down), `Axis 15-` (Left), `Axis 15+` (Right)
- System: `Start`, `Select`, `Mode` (Home)
- Thumbsticks: `Axis 0` / `Axis 1` (Left Stick), `Axis 11` / `Axis 14` (Right Stick)

### C. Final Active WiimoteNew.ini (Wii Classic Controller)
Captured directly from user manual mapping on device and verified by readback:
```ini
[Wiimote1]
Device = Android/1/Xbox Wireless Controller
Source = 1
Extension = Classic
Buttons/A = `Button A`
Buttons/B = `Button B`
Buttons/1 = `Button X`
Buttons/2 = `Button Y`
Buttons/- = Select
Buttons/+ = Start
Buttons/Home = Mode
D-Pad/Up = `Up`
D-Pad/Down = `Down`
D-Pad/Left = `Left`
D-Pad/Right = `Right`
Classic/Buttons/A = `Button A`
Classic/Buttons/B = `Button B`
Classic/Buttons/X = `Button Y`
Classic/Buttons/Y = `Button X`
Classic/Buttons/ZL = `Button L1`
Classic/Buttons/ZR = `Button R1`
Classic/Buttons/+ = Start
Classic/D-Pad/Up = `Axis 16-`
Classic/D-Pad/Down = `Axis 16+`
Classic/D-Pad/Left = `Axis 15-`
Classic/D-Pad/Right = `Axis 15+`
Classic/Left Stick/Up = `Axis 1-`
Classic/Left Stick/Down = `Axis 1+`
Classic/Left Stick/Left = `Axis 0-`
Classic/Left Stick/Right = `Axis 0+`
Classic/Right Stick/Up = `Axis 14-`
Classic/Right Stick/Down = `Axis 14+`
Classic/Right Stick/Left = `Axis 11-`
Classic/Right Stick/Right = `Axis 11+`
Classic/Triggers/L = `Axis 17+`&`Axis 23+`
Classic/Triggers/R = `Axis 18+`&`Axis 22+`
Classic/Triggers/Threshold = 50.
Classic/Triggers/L-Analog = `Axis 17+`&`Axis 23+`
Classic/Triggers/R-Analog = `Axis 18+`&`Axis 22+`
Classic/Buttons/- = Select
Classic/Buttons/Home = Mode
```

### D. Final Active GCPadNew.ini (GameCube Controller)
Captured directly from user manual mapping on device and verified by readback:
```ini
[GCPad1]
Device = Android/1/Xbox Wireless Controller
Buttons/A = `Button A`
Buttons/B = `Button B`
Buttons/X = `Button Y`
Buttons/Y = `Button X`
Buttons/Z = `Button R1`
Buttons/Start = `Start`
Main Stick/Up = `Axis 1-`
Main Stick/Down = `Axis 1+`
Main Stick/Left = `Axis 0-`
Main Stick/Right = `Axis 0+`
Main Stick/Modifier = `Shift`
C-Stick/Up = `Axis 14-`
C-Stick/Down = `Axis 14+`
C-Stick/Left = `Axis 11-`
C-Stick/Right = `Axis 11+`
C-Stick/Modifier = `Control`
D-Pad/Up = `Axis 16-`
D-Pad/Down = `Axis 16+`
D-Pad/Left = `Axis 15-`
D-Pad/Right = `Axis 15+`
Triggers/L = `Axis 17+`&`Axis 23+`
Triggers/R = `Axis 18+`&`Axis 22+`
Triggers/Threshold = 50.
Triggers/L-Analog = `Axis 17+`&`Axis 23+`
Triggers/R-Analog = `Axis 18+`&`Axis 22+`
```

---

## 2. Mario Kart Wii Configuration Architecture

### A. GameSettings RMC.ini
As verified in `GameConfigLoader.cpp`:
- `Dolphin.ini` sets global defaults (`SIDevice0 = 6`, `WiimoteSource0 = 1`).
- For Mario Kart Wii series (`RMC.ini`), `[Core] SIDevice0 = 6` and `[Controls] WiimoteSource0 = 0` ensures the GameCube controller has exclusive control without double-controller ghost input from an emulated Wiimote.
```ini
# RMC - Mario Kart Wii (Global Series Override)
[Core]
SIDevice0 = 6

[Controls]
WiimoteSource0 = 0

[Video_Settings]
AspectRatio = 1
MSAA = 0

[Video_Hacks]
EFBEmulateFormatChanges = True
FastDepthCalc = True
```
- Duplicate controller blocks have been removed from all regional files (`RMCE01.ini`, `RMCEA2.ini`, `RMCJ01.ini`, `RMCP01.ini`) so that `RMC.ini` is the single source of truth.

---

## 3. ARM SX2 & Gran Turismo 4 Spec II Widescreen Status

- **ELF Checksum (CRC)**: `646B2E29`
- **Patches Deployed**: `/sdcard/Android/data/com.armsx2/files/patches/646B2E29.pnach` and `cheats/646B2E29.pnach`
- **GameSettings Deployed**: `gamesettings/646B2E29.ini` (`AspectRatio = 16:9`, `CropMode = Overscan`, `HardwareDownloadMode = 1`)
- **Live Verification**:
  - `emulog.txt` confirms:
    ```text
    Found 3 game patches in .../646B2E29.pnach
    Enabled patch: Widescreen 16:9
    Enabled patch: No-Interlacing
    OSD [LoadPatches]: 2 game patches are active.
    Mode Changed to SDTV 480p.
    PerfLog: 59.9 fps
    ```
- **Screenshot Geometry Analysis**:
  - Active viewport measured at exactly 1920x1080 (1.7778 aspect ratio) with zero pillarbox black bars.
  - Pre-rendered 4:3 MPEG-2 video FMVs stretch to 16:9 as expected for all PS2 titles.
  - In-game 3D geometry renders native 16:9 FOV with progressive 480p scan.

---

## 4. Pipeline Robustness Improvements
1. **Force-Stop Enforcement**: `configure_standalones.py` now runs `am force-stop` before pushing configurations to any emulator, preventing live emulators from overwriting pushed INIs on exit.
2. **Eliminated Inline Strings**: `configure_standalones.py` reads `configs/dolphin/GCPadNew.ini` and `configs/dolphin/WiimoteNew.ini` directly from the repository rather than generating them from hardcoded inline strings.
3. **No Backtick Escaping**: Pushes are executed directly via `adb push` without passing config content through PowerShell string interpolation.
