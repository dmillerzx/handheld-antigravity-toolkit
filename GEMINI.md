# GEMINI.md — Gemini Directives for Retroid Pocket 5 Automation

This file provides system context and operational instructions for Google Gemini models interacting with this Retroid Pocket 5 (RP5) workspace.

---

## 1. Persona & Context

You are assisting with the automated provisioning and maintenance of a **Retroid Pocket 5** retro gaming handheld running **Android 13** on the **Snapdragon 865** chipset.

Your primary interface to the device is **ADB (Android Debug Bridge)** over USB or local Wi-Fi pairing.

---

## 2. Environment Invariants

- **Workspace Root**: Workspace root directory (`<WORKSPACE_ROOT>`)
- **Local Platform Tools**: `platform-tools/adb.exe`
- **Installed Python**: `python` (Python 3.12)
- **Git Binary**: `git.exe`
- **RP5 serial**: Read dynamically via `adb devices` (multiple devices may be attached - always use `adb -s <serial>`)
- When running commands in Windows PowerShell where PATH might not be reloaded in inherited subprocesses, ensure ADB and Python are referenced cleanly using environment refreshes or absolute fallbacks.

---

## 3. CANONICAL STORAGE LAYOUT (STRICT - DO NOT DEVIATE)

```text
Internal storage   /sdcard/bios
MicroSD            /storage/<SD_ID>/bios
                   /storage/<SD_ID>/ROMs
                   /storage/<SD_ID>/ES-DE
                   /storage/<SD_ID>/RetroArch
                   /storage/<SD_ID>/Saves_Backup
                   /storage/<SD_ID>/Games/Steam
```

**Forbidden - never create, push to, or document these on the device:**

- `Games/BIOS`, `BIOS/` (upper-case), `Bios/`
- `roms/` (lower-case), `Emulation/`, `Emulation/roms`, `Emulation/bios`
- `/sdcard/ROMs`, `/sdcard/roms`, `/sdcard/Emulation` (no ROM directories on internal storage)
- Any other new top-level directory on `/storage/<SD_ID>/` besides `bios`, `ROMs`, `ES-DE`, `RetroArch`, `Saves_Backup`, `Games/Steam`

If a task seems to require a different path, stop and ask the user instead of creating a new folder variant. `AGENTS.md` Section 2 is the source of truth.

---

## 4. Provisioning Checklist

When executing or modifying `scripts/setup_rp5.py` and `scripts/provision_all.ps1`, verify the following stages:

| Stage | Action | Verification Command |
|---|---|---|
| **Connectivity** | Confirm device is online and authorized | `adb devices` |
| **Phantom Process** | Disable Android 13 phantom process restrictions | `adb shell "/system/bin/device_config get activity_manager max_phantom_processes"` |
| **Storage Scaffolding** | Create canonical directories | `adb shell "ls -la /sdcard/bios /storage/<SD_ID>"` |
| **Obtainium Staging** | Push `rp5_master_obtainium.json` to `/sdcard/Download/` (Libretro buildbot intermediateLink array for RetroArch) | `adb shell "ls -l /sdcard/Download/rp5_master_obtainium.json"` |
| **ES-DE Pre-Config** | Push `es_settings.xml` configured with MicroSD ROM path & direct ARMSX2 ROMSAF launch | `adb shell "cat /sdcard/ES-DE/settings/es_settings.xml"` |
| **Turnip Drivers** | Stage Mesa Turnip GPU drivers in `/sdcard/Download/drivers/` | `adb shell "ls -la /sdcard/Download/drivers"` |
| **Hardware Tuning** | Lockscreen disabled, overlay hidden, auto-rotate disabled (`accelerometer_rotation 0`), Smart fan mode (`fan_mode 4`), Xbox layout, Both triggers (`persist.sys.trigger.mode 2`) | `adb shell "getprop persist.sys.trigger.mode; settings get system fan_mode"` |
| **DroidDeck & Steam** | Stage DroidDeck 720p/FSR profile, env overrides, libraryfolders.vdf, and Sony Vita firmware | `adb shell "cat /sdcard/DroidDeck/config.json"` |
| **RetroArch 2D Engine** | Deploy Vulkan, Ozone, 48ms OpenSLES, Genesis Model 1 LPF, GBA 5.5kHz DSP, mGBA LCD grid | `adb shell "ls -la /storage/<SD_ID>/RetroArch/filters/audio"` |
| **2D/Arcade Cores** | Fetch & stage 11 designated cores and frontend assets | `adb shell "ls -la /storage/<SD_ID>/RetroArch/cores"` |
| **Standalone 3D Profiles** | Inject tuned Vulkan/audio profiles into DuckStation, NetherSX2 (16:9 Overscan), ARM SX2 (16:9 Overscan, Disable Readbacks, %DATA%=%ROMSAF%), Dolphin (global GFX.ini AspectRatio=0 Auto, SIDevice0=6 standard GC controller, WiimoteSource0=1, WiimoteProfile1=Classic_Controller, analog triggers L=Axis 22+ R=Axis 23+, no broken PadType0 overrides), PPSSPP, Flycast, Azahar, Vita3K (initial-setup: false, Vulkan backend, pref-path) | `adb shell "cat /sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Dolphin.ini"` |
| **Universal Patches** | Stage 4,700+ PS2 pnach cheats & 550 GameCube per-game profiles in patches/gcn/ smartly merged with upstream Dolphin GameSettings (Video_Settings AspectRatio=1, Gecko_Enabled) | `adb shell "ls /sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings"` |
| **Save Backup Sync** | Mirror saves, savestates, and memory cards to `/storage/<SD_ID>/Saves_Backup/latest/` | `adb shell "ls -la /storage/<SD_ID>/Saves_Backup/latest"` |
| **Permissions** | Grant `MANAGE_EXTERNAL_STORAGE` across all emulators and frontends | `adb shell "appops get <package> MANAGE_EXTERNAL_STORAGE"` |
| **Native Port Profiles** | Stage Perfect Dark (`com.perfectdark.port`) XBLA Duty Calls profile (`StickCButtons=0`, Style 8 "Ext", `MouseAimMode=1`, `CrosshairSway=0`, Lookspring OFF, `CK_8000` crouch) | `adb shell "cat /sdcard/Android/data/com.perfectdark.port/files/pd.ini"` |
| **ROM Compression** | Verify cartridge ROMs are Deflate `.n64.zip` (clean root `.z64`, no `.7z`), disc ROMs are `.chd`, GC/Wii are `.rvz` | `adb shell "ls -la /storage/<SD_ID>/ROMs/n64"` |

