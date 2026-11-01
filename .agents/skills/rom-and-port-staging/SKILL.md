---
name: rom-and-port-staging
description: >-
  Standardized runbook and toolchain for packaging and staging ROMs (Deflate .n64.zip, .rvz, .chd)
  and deploying native Android port profiles (e.g., Perfect Dark XBLA twin-stick controls).
---

# ROM Packaging & Native Port Staging Skill

This skill provides deterministic procedures and Python toolchains for packaging ROMs according to handheld emulation standards, verifying archive integrity, and deploying native Android port profiles with modern controls.

---

## 1. ROM Packaging & Compression Standards

Handheld frontends (ES-DE) and emulators (RetroArch cores, Mupen64Plus FZ, Dolphin, DuckStation, NetherSX2) require clean archive structures without nested subdirectories.

### A. Nintendo 64 (N64) — Russ's Retro Game Corps Best Practice
- **Format**: Strictly uncompressed / extracted `.z64` (big-endian byte order).
- **Why Uncompressed**: In Russ's Retro Game Corps guides (including the *Android Emulation Starter Guide* and device-specific setup guides), keeping N64 games unzipped rather than leaving them in `.zip` or `.7z` archives is strongly recommended. Standalone emulators (such as Mupen64Plus FZ) and certain frontends (ES-DE) experience loading, parsing, or background extraction issues with compressed N64 archives.
- **Why `.z64` (Big-Endian)**: `.z64` files use big-endian byte ordering (the native format of the Nintendo 64 hardware), making them the universal standard across modern emulators and native PC/Android recompilation ports (Banjo-Kazooie, DKR-R, Starship, SpaghettiKart) without requiring on-the-fly byte-swapping.
- **Rule**: Never leave N64 games in `.zip` or `.7z` archives in `/storage/<SD_ID>/ROMs/n64/`.

### B. Nintendo DS (NDS)
- **Format**: Uncompressed `.nds`. Eliminates duplicate `.zip` containers and ensures instant discovery in DraStic and melonDS DS.

### C. 16-bit / 8-bit Cartridge Systems (SNES, GBA, Genesis, NES)
- **Format**: Standard ZIP archive using Deflate compression (`ZIP_DEFLATED`, `compresslevel=9`).
- **Archive Contents**: Exactly **one** ROM binary file directly at the root of the `.zip`. Never include nested subdirectories, `.txt` documentation, or patch notes inside the archive.
- **Naming Rule**:
  - SNES: `<Game Title>.sfc.zip` containing `<Game Title>.sfc`.
  - GBA: `<Game Title>.gba.zip` containing `<Game Title>.gba`.
  - Genesis: `<Game Title>.md.zip` containing `<Game Title>.md`.
- **Why Avoid `.7z` on Android Handhelds**:
  1. Standalone emulators frequently do not support `.7z`.
  2. RetroArch must decompress the full `.7z` into RAM/cache storage before booting, introducing launch lag.
  3. Community `.7z` distributions frequently contain nested subfolders that break automated frontend scraper matching.

### D. Python Repackaging Pipeline (7z / Zip -> Clean Uncompressed .z64)

```python
import py7zr, zipfile, os, shutil

def extract_to_clean_z64(in_archive: str, out_dir: str):
    """Extracts N64 archive to pure big-endian .z64 per RGC best practice."""
    if in_archive.lower().endswith(".7z"):
        with py7zr.SevenZipFile(in_archive, mode='r') as z:
            names = z.getnames()
            rom_entries = [n for n in names if n.lower().endswith(('.z64', '.n64', '.v64'))]
            if not rom_entries:
                raise FileNotFoundError("No ROM binary found in archive")
            target = rom_entries[0]
            z.extract(path=out_dir, targets=[target])
    elif in_archive.lower().endswith(".zip"):
        with zipfile.ZipFile(in_archive, mode='r') as z:
            names = z.namelist()
            rom_entries = [n for n in names if n.lower().endswith(('.z64', '.n64', '.v64'))]
            if not rom_entries:
                raise FileNotFoundError("No ROM binary found in archive")
            target = rom_entries[0]
            z.extract(target, path=out_dir)
```

### C. Disc-Based Systems
- **PS1, PS2, PSP, Dreamcast, Sega CD, Saturn**: Compressed `.chd` (CD-ROM/DVD MAME chdman format).
- **GameCube, Wii**: Compressed `.rvz` (Dolphin RVZ format with zstd and 128KB block size).
- **Original Xbox (hakuX)**: Sector-aligned XDVDFS `.iso` generated via `extract-xiso -c <game_folder> <target.iso>`. (See Section 10).

