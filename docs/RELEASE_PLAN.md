# Community Release Plan: Retroid Pocket 5 Setup Toolkit

*Document Status: Draft for User Approval (No Code Written)*  
*Target Release: v0.1 (Retroid Pocket 5 Only, Windows / macOS / Linux)*

---

## 1. Automation & Verification Taxonomy

Every configuration routine in the provisioning pipeline is classified into one of three strict operational tiers:

| Subsystem / Task | Tier | Execution Mechanism | Verification Gate |
|---|---|---|---|
| **Phantom Process Killer** | `AUTOMATE` | ADB shell `device_config` & `settings` | Read back `max_phantom_processes` == `2147483647` |
| **Canonical Directory Scaffolding** | `AUTOMATE` | ADB shell `mkdir -p` on `/sdcard` & `/storage/<SD_ID>` | Check directory presence via `[ -d <path> ]` |
| **Retroid OS Hardware Tuning** | `AUTOMATE` | Set `persist.sys.trigger.mode 2`, `persist.sys.gamepad.type`, auto-rotate | Read back system properties & settings via ADB |
| **Scoped Storage Permissions** | `AUTOMATE` | `appops set <pkg> MANAGE_EXTERNAL_STORAGE allow` | Read back `appops get <pkg>` |
| **Obtainium Staging & Tracking** | `AUTOMATE` | Push JSONs to `/sdcard/Android/data/.../files/app_data/` | Verify 8 JSON manifests present on storage |
| **RetroArch Engine Configuration** | `AUTOMATE` | Push verified `retroarch.cfg`, core options, DSP filters | Key-value parse of Vulkan, OpenSLES 48ms, hotkeys |
| **RetroArch Core & Asset Fetching** | `AUTOMATE` | Download 11 cores + 3 asset zips from Libretro buildbot | Verify `.so` and unzipped info/assets on device |
| **Community Widescreen & 60fps Patches** | `AUTOMATE` | Push 1,891 Dolphin GameSettings & PCSX2/ARM SX2 CRC pnachs | Verify file counts & checksums |
| **Save & Memory Card Backups** | `AUTOMATE` | `sync_all_saves.py` mirroring to SD archive & host PC | Byte-size and file existence check |
| **Configuration Snapshots** | `AUTOMATE` | `snapshot_device.py` capturing 23 target directories | Manifest integrity check in `snapshots/<date>/` |
| **Dolphin Pre-Calibrated Controller Files** | `AUTOMATE` | Ship verified RP5 `GCPadNew.ini`, `WiimoteNew.ini`, profiles | Deploy untouched from repository |
| **Controller Verification Gate** | `PROMPT-THEN-VERIFY` | Prompt user to boot Mario Kart Wii and press `A` | If input fails, user maps 1 button in UI; script force-stops, captures Dolphin file, and preserves it |
| **Google Play Store Login** | `USER-ONLY` | Interactive prompt for user to sign into Google account | Script verifies Play Store package is accessible |
| **Paid Emulators (ES-DE, DraStic)** | `USER-ONLY` | Purchased and installed by user via Play Store / website | Script polls `pm list packages` until package detected |
| **Initial Storage Permission Prompts** | `PROMPT-THEN-VERIFY` | First-launch OS prompts for Dolphin/DuckStation/ARM SX2 | Script checks file readability in app data |
| **GPU Driver Selection** | `PROMPT-THEN-VERIFY` | User stages or picks Mesa Turnip revision in app UI | Script pulls updated config and validates driver link |
| **BIOS & Game ROM Ingestion** | `USER-ONLY` | User supplies their own dumped BIOS & game backups | Script audits canonical folder layout (`/storage/<SD_ID>/ROMs/<sys>`) |

> [!IMPORTANT]
> **The Prompt-Then-Verify Rule**: Every user interaction prompt MUST have an automated programmatic verification gate. Prompts that the user can skip without automated verification are forbidden, as unverified manual steps cause setup drift and false assumptions.

---

## 2. Upstream App Tracking: Catalog vs. RJNY Obtainium Emulation Pack

### Comparison Matrix