---

## 5. Emulator Package Reference & Distribution Channels

### A. Google Play Store (Manual install / no standalone GitHub APKs)
- **Dolphin (GameCube / Wii)**: `org.dolphinemu.dolphinemu`
- **DuckStation (PS1)**: `com.github.stenzek.duckstation`
*(Once downloaded from Play Store, re-run setup_rp5.py to apply MANAGE_EXTERNAL_STORAGE AppOps automatically.)*

### B. Tracked via Obtainium (`rp5_master_obtainium.json`) & Staged APKs
- **Obtainium App Updater**: `dev.imranr.obtainium`
- **ES-DE Frontend**: `org.es_de.frontend`
- **RetroArch (64-bit)**: `com.retroarch.aarch64`
- **ARM SX2 (PS2 Primary)**: `com.armsx2`
- **NetherSX2 (PS2 Fallback)**: `xyz.aethersx2.android`
- **PPSSPP (PSP)**: `org.ppsspp.ppsspp`
- **Azahar (3DS)**: `org.azahar_emu.azahar`
- **Vita3K (PS Vita)**: `org.vita3k.emulator`
- **Flycast (Dreamcast)**: `com.flycast.emulator`
- **Daijisho (Frontend)**: `com.magneticchen.daijishou`
- **DroidDeck (Steam Launcher)**: `com.droiddeck.launcher`
- **Additional Frontends / Tools**: `com.magneticstarlight.beacon` (Beacon), `org.mupen64plusae.v3.fzurita` (Mupen64Plus FZ)

---

## 6. Script Invocation

To run the complete zero-touch provisioning pipeline:
```powershell
.\scripts\provision_all.ps1 -Serial <SERIAL>
```
Or directly via Python:
```powershell
python scripts/setup_rp5.py --serial <SERIAL> --all
```
Options available:
- `--all`: Execute complete community provisioning pipeline (hardware tuning, storage, Obtainium, DroidDeck, Vita firmware, RetroArch low-pass engine, standalone 3D profiles, widescreen patches, and save backup sync).
- `--dry-run`: Preview ADB commands without applying them.
- `--status`: Check device connection and print hardware specs, then exit.
- `--serial <id>` / `-s <id>`: Target a specific device if multiple ADB instances exist.
- `--install-apks`: Install every `.apk` staged in `apks/`.
- `--skip-phantom`: Skip the Phantom Process Killer unlock.
- `--skip-scaffold`: Skip canonical directory scaffolding.
- `--skip-obtainium`: Skip pushing `rp5_master_obtainium.json`.
- `--skip-esde`: Skip staging headless ES-DE `es_settings.xml`.
- `--skip-drivers`: Skip staging Mesa Turnip GPU drivers.
- `--skip-tuning`: Skip Retroid OS hardware & system tuning.
- `--skip-permissions`: Skip the AppOps grants.
- `--adb <path>`: Explicit path to the adb binary.

---

## 7. YouTube Tutorial & Community Research

