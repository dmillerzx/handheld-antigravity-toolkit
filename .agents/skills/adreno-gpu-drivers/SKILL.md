---
name: adreno-gpu-drivers
description: >-
  Sourcing, verification, and deployment runbook for Qualcomm Adreno 650 Mesa Turnip
  GPU drivers on the Retroid Pocket 5 (Snapdragon 865). Outlines the Adreno 650 driver
  hierarchy, AdrenoTools injection workflows, and native Android port rendering boundaries.
---

# Qualcomm Adreno 650 (Snapdragon 865) GPU Driver Runbook

This skill outlines the sourcing, verification, configuration, and architectural boundaries of GPU drivers on the **Retroid Pocket 5 (RP5)** retro gaming console running **Android 13** on the **Qualcomm Snapdragon 865 (SM8250)** with **Adreno 650** GPU.

---

## 1. Hardware Architecture Context

- **SoC**: Qualcomm Snapdragon 865 (SM8250 / Kona)
- **GPU**: Adreno 650 (`a6xx` architecture family)
- **Stock Driver**: `/vendor/app/com.qualcomm.qti.gpudrivers.kona.api30` (Qualcomm Kona BSP driver)
- **Vulkan Version**: Vulkan 1.1 / 1.2 (Stock) ➔ Vulkan 1.3 / 1.4 (Turnip / Mesa)
- **Driver Staging Location**: `/sdcard/Download/drivers/`

---

## 2. Adreno 650 Driver Hierarchy

