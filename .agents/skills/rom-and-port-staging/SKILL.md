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

### A. Cartridge Systems (Nintendo 64, SNES, GBA, Genesis)
- **Format**: Standard ZIP archive using Deflate compression (`ZIP_DEFLATED`, `compresslevel=9`).
- **Archive Contents**: Exactly **one** ROM binary file directly at the root of the `.zip`. Never include nested subdirectories, `.txt` documentation, or patch notes inside the archive.
- **Naming Rule**:
  - N64: `<Game Title>.n64.zip` containing `<Game Title>.z64` at root.
  - SNES: `<Game Title>.sfc.zip` containing `<Game Title>.sfc`.
  - GBA: `<Game Title>.gba.zip` containing `<Game Title>.gba`.
- **Why Avoid `.7z` on Android Handhelds**:
  1. Standalone emulators (such as Mupen64Plus FZ) do not support `.7z`.
  2. RetroArch must decompress the full `.7z` into RAM/cache storage before booting, introducing severe launch lag on 64MB expanded ROMs.
  3. Community `.7z` distributions frequently contain nested subfolders that break automated emulator ROM path resolution.

### B. Python Repackaging Pipeline (7z -> Canonical Deflate .n64.zip)

```python
import py7zr, zipfile, os, shutil

def repack_7z_to_clean_n64_zip(in_7z: str, out_zip: str, temp_dir: str = "_temp"):
    with py7zr.SevenZipFile(in_7z, mode='r') as z:
        names = z.getnames()
        # Find the .z64 / .n64 file
        rom_entries = [n for n in names if n.lower().endswith(('.z64', '.n64', '.v64'))]
        if not rom_entries:
            raise FileNotFoundError("No ROM binary found in archive")
        target_entry = rom_entries[0]
        z.extract(path=temp_dir, targets=[target_entry])
    
    extracted_path = os.path.join(temp_dir, target_entry)
    clean_filename = os.path.basename(target_entry)
    
    with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        zout.write(extracted_path, arcname=clean_filename)
    
    shutil.rmtree(temp_dir)
```

### C. Disc-Based Systems
- **PS1, PS2, PSP, Dreamcast, Sega CD, Saturn**: Compressed `.chd` (CD-ROM/DVD MAME chdman format).
- **GameCube, Wii**: Compressed `.rvz` (Dolphin RVZ format with zstd and 128KB block size).

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
