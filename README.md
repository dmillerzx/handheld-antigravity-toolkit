# Handheld Community Provisioning Toolkit (handheld-antigravity-toolkit)

**Status:** `v1.0-baseline (Active Testing & Community QA)`

A device-aware, dynamic ADB automation and provisioning toolkit designed for Android gaming handhelds. Provides instant zero-touch setup, Android 12/13 background process tuning, strict canonical storage management, 2D ultra-low-latency audio/video pipelines, standalone 3D emulator profile injection, universal widescreen patches, and containerized Steam Big Picture integration.

---

## 🚀 Dual-Tier Release Model

This repository is architected for both standalone community gamers and AI-assisted handheld developers:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TIER 1: 1-CLICK STANDALONE RUNNER                     │
│  - Zero AI / Antigravity CLI dependencies.                                  │
│  - Double-click Run_Setup.bat (or Run_RP5_Setup.bat).                       │
│  - Auto-downloads Google Platform-Tools (adb) if missing.                   │
│  - Auto-detects device model via ADB getprop.                               │
│  - Dynamic MicroSD UUID resolution & /sdcard/ fallback.                     │
│  - Interactive breakpoints for Google Play Store & Steam 2FA login.         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴──────────────────────────────────────┐
│                       TIER 2: ANTIGRAVITY AI ENGINE                         │
│  - Autonomous pair-programming with Google DeepMind Antigravity agent.      │
│  - Interactive ADB inspection, UI hierarchy dumps, and frame analysis.      │
│  - Automated profile generator for new SoCs, screen ratios & controllers.   │
│  - Self-healing regression tests & save synchronization across fleet.       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Standalone 1-Click Community Installer (Zero AI)
For everyday players and handheld owners who want a perfected retro gaming and Steam setup in minutes:
1. Connect your Android handheld to your PC via USB-C with **USB Debugging** enabled.
2. Double-click **`Run_Setup.bat`** (or **`Run_RP5_Setup.bat`** for Retroid Pocket 5).
3. The runner automatically:
   * Downloads official Google `platform-tools` (ADB) if not present locally.
   * Auto-detects your connected handheld model and matches the hardware profile.
   * Prompts you at the **Play Store breakpoint** if standalone emulators (Dolphin/DuckStation) need installation.
   * Bootstraps **Steam Big Picture** inside DroidDeck and pauses at the **Steam 2FA breakpoint** for 60-second mobile authentication.
   * Deploys all low-pass audio filters, shaders, and 4,700+ widescreen patches.

### Tier 2: Antigravity AI Engine
For developers, hardware modders, and maintainers using the Antigravity CLI / agentic coding environment:
* Run full automation with `/goal` overnight tasks.
* Automatically generate and validate new device profiles under `profiles/<device>.json`.
* Inspect real-time display refresh rates, frame pacing, and Android 13 FUSE storage locks over ADB.
* Execute regression tests and community QA suites headlessly.

---

## 🎮 Supported Devices & Hardware Profiles

The provisioning engine dynamically inspects `ro.product.model` and `ro.soc.model` over ADB and applies hardware-specific rendering scales, controller mappings, and GPU drivers from [`profiles/`](profiles/):

| Profile | Target Handheld | Display | SoC & GPU | Turnip Driver | Triggers | Widescreen Patches |
|---|---|---|---|---|---|---|
| [`rp5.json`](profiles/rp5.json) | **Retroid Pocket 5** | 5.5" 1080p 16:9 AMOLED | Snapdragon 865 (Adreno 650) | `Turnip a6xx` | Both (Analog + Click) | Force 16:9 Gecko & pnach |
| [`rp_mini.json`](profiles/rp_mini.json) | **Retroid Pocket Mini** | 3.7" 960p 4:3 OLED | Snapdragon 865 (Adreno 650) | `Turnip a6xx` | Both (Analog + Click) | **Disabled** (Native 4:3) |
| [`rp4_pro.json`](profiles/rp4_pro.json) | **Retroid Pocket 4 Pro** | 4.7" 720p 16:9 IPS | Dimensity 1100 (Mali-G77) | **Disabled (GPU Guard)** | Both (Analog + Click) | Force 16:9 Gecko & pnach |
| [`odin2.json`](profiles/odin2.json) | **AYN Odin 2** | 6.0" 1080p 16:9 IPS | Snapdragon 8 Gen 2 (Adreno 740) | `Turnip a7xx` | Both (Analog + Click) | Force 16:9 Gecko & pnach |
| [`generic.json`](profiles/generic.json) | **Generic Android** | 1080p 16:9 Standard | Generic ARM64 | **Disabled** | Digital Standard | Standard 4:3 Baseline |