### D. Sony PlayStation Portable (PSP) CHD Staging & 60 FPS Optimization

1. **Extraction & MAME CHD Conversion**:
   - Extract raw `.iso` from `.7z` / `.zip` archive.
   - Convert to standard MAME UMD/DVD CHD format:
     ```powershell
     .\scratch\chdman.exe createdvd -i "<game>.iso" -o "<game>.chd" -f
     ```
   - Delete temporary `.iso` immediately to preserve host storage.

2. **Canonical SD Staging**:
   - Push to `/storage/<SD_ID>/ROMs/psp/<game>.chd`.
   - Update `/sdcard/ES-DE/gamelists/psp/gamelist.xml` with `<game>` metadata entry to ensure instant frontend discovery.

3. **PPSSPP Dynamic Framerate Unlocking**:
   - For titles with internal variable framerate limiters (e.g., *OutRun 2006*):
   - Inject per-game configuration into `/sdcard/PSP/SYSTEM/<GAME_ID>_ppsspp.ini`:
     ```ini
     [Graphics]
     GraphicsBackend = 3       # Vulkan
     InternalResolution = 4    # 4x Native (1920x1088 for 1080p AMOLED)
     AnisotropyLevel = 16

     [CPU]
     FastMemory = True
     LockedCPUSpeed = 444      # Overclocks emulated PSP CPU from 222/333MHz to maintain 60 FPS ceiling
     ```

---

## 2. On-Device Verification Protocol

Always verify archive integrity on the physical device over ADB:

```powershell
# 1. Push to canonical MicroSD path
adb -s <serial> push "<local_path>" "/storage/<SD_ID>/ROMs/<system>/<filename>"

# 2. Test archive integrity
adb -s <serial> shell "unzip -t '/storage/<SD_ID>/ROMs/<system>/<filename>'"

# 3. Verify zero errors detected in output
```

---

## 3. Native Android Port Configurations (e.g., Perfect Dark)

For standalone native Android ports (such as `com.perfectdark.port`), configure modern twin-stick FPS controls matching Xbox Live Arcade (*Duty Calls* / *Spartan*) presets:

### Perfect Dark Engine Invariants (`libpd.so`)
1. **`StickCButtons = 0`**: Prevents quantization of the right analog stick into 4-way discrete digital pulses. Delivers raw 360° analog pitch/yaw to `rstick_x` and `rstick_y`.
2. **Control Style 8 ("Ext")**: In `bmoveProcessInput`, true analog look code is gated behind `cmp w20, #8`. In-game control style MUST be set to **"Ext"** (never 1.1 or 1.2 Solitaire).
3. **`MouseAimMode = 1`**: Locks reticle dead-center on screen, eliminating the sluggish N64 floating cursor bounding box.
4. **`CrosshairSway = 0`**: Disables weapon wobble during locomotion.
5. **In-Game `Lookspring = OFF`**: Prevents the camera from auto-leveling the vertical pitch to horizon when moving forward.
6. **Key Action Binds**:
   - `Z_TRIG = JOY1_RTRIGGER` (RT Fire)
   - `R_TRIG = JOY1_LTRIGGER` (LT Precision Aim/Zoom)
   - `L_TRIG = JOY1_LSHOULDER, JOY1_RSHOULDER` (RB/LB Alt-Fire / Weapon Function)
   - `X_BUTTON = JOY1_X` with `UseKeyReloads = 1` (Dedicated Reload)
   - `Y_BUTTON = JOY1_Y` (Next Weapon)
   - `A_BUTTON = JOY1_A` (Action / Open Doors / Accept)
   - `B_BUTTON = JOY1_B` / `CANCEL_BUTTON = JOY1_B, JOY1_BACK` (Cancel / Back)
   - `CK_8000 = JOY1_B, JOY1_RSTICK` (Cycle Crouch on B and R3 Click)
- Profile maintained in `configs/ports/perfect_dark/pd.ini` and staged via `stage_port_configs()`.

