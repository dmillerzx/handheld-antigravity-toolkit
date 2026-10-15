# QA_CHECKLIST.md — Quality Assurance & Validation Matrix

This document provides systematic, platform-by-platform validation procedures for the **v1.0-baseline** community provisioning release. Use these test cases to verify emulator performance, audio filtering, input latency, widescreen rendering, and storage streaming across all supported handhelds.

---

## 1. Quick Verification Dashboard

| Platform / Subsystem | Primary Verification Target | Expected Behavior | Status |
|---|---|---|---|
| **RetroArch 2D** | Frame Pacing & Run-Ahead | Solid 60.0 fps, 1-frame sub-frame response, Vulkan swapchain | `[PASS]` |
| **RetroArch Audio** | GBA 5.5kHz DSP & Genesis M1 LPF | Muffled harsh DAC noise eliminated, authentic analog timbre | `[PASS]` |
| **DuckStation (PS1)** | PGXP 1080p Geometry Precision | No polygon jitter/wobble, 5x native scaling, Cubeb 20ms | `[PASS]` |
| **NetherSX2 (PS2)** | CRC pnach Widescreen & CRT Crop | 16:9 widescreen without stretching; Crop=1 overscan border removal (Verified in GT4 Spec II) | `[PASS]` |
| **Dolphin (GC/Wii)** | Dynamic Controller Node & Classic Pad | Hardware auto-discovery, Classic mapping & L3+R3 pause hotkeys (Verified in Mario Kart Wii) | `[PASS]` |
| **Azahar (3DS)** | Mesa Turnip Driver Stability | Vulkan Async shaders compile without pipeline stalls | `[PASS]` |
| **Vita3K (PS Vita)** | Mesa Turnip 1080p Rendering | Stable 2x scaling without texture corruption or crashing | `[PASS]` |
| **DroidDeck (Steam)** | 720p FSR & MicroSD Steam Mount | MicroSD library mounted; 60fps UI; native XInput gamepad | `[PASS]` |

---

## 2. Platform-by-Platform Validation Procedures

### A. RetroArch (2D & Arcade Low-Latency Engine)

#### Test Case RA-01: Frame Pacing & Run-Ahead Latency Check
* **Objective:** Ensure ultra-responsive frame execution with zero dropped frames.
* **Test Rom:** *Super Mario World* (SNES) or *Sonic the Hedgehog 2* (Genesis).
* **Procedure:**
  1. Launch content via ES-DE or RetroArch.
  2. Press **Hotkey + X** or tap the screen to bring up the Ozone Quick Menu.
  3. Navigate to **Latency Settings**:
     * Verify `Run-Ahead to Reduce Latency` is **ON**.
     * Verify `Number of Frames to Run-Ahead` is set to **1** (or 2 for SNES).
  4. Perform jumps and twitch inputs using the D-Pad and Face Buttons.
* **Pass Criteria:** Input registers instantly on the subsequent display refresh cycle; no audio crackling or stuttering during normal gameplay.

#### Test Case RA-02: Game Boy Advance 5.5kHz IIR Audio Low-Pass Filter
* **Objective:** Verify authentic analog audio output replicating the original GBA speaker acoustic rolloff.
* **Test Rom:** *Castlevania: Aria of Sorrow* (GBA) or *Golden Sun* (GBA).
* **Procedure:**
  1. Open mGBA in RetroArch.
  2. Verify that DSP Audio Plugin is active (`/storage/<SD_ID>/RetroArch/filters/audio/gba_lowpass.dsp`).
  3. Check video shader preset: `/storage/<SD_ID>/RetroArch/config/mGBA/mGBA.slangp` (GBA Color Correction + LCD Grid v2).
* **Pass Criteria:** High-frequency digital DAC screeching is smoothed out; visuals display authentic GBA color profile and pixel grid without moiré patterns.

#### Test Case RA-03: Genesis Plus GX Model 1 Audio Filter
* **Objective:** Emulate the discrete discrete low-pass filter of the original Sega Genesis Model 1 (VA3–VA6 motherboards).
* **Test Rom:** *Streets of Rage 2* (Genesis) or *Sonic the Hedgehog* (Genesis).
* **Procedure:**
  1. Open Genesis Plus GX in RetroArch.
  2. Open Quick Menu -> **Core Options** -> **Audio**:
     * Verify `Low-Pass Filter` is set to **ON**.
     * Verify `Low-Pass Filter Range` is set to **60**.
     * Verify `Sound Output` is set to **YM2612 (MAME)**.
* **Pass Criteria:** FM synth bass lines (Slap Bass, FM Snare) sound deep, warm, and authentic without harsh piercing treble clipping.

---

### B. Standalone 3D Emulators

#### Test Case 3D-01: DuckStation (PS1) — PGXP Precision & Frame Pacing
* **Objective:** Validate perspective-correct polygon rendering and audio buffer stability.
* **Test Game:** *Ridge Racer Type 4* or *Crash Bandicoot 3: Warped*.
* **Procedure:**
  1. Launch DuckStation.
  2. Verify Graphics settings:
     * Renderer: **Vulkan**
     * Resolution Scale: **5x (1080p)**
     * PGXP Geometry Correction: **Enabled**
     * PGXP Texture Correction: **Enabled**
     * Audio Backend: **Cubeb** (Buffer: 20ms)
* **Pass Criteria:** 3D road tracks and character models remain stable without vertex wobble or texture warping; audio stays perfectly synced with 0 crackling.

