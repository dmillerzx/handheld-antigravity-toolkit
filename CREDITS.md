# Acknowledgments & Upstream Attributions

The **Handheld Community Provisioning Toolkit** (`rp5-antigravity-toolkit`) is an orchestration and configuration framework. It does not reinvent the emulation, translation, driver, or frontend stacks—rather, it builds directly upon the tireless open-source contributions of emulator developers, driver engineers, shader artists, patch authors, and community creators.

We extend our deep gratitude to the upstream projects, maintainers, and communities that make high-performance retro gaming and PC translation possible on modern Android handhelds.

---

## 🎮 Standalone Emulators & Runtimes

| Project | Author / Maintainers | License / Repository | Key Role & Contribution |
|---|---|---|---|
| **[DuckStation](https://github.com/stenzek/duckstation)** | Stenzek | GPL-3.0 / [duckstation](https://github.com/stenzek/duckstation) | Sony PlayStation 1 emulation, PGXP subpixel precision geometry, 5x 1080p rendering, and Cubeb low-latency audio. |
| **[NetherSX2](https://github.com/Trixarian/NetherSX2-patch)** | Trixarian & PCSX2 Team | LGPL-3.0 / [NetherSX2-patch](https://github.com/Trixarian/NetherSX2-patch) | PlayStation 2 Android runtime, removing frontend telemetry, fixing touchscreen overlays, and loading master `.pnach` widescreen patches. |
| **[Dolphin](https://github.com/dolphin-emu/dolphin)** | Dolphin Emulator Project | GPL-2.0+ / [dolphin](https://github.com/dolphin-emu/dolphin) | Nintendo GameCube & Wii emulation, Gecko code parsing engine, OpenSLES DSP audio backend, and dual analog trigger threshold mapping. |
| **[PPSSPP](https://github.com/hrydgard/ppsspp)** | Henrik Rydgård & Contributors | GPL-2.0+ / [ppsspp](https://github.com/hrydgard/ppsspp) | Sony PSP Vulkan emulation, 4x 1080p upscaling, 16x anisotropic filtering, and zero-latency audio buffering. |
| **[Azahar / Lime3DS](https://github.com/azahar-emu/azahar)** | Azahar Team (fork of Lime3DS/Citra) | GPL-2.0+ / [azahar](https://github.com/azahar-emu/azahar) | Nintendo 3DS Android runtime, asynchronous shader compilation, and custom AdrenoTools/Turnip GPU driver support. |
| **[Vita3K](https://github.com/Vita3K/Vita3K-Android)** | Vita3K Team (Macdu, slipstream, et al.) | GPL-2.0 / [Vita3K-Android](https://github.com/Vita3K/Vita3K-Android) | Sony PlayStation Vita Android emulation, Vulkan backend, and Mesa Turnip Adreno compatibility. |
| **[Flycast](https://github.com/flyinghead/flycast)** | flyinghead & Contributors | GPL-2.0 / [flycast](https://github.com/flyinghead/flycast) | Sega Dreamcast, Naomi, and Atomiswave emulation with custom widescreen geometry and low-latency audio buffering. |

---

## 🕹️ RetroArch & Libretro Ecosystem

| Component | Authors / Contributors | Repository / Details | Description |
|---|---|---|---|
| **[RetroArch](https://github.com/libretro/RetroArch)** | Twinaphex & Libretro Team | GPL-3.0 / [RetroArch](https://github.com/libretro/RetroArch) | Unified cross-platform frontend, Ozone user interface, Vulkan pipeline, 1-frame Run-Ahead latency reduction, and OpenSLES audio synchronization. |
| **[Mesen Core](https://github.com/SourMesen/Mesen)** | Sour | GPL-3.0 / [libretro-mesen](https://github.com/libretro/mesen) | Cycle-accurate Nintendo Entertainment System (NES) and Famicom emulation. |
| **[Snes9x Core](https://github.com/snes9xgit/snes9x)** | BearOso, zones, and Snes9x Team | Snes9x License / [snes9x](https://github.com/libretro/snes9x) | Super Nintendo / Super Famicom emulation with hardware Gaussian audio interpolation. |
| **[Gambatte Core](https://github.com/sinamas/gambatte)** | sinamas | GPL-2.0 / [gambatte-libretro](https://github.com/libretro/gambatte-libretro) | Cycle-accurate Game Boy & Game Boy Color emulation with high-fidelity Sinc audio resampling. |
| **[mGBA Core](https://github.com/mgba-emu/mgba)** | endrift & Contributors | MPL-2.0 / [mgba](https://github.com/libretro/mgba) | High-speed, cycle-accurate Game Boy Advance emulation. |
| **[Genesis Plus GX](https://github.com/ekeeke/Genesis-Plus-GX)** | ekeeke | Non-commercial / [Genesis-Plus-GX](https://github.com/libretro/Genesis-Plus-GX) | Sega Genesis, Mega Drive, Master System, and Game Gear emulation with discrete Model 1 YM2612 low-pass filtering. |
| **[PicoDrive](https://github.com/notaz/picodrive)** | notaz & Contributors | MAME/Custom / [picodrive](https://github.com/libretro/picodrive) | Optimized Sega 32X and Mega-CD emulation. |
| **[Mednafen / Beetle Cores](https://github.com/libretro/beetle-pce-fast-libretro)** | Ryphecha & Libretro Team | GPL-2.0 / [beetle cores](https://github.com/libretro) | PC Engine / TurboGrafx-16 (`mednafen_pce_fast`), Neo Geo Pocket (`mednafen_ngp`), and WonderSwan (`mednafen_wswan`). |
| **[FinalBurn Neo](https://github.com/finalburnneo/FBNeo)** | FBNeo Team | Custom / Non-commercial / [FBNeo](https://github.com/finalburnneo/FBNeo) | Arcade and Neo Geo MVS emulation with 4-point sample interpolation. |
| **[Stella Core](https://github.com/stella-emu/stella)** | Stella Team | GPL-2.0 / [stella-libretro](https://github.com/libretro/stella-libretro) | Atari 2600 VCS emulation. |
| **Shaders & DSP Filters** | pokefan531, hunterk, Libretro contributors | [slang-shaders](https://github.com/libretro/slang-shaders) / [retroarch-dsp-filters](https://github.com/libretro/retroarch-dsp-filters) | `gba-color` color-correction, `lcd-grid-v2` dot-matrix simulation, and the discrete 5.5kHz IIR GBA low-pass filter (`gba_lowpass.dsp`). |

---

## 💻 PC Gaming & Container Translation

| Project | Organization / Maintainers | License / Repository | Key Role & Contribution |
|---|---|---|---|
| **[DroidDeck](https://github.com/Droid-Deck/DroidDeck)** | Droid-Deck Team | GPL-3.0 / [DroidDeck](https://github.com/Droid-Deck/DroidDeck) | Dedicated Android container launcher providing native Steam Big Picture runtime, FSR upscaling, and Turnip driver integration. |
| **[Valve / Steam](https://store.steampowered.com)** | Valve Corporation | Proprietary | Steam client, Steam Big Picture mode, and Proton runtime foundations. |
| **[FEX-Emu](https://github.com/FEX-Emu/FEX)** | FEX-Emu Team | MIT / [FEX](https://github.com/FEX-Emu/FEX) | Fast x86/x86-64 binary translation on ARM64 Linux and Android environments. |
| **[Box64](https://github.com/ptitSeb/box64)** | Sébastien Chevalier (ptitSeb) | MIT / [box64](https://github.com/ptitSeb/box64) | Linux x86_64 emulator with dynamic recompilation for ARM64 architectures. |
| **[WineHQ](https://www.winehq.org/)** | WineHQ Contributors | LGPL-2.1+ / [wine](https://gitlab.winehq.org/wine/wine) | Windows API compatibility layer on POSIX/Android systems. |
| **[DXVK](https://github.com/doitsujin/dxvk)** | Philip Rebohle (doitsujin) & Contributors | zlib / [dxvk](https://github.com/doitsujin/dxvk) | Vulkan-based translation layer for Direct3D 9, 10, and 11, including asynchronous pipeline caching. |

---

## ⚡ GPU Drivers (Mesa Turnip & Adreno Tools)

| Project | Authors / Maintainers | Repository / Details | Description |
|---|---|---|---|
| **[Mesa Turnip (freedreno)](https://gitlab.freedesktop.org/mesa/mesa)** | Rob Clark, Danylo Piliaiev, Connor Abbott, and Mesa Contributors | MIT / [mesa/mesa](https://gitlab.freedesktop.org/mesa/mesa) | Open-source Vulkan driver for Qualcomm Adreno GPUs, delivering desktop-class Vulkan compliance, descriptor indexing, and performance on the Snapdragon 865 Adreno 650. |
| **Turnip Community Distribution** | K11MCH1, Mr-Purple-PSA, and AdrenoTools maintainers | [AdrenoToolsDrivers](https://github.com/K11MCH1/AdrenoToolsDrivers) / [Turnip-Drivers](https://github.com/Mr-Purple-PSA/Turnip-Drivers) | Packaging, compiling, and distributing loadable Turnip zip packages for Android emulator driver hooks. |

---

## 🗄️ Community Databases & Patch Authors

| Project | Maintainers / Authors | Repository / Source | Description |
|---|---|---|---|
| **[PCSX2 Patches Collection](https://github.com/PCSX2/pcsx2_patches)** | PCSX2 Community & Contributors | Public Domain / CC0 / [pcsx2_patches](https://github.com/PCSX2/pcsx2_patches) | Over 4,700 `.pnach` master patch definitions providing 16:9 widescreen fixes, 60fps unlocked framerates, and deinterlacing hooks across worldwide PS2 titles. |
| **[Dolphin GameSettings](https://github.com/dolphin-emu/dolphin/tree/master/Data/Sys/GameSettings)** | Dolphin Community Gecko Patchers | GPL-2.0+ / [GameSettings](https://github.com/dolphin-emu/dolphin/tree/master/Data/Sys/GameSettings) | Upstream Gecko code authors creating anamorphic 16:9 widescreen and 60fps patches across the entire GameCube and Wii software libraries. |

---

## 📱 Frontends & Android App Management

| Application | Authors / Maintainers | License / Repository | Description |
|---|---|---|---|
| **[ES-DE (EmulationStation-DE)](https://gitlab.com/es-de/emulationstation-de)** | Leon Styhre & Contributors | Custom / [es-de](https://gitlab.com/es-de/emulationstation-de) | Canonical multi-platform emulation frontend providing theme support, media scraping, and unified ROM directory management. |
| **[Daijishō](https://github.com/TapiocaFox/Daijishou)** | TapiocaFox / magneticchen | GPL-3.0 / [Daijishou](https://github.com/TapiocaFox/Daijishou) | Elegant, Pegasus-style Android retro gaming frontend. |
| **[Obtainium](https://github.com/ImranR98/Obtainium)** | ImranR98 | GPL-3.0 / [Obtainium](https://github.com/ImranR98/Obtainium) | Headless and automated release aggregator tracking and updating open-source Android APKs directly from GitHub and GitLab releases. |

---

## 📖 Community Guides & Ergonomic Standards

- **[Retro Game Corps (Russ)](https://retrogamecorps.com/)**: Standardizing handheld retro gaming best practices, including the canonical `SELECT`-based hotkey conventions, Run-Ahead latency benchmarks, 5.5kHz GBA low-pass filter recommendations, and Android handheld setup methodology.
- **[Retroid Pocket Community & Subreddit](https://www.reddit.com/r/retroid/)**: Hardware reverse engineering, AMOLED panel mode discoveries, trigger mode tuning (`persist.sys.trigger.mode 2`), and community testing on the Retroid Pocket 5 and Retroid Pocket Mini.