### B. Super Mario 64 ALO (`com.izzyagamer.sm64alo`)
- Built natively on Snapdragon 865 with 60 FPS animation interpolation and 1080p widescreen canvas.
- Deployed touchless binary (`sm64.alo.clean.apk`) removing hardcoded touch overlays.
- Controller profile:
  - `key_z` bound to ZL (`101a`) + L1 (`1009`) + L3 (`1007`) for responsive crouch/ground-pound/long-jump.
  - `key_b` bound to both X (`1002`) and B (`1001`) for versatile attack/dive.
  - `key_r` bound to R1 (`100a`) and ZR (`101b`).
  - BetterCamera 360° analog stick look active (`bettercam_analog true`, sensitivity 70).
  - VSync enabled (`vsync true`) locking 60.0 FPS without tearing.

### C. Sonic Mania Plus (`com.decomp.rsdkv5`)
- Decompilation engine installed via `com.decomp.rsdkv5`.
- Data file `Data.rsdk` (208 MB) and `Settings.ini` staged to `/sdcard/RSDK/v5/` and `/sdcard/Android/data/com.decomp.rsdkv5/files/`.
- 1080p 60 FPS native rendering with physical controller auto-detection.

### D. GoldenEye 007 Recomp (`com.sunjaycy.goldeneye`)
- Requires game files and `default.xex` located directly in the root files folder `/sdcard/Android/data/com.sunjaycy.goldeneye/files/` (never nested under `files/assets/`, which causes missing asset errors).

### E. CannonBall Arcade OutRun (`CannonBall - OutRun.game`)
- Deploys Libretro CannonBall core (`cannonball_libretro_android.so`) to `/storage/<SD_ID>/RetroArch/cores/`.
- Arcade Revision B ROMs and engine data staged to `/storage/<SD_ID>/RetroArch/system/cannonball/`.
- Configured with 60 FPS, 16:9 widescreen, and high-res rendering via `Cannonball.opt`.
- Eliminates 32-bit PC container overhead for OutRun on RP5.

---

## 4. LibUltraShip & Torch Decompilation Ports Runbook

Applies to HarbourMasters LibUltraShip ports: **Ship of Harkinian** (`com.dishii.soh`), **2 Ship 2 Harkinian** (`com.dishii.mm`), **Star Fox 64 Starship** (`com.starship.android`), and **Paper Mario 64 PaperBoat** (`dev.net64.paperboat`).

### A. Upstream CI Discovery
- HarbourMasters repositories compile automated Android artifacts (`*.apk`) on push to `develop`.
- Download artifacts via GitHub CLI:
  ```powershell
  gh run download <run_id> --repo <owner/repo> --dir scratch/<port>_run
  ```
- Staged APKs reside in `apks/ports/<name>.apk`.

### B. Zero-Touch On-Device Torch Extraction
Rather than running complex host-side desktop extraction tools, LibUltraShip Android APKs embed the C++ `Torch` asset extractor inside `libmain.so`:
1. Push verified clean N64 ROM to the app's external files directory as `baserom.us.z64`:
   ```powershell
   adb -s <serial> shell "mkdir -p /sdcard/Android/data/<package>/files/"
   adb -s <serial> push "<clean_rom.z64>" "/sdcard/Android/data/<package>/files/baserom.us.z64"
   ```
2. Grant storage permissions:
   ```powershell
   adb -s <serial> shell "appops set <package> MANAGE_EXTERNAL_STORAGE allow"
   ```
3. Launch `LauncherActivity`:
   ```powershell
   adb -s <serial> shell "am start -n <package>/.LauncherActivity"
   ```
4. The launcher executes `Torch` in a background worker, unpacks `config.yml`, hashes the ROM, and generates `*.o2r` (e.g. `pm64.o2r` 40.1 MB) and `torch.hash.yml`. The launcher exits via `Runtime.exit()` once finished, cleanly releasing memory.

### C. Headless Config Tuning & Touch Control Suppression
In `/sdcard/Android/data/<package>/files/<port>.cfg.json`:
- Suppress on-screen virtual buttons:
  ```json
  "gTouchControls": {
      "EditMode": 0,
      "Enabled": 0,
      "Opacity": 0.8,
      "Scale": 1.0
  }
  ```
- Align backend ID to OpenGL:
  ```json
  "Window": {
      "AudioBackend": "sdl",
      "Backend": {
          "Id": 1,
          "Name": "OpenGL"
      }
  }
  ```

### D. ES-DE Launcher Registration
Register the port in the canonical MicroSD launcher path:
```powershell
adb -s <serial> shell "echo '<package>' > '/storage/<SD_ID>/ROMs/ports/<Title>.app'"
```
Dispatched cleanly by ES-DE via `<command label="Android App">%ANDROIDAPP%=%FILEINJECT%</command>` in `es_systems.xml`.

