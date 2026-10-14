# rp5-antigravity-toolkit

ADB automation for provisioning a **Retroid Pocket 5** handheld: Android 13 tweaks, a strict on-device storage layout, Obtainium bootstrap, and storage AppOps.

## Hardware

| Item | Spec |
|---|---|
| Device | Retroid Pocket 5 (RP5) |
| SoC | Qualcomm Snapdragon 865 (SM8250) |
| GPU | Adreno 650 (custom Turnip/Mesa Vulkan drivers supported in some emulators) |
| OS | Android 13 (SDK 33), AOSP-based Retroid OS |
| Display | 5.5" 1080p AMOLED (1920x1080), 60 Hz |
| Storage | Internal (`/sdcard`) + MicroSD (`/storage/<SD_ID>/`, exFAT/FAT32) |
| Connectivity | USB-C, ADB debugging |

## Canonical storage map

This is the only supported on-device layout. It is hardcoded in [`scripts/setup_rp5.py`](scripts/setup_rp5.py) (`INTERNAL_DIRS`, `SD_DIRS`).

```text
Internal storage   /sdcard/
└── bios/                  # BIOS copy

MicroSD            /storage/<SD_ID>/
├── bios/                  # BIOS files (shared by all emulators)
├── ROMs/                  # ROMs, one subfolder per system
└── ES-DE/                 # ES-DE frontend data
```

Not supported (never created): `Games/`, `Games/BIOS`, `BIOS/`, `roms/`, `Emulation/`, or any ROM directory on internal storage. See [`AGENTS.md`](AGENTS.md) for the full rules.

## Provisioning pipeline

You can provision the entire Retroid Pocket 5 retro gaming ecosystem end-to-end with a single zero-touch command:

```powershell
.\scripts\provision_all.ps1 -Serial <RP5_SERIAL>
```

or via Python directly:

```powershell
python scripts/setup_rp5.py --serial <RP5_SERIAL> --all
```

The pipeline executes the following stages end-to-end headlessly over ADB:

1. **Connectivity & Specs Verification** - Confirms ADB authorization, retrieves hardware properties (Snapdragon 865, Adreno 650, Android 13).
2. **Phantom Process Killer Unlock** - Bypasses Android 13's background process limit (`max_phantom_processes = 2147483647`) to prevent silent emulator terminations.
3. **Canonical Storage Scaffolding** - Creates `/sdcard/bios` and `/storage/<SD_ID>/{bios,ROMs,ES-DE}`.
4. **Retroid Hardware & Input Profiles** -
   - Enforces **Both** trigger mode (analog axis + digital button click: `persist.sys.trigger.mode = 2`).
   - Sets gamepad style to Xbox mode (`persist.sys.gamepad.type = 0`).
   - Disables lock screen (`locksettings set-disabled true`) and disables floating game assistant overlay (`settings put system is_show_floatingIcon 0`).
5. **Obtainium Catalog & DroidDeck Deployment** -
   - Pushes `configs/rp5_master_obtainium.json` to `/sdcard/Download/` for 1-click package management.
   - Deploys DroidDeck (`com.droiddeck.launcher`) pre-configured with 720p base rendering, FSR 1080p, `DXVK_ASYNC=1`, Turnip driver, internal ext4 prefix `/sdcard/DroidDeck/prefixes/default/`, and MicroSD Steam library `/storage/<SD_ID>/Games/Steam/`.
   - Stages Sony PS Vita OS Firmware (`PSP2UPDAT.PUP`) in `/sdcard/Download/vita3k/` and Mesa Turnip Adreno 650 drivers in `/sdcard/Download/drivers/`.
6. **Ultra-Low-Latency 2D RetroArch Engine & Low-Pass Audio Filters** -
   - Vulkan backend, Ozone menu UI, 4 frame delay, 48ms OpenSLES latency, 1-frame run-ahead.
   - MicroSD paths mapped to `/storage/<SD_ID>/ROMs/` and `/storage/<SD_ID>/RetroArch/`.
   - Russ Standard Hotkeys enabled (SELECT = 109 hold hotkey, Start = Quit, X = Menu, Y = Savestate search, L1 = Load state, R1 = Save state, L2 = Rewind, R2 = Fast Forward).
   - **Low-pass audio filters & authentic acoustics**:
     * Sega Genesis / Mega Drive (Genesis Plus GX): Model 1 audio low-pass filter (range 60, YM2612 MAME).
     * Super Nintendo (Snes9x): Gaussian interpolation.
     * Game Boy / Game Boy Color (Gambatte): Sinc audio resampler.
     * Game Boy Advance (mGBA): IIR Low-Pass Filter DSP (`gba_lowpass.dsp`, cutoff 5500.0 Hz) + `mGBA.slangp` shader chain (`gba-color.slang` + `lcd-grid-v2.slang`, target gamma 2.2, grid strength 0.18).
     * Arcade / Neo Geo (FBNeo): 4-point audio interpolation.