| Application | Our Catalog (`rp5_master_obtainium.json`) | RJNY Emulation Pack (`RJNY/Obtainium-Emulation-Pack`) | Strategy & Recommendation |
|---|---|---|---|
| **PPSSPP** | Removed (Direct Play Store / ppsspp.org install) | Uses `https://www.ppsspp.org` HTML scraper with direct APK links | Keep as Play Store / manual install to avoid HTML scraper drift. |
| **Vita3K** | Tracks `Vita3K/Vita3K` continuous with partial APK hash | Tracks `https://github.com/Vita3K/Vita3K-builds` with clean build tags (`4190`) and versioned APKs | **Adopt `Vita3K-builds`**: Native tags eliminate pseudo-versioning entirely. |
| **ARM SX2** | Pinned to Stable 2.8.3 (`includePrereleases: false`) | Flagged with issue #183 due to nightly package mismatch (`com.armsx2.nightly`) | Keep pinned to stable; contribute package split finding upstream. |
| **Azahar (3DS)** | Regex pinned to vanilla build (`azahar-android-vanilla.*\.apk$`) | Uses vanilla APK filter | Aligned. |
| **NetherSX2** | Builder patch release | Pre-configured builder tracking | Aligned. |
| **Flycast** | Stable releases | Stable releases | Aligned. |
| **RetroArch** | Libretro buildbot 2-level intermediate HTML scraper | Stable Libretro scraper | Aligned. |
| **Obtainium** | Clean regex `^app-arm64-v8a-release\.apk$` | Clean arm64 filter | Aligned. |

### Proposed Strategy
Maintain our focused 8-app catalog tailored to the Retroid Pocket 5, but continuously validate our schemas against RJNY's daily CI test suite. Adopt `Vita3K/Vita3K-builds` upstream directly from RJNY's discoveries.

---

## 3. Cross-Platform Host Architecture (Python Core)

To ensure identical behavior across Windows, macOS, and Linux:
1. **Move all prompts and orchestrations into Python (`scripts/provision.py`)**:
   - Play Store login breakpoint
   - Controller A-button verification prompt
   - Save restore confirmation prompt
2. **Ultra-thin OS Launchers**:
   - `Run_Setup.bat` (Windows): 5 lines finding `python.exe` and `platform-tools\adb.exe`, invoking `python scripts/provision.py`.
   - `Run_Setup.sh` (macOS / Linux): 5 lines verifying `python3` and `adb`, invoking `python3 scripts/provision.py`.
   - Eliminates duplicate PowerShell vs Shell logic.

---

## 4. Multi-Device Expansion Roadmap

### Version 0.1 (Immediate)
- Strictly Retroid Pocket 5. Single, tested, golden hardware baseline.

### Version 0.2 (Interactive Device Profiler & Capture Mode)
- For unprofiled devices (e.g. Doug's **Konkr Pocket Advance**):
  1. Detect new device identifier via `ro.product.model`.
  2. Walk user through mapping controls once in Dolphin, ARM SX2, and RetroArch.
  3. Force-stop emulators, pull generated configuration files, extract button tokens, and generate a new `profiles/<device>.json`.
  4. Test and validate on Konkr Pocket Advance.
- RP Mini, Retroid Flip 2, and AYN Odin 2 profiles will be labeled explicitly as **Community Profiles (Untested)** until verified on physical hardware.

---

## 5. Release Verification Gates

Before any public announcement:
1. **Gate A: Factory-Reset Verification Run**:
   - Back up all device saves and memory cards via `sync_all_saves.py`.
   - Factory reset the Retroid Pocket 5 to stock firmware.
   - Run the complete setup from scratch over USB using `Run_Setup.bat`.
   - Confirm zero manual terminal interventions required; verify Mario Kart Wii and GT4 boot and control properly.
2. **Gate B: Independent RP5 Owner Test**:
   - Have one external RP5 community member execute the setup following `README.md` alone.
   - Collect and resolve any friction points or missing prerequisites.

---

## 6. Pre-Publishing Hygiene & Licensing

- **Clean-Room Repository**:
  - The commit history of this development repository contains early video transcripts (deleted in `7af289f`).
  - The public release will be pushed as an initial clean commit (`v0.1.0`) to a fresh repository (`handheld-setup-toolkit`), leaving this repo private.
- **License**: MIT License.
- **Copyright & BIOS Policy**: Zero copyrighted assets, zero BIOS files, and zero game ROMs will ever be distributed, hosted, or linked.
- **Attribution & Transparency**: The README will clearly declare:
  - Development was AI-assisted.
  - Tested exclusively on a single Retroid Pocket 5.
  - Support and issue triage are best-effort community maintenance.

---

## 7. Upstream Contributions

Findings and technical documentation will be contributed back to upstream projects rather than kept proprietary:

1. **RJNY/Obtainium-Emulation-Pack**:
   - Provide findings on issues #183 and #187 regarding `com.armsx2.nightly` package separation.
2. **Dolphin Android Community / Forums**:
   - Document the `KEYCODE_NAMES` token requirement vs obsolete `Button 96` numeric scan-codes.
   - Share findings on `[Controls]` `WiimoteProfile1 = Classic_Controller` and `WiimoteSource0 = 1` vs `SIDevice0`.
3. **Community Handheld Post**:
   - Publish `docs/TECHNICAL_FINDINGS.md` as a technical reference guide on r/retroid and SBCGaming.