#### Test Case 3D-02: NetherSX2 (PS2) — CRC pnach Widescreen Hooks & CRT Overscan Crop
* **Objective:** Ensure automated master widescreen cheat injection functions without stretching 4:3 viewports, and eliminate CRT analog overscan blanking borders.
* **Test Game:** *Gran Turismo 4 Spec II*, *Final Fantasy X*, or *Burnout 3: Takedown*.
* **Procedure:**
  1. Launch NetherSX2.
  2. Verify that `Enable Widescreen Patches` is active and `Crop = 1` is configured under `[EmuCore/GS]` in `PCSX2.ini`.
  3. Launch *Gran Turismo 4 Spec II*. Observe menu navigation and in-race transition.
* **Pass Criteria:** 
  - Menus render cleanly in 4:3 pillarboxed format.
  - Race gameplay seamlessly shifts to native 16:9 widescreen perspective without geometry stretching.
  - `Crop = 1` successfully trims the analog CRT scanline borders on the top/bottom/sides, enabling the race viewport to cleanly fill the 1080p AMOLED panel.
  - Calibrated RP5 input profile maps face buttons, analog sticks, and triggers accurately.

#### Test Case 3D-03: Dolphin (GameCube / Wii) — Dynamic Controller Discovery & Classic Pad Fallback
* **Objective:** Validate programmatic input device resolution, Classic Controller scan-code bindings, analog trigger thresholds, and back/pause hotkey safety.
* **Test Game:** *Mario Kart Wii* and *Super Mario Sunshine* (GC).
* **Procedure:**
  1. Launch *Mario Kart Wii*.
  2. Check ADB logs or config files (`GCPadNew.ini`, `WiimoteNew.ini`) to ensure the device node was auto-resolved (e.g. `Android/8/Retroid Pocket Controller`).
  3. Verify that `WiimoteNew.ini` has `Source = 1` (Emulated), `Extension = Classic`, and `[Classic1]` bound to physical Retroid scan codes.
  4. Press **Button B** during race and menu navigation.
  5. Press **L3 + R3** (Left & Right thumbstick click combo).
  6. Test analog trigger spray modulation in *Super Mario Sunshine*.
* **Pass Criteria:**
  - Physical buttons and thumbsticks steer, accelerate, and drift in *Mario Kart Wii* without any manual remapping.
  - Pressing **Button B** acts strictly as an in-game action (drift / cancel / reverse) and **never** opens Dolphin's Android pause navigation drawer.
  - Dolphin's pause menu is triggered strictly via the safety combo (**L3 + R3** / `Button 106 & Button 107`).
  - Analog trigger threshold (`Axis 22+`, `Axis 23+`) and digital click register accurately.

#### Test Case 3D-04: Azahar (3DS) & Vita3K — Mesa Turnip Driver Stability
* **Objective:** Confirm Turnip Adreno Vulkan driver stability and shader compilation.
* **Test Game:** *The Legend of Zelda: A Link Between Worlds* (3DS) / *Persona 4 Golden* (Vita).
* **Procedure:**
  1. Launch Azahar -> Verify Custom Driver points to `/sdcard/Download/drivers/Turnip_v26.0.0_R8.zip`.
  2. Launch Vita3K -> Verify GPU Driver is set to Turnip v26.0.0 R8.
  3. Play through introductory sequence and shader-heavy area.
* **Pass Criteria:** Game boots without GPU hang (`VK_ERROR_DEVICE_LOST`); frame rate remains solid at 3x (3DS) and 2x (Vita).

---

### C. DroidDeck (Steam & PC Translation)

#### Test Case DD-01: 720p FSR Upscaling Performance
* **Objective:** Confirm DXVK 720p rendering upscaled to 1080p via AMD FidelityFX Super Resolution.
* **Test Game:** *Hollow Knight*, *Dead Cells*, or *Celeste*.
* **Procedure:**
  1. Launch DroidDeck Session Activity.
  2. Verify `/sdcard/DroidDeck/config.json`:
     * `render_width`: 1280, `render_height`: 720
     * `fsr_enabled`: true
     * `dxvk_async`: 1
  3. Launch title from Steam Big Picture.
* **Pass Criteria:** Game renders sharply at 60fps with clear text legibility and low thermal output.

#### Test Case DD-02: MicroSD Steam Library Streaming & Mount Verification
* **Objective:** Confirm external MicroSD card write speed and Steam runtime path resolution.
* **Procedure:**
  1. Execute verification check over ADB:
     ```bash
     adb shell "cat '/sdcard/DroidDeck/prefixes/default/drive_c/Program Files (x86)/Steam/config/libraryfolders.vdf'"
     ```
  2. Verify that `/storage/<SD_ID>/Games/Steam` appears under `path`.
  3. Install or run a lightweight game from the MicroSD library.
* **Pass Criteria:** Steam downloads and installs directly to external storage; game loads seamlessly without file lock timeouts.

---

## 3. Automated Validation Script Commands

To verify permissions, directory integrity, and active settings in one command over ADB:

```powershell
# Verify Canonical Scaffolding
.\platform-tools\adb.exe -s ff152647 shell "ls -d /sdcard/bios /storage/*/ROMs /storage/*/ES-DE /storage/*/RetroArch"

# Verify AppOps MANAGE_EXTERNAL_STORAGE Grants
.\platform-tools\adb.exe -s ff152647 shell "appops get org.es_de.frontend MANAGE_EXTERNAL_STORAGE; appops get com.retroarch.aarch64 MANAGE_EXTERNAL_STORAGE"

# Verify Android 13 Phantom Process Limit Bypass
.\platform-tools\adb.exe -s ff152647 shell "/system/bin/device_config get activity_manager max_phantom_processes"
```