7. **Automated 2D/Arcade Core & Asset Downloader** - Fetches 11 designated 2D/Arcade Libretro cores (`mesen`, `snes9x`, `gambatte`, `mgba`, `genesis_plus_gx`, `picodrive`, `mednafen_pce_fast`, `mednafen_ngp`, `mednafen_wswan`, `fbneo`, `stella`) and frontend assets (`info.zip`, `autoconfig.zip`, `shaders_slang.zip`) from Libretro Buildbot and deploys to MicroSD and internal storage.
8. **Standalone 3D Emulators Tuning** -
   - **DuckStation (PS1)**: Vulkan backend, 5x native resolution (1080p), PGXP perspective correction enabled, Cubeb audio backend (20ms latency), Gaussian interpolation, BIOS mapped to `/storage/<SD_ID>/bios`.
   - **NetherSX2 (PS2)**: Vulkan backend, 2.25x native (1080p), SPU2 Hermite interpolation (mode 4), Latency mode 1, 16:9 widescreen patches enabled, BIOS mapped to `scph70012.bin`.
   - **Dolphin (GameCube/Wii)**: Vulkan backend, 2.5x resolution (1080p), OpenSLES DSP audio, full RP5 physical gamepad mapping with analog trigger axes (`Threshold = 50.0`, `Trigger = 100.0`) in `GCPadNew.ini` and Classic Controller in `WiimoteNew.ini`.
   - **PPSSPP (PSP)**: Vulkan backend, 4x native (1080p), AudioLatency=0, Resampler=True, 16x Anisotropic filtering.
   - **Flycast (Dreamcast)**: Vulkan backend, 2x internal resolution (960p/1080p), Widescreen hack enabled, AICA AutoLatency, DSP enabled.
   - **Azahar (3DS)**: Vulkan backend, 3x native (1080p), async shader compilation enabled, custom Mesa Turnip Adreno 650 driver configured.
   - **Vita3K (PS Vita)**: Vulkan backend, 2x resolution (1080p), custom Mesa Turnip driver configured.
9. **Widescreen Patches & ES-DE Routing** -
   - GameCube Gecko widescreen patches (`GMSE01`, `GZLE01`, `GALE01`, `GFZE01`, `GM8E01`) staged in Dolphin's `GameSettings`.
   - NetherSX2 master PCSX2 `.pnach` cheats staged in `xyz.aethersx2.android/files/cheats/`.
   - Pre-configured `es_settings.xml` routes all 3D systems (`gc`, `wii`, `ps2`, `psx`, `psp`, `dreamcast`, `n3ds`, `psvita`) to standalone emulators while routing 2D/Arcade systems to RetroArch cores.
10. **Automated Save & Savestate Backup Pipeline** - Systematically syncs active saves, savestates, and virtual memory cards across all emulators to `/storage/<SD_ID>/Saves_Backup/latest/`.
11. **AppOps MANAGE_EXTERNAL_STORAGE Grants** - Automatically applies full storage permissions to all target emulators and frontends.

### Master Runner CLI Options

| Flag | Effect |
|---|---|
| `--all` | Execute complete zero-touch community provisioning pipeline |
| `--serial`, `-s <id>` | Target a specific device serial (default: `ff152647`) |
| `--dry-run` | Print ADB commands without modifying device |
| `--status` | Print connection and hardware specs, then exit |
| `--install-apks` | Install any staged APKs in `apks/` |
| `--skip-phantom` | Skip Android 13 phantom process limit bypass |
| `--skip-scaffold` | Skip canonical storage directory scaffolding |
| `--skip-obtainium` | Skip staging `rp5_master_obtainium.json` |
| `--skip-esde` | Skip staging headless ES-DE `es_settings.xml` |
| `--skip-drivers` | Skip staging Mesa Turnip GPU drivers |
| `--skip-tuning` | Skip Retroid OS hardware and trigger mode tuning |
| `--skip-permissions` | Skip granting `MANAGE_EXTERNAL_STORAGE` AppOps |

---

## Ecosystem Matrix