---

## 📁 Canonical Storage Architecture

The toolkit enforces a strict, standardized storage map. It dynamically queries `adb shell ls /storage` with regex `^[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$` to identify external MicroSD cards and falls back cleanly to internal storage (`/sdcard/`) if no card is inserted.

```text
Internal Storage   /sdcard/
└── bios/                          # Internal BIOS mirror

MicroSD Storage    /storage/<SD_ID>/   (or /sdcard/ fallback)
├── bios/                          # Master BIOS files (shared across all emulators)
├── ROMs/                          # Canonical game ROM storage (one subfolder per system)
├── ES-DE/                         # ES-DE frontend data (themes, media, gamelists)
├── RetroArch/                     # RetroArch configs, cores, joypad profiles, shaders
├── Saves_Backup/                  # Automated backup mirrors of saves, states & memcards
└── Games/Steam/                   # External DroidDeck Steam library (Drive D:\)
```

> [!IMPORTANT]
> **Strict Storage Rules:** The script eliminates non-standard folder variants (`Games/BIOS`, `BIOS/`, `roms/`, `Emulation/`). ROMs live strictly in `/storage/<SD_ID>/ROMs/<system>/`.

---

## 🕹️ Ecosystem & Emulator Matrix

| System / Platform | Assigned Emulator | Audio Backend & Filters | Resolution Scale | Canonical ROM Path |
|---|---|---|---|---|
| **NES / Famicom** | RetroArch (`mesen`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/nes` |
| **SNES / SFC** | RetroArch (`snes9x`) | Gaussian Interpolation | Native | `/storage/<SD_ID>/ROMs/snes` |
| **Game Boy / GBC** | RetroArch (`gambatte`) | Sinc Resampler | Native | `/storage/<SD_ID>/ROMs/gb`, `/gbc` |
| **Game Boy Advance** | RetroArch (`mgba`) | IIR 5.5kHz LPF (`gba_lowpass.dsp`) + LCD Grid | Native | `/storage/<SD_ID>/ROMs/gba` |
| **Sega Genesis / MD** | RetroArch (`genesis_plus_gx`) | Discrete Model 1 LPF (Range 60) | Native | `/storage/<SD_ID>/ROMs/genesis` |
| **Sega 32X / Master System** | RetroArch (`picodrive`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/sega32x`, `/mastersystem` |
| **PC Engine / TG-16** | RetroArch (`mednafen_pce_fast`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/pcengine` |
| **Neo Geo Pocket / Color** | RetroArch (`mednafen_ngp`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/ngpc` |
| **WonderSwan / Color** | RetroArch (`mednafen_wswan`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/wswan` |
| **Arcade / Neo Geo** | RetroArch (`fbneo`) | 4-point Interpolation | Native | `/storage/<SD_ID>/ROMs/arcade`, `/neogeo` |
| **Atari 2600** | RetroArch (`stella`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/atarias` |
| **PlayStation (PS1)** | DuckStation (Standalone) | Cubeb (20ms) Gaussian | 5x (1080p PGXP) | `/storage/<SD_ID>/ROMs/psx` |
| **PlayStation 2 (PS2)** | NetherSX2 (Standalone) | SPU2 Hermite (Mode 4) | 2.25x (1080p Widescreen) | `/storage/<SD_ID>/ROMs/ps2` |
| **Nintendo GameCube** | Dolphin (Standalone) | OpenSLES DSP / Analog Triggers | 2.5x (1080p Gecko) | `/storage/<SD_ID>/ROMs/gc` |
| **Nintendo Wii** | Dolphin (Standalone) | OpenSLES DSP / Classic Pad | 2.5x (1080p Widescreen & Deflicker Off) | `/storage/<SD_ID>/ROMs/wii` |
| **Sony PSP** | PPSSPP (Standalone) | Low Latency (Latency=0) | 4x (1080p 16x Aniso) | `/storage/<SD_ID>/ROMs/psp` |
| **Sega Dreamcast** | Flycast (Standalone) | AICA DSP / AutoLatency | 2x (1080p Widescreen) | `/storage/<SD_ID>/ROMs/dreamcast` |
| **Nintendo 3DS** | Azahar (Standalone) | Audio Engine 0 / Mesa Turnip | 3x (1080p Async) | `/storage/<SD_ID>/ROMs/n3ds` |
| **Sony PS Vita** | Vita3K (Standalone) | Vulkan / Mesa Turnip Vulkan | 2x (1080p) | `/storage/<SD_ID>/ROMs/psvita` |
| **PC / Steam Gaming** | DroidDeck (Standalone) | PulseAudio / DXVK Async | 720p base -> FSR 1080p | `/storage/<SD_ID>/Games/Steam` |

---

## 🛠️ CLI Script Execution

To run the master orchestrator directly from PowerShell or terminal:

```powershell
# Run complete provisioning on connected device (auto-detects serial and profile)
.\scripts\provision_all.ps1

# Target a specific device serial and force a profile
.\scripts\provision_all.ps1 -Serial ff152647 -Profile rp5

# Dry-run execution to preview commands without modifying device
.\scripts\provision_all.ps1 -DryRun
```

Or via Python:

```powershell
python scripts/setup_rp5.py --serial ff152647 --profile rp5 --all
```

---

## 🧪 Quality Assurance & Testing

Refer to [`QA_CHECKLIST.md`](QA_CHECKLIST.md) for platform-by-platform verification tests covering:
* RetroArch frame pacing and 1-frame Run-Ahead responsiveness.
* GBA 5.5kHz IIR audio filtering and Genesis Model 1 LPF tone.
* DuckStation PGXP precision and NetherSX2 CRC widescreen hooks.
* Dolphin analog trigger stroke thresholds (`Threshold = 50.0`, `Trigger = 100.0`).
* Azahar / Vita3K Mesa Turnip driver stability.
* DroidDeck 720p FSR upscaling and MicroSD Steam library streaming throughput.

---

## 📂 Repository Layout

```text
.
├── CREDITS.md                       # Comprehensive upstream credits & attributions
├── Run_Setup.bat                    # Double-click root standalone launcher (all handhelds)
├── Run_RP5_Setup.bat                # Alias launcher for Retroid Pocket 5
├── QA_CHECKLIST.md                  # Quality assurance validation test suite
├── README.md                        # Master documentation and ecosystem specs
├── AGENTS.md                        # Strict agent guidance & storage layout rules
├── GEMINI.md                        # Model directives for Retroid Pocket automation
├── profiles/                        # Dynamic hardware profiles
│   ├── rp5.json                     # Retroid Pocket 5 (1080p 16:9, SD865, Turnip a6xx)
│   ├── rp_mini.json                 # Retroid Pocket Mini (960p 4:3, SD865, Native 4:3)
│   ├── rp4_pro.json                 # Retroid Pocket 4 Pro (720p 16:9, Dimensity 1100, Mali)
│   ├── odin2.json                   # AYN Odin 2 (1080p 16:9, SD8 Gen 2, Turnip a7xx)
│   └── generic.json                 # Generic safe baseline
├── scripts/
│   ├── device_profile.py            # Dynamic hardware profiling & MicroSD resolver
│   ├── provision_all.ps1            # Master PowerShell orchestrator & breakpoint engine
│   ├── setup_rp5.py                 # Core ADB provisioning engine (--all)
│   ├── configure_standalones.py     # Standalone 3D emulator profile injector
│   ├── stage_community_patches.py   # Universal PS2 & GameCube/Wii patch engine
│   ├── download_retroarch_cores.py  # Headless 2D/Arcade core & asset deployer
│   └── sync_all_saves.py            # Save, state & memory card backup sync
├── configs/
│   ├── rp5_master_obtainium.json    # Upstream emulator catalog for Obtainium
│   ├── es_systems.xml               # ES-DE custom systems standalone emulator overrides
│   ├── es_settings.xml              # Headless ES-DE storage & emulator routing
│   ├── droiddeck_config.json        # DroidDeck 720p/FSR 1080p Turnip profile
│   ├── libraryfolders.vdf           # Pre-seeded Steam MicroSD library definition
│   └── retroarch/                   # Ultra-low-latency 2D RetroArch configuration
│       ├── retroarch.cfg            # Main config (Vulkan, Ozone, 48ms, hotkeys)
│       ├── retroarch-core-options.cfg # Low-pass audio & interpolation options
│       ├── filters/audio/gba_lowpass.dsp # GBA 5.5kHz IIR low-pass DSP filter
│       └── config/mGBA/             # mGBA overrides & GBA LCD grid shader chain
├── patches/
│   ├── gcn/                         # GameCube Gecko widescreen/60fps patches
│   ├── wii/                         # Wii Gecko widescreen/deflicker/bloom overrides
│   └── ps2/                         # PS2 PCSX2 master pnach cheats
└── drivers/                         # Mesa Turnip Adreno 650 drivers (.gitkeep)
```

---

## 🤝 Acknowledgments & Credits

This toolkit builds directly upon the incredible work of emulator authors, driver developers, shader artists, and community patch creators. See [CREDITS.md](CREDITS.md) for full attributions and upstream projects.