### E. OpenGLES Fast3D Shader Limitations & Mupen64Plus FZ Fallback
- In LibUltraShip ports under Android OpenGLES (e.g., PaperBoat `dev.net64.paperboat`), 2D paletted textures (CI4, CI8, IA fonts, UI text cards, and character billboard sprites) experience severe vertical striping/aliasing due to Fast3D GLES palette sampling math (`paletteSample()` in `palette.glsli` / `interpreter.cpp`). 3D polygon geometry renders normally at 60 FPS.
- This is an upstream shader/engine defect and cannot be resolved by editing `paperboat.cfg.json` CVars on-device. Tracked upstream in [HarbourMasters/PaperBoat#274](https://github.com/HarbourMasters/PaperBoat/issues/274).
- For immediate 1080p 60 FPS playthroughs with high-resolution texture packs, maintain clean Deflate 9 `.n64.zip` archives in `/storage/<SD_ID>/ROMs/n64/` playable via standalone **Mupen64Plus FZ**.

---

## 5. Native Android Port APK Asset & Launcher Icon Injection Runbook

Community native ports frequently lack `res/mipmap` drawables and `android:icon` manifest attributes, causing Android 13 to fall back to a placeholder icon (purple circle with white Android robot).

### A. APK Decompilation
Disassemble the port APK without altering dex bytecode:
```powershell
java -jar scratch/tools/apktool.jar d "apks/ports/<port>.apk" -o "scratch/<port>_src" -f
```

### B. Master Badge Geometry & Mipmap Generation
1. Design or extract a 1024x1024 circular master image with antialiased transparent padding outside the outer rim (badge diameter ~90% of canvas width).
2. Generate the complete density suite using PIL:
   - `mipmap-mdpi`: 48x48 (standard), 108x108 (adaptive)
   - `mipmap-hdpi`: 72x72 (standard), 162x162 (adaptive)
   - `mipmap-xhdpi`: 96x96 (standard), 216x216 (adaptive)
   - `mipmap-xxhdpi`: 144x144 (standard), 324x324 (adaptive)
   - `mipmap-xxxhdpi`: 192x192 (standard), 432x432 (adaptive)
3. Stage `ic_launcher.png`, `ic_launcher_round.png`, and `ic_launcher_foreground.png`.
4. Configure adaptive vector definition in `res/mipmap-anydpi-v26/ic_launcher.xml` and `ic_launcher_round.xml` referencing `@color/ic_launcher_background` (`#FF101216`).

### C. Manifest Injection
In `AndroidManifest.xml`, update `<application>` and launcher `<activity>`:
```xml
<application android:icon="@mipmap/ic_launcher"
             android:roundIcon="@mipmap/ic_launcher_round"
             android:isGame="true" ...>
    <activity android:icon="@mipmap/ic_launcher"
              android:roundIcon="@mipmap/ic_launcher_round" ...>
```

### D. Recompilation & Alignment Signing
```powershell
java -jar scratch/tools/apktool.jar b "scratch/<port>_src" -o "scratch/<port>_unaligned.apk"
java -jar scratch/tools/uber-apk-signer.jar -a "scratch/<port>_unaligned.apk" -o "apks/ports/" --allowResign
```

### E. Data Protection Invariant During Signature Migration
When replacing an existing installation whose signing key differs:
1. `adb install -r` rejects with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`.
2. **SAFETY INVARIANT**: Never run `pm uninstall` without first backing up game assets and saves:
   ```powershell
   adb shell "mkdir -p /sdcard/<port>_backup && cp -r /sdcard/Android/data/<package>/files/* /sdcard/<port>_backup/"
   ```
3. Execute `adb shell pm uninstall <package>`.
4. Install rebuilt APK: `adb install "apks/ports/<rebuilt>.apk"`.
5. Restore files:
   ```powershell
   adb shell "mkdir -p /sdcard/Android/data/<package>/files && cp -r /sdcard/<port>_backup/* /sdcard/Android/data/<package>/files/"
   ```
6. Grant storage access: `adb shell appops set <package> MANAGE_EXTERNAL_STORAGE allow`.

### F. Frontend Media Mirroring
Mirror master icon PNG to ES-DE frontend media paths:
- `/sdcard/ES-DE/downloaded_media/ports/covers/<Title>.png`
- `/storage/<SD_ID>/ROMs/ports/media/covers/<Title>.png`

---

## 7. N64Recomp & RT64 Engine Port Architecture (DKR-R / Banjo Recomp)

### A. Rendering Pipeline & TBDR Constraints
- **N64Recomp** (Mr-Wiseguy) statically recompiles N64 MIPS R4300i binaries to native C/C++.
- The graphics backend relies on **RT64** (Vulkan/D3D12), an engine built for modern PC raytracing, 60fps/uncapped interpolation, and post-processing.
- **Mobile Hardware Mismatch**: Mobile GPUs (Qualcomm Adreno 650) use Tile-Based Deferred Rendering (TBDR). RT64's render passes and constant buffer churn create memory bandwidth bottlenecks.
- **Qualcomm Stock Driver Bug**: Qualcomm's proprietary driver (`/vendor/lib64/hw/vulkan.adreno.so`) fails on RT64's SPIR-V shaders, returning `VK_NULL_HANDLE` and triggering a fatal `SIGSEGV` null pointer dereference inside `vkCmdBindPipeline`.

### B. Two-Phase Remediation Strategy
1. **Phase 1: Boot & Driver Injection**:
   - Integrate **AdrenoTools** into the Android NDK JNI wrapper to dynamically inject Mesa Turnip (`turnip_v24.3.0_R9v2.zip`), bypassing Qualcomm's broken SPIR-V compiler.
   - Patch `RT64::DisplayList::draw()` and `recompui::renderer::RT64Context` with null-checks to catch failed pipeline handles gracefully.
2. **Phase 2: Performance Profiling**:
   - Disable heavy desktop post-processing bloom/shadow passes in mobile builds.
   - Simplify descriptor set churn for TBDR architecture.

---

## 8. Downstream Handheld Fork Governance & Community Release Automation

When an upstream maintainer drops platform support (e.g. ThatGuyMcd on DKR-R Android):
1. **Maintain an `upstream` Remote**:
   - Point to the official upstream repository:
     ```powershell
     git remote add upstream <upstream_url>
     git fetch upstream --tags
     ```
2. **Continuous Upstream Synchronization**:
   - Routinely rebase or merge upstream releases/commits onto the downstream platform branch:
     ```powershell
     git rebase upstream/main # or upstream tag like Version1.0.11
     ```
   - Always verify `ahead_by: N, behind_by: 0` before cutting community releases.
3. **Android CMake Target Boundary**:
   - Never execute default `ninja -C build/android-arm64`, which attempts to compile desktop host tests (such as `DKRMipmapLoadingTests` which fails because `RenderWindow` is `ANativeWindow*` rather than `SDL_Window*`).
   - Explicitly target the Android shared library:
     ```powershell
     ninja -C build/android-arm64 DKRPortGame
     ```
     This produces `libDKR-R.so` with zero desktop test overhead.
4. **Align CMake Version Cache with Packaging**:
   - Pass `-DDKR_RELEASE_VERSION=<version>` during CMake configuration to match the version requested by packaging scripts (`Package-Android-Preview.ps1`).
5. **Automated GitHub Community Release**:
   - Handheld console users lack NDK/CMake buildchains. Build standalone APKs via packaging scripts and publish immediately to GitHub Releases:
     ```powershell
     gh release create <tag> <apk_path> --title "<title>" --notes "<notes>"
     ```
   - Always include SHA-256 checksums and controller mapping instructions in the release body.

---

## 9. N64Recomp Input Engine Mutex Law & Handheld Deadzone Tuning

### A. Single-Action Binding Exclusivity (`runtime_input.cpp`)
In N64Recomp engine input systems (`set_controller_binding`), binding an existing controller source ID to an action forcibly unbinds it from any previous action. Handheld layouts must allocate physical buttons mutually exclusively:
- **Accelerate / Gas**: RT (`1011`) [Primary] / A (`0`) [Alternate]
- **Item Fire**: LT (`1009`)
- **Drift**: RB (`10`)
- **Horn / Map Display**: LB (`9`)
- **Brake / Reverse**: X (`2`) and B (`1`)
- **Look Back**: R3 Click (`8`) and Y (`3`)

### B. Hall-Effect Stick Deadzone & Trigger Calibration
Handheld consoles like the Retroid Pocket 5 feature precision Hall-effect sticks and analog triggers. The default desktop recomp settings introduce massive deadband slop:
- **`stick_deadzone`**: Reduce from default `23.95` down to `6.0` (eliminates deadband slop without stick drift).
- **`trigger_threshold`**: Reduce down to `0.20` for hair-trigger response.
- **Config Deployment**: Deploy profile deterministically to `/sdcard/Android/data/<package>/files/config/<port>-settings.ini`.

### C. Retroid Pocket 5 Snapdragon 865 Real-World Profiling Receipt
- **Display Refresh**: Locked 60.0 FPS native 1080p (`1920x1080`).
- **GPU Frametime**: 4.65 ms (~28% of 16.66 ms budget on Adreno 650).
- **CPU Frametime**: 5.84 ms (~35% of Kryo 585 Prime core).
- **Interpolation**: RT64 motion-interpolates 30 Hz N64 simulation ticks to 60 Hz display refresh with zero judder.

---

## 10. Original Microsoft Xbox (hakuX) ROM Packaging & XDVDFS Deployment Standard

### A. Architectural Boundary & Disc Geometry
- **Emulator Core**: `hakuX` (`com.rfandango.haku_x`) is a high-level reimplementation of the Xbox kernel drawing to Vulkan with an integrated x86 FEX JIT. It requires **no BIOS, MCPX ROM, or hard disk image**.
- **Block-Level Disc Mount**: hakuX mounts games as block-level disk images reading the proprietary Xbox DVD File System (XDVDFS).
- **Why Raw `.7z` or Extracted Folders Fail**:
  1. Loose folder structures containing `default.xbe` cannot be mounted by hakuX's virtual disc drive and are ignored by ES-DE's Xbox system dispatch.
  2. Raw `.7z` archives cannot be decompressed into RAM dynamically on mobile devices without causing severe out-of-memory crashes.

### B. Sector-Aligned XDVDFS Packaging (`extract-xiso`)
Transform extracted game folders containing `default.xbe` into sector-aligned XDVDFS `.iso` images using `extract-xiso`:
```powershell
extract-xiso.exe -c "<path_to_game_folder_with_default.xbe>" "<output_name>.iso"
```

### C. Compression Economics: Trimmed XISO vs. 1:1 Redump vs. CSO/ZSO
1. **1:1 Redump DVD-9 Dumps**: Fixed at **7.28 GiB (7.48 GB)** per game due to zero-padding, layer-break padding, and the outer DVD-Video partition. An 11-game library consumes **80.17 GiB (86.08 GB)**.
2. **Trimmed XDVDFS `.iso` (Community Standard)**: Strips all dummy padding and video security partitions, retaining only active game sectors. The same 11 games consume **17.55 GiB (18.84 GB)** — a **78.1% space reduction** (62.62 GiB saved).
3. **Why We Lead with Uncompressed Trimmed XISO Over CSO/ZSO**:
   - **Zero CPU Decompression Overhead**: Raw DMA reads from MicroSD have 0% CPU cost, reserving 100% of the Snapdragon 865's CPU cycles for FEX x86 JIT translation and game logic.
   - **Eliminates Asset Streaming Stutter**: Real-time decompression of `.cso` (Deflate) or `.zso` (LZ4) blocks causes micro-stutter and audio crackling during streaming in open-world/racing titles (*OutRun 2006*, *Crazy Taxi 3*, *Castlevania*).
   - **Emulator Maturity**: Early-stage emulators (hakuX v1.2.x) are most stable against uncompressed sector offsets. Reserve CSO/ZSO only when card capacity is critically depleted (< 15 GB free).

### D. Automated Pipeline Tooling (`scripts/deploy_xbox_roms.py`)
Use `scripts/deploy_xbox_roms.py` to automate unpacking `.7z`, locating `default.xbe`, building XDVDFS `.iso`, deploying to `/storage/<SD_ID>/ROMs/xbox/`, and scrubbing scratch files. Always dynamically detect device serial and SD card UUID to satisfy privacy and portability constraints.

### E. ES-DE Launch Dispatch & SAF Intent Token Standards (`%DATA%=%ROMSAF%`)
- **Canonical Custom Systems Location**: Deploy to `/sdcard/ES-DE/custom_systems/es_systems.xml` (internal) and `/storage/<SD_ID>/ES-DE/custom_systems/es_systems.xml` (MicroSD).
- **XML Schema Strictness**: ES-DE parses `es_systems.xml` strictly on startup; any unclosed tag or syntax error causes an immediate fatal crash on launch. Validate XML with `python -c "import xml.etree.ElementTree as ET; ET.parse('configs/es_systems.xml')"` before pushing.
- **Intent Binding Syntax**:
  ```xml
  <system>
      <name>xbox</name>
      <fullname>Microsoft Xbox</fullname>
      <path>%ROMPATH%/xbox</path>
      <extension>.iso .ISO .xiso .XISO</extension>
      <platform>xbox</platform>
      <theme>xbox</theme>
      <command label="hakuX (Standalone)">%EMULATOR_HAKUX% %ACTION%=android.intent.action.VIEW %DATA%=%ROMSAF%</command>
      <command label="hakuX Direct (Standalone)">%EMULATOR_HAKUX% %ACTION%=android.intent.action.VIEW %DATA%=%ROM%</command>
  </system>
  ```
  - **Android Scoped Storage (SAF)**: Android 11+ prevents external applications from reading raw storage paths (`%ROM%`). ES-DE generates a Content URI with read permissions via `%ROMSAF%` mapped into `%DATA%`.

### F. Xbox Aspect Ratio Architecture & Screen Format Standards (Crazy Taxi 3 Case Study)
- **Two-Tier Geometry Control**: Xbox display aspect ratio is controlled by console EEPROM `Screen Format` (`Normal` 4:3 vs `Wide screen` 16:9 anamorphic) and game engine capabilities.
- **Non-Widescreen Titles**: Games coded strictly for 4:3 (e.g. *Crazy Taxi 3: High Roller*, *Jet Set Radio Future* v1) do not inspect or support 16:9 flags.
  - When hakuX's **Screen Format** is set to `Wide screen` and **Aspect Ratio** is set to `Auto`, hakuX treats the output as 16:9, causing horizontal stretching across the 16:9 display.
  - **Pillarboxing Standard**: For 4:3-only titles, set hakuX global **`Aspect Ratio` = `4:3`** (or change `Screen Format` to `Normal`). Setting `Aspect Ratio: 4:3` forces clean 1:1 circular pillarboxing (black sidebars) with undistorted HUD and geometry.
- **hakuX Per-Game Override Scope**: Reverse engineering of `libhaku.so` (`gameOverrides` / `per_game_settings`) shows that hakuX v1.2.x only supports per-game overrides for `render_scale`, `upscale_filter`, and `driver`. Aspect ratio and screen format are global emulator settings.

### G. Retroid Pocket 5 Hall Effect Analog Stick Deadband Standards
- **Sensor Mechanics**: The RP5 features Hall effect magnetic analog joysticks. While immune to physical wear and drift, magnetic zero-point sensing produces microscopic resting electrical variance (±3-5%).
- **Micro-Input Elimination**: Without software deadbands, this resting variance causes character creeping, unintentional sprinting, or menu drift.
- **Standardized Deadbands**:
  - **Dolphin**: `Main Stick/Dead Zone = 10.0` and `C-Stick/Dead Zone = 10.0` in `GCPadNew.ini`.
  - **ARM SX2**: `Deadzone = 0.06` with `AxisScale = 1.33` in `RP5r.ini` (ensures 100% diagonal travel).
  - **RetroArch**: `input_analog_deadzone = 0.10`.
  - **Native Ports**: `stick_deadzone = 6.0` to `10.0`.

---

## 11. N64 Recompilation Handheld Profile Standards (RT64 & RecompUI)

When porting, building, or configuring N64 recompiled native Android ports (such as *Banjo-Kazooie Recompiled* and *Diddy Kong Racing Recompiled*):

### A. Android Modern Handheld Presentation Baseline
Desktop defaults (original 30 FPS, 4:3 pillarboxing, 240p original resolution) cause jarring judder and black sidebars on handheld AMOLED panels. Handheld ports must apply the following presentation policy on first launch:
1. **Target Refresh Rate**: 60 FPS (`presentation_policy.hpp` / `config.cpp`). Synchronizes with the RP5's 60 Hz display, eliminating stutter.
2. **Aspect Ratio**: 16:9 Expand (`AspectRatioMode::Expand`). Renders full-width widescreen while clamping UI and 2D elements within safe 16:9 boundaries without stretching 3D geometry.
3. **Internal Resolution**: `Original 2x` (480p). Provides pixel-clean retro presentation and rock-solid 60 FPS without GPU thermal throttling on Snapdragon 865 Adreno 650.
4. **Code Architecture Boundary**: Enforce all handheld defaults under `#if defined(__ANDROID__)` preprocessor guards in engine config sources (e.g. `src/game/config.cpp` and `RecompUI/ui_config_tab_graphics.cpp`) to preserve upstream compatibility on desktop/Linux targets.

### B. Ergonomic Twin-Stick & Dual-Trigger Controls
Handheld grips require modern twin-stick conventions:
1. **Z-Trigger Multi-Binding**: Map `GameInput::Z` to both Left Trigger (ZL, axis 22/LT) and Left Shoulder (L1/LB). Handheld players frequently use L1 for precision crouch, ground pounds, and long jumps.
2. **C-Down & Right Analog Camera**: In upstream configs, L1 is frequently overloaded as C-Down. Map `GameInput::C_DOWN` strictly to the Right Analog Stick (`SDL_CONTROLLER_AXIS_RIGHTY +`), freeing L1 from conflicting actions.

### C. Obtainium Direct Download URL Standard
1. **Format Invariant**: All Obtainium manifest records in `rp5_master_obtainium.json` and on-device records (`/data/data/dev.imranr.obtainium/app_flutter/app_data/*.json`) must use public browser download URLs:
   ```text
   https://github.com/<owner>/<repo>/releases/download/<tag>/<filename>.apk
   ```
2. **Never Use GitHub REST API Asset URLs**: `https://api.github.com/repos/.../releases/assets/<id>` returns JSON metadata headers on unauthenticated GET requests, causing Obtainium to toast `"no APK found"` during batch updates.
3. **Synchronous Release Packaging**: Never publish release tags or announce updates before the APK artifact is compiled and attached to the GitHub release.

### D. Downstream Fork GitHub Actions Workflow Permissions
Forked community repositories (`dmillerzx/*`) default to read-only workflow permissions on GitHub Actions. Even if `permissions: contents: write` is declared in workflow YAMLs, release attachment fails with HTTP 403 `Resource not accessible by integration`.
- **Remediation**: Execute via GitHub CLI before triggering release builds:
  ```powershell
  gh api -X PUT /repos/<owner>/<repo>/actions/permissions/workflow -f default_workflow_permissions=write
  ```

### E. Static Binary Recompilation ROM Governance & Header Inspection Standard
1. **Base Revision Requirement**: Recompilation ports (N64Recomp, Banjo-Kazooie Recompiled, Zelda64Recomp) statically recompile specific base ROMs (e.g. NTSC-U v1.0). Alternate revisions (Rev A / v1.1) shift code offsets and fail cryptographic hash checks (`RomValidationError::IncorrectVersion`).
2. **Cartridge Header Validation**:
   - Offset `0x3B–0x3E`: 4-character ID (e.g. `NBKE` for Banjo-Kazooie, `NDRE` for DKR, `CZLE` for OOT).
   - Offset `0x3F`: Cartridge version byte (`0x00` = v1.0 / Rev 0, `0x01` = Rev A / v1.1).
   - Android wrappers must inspect byte `0x3F` on selection and display an `AlertDialog` if an unsupported revision is selected, avoiding silent returns to the menu.
3. **Zero-Touch Boot Hydration**:
   - In `Activity.onCreate()`, scan `/sdcard/Android/data/<pkg>/files/` and `/storage/*/ROMs/n64/` for authentic base ROMs (`NBKE\0`).
   - Atomically copy verified ROMs to internal storage (`data/<game_id>.z64`).
   - Ensures `recomp::is_rom_valid()` evaluates to `true` on first boot, presenting "Start Game" without file picker interaction.
4. **MicroSD Library Deduplication**:
   - Prune redundant or incompatible revisions (e.g. `Banjo-Kazooie (USA) (Rev A).z64`) from `/storage/<SD_ID>/ROMs/n64/` once the working base ROM is staged to prevent user confusion and duplicate ES-DE wheel entries.

### F. Downstream Handheld Repository Discoverability Protocol
1. **Repository Topics**: Configure comprehensive tags on GitHub via `gh repo edit --add-topic <tag>` (`retroid-pocket-5`, `snapdragon-865`, `adreno-650`, `turnip`, `vulkan`, `recompilation`, `handheld-gaming`, `ayn-odin`).
2. **Homepage Release Prominence**: Standalone APK releases must be promoted as `--latest` (`--prerelease=false`) so the release card and download badge render prominently on the repository homepage.