| Platform | Assigned Emulator / Core | Audio Backend & Filters | Resolution Multiplier | Storage Path |
|---|---|---|---|---|
| **NES / Famicom** | RetroArch (`mesen`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/nes` |
| **SNES / SFC** | RetroArch (`snes9x`) | OpenSLES / Gaussian Interpolation | Native | `/storage/<SD_ID>/ROMs/snes` |
| **Game Boy / GBC** | RetroArch (`gambatte`) | OpenSLES / Sinc Resampler | Native | `/storage/<SD_ID>/ROMs/gb`, `/gbc` |
| **Game Boy Advance** | RetroArch (`mgba`) | IIR 5.5kHz LPF (`gba_lowpass.dsp`) + LCD Grid | Native | `/storage/<SD_ID>/ROMs/gba` |
| **Sega Genesis / MD** | RetroArch (`genesis_plus_gx`) | Genesis Model 1 LPF (Range 60) | Native | `/storage/<SD_ID>/ROMs/genesis` |
| **Sega 32X / Master System** | RetroArch (`picodrive`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/sega32x`, `/mastersystem` |
| **PC Engine / TG-16** | RetroArch (`mednafen_pce_fast`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/pcengine` |
| **Neo Geo Pocket / Color** | RetroArch (`mednafen_ngp`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/ngpc` |
| **WonderSwan / Color** | RetroArch (`mednafen_wswan`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/wonderswancolor` |
| **Arcade / Neo Geo** | RetroArch (`fbneo`) | 4-point Interpolation | Native | `/storage/<SD_ID>/ROMs/arcade`, `/neogeo` |
| **Atari 2600** | RetroArch (`stella`) | OpenSLES (48ms) | Native | `/storage/<SD_ID>/ROMs/atarias` |
| **Sony PlayStation (PS1)** | DuckStation (Standalone) | Cubeb (20ms) / Gaussian | 5x (1080p PGXP) | `/storage/<SD_ID>/ROMs/psx` |
| **Sony PlayStation 2** | NetherSX2 (Standalone) | SPU2 Hermite (Mode 4) / Latency 1 | 2.25x (1080p Widescreen) | `/storage/<SD_ID>/ROMs/ps2` |
| **Nintendo GameCube** | Dolphin (Standalone) | OpenSLES DSP / Gecko Widescreen | 2.5x (1080p) | `/storage/<SD_ID>/ROMs/gc` |
| **Nintendo Wii** | Dolphin (Standalone) | OpenSLES DSP / Classic Controller | 2.5x (1080p) | `/storage/<SD_ID>/ROMs/wii` |
| **Sony PSP** | PPSSPP (Standalone) | Low Latency (Latency=0, Resampler) | 4x (1080p 16x Aniso) | `/storage/<SD_ID>/ROMs/psp` |
| **Sega Dreamcast** | Flycast (Standalone) | AICA AutoLatency / DSP Enabled | 2x (1080p Widescreen) | `/storage/<SD_ID>/ROMs/dreamcast` |
| **Nintendo 3DS** | Azahar (Standalone) | Audio Engine 0 / Mesa Turnip Vulkan | 3x (1080p Async) | `/storage/<SD_ID>/ROMs/n3ds` |
| **Sony PS Vita** | Vita3K (Standalone) | Vulkan / Mesa Turnip Vulkan | 2x (1080p) | `/storage/<SD_ID>/ROMs/psvita` |
| **PC / Steam Gaming** | DroidDeck (Standalone) | PulseAudio / DXVK Async | 720p base -> FSR 1080p | `/storage/<SD_ID>/Games/Steam` |

---

## Repository Layout

```text
.
├── scripts/
│   ├── provision_all.ps1            # Master PowerShell orchestrator
│   ├── setup_rp5.py                 # Core ADB provisioning & pipeline (--all)
│   ├── configure_standalones.py     # Standalone 3D emulator profile injector
│   ├── download_retroarch_cores.py  # Headless 2D/Arcade core & asset deployer
│   ├── sync_all_saves.py            # Save, state & memory card backup sync
│   └── run_setup.ps1                # PowerShell wrapper for setup_rp5.py
├── configs/
│   ├── rp5_master_obtainium.json    # Upstream emulator catalog for Obtainium
│   ├── es_settings.xml              # Headless ES-DE storage & emulator routing
│   ├── droiddeck_config.json        # DroidDeck 720p/FSR 1080p Turnip profile
│   └── retroarch/                   # Ultra-low-latency 2D RetroArch configuration
│       ├── retroarch.cfg            # Main config (Vulkan, Ozone, 48ms, hotkeys)
│       ├── retroarch-core-options.cfg # Low-pass audio & interpolation options
│       ├── filters/audio/gba_lowpass.dsp # GBA 5.5kHz IIR low-pass DSP filter
│       └── config/mGBA/             # mGBA overrides & GBA LCD grid shader chain
├── patches/
│   ├── gcn/                         # GameCube Gecko widescreen/60fps patches
│   └── ps2/                         # PS2 PCSX2 master pnach cheats (.gitkeep)
├── drivers/                         # Mesa Turnip Adreno 650 drivers (.gitkeep)
├── apks/                            # Local APK staging directory (.gitkeep)
├── bios/                            # Local BIOS staging directory (.gitkeep)
├── roms/                            # Local ROM staging directory (.gitkeep)
├── AGENTS.md                        # Strict agent guidance & storage layout rules
├── GEMINI.md                        # Gemini model automation directives
└── README.md                        # Hardware specs, pipeline docs, ecosystem matrix
```
