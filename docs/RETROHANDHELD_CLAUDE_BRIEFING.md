# RETROHANDHELD AUTOMATION STATUS & TROUBLESHOOTING DOSSIER
**Prepared for**: Claude Integration & Cross-Agent Hand-off  
**Date**: October 16, 2026  
**Target Device**: Retroid Pocket 5 (RP5) — Serial `ff152647`  
**Repository**: [dmillerzx/handheld-antigravity-toolkit](https://github.com/dmillerzx/handheld-antigravity-toolkit) (branch: `main`)

---

## 1. Executive Summary

This dossier provides a comprehensive technical briefing on the Retroid Pocket 5 automated provisioning project. Over the past 48 hours, Antigravity and Gemini agents have provisioned the device, staged community assets, unlocked Android 13 phantom process limits, configured ultra-low latency RetroArch 2D audio DSP pipelines, and staged frontends (ES-DE, Daijisho, Obtainium).

However, **two critical functional issues** have stalled full verification in the active debugging session:
1. **Dolphin Input Failure in Mario Kart Wii**: Handheld physical buttons do not respond when launching Mario Kart Wii (`RMCE01` / `RMCEA2`).
2. **Gran Turismo 4 Spec II (ARM SX2) 16:9 Widescreen**: While ES-DE direct launching now successfully hooks into ARM SX2, GT4 Spec II renders in 4:3 with side pillarboxes rather than filling the 1080p display.

This document details the exact hardware state, root causes identified during live device diagnostics, file paths on the device, and the precise corrective actions required.

---

## 2. Hardware & Device Invariants

| Attribute | Specification / Hardware State |
|---|---|
| **Device Model** | Retroid Pocket 5 (RP5) |
| **SoC / GPU** | Qualcomm Snapdragon 865 (SM8250) / Adreno 650 GPU |
| **ADB Connection** | USB / Wi-Fi (`-s ff152647`) |
| **Operating System** | Android 13 (Retroid OS, AOSP) |
| **Display** | 5.5" AMOLED, 1920x1080 (16:9 native), 60Hz |
| **Gamepad Mode** | **Xbox Mode** (`persist.sys.gamepad.type 0`) |
| **Trigger Mode** | **Both** (`persist.sys.trigger.mode 2` — analog axes + digital click) |
| **Android Input Device**| `Device 10: Xbox Wireless Controller` |
| **Canonical MicroSD UUID** | `/storage/EEEF-F762/` |

### Canonical Storage Rules (Strict)
The filesystem on the device is strictly standardized. Any deviation causes broken paths:
- **Internal Storage**: `/sdcard/bios/` (staging and fallback BIOS only).
- **MicroSD Card**: `/storage/EEEF-F762/`
  - `/storage/EEEF-F762/bios/` (Shared master BIOS for all emulators)
  - `/storage/EEEF-F762/ROMs/<system>/` (All game ROMs; e.g. `ps2/`, `gc/`, `wii/`)
  - `/storage/EEEF-F762/ES-DE/` (Frontend metadata and configs)
  - `/storage/EEEF-F762/RetroArch/` (RetroArch cores, configs, audio filters)
  - `/storage/EEEF-F762/Saves_Backup/latest/` (Systematic save backups)
- **Forbidden Paths**: Do not create or push to `/sdcard/ROMs`, `/sdcard/roms`, `Games/`, or `Emulation/`.

---

## 3. Deep-Dive: Issue 1 — Dolphin Mario Kart Wii Controller Mappings

### A. Symptom Description
When launching Mario Kart Wii (`RMCE01` or `RMCEA2` Deluxe X) through ES-DE or directly in Dolphin:
- Physical gamepad buttons (A, B, X, Y, Triggers, D-pad) have zero effect in the game.
- The user is unable to pass the initial title/license screens or navigate menus.
- After recent automated config pushes, holding buttons to bring up the Dolphin in-game side drawer was also unresponsive.

### B. Root Cause Breakdown
Through live ADB inspection of Dolphin configuration files on device `ff152647`, four distinct causes were identified:

#### 1. Invalid Section Name in GameSettings (`[Controls]` vs `[Core]`)
In `/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings/RMCE01.ini` and `RMCEA2.ini`, the automation script had written:
```ini
[Controls]
WiimoteSource0 = 1
SIDevice0 = 0
```
**Dolphin's GameSettings engine does NOT recognize a section named `[Controls]`!**  
In Dolphin, game-specific overrides for hardware controller ports (`SIDevice0` to `SIDevice3` and `WiimoteSource0` to `WiimoteSource3`) belong strictly under the **`[Core]`** section. Because `[Controls]` was ignored as an unknown section, Dolphin completely disregarded these overrides and fell back to global `Dolphin.ini`.

#### 2. Dual Active Controller Port Conflict
In global `/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Dolphin.ini`:
```ini
[Core]
SIDevice0 = 6
WiimoteSource0 = 1
WiimoteEnableGCControllers = True
```
- `SIDevice0 = 6` tells Dolphin that a Standard GameCube Controller is plugged into Port 1.
- `WiimoteSource0 = 1` tells Dolphin that an Emulated Wii Remote is also connected to Port 1.
- Mario Kart Wii is unique: it natively supports **both** GameCube controllers and Wii Remotes (with Classic Controller or Nunchuk attachments). When both ports are actively declared for Player 1, Mario Kart Wii locks input or listens to the wrong controller channel.

#### 3. PowerShell Escaping Corruption in Config Files
When earlier scripts pushed `GCPadNew.ini`, PowerShell string escaping converted backticks into literal backslashes:
```ini
# CORRUPTED CONFIG FOUND ON DEVICE:
Buttons/X = \Button X\
Buttons/Y = \Button Y\
Buttons/Z = \Button 103\
```
Instead of valid Dolphin token syntax:
```ini
Buttons/X = `Button X`
Buttons/Y = `Button Y`
Buttons/Z = `Button 103`
```

#### 4. Android Keycode Token Mismatch (`Button 96` vs `Button A`)
When the user manually remapped the controller in the Dolphin Android UI, Dolphin generated:
```ini
[GCPad1]
Device = Android/1/Xbox Wireless Controller
Buttons/A = `Button A`
Buttons/B = `Button B`
```
However, the script injected numeric keycodes (`Button 96`, `Button 97`), which Dolphin's Android input handler frequently drops or misinterprets depending on the input driver.

### C. Corrective Action Plan for Mario Kart Wii

#### Recommended Strategy: Native GameCube Controller Routing (Cleanest & Most Reliable)
Because Mario Kart Wii has full, native GameCube controller support built into the game engine, routing Port 1 directly to a GameCube controller completely eliminates Wiimote pointer / infrared emulation overhead and Classic Controller extension bugs.

1. **Update GameSettings INIs (`RMCE01.ini`, `RMCEA2.ini`, `RMCJ01.ini`, `RMCP01.ini`)**:
   Under `[Core]`:
   ```ini
   [Core]
   SIDevice0 = 6
   WiimoteSource0 = 0
   ```
2. **Deploy Valid `GCPadNew.ini` to `/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/GCPadNew.ini`**:
   ```ini
   [GCPad1]
   Device = Android/1/Xbox Wireless Controller
   Buttons/A = `Button A`
   Buttons/B = `Button B`
   Buttons/X = `Button X`
   Buttons/Y = `Button Y`
   Buttons/Z = `Button 103`
   Buttons/Start = `Button 108`
   Main Stick/Up = `Axis 1-`
   Main Stick/Down = `Axis 1+`
   Main Stick/Left = `Axis 0-`
   Main Stick/Right = `Axis 0+`
   Main Stick/Modifier = `Shift`
   Main Stick/Modifier/Range = 50.000000
   C-Stick/Up = `Axis 14-`
   C-Stick/Down = `Axis 14+`
   C-Stick/Left = `Axis 11-`
   C-Stick/Right = `Axis 11+`
   C-Stick/Modifier = `Control`
   C-Stick/Modifier/Range = 50.000000
   D-Pad/Up = `Button 19`
   D-Pad/Down = `Button 20`
   D-Pad/Left = `Button 21`
   D-Pad/Right = `Button 22`
   Triggers/L = `Axis 22+`
   Triggers/R = `Axis 23+`
   Triggers/Threshold = 50.000000
   Triggers/L-Analog = `Axis 22+`
   Triggers/R-Analog = `Axis 23+`
   ```

---

## 4. Deep-Dive: Issue 2 — Gran Turismo 4 Spec II (ARM SX2) Widescreen

### A. Symptom Description
1. ES-DE direct launching is now **working**: Selecting GT4 Spec II boots straight into the game engine via:
   `%EMULATOR_ARMSX2% %ACTION%=android.intent.action.VIEW %DATA%=%ROM%`
2. However, the game renders in **4:3 aspect ratio** (black bars on the sides) on the 16:9 AMOLED display, even though ARM SX2 global settings specify `AspectRatio = 16:9` (`"aspectRatio": 1`).

### B. Root Cause Breakdown

#### 1. In-Game 16:9 Option Requirement
Gran Turismo 4 (like many high-end PS2 titles) has native anamorphic 16:9 widescreen built directly into its engine. If the in-game display setting is set to 4:3 (the default), the PS2 renders a 4:3 viewport. In an emulator set to 16:9, a 4:3 signal is either letterboxed or horizontally stretched unless the in-game toggle is engaged:
- **In GT4 Menu**: Go to `Options` -> `Picture Quality / Setup` -> `Screen Size` -> Toggle to `16:9`.

#### 2. Widescreen `.pnach` Format & Staging Directory
The patch `patches/ps2/646B2E29.pnach` was staged to:
`/sdcard/Android/data/com.armsx2/files/cheats/646B2E29.pnach` and `patches/`

However:
- In PCSX2 / ARM SX2 / NetherSX2 architectures:
  - Widescreen patches loaded by `EnableWideScreenPatches = true` are expected in **`cheats_ws/`**, NOT `patches/` or `cheats/`!
  - Files placed in `cheats/` are only executed if `EnableCheats = true` is active.
- **PNACH Syntax Error**:
  The file contained RPCS3/Qt-style headers:
  ```ini
  [Widescreen 16:9]
  gsaspectratio=16:9
  description=Widescreen Text Correction & 16:9 FOV
  patch=1,EE,2033D7DC,extended,3C013F40
  ```
  Traditional PCSX2 / AetherSX2 / ARM SX2 `.pnach` interpreters fail on bracketed section headers (`[...]`). Standard `.pnach` format requires comment lines starting with `//`:
  ```text
  gametitle=Gran Turismo 4 Spec II [SCUS-97436] (CRC: 646B2E29)
  // Widescreen 16:9 Text Correction & FOV
  patch=1,EE,2033D7DC,extended,3C013F40
  patch=1,EE,2033D7E0,extended,34210000
  // No-Interlacing (480p Progressive)
  patch=1,EE,20312544,extended,34080001
  patch=1,EE,20312558,extended,AE481718
  ```

### C. Corrective Action Plan for GT4 Spec II
1. Convert `646B2E29.pnach` to clean PCSX2 comment syntax.
2. Push `646B2E29.pnach` to both:
   - `/sdcard/Android/data/com.armsx2/files/cheats_ws/646B2E29.pnach`
   - `/sdcard/Android/data/com.armsx2/files/cheats/646B2E29.pnach`
3. Ensure `/sdcard/Android/data/com.armsx2/files/gamesettings/646B2E29.ini` and `SCUS-97436.ini` include:
   ```ini
   [EmuCore/GS]
   AspectRatio = 16:9
   Crop = 1
   CropMode = Overscan
   UpscaleMultiplier = 2.0
   EnableWideScreenPatches = true
   EnableCheats = true
   ```
4. Confirm GT4 in-game screen option is set to 16:9.

---

## 5. Summary of Key Files on Host and Target

### Host Repository Files
- `CLAUDE.md`: Claude Code workspace orientation and handoff summary.
- `AGENTS.md` / `GEMINI.md`: Strict agent guidelines and canonical layout rules.
- `configs/es_systems.xml`: Custom ES-DE system definitions prioritizing standalone emulators.
- `configs/dolphin/GCPadNew.ini`: Verified GameCube controller profile.
- `configs/dolphin/WiimoteNew.ini`: Wii Classic Controller profile.
- `patches/wii/RMCE01.ini` & `RMCEA2.ini`: Dolphin Mario Kart Wii GameSettings.
- `patches/ps2/646B2E29.pnach` & `646B2E29.ini`: GT4 Spec II patch and game profile.
- `scripts/setup_rp5.py`: Master automated provisioning script.
- `scripts/configure_standalones.py`: Standalone profile deployer.

### Device Paths
- **Dolphin Config**: `/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/`
- **Dolphin GameSettings**: `/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings/`
- **ARM SX2 Data**: `/sdcard/Android/data/com.armsx2/files/`
- **ES-DE Configs**: `/sdcard/ES-DE/settings/`
- **Canonical MicroSD**: `/storage/EEEF-F762/`

---

## 6. How to Run & Verify

To execute provisions on the device:
```powershell
# From workspace root
.\scripts\run_setup.ps1 --serial ff152647 --all
```
Or directly with Python:
```powershell
python scripts/setup_rp5.py --serial ff152647 --all
```

To test input and dump live logs:
```powershell
.\platform-tools\adb.exe -s ff152647 shell dumpsys input
.\platform-tools\adb.exe -s ff152647 shell logcat -d | Select-String -Pattern "dolphin|armsx2|es-de"
```
