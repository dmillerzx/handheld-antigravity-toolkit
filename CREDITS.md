# Upstream Credits & Attributions

The **Retroid Pocket 5 (RP5) Automated Provisioning Workspace** is made possible by an exceptional ecosystem of open-source emulators, translation layers, graphics drivers, frontends, and community research. We express our deepest gratitude to all upstream developers, maintainers, and community contributors whose work powers this toolkit.

---

## 1. Standalone Emulators & Runtimes

* **[Dolphin Emulator](https://dolphin-emu.org/)** — Developed by the Dolphin Emulator Project & Dolphin Team. High-efficiency GameCube and Wii emulation, dual-core JIT translation, and extensive Gecko patch engines.
* **[NetherSX2 / PCSX2](https://github.com/Trixarian/NetherSX2-patch)** — Developed by Trixarian and the PCSX2 team (based on AetherSX2 by Tahlreth). High-performance PlayStation 2 emulation on Android with custom widescreen and 60fps `.pnach` patch engines.
* **[DuckStation](https://github.com/stenzek/duckstation)** — Developed by Stenzek. Precision PlayStation (PS1) emulation featuring PGXP geometric precision, Vulkan rendering, and low-latency Cubeb audio pipelines.
* **[PPSSPP](https://www.ppsspp.org/)** — Developed by Henrik Rydgård and open-source contributors. Industry-standard PlayStation Portable (PSP) emulator with high-efficiency Vulkan backends.
* **[Azahar / Lime3DS](https://github.com/lime3ds/lime3ds)** — Developed by the Azahar & Lime3DS teams (building upon Citra by the Citra Team). Nintendo 3DS Android runtime featuring custom GPU driver loading and async shader compilation.
* **[Vita3K](https://vita3k.org/)** — Developed by the Vita3K Team. Experimental PlayStation Vita emulator with Vulkan rendering and custom driver staging.
* **[Flycast](https://github.com/flyinghead/flycast)** — Developed by flyinghead. Multi-platform Sega Dreamcast, Naomi, and Atomiswave emulator with AICA DSP audio emulation and Vulkan widescreen rendering.

---

## 2. RetroArch & Libretro Ecosystem

* **[Libretro / RetroArch](https://www.libretro.com/)** — Developed by the Libretro Team and Twinaphex. Unified ultra-low-latency 2D emulation frontend, Ozone UI, OpenSLES low-latency audio, Vulkan video drivers, and run-ahead frame latency reduction.
* **Libretro Emulation Cores**:
  * **Mesen** — Developed by Sour. Cycle-accurate Nintendo Entertainment System (NES) emulation.
  * **Snes9x** — Developed by BearOso, zones, and the Snes9x team. High-compatibility Super Nintendo Entertainment System (SNES) core with Gaussian audio interpolation.
  * **Gambatte** — Developed by sinamas. Accurate Game Boy and Game Boy Color emulation with Sinc audio resampling.
  * **mGBA** — Developed by endrift. Cycle-accurate Game Boy Advance (GBA) emulation.
  * **Genesis Plus GX** — Developed by ekeeke. Cycle-accurate Sega Genesis / Mega Drive, Master System, and Game Gear emulation with Model 1 YM2612 low-pass audio filtering.
  * **PicoDrive** — Developed by notaz. Fast Sega 32X and Mega-CD emulation.
  * **Beetle / Mednafen Cores** — Developed by Ryphecha and the Mednafen/Libretro teams (Beetle PCE, Beetle Saturn). High-accuracy PC Engine and Sega Saturn emulation.
  * **FinalBurn Neo (FBNeo)** — Developed by the FBNeo team. Universal arcade hardware emulation.
  * **Stella** — Developed by the Stella Team. High-compatibility Atari 2600 VCS emulation.
* **Shaders & DSP Audio Filters**:
  * **`gba-color` & `lcd-grid-v2`** — Authored by pokefan531, hunterk, and the Libretro shader community. Color reproduction and subpixel grid simulation for handheld displays.
  * **Audio DSP Filters** — Contributors to Libretro audio DSP plugins (`gba_lowpass.dsp`, IIR low-pass filter implementations).

---

## 3. PC Gaming & Translation Runtimes

* **[DroidDeck](https://github.com/Droid-Deck/DroidDeck)** — Developed by the Droid-Deck Team. Open-source Android PC gaming container launcher tailored for handheld gaming devices.
* **[Valve / Steam](https://store.steampowered.com/)** — Steam client runtime and Big Picture mode.
* **[Box64](https://github.com/ptitSeb/box64)** — Developed by Sébastien Chevalier (ptitSeb). Linux Userspace x86_64 emulator with dynamic recompilation for ARM64 platforms.
* **[FEX-Emu](https://fex-emu.com/)** — Fast x86/x86-64 emulation targeting ARM64 Linux systems.
* **[WineHQ](https://www.winehq.org/)** — Windows API compatibility layer.
* **[DXVK](https://github.com/doitsujin/dxvk)** — Developed by Philip Rebohle (doitsujin) and contributors. Vulkan-based translation layer for Direct3D 9/10/11.

---

## 4. GPU Drivers & Graphics Enhancements

* **[Mesa Turnip / freedreno](https://docs.mesa3d.org/drivers/freedreno.html)** — Developed by Rob Clark and the Mesa/freedreno team. Open-source Vulkan driver for Qualcomm Adreno GPUs providing compliance and performance beyond stock OEM drivers.
* **Community Driver Packagers**:
  * **K11MCH1** & **Mr-Purple-PSA** — Compiling, packaging, and testing installable Mesa Turnip driver bundles for Qualcomm Adreno 600/700 series GPUs.

---

## 5. Community Patch Databases & GameSettings

* **[PCSX2 Master Patches](https://github.com/PCSX2/pcsx2_patches)** — Curated by the PCSX2 community and patch authors. Over 4,700 `.pnach` files providing widescreen, 60fps, and progressive scan enhancements for PlayStation 2 titles.
* **[Dolphin GameSettings Repository](https://github.com/dolphin-emu/dolphin/tree/master/Data/Sys/GameSettings)** — Curated by the Dolphin community. Pre-configured game compatibility profiles, widescreen Gecko codes, and performance fixes.

---

## 6. Frontends & Handheld Community Resources

* **[ES-DE (EmulationStation Desktop Edition)](https://es-de.org/)** — Developed by Leon Styhre. Clean, extensible, and theme-rich frontend for retro handhelds and desktop platforms.
* **[Daijishō](https://github.com/Magneticchen/Daijishou)** — Developed by TapiocaFox. Modern retro launcher frontend for Android.
* **[Obtainium](https://github.com/ImranR98/Obtainium)** — Developed by ImranR98. Seamless open-source package manager fetching APK releases directly from upstream repositories.
* **[Retro Game Corps](https://retrogamecorps.com/)** — Authored by Russ. Benchmark analyses, handheld setup methodologies, and community hotkey mapping standards.