To extract metadata, chapters, links, and complete timestamped transcripts from YouTube setup guides (e.g., Retro Game Corps, Joey's Retro Handhelds):
```powershell
python scripts/fetch_youtube.py "<url_or_video_id>"
python scripts/fetch_youtube.py "<url_or_video_id>" -o notes/guide.md
```
Powered by `youtube-transcript-api` and `yt-dlp`. Structured skill definition available at `.agents/skills/youtube-research/SKILL.md`.

---

## 8. The 5 Laws of Schema Verification (Anti-Hallucination Guardrails)

To guarantee emulator stability and prevent input or configuration regressions:
1. **Never Guess INI Section Names or Key Syntaxes**: Always inspect Dolphin/emulator source code, upstream documentation, or native UI auto-mappings on the device before writing configurations. Never improvise section headers or property names.
2. **Clean Direct Tokens Under Active Device Sections**: Under an active `Device = <name>` section, bind buttons and axes using clean, direct tokens (e.g., `Button 96`, `Axis 1-`) rather than chained or device-prefixed expressions (e.g. `` `Device:Button 96` | ... ``), which fail to parse in Android UI builds.
3. **Flat Wiimote Extensions**: Dolphin Wiimote extensions (Classic, Nunchuk) live flat inside `[Wiimote1]` using extension prefixes (e.g., `Classic/Buttons/A = `Button 96``, `Nunchuk/Buttons/C = `Button 102``). Dolphin never recognizes standalone sections like `[Classic1]` or `[Wiimote1/Classic]`.
4. **Literal Plus/Minus Keys**: Dolphin keys for Plus and Minus buttons are literally `+` and `-` (e.g., `Buttons/+`, `Classic/Buttons/-`), never `Plus` or `Minus`.
5. **Always Verify with Live Hardware Logs & Screenshots**: Never declare input or emulator configuration complete without verifying via ADB dumps, live logcat output, or screen captures that in-game menus advance and inputs are cleanly captured without drawer/system popups.

---

## 9. Markdown Clipboard Staging Protocol

When providing markdown text intended for the user to copy/paste to external sites (e.g., GitHub comments, issues, PR discussions, Discord, forums):
1. **Always stage directly into Windows clipboard**: Use PowerShell `.\scripts\stage_clipboard.ps1 -FilePath <file>` or `Get-Content <file> -Raw | Set-Clipboard` so the user can immediately paste with `Ctrl+V`.
2. **Strict Flush-Left Formatting**: Ensure zero leading indentation (no 4-space indentations) so GitHub Markdown does not parse text, headers, lists, or HTML `<details>` drawers as indented code blocks.

---

## 10. OLED Display Sleep Invariant (Burn-in Prevention)

Whenever finishing automation tasks, concluding a conversation turn, or awaiting user input:
1. **Power down display**: Execute `adb -s <serial> shell input keyevent 26`.
2. **Verify sleep status**: Execute `adb -s <serial> shell "dumpsys power | grep -E 'mHoldingDisplay|mWakefulness'"` to ensure `mHoldingDisplaySuspendBlocker=false` and `mWakefulness=Dozing`.

---

## 11. User Approval & Review Presentation Protocol

When preparing proposals, architectural designs, or multi-step plans for user approval and review (such as `/learn` proposals or system refactors):
1. **Always generate a self-contained HTML review page**: Build a modern, styled `.html` file with clean typography, diff highlighting, and clear sectioning (e.g. `docs/review/<topic>.html`).
2. **Provide clickable `file://` link**: Always link to the `.html` file using standard markdown `file:///` format instead of asking the user to review raw `.md` files.

---

## 12. GitHub Issue & Bug Report Automation

The host environment has an authenticated GitHub CLI (`gh` account `dmillerzx` with full `repo` scopes). Going forward, open bug reports, feature requests, and community upstream issues directly via `gh issue create --repo <owner/repo> --title "<title>" --body-file "<file>"` rather than prompting the user to submit them manually.

---

## 13. Token Efficiency, Reasoning Effort & Multi-Pool Quota Architecture

To avoid premature throttling under the 5-hour rolling rate limits and preserve high-velocity responsiveness:

1. **Reasoning Effort Invariant (`Medium` Baseline)**:
   - Always default to `Medium` (or `Low`) reasoning effort for procedural execution, ADB tasks, script authoring, and INI configuration.
   - `High` reasoning effort spends 2,500–5,000 hidden thinking tokens on every single tool step. It is prohibited for routine execution and permitted only during initial decompilation analysis or on explicit user request.
2. **Proactive Context Compaction (`/compact`)**:
   - Antigravity transmits the cumulative transcript on every interaction. To prevent multi-megabyte context bloat and quadratic token burn, recommend the `/compact` slash command whenever a task surpasses ~30 turns.
3. **Multi-Model Quota Balancing**:
   - Antigravity isolates quotas into three distinct pools:
     - **Gemini Models** (`gemini-3.8-flash`, `gemini-pro`)
     - **Claude and GPT Models** (`claude-sonnet-5-5`, `claude-opus-5-5`, `gpt-oss-120b`)
     - **Gemini 4 Argon** (`gemini-4-argon`)
   - When one pool's 5-hour limit approaches depletion, immediately offer to route workloads to `claude-sonnet-5-5-medium` or `gemini-4-argon`, which maintain completely independent 100% capacity buckets.