| Tier | Driver Package | Maintainer / Source | Recommended Usage |
| :--- | :--- | :--- | :--- |
| **Tier 1 (Universal Stable)** | `turnip_v24.3.0_R9v2.zip` | K11MCH1 (`AdrenoToolsDrivers`) | **Default baseline** for general 3D emulation, Azahar (3DS), DroidDeck (PC/Steam DXVK), and Dolphin fallback. Rock-solid stability, zero memory leaks, no vertex explosions. |
| **Tier 1b (SD865 Tuned)** | `TurnipZ-0.3.0.zip` | AlexSanz0902 (`turnip-sd865-z`) | **High performance & Switch emulation**. Custom-compiled Mesa 27.0-devel branch specifically for Snapdragon 865. Re-enables 4x anisotropic filtering, fixes Unreal Engine red/blue color swap, delivers up to +74% FPS in heavy titles. |
| **Tier 2 (a6xx Bugfix)** | `Turnip-24.1.0.adpkg_R18.a6xx.zip` | K11MCH1 (`AdrenoToolsDrivers`) | Dedicated `a6xx` depth-clearing and tessellation bugfix revision. Primary driver used when building custom `NetherSX2-Turnip` APKs. |
| **Tier 3 (OEM Baseline)** | Qualcomm Kona System Driver | Stock Android 13 Firmware | Built-in system driver. Primary for PS2 (ARM SX2 / NetherSX2), GameCube/Wii baseline (Dolphin), and mandatory fallback for titles that dislike Mesa (e.g. *Zelda: Link's Awakening*). |

> [!CAUTION]
> **Adreno 6xx vs. 7xx Invariant**: Never deploy Adreno 7xx-only (`vulkan.ad07xx.so` packages like unpatched Turnip v25/v26) as primary drivers on the RP5. Always inspect `meta.json` inside driver `.zip` archives to verify Adreno 600 (`a6xx`) compatibility.

---

## 3. Application Taxonomy & Driver Boundaries

### A. Native Android Ports & Decompilations
- **Standard Direct Native Ports**: *Perfect Dark*, *Super Mario 64 ALO*, *Sonic Mania Plus*, *GoldenEye 007 Recomp*, *Ship of Harkinian*, *2 Ship 2 Harkinian*, *Starship*, *Paperboat*, *Spaghetti Kart*, *DKR-R*, *AM2R*, *Balatro*, *PokeMMO*, *Sonic 3 A.I.R.*
  - **Rendering Boundary**: These are native C/C++ ARM64 binaries (`arm64-v8a`) compiled with SDL2, OpenGL ES 2/3, or native Vulkan. They link directly to Android's `/system/lib64/libvulkan.so` and `/system/lib64/libGLESv2.so` via Bionic libc.
  - **Rule**: Standard Android APKs **cannot and should not** load external Turnip ZIPs. They execute directly on Qualcomm's hardware Kona GPU driver at native 1080p 60 FPS with near-zero overhead.
- **AdrenoTools-Hooked Native Recompilations**: *Banjo-Kazooie Recompiled* (`com.aure.banjorecomp`)
  - **Why Custom Drivers Are Required**: RT64's Vulkan rendering engine triggers pipeline state crashes (`qglinternal::vkCmdBindPipeline` null pipeline dereference) on Qualcomm's stock Kona BSP driver (`api30`).
  - **Mechanism**: The Android wrapper embeds `AdrenoTools` (`BanjoGpuDriver.java` / `libadreno_tools.so`) and scans `/sdcard/Download/drivers/` on first launch, auto-importing `TurnipZ-0.3.0.zip` or `turnip_v24.3.0_R9v2.zip` with zero user configuration required.

### B. AdrenoTools Root Driver Packaging & `meta.json` Invariant
- **The Law**: AdrenoTools driver loaders must locate driver shared libraries by reading `meta.json`'s `libraryName` (e.g. `libvulkan_freedreno.so`) and accept root-level files, rather than mandating an `arm64-v8a/` directory hierarchy.
- **Failure Mode**: Standard community Turnip driver archives (e.g. `TurnipZ-0.3.0.zip`, `turnip_v24.3.0_R9v2.zip`) store `meta.json` and `libvulkan_freedreno.so` directly at the root of the ZIP. Enforcing that the `.so` parent directory must be named `arm64-v8a` causes driver import rejection with:
  `java.io.IOException: GPU driver package contains a supported Vulkan driver soname, but not for required ABI arm64-v8a`
- **Dynamic Soname Resolution Pattern**:
  ```java
  String targetSoname = (meta != null && meta.has("libraryName")) ? meta.getString("libraryName") : null;
  if (entryName.endsWith(".so") && (targetSoname == null || entryName.endsWith(targetSoname))) {
      // Valid driver entry accepted regardless of parent directory name
  }
  ```

### C. AdrenoTools Injected Standalone 3D Emulators
These emulators bundle the `AdrenoTools` dynamic linker hook library to dynamically inject external Mesa Turnip ZIPs:
- **Azahar (Nintendo 3DS)**:
  - File: `/sdcard/Android/data/org.azahar_emu.azahar/files/config/config.ini`
  - Setting: `custom_driver = /sdcard/Download/drivers/turnip_v24.3.0_R9v2.zip`
- **DroidDeck (Steam / PC Translation)**:
  - File: `/sdcard/DroidDeck/config.json`
  - Setting: `"CUSTOM_GPU_DRIVER": "/sdcard/Download/drivers/turnip_v24.3.0_R9v2.zip"`
- **Dolphin (GameCube & Wii)**:
  - Default: Qualcomm Stock Vulkan.
  - Optional Turnip: Settings (Gear) ➔ Graphics ➔ GPU Driver ➔ Install ➔ select driver ZIP.
- **Vita3K (PS Vita)**:
  - Default: Qualcomm Stock Vulkan.
  - Optional Turnip: Configuration ➔ Settings ➔ GPU ➔ Add Custom Driver ➔ select driver ZIP.
- **Switch Emulators (Sudachi / Citron / Yuzu)**:
  - Settings ➔ GPU Driver Manager ➔ Install ➔ select `TurnipZ-0.3.0.zip` or `turnip_v24.3.0_R9v2.zip`.

### D. Direct OS Bounded Emulators
- **ARM SX2 & NetherSX2 (PS2)**: Link directly to Android's system Vulkan ICD. In-app `.zip` file picking is unsupported. Performance is locked at 2.0x 1080p Vulkan using `HardwareDownloadMode = 1` (Disable Readbacks).
- **DuckStation (PS1)**: 5x 1080p PGXP on native Qualcomm Vulkan.
- **PPSSPP (PSP)**: 4x 1080p on native Qualcomm Vulkan.
- **Flycast (Dreamcast)**: 2x 1080p on native Qualcomm Vulkan.
- **RetroArch**: Native Vulkan backend (`video_driver = "vulkan"`).

---

## 4. Verification & Inspection Runbook

### Checking Driver ZIP Manifest
```python
import zipfile, json
with zipfile.ZipFile("driver.zip") as z:
    meta = json.loads(z.read("meta.json").decode("utf-8"))
    print("Driver Name:", meta.get("name"))
    print("Driver Version:", meta.get("driverVersion"))
    print("Library Name:", meta.get("libraryName"))
```

### Staging Drivers to Device via ADB
```bash
adb -s <serial> push drivers/turnip_v24.3.0_R9v2.zip /sdcard/Download/drivers/turnip_v24.3.0_R9v2.zip
adb -s <serial> push drivers/TurnipZ-0.3.0.zip /sdcard/Download/drivers/TurnipZ-0.3.0.zip
adb -s <serial> push drivers/Turnip-24.1.0.adpkg_R18.a6xx.zip /sdcard/Download/drivers/Turnip-24.1.0.adpkg_R18.a6xx.zip
```

### Operational Rules
1. **Shader Cache Invariant**: Always clear the target emulator's shader cache when switching drivers to avoid corrupted cached shaders.
2. **Active Cooling Invariant**: Ensure the RP5 fan profile is set to **Smart Fan** (Mode 4) or **Sport Fan** during heavy Turnip sessions.
