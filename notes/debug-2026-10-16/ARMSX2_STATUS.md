# ARM SX2 & Gran Turismo 4 Spec II Widescreen Status

## Background & CRC Identification
- Game: **Gran Turismo 4 - Spec II (v1.09)**
- Executable: `SCUS_974.36`
- ELF Checksum (CRC): **`646B2E29`** (Notice: vanilla GT4 US has CRC `77E9F3C6`. Because Spec II is a community mod, upstream PCSX2 cheat databases did not match its checksum).

## Patches & Settings Staged on Device
The following files are deployed to `/sdcard/Android/data/com.armsx2/files/`:

1. **`cheats/646B2E29.pnach`** and **`patches/646B2E29.pnach`**:
   - Widescreen 16:9 text correction & FOV patch (Aero_ & Silent)
   - 480p progressive autoboot
   - Calibrated analog trigger sensitivity

2. **`gamesettings/646B2E29.ini`**:
   ```ini
   [EmuCore/GS]
   AspectRatio = 16:9
   Crop = 1
   CropMode = Overscan
   HardwareDownloadMode = 1
   UpscaleMultiplier = 2.0
   EnableWideScreenPatches = true
   EnableCheats = true
   ```

3. **Global `armsx2-settings.json`**:
   - `hardwareDownloadMode = 1` (disables GS readbacks, which resolves the GT4 night/tunnel lag)
   - `aspectRatio = 1` (16:9)
   - `enableWideScreenPatches = true`
   - `enableNoInterlacingPatches = true`
   - `touchControllerOpacity = 0` (hides on-screen virtual touchscreen controls)

## In-Game Step Required for Native 16:9
Gran Turismo 4 is an anamorphic widescreen PS2 title. To enable true 16:9 geometry without stretching:
1. In GT4 main menu / Home: go to **Options** -> **Screen / Picture**.
2. Change **Screen Size** from **Normal (4:3)** to **16:9**.
3. With ARM SX2's `AspectRatio = 16:9` and `CropMode = Overscan`, the game will render full 1080p widescreen with correct car aspect ratios and no black bars.
