# GEMINI.md — Gemini Directives for Retroid Pocket 5 Automation

This file provides system context and operational instructions for Google Gemini models interacting with this Retroid Pocket 5 (RP5) workspace.

---

## 1. Persona & Context

You are assisting with the automated provisioning and maintenance of a **Retroid Pocket 5** retro gaming handheld running **Android 13** on the **Snapdragon 865** chipset (Qualcomm Adreno 650 GPU).
Your primary interface to the device is **ADB (Android Debug Bridge)** over USB or local Wi-Fi pairing.

---

## 2. Environment Invariants

- **Workspace Root**: Workspace root directory (`<WORKSPACE_ROOT>`)
- **Local Platform Tools**: `platform-tools/adb.exe`
- **Installed Python**: `python` (Python 3.12)
- **Git Binary**: `git.exe`
- **RP5 serial**: Read dynamically via `adb devices` (always use `adb -s <serial>` when targeting hardware).
- When running commands in Windows PowerShell where PATH might not be reloaded in inherited subprocesses, ensure ADB and Python are referenced cleanly using environment refreshes or absolute fallbacks.

---

## 3. CANONICAL STORAGE LAYOUT (STRICT - DO NOT DEVIATE)

```text
Internal storage   /sdcard/bios
MicroSD            /storage/<SD_ID>/bios
                   /storage/<SD_ID>/ROMs
                   /storage/<SD_ID>/ROMs/xbox
                   /storage/<SD_ID>/ES-DE
                   /storage/<SD_ID>/RetroArch
                   /storage/<SD_ID>/Saves_Backup
                   /storage/<SD_ID>/Games/Steam
```

**Forbidden - never create, push to, or document these on the device:**
- `Games/BIOS`, `BIOS/` (upper-case), `Bios/`
- `roms/` (lower-case), `Emulation/`, `Emulation/roms`, `Emulation/bios`
- `/sdcard/ROMs`, `/sdcard/roms`, `/sdcard/Emulation` (no ROM directories on internal storage)
- Any other new top-level directory on `/storage/<SD_ID>/` besides `bios`, `ROMs`, `ES-DE`, `RetroArch`, `Saves_Backup`, `Games/Steam`.

---

## 4. Provisioning Checklist

When executing or modifying `scripts/setup_rp5.py` and `scripts/provision_all.ps1`, verify the following stages:

| Stage | Action | Verification Command |
|---|---|---|
| **Connectivity** | Confirm device is online and authorized | `adb devices` |
| **Phantom Process** | Disable Android 13 phantom process restrictions | `adb shell "/system/bin/device_config get activity_manager max_phantom_processes"` |
| **Storage Scaffolding** | Create canonical directories | `adb shell "ls -la /sdcard/bios /storage/<SD_ID>"` |
| **Obtainium Staging** | Push `rp5_master_obtainium.json` to `/sdcard/Download/` (intermediateLink for RetroArch) | `adb shell "ls -l /sdcard/Download/rp5_master_obtainium.json"` |
| **ES-DE Pre-Config** | Push `es_settings.xml` & validate `es_systems.xml` schema (%DATA%=%ROMSAF%) | `adb shell "cat /sdcard/ES-DE/custom_systems/es_systems.xml"` |
| **Turnip Drivers** | Stage Mesa Turnip GPU drivers (turnip_v24.3.0_R9v2 baseline) in `/sdcard/Download/drivers/` | `adb shell "ls -la /sdcard/Download/drivers"` |
| **Hardware Tuning** | Lockscreen disabled, overlay hidden, auto-rotate disabled (`accelerometer_rotation 0`), fan smart (`fan_mode 4`), Xbox layout, Both triggers (`persist.sys.trigger.mode 2`), Regular Performance mode (`performance_mode 1`, Never High), OLED display saturation tuned (`persist.sys.sf.color_saturation 0.90` default, `0.70` sRGB reference; auto adaptation disabled) | `adb shell "getprop persist.sys.trigger.mode; settings get system fan_mode; settings get system performance_mode; getprop persist.sys.sf.color_saturation"` |
| **DroidDeck & Steam** | Stage DroidDeck 720p/FSR profile, libraryfolders.vdf, and Sony Vita firmware | `adb shell "cat /sdcard/DroidDeck/config.json"` |
| **RetroArch 2D Engine** | Deploy Vulkan, Ozone, 48ms OpenSLES, Genesis Model 1 LPF, GBA 5.5kHz DSP, mGBA LCD grid | `adb shell "ls -la /storage/<SD_ID>/RetroArch/filters/audio"` |
| **2D/Arcade Cores** | Fetch frontend assets; cores downloaded via in-app Online Updater | `adb shell "ls -la /storage/<SD_ID>/RetroArch/cores"` |
| **Standalone 3D Profiles** | Inject tuned Vulkan/audio profiles into DuckStation, NetherSX2 (16:9 Overscan), ARM SX2 (16:9 Overscan, Disable Readbacks, %DATA%=%ROMSAF%), Dolphin (global GFX.ini AspectRatio=0 Auto, SIDevice0=6, WiimoteSource0=1, analog triggers L=Axis 22+ R=Axis 23+), PPSSPP, Flycast, Azahar, Vita3K | `adb shell "cat /sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Dolphin.ini"` |
| **Universal Patches** | Stage 4,700+ PS2 pnach cheats & 550 GameCube per-game profiles in patches/gcn/ | `adb shell "ls /sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings"` |
| **Save Backup Sync** | Mirror saves, states, and memory cards to `/storage/<SD_ID>/Saves_Backup/latest/` | `adb shell "ls -la /storage/<SD_ID>/Saves_Backup/latest"` |
| **Permissions** | Grant `MANAGE_EXTERNAL_STORAGE` across all emulators and frontends | `adb shell "appops get <package> MANAGE_EXTERNAL_STORAGE"` |
| **Native Port Profiles** | Stage Perfect Dark XBLA Duty Calls profile (`StickCButtons=0`, Style 8 "Ext", `MouseAimMode=1`, `CK_8000` crouch), SM64 ALO touchless/BetterCamera/ZL multi-bind, Sonic Mania RSDKv5, GoldenEye root files + gunbarrel icon, CannonBall OutRun | `adb shell "cat /sdcard/Android/data/com.perfectdark.port/files/pd.ini"` |
| **LibUltraShip Ports** | Verify `baserom.us.z64` extraction generates `*.o2r`, touch overlay disabled, backend ID 1 OpenGL, ES-DE `.app` registered | `adb shell "ls -l /sdcard/Android/data/dev.net64.paperboat/files/pm64.o2r"` |
| **Xbox (hakuX) ROMs** | Staged to `/storage/<SD_ID>/ROMs/xbox/` formatted as trimmed XDVDFS `.iso` via `extract-xiso -c` | `adb shell "ls -la /storage/<SD_ID>/ROMs/xbox"` |
| **ROM Compression** | N64 strictly uncompressed `.z64` (big-endian), NDS `.nds`, 16/8-bit cartridges `.zip`, disc ROMs `.chd`, GC/Wii `.rvz`, Xbox trimmed `.iso` | `adb shell "ls -la /storage/<SD_ID>/ROMs/n64"` |

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
- **hakuX (Original Xbox)**: `com.rfandango.haku_x`
- **PPSSPP (PSP)**: `org.ppsspp.ppsspp`
- **Azahar (3DS)**: `org.azahar_emu.azahar`
- **Vita3K (PS Vita)**: `org.vita3k.emulator`
- **Flycast (Dreamcast)**: `com.flycast.emulator`
- **Daijisho (Frontend)**: `com.magneticchen.daijishou`
- **DroidDeck (Steam Launcher)**: `com.droiddeck.launcher`
- **Tracked Native Android Ports (Tier 1)**: `io.github.thatguymcd.dkrr.preview` (DKR-R), `com.fexed.spacecadetpinball`, `org.stjr.srb2`, `org.eukaryot.sonic3air`, `com.apotris.android`, `com.izzy.kart`, `com.starship.android`, `com.perfectdark.port`, `com.dishii.soh`, `com.dishii.mm`, `com.dishii.zelda3`, `com.dishii.banjo` (BanjoRecomp)
- **Additional Frontends / Tools**: `com.magneticstarlight.beacon` (Beacon), `org.mupen64plusae.v3.fzurita` (Mupen64Plus FZ)

---

## 6. Script Invocation

To run the complete zero-touch provisioning pipeline:
```powershell
.\\scripts\\provision_all.ps1 -Serial <SERIAL>
# Or via Python:
python scripts/setup_rp5.py --serial <SERIAL> --all
```
Common options: `--status` (inspect connection), `--install-apks` (install staged APKs), `--dry-run` (preview commands).

---

## 7. The 17 Laws of Schema Verification & Device Standards (Anti-Hallucination Guardrails)

1. **Never Guess INI Section Names or Key Syntaxes**: Always inspect Dolphin/emulator source code, upstream docs, or native UI auto-mappings on-device before writing configs.
2. **Clean Direct Tokens Under Active Device Sections**: Under an active `Device = <name>` section, bind buttons and axes using clean, direct tokens (e.g. `Button 96`, `Axis 1-`) rather than chained or device-prefixed expressions.
3. **Flat Wiimote Extensions**: Dolphin Wiimote extensions live flat inside `[Wiimote1]` using extension prefixes (e.g. `Classic/Buttons/A = \`Button 96\``, `Nunchuk/Buttons/C = \`Button 102\``). Standalone sections like `[Classic1]` are invalid.
4. **Literal Plus/Minus Keys**: Dolphin keys for Plus and Minus buttons are literally `+` and `-` (e.g. `Buttons/+`, `Classic/Buttons/-`), never `Plus` or `Minus`.
5. **Always Verify with Live Hardware Logs & Screenshots**: Never declare input or emulator configuration complete without verifying via ADB dumps, live logcat output, or screen captures that in-game menus advance cleanly.
6. **Strict ES-DE Custom Systems XML Schema & `%DATA%=%ROMSAF%` Law**: Custom systems reside at `/sdcard/ES-DE/custom_systems/es_systems.xml`. Preflight with `xml.etree.ElementTree`. Standalone Android emulators requiring SAF Content URIs must use `%DATA%=%ROMSAF%` rather than raw `-d %ROM%`.
7. **Xbox Aspect Ratio & EEPROM Screen Format Standards**: Original Xbox display geometry is governed by emulated EEPROM `Screen Format` (`Normal` 4:3 vs `Wide screen` 16:9). For authentic geometry in 4:3 titles (*Crazy Taxi 3*, *JSRF* v1), force global `Aspect Ratio: 4:3` in hakuX.
8. **Hall Effect Joystick Resting Deadband Invariant**: Enforce a 10% deadband across Dolphin (`Dead Zone = 10.0`), ARM SX2 (`Deadzone = 0.06`), RetroArch (`input_analog_deadzone = 0.10`), PPSSPP (`AnalogDeadzone = 0.10`), Flycast (`dead_zone = 10`), and hakuX (`0.10`) to eliminate premature camera drift.
9. **Obtainium Tag-to-Manifest Divergence & Version Detection Standard**: When upstream release tags diverge from Gradle `versionName`, set `"versionDetection": false` in `rp5_master_obtainium.json` and track GitHub release tags directly, clearing endless pending update loops.
10. **Downstream CI Hot-Loop Optimization vs. Substring Contract Test Invariant**: When removing hot-loop log statements in downstream graphics pipelines, update contract tests to assert functional branch guards rather than removed `fprintf` strings.
11. **Platform-Agnostic Git Patch Streaming in Tests**: Never pass absolute Windows paths (`C:\\...`) to `git apply`. Always stream patch bytes via standard input: `subprocess.run(["git", "-C", stage, "apply", ...], input=patch_path.read_bytes(), check=True)`.
12. **Android Component Resolution & UI Automation Focus Assertion Invariant**: Resolve exact activity names via `dumpsys package <pkg> | grep -i Activity`. QA scripts must assert `mCurrentFocus` matches the target component before injecting inputs or capturing screenshots.
13. **Vulkan Mobile Scissor Rect & Viewport Clamping Invariant (`VUID-00282`)**: On mobile TBDR architectures (Adreno 650), clamp all scissor coordinates to framebuffer bounds (`[0, fbWidth]`, `[0, fbHeight]`) before calling `vkCmdSetScissor` to avoid driver draw discards.
14. **Static Binary Recompilation ROM Version & Silent Android Failure Law**: Recompilations hardcode binary mappings to specific base ROM revisions (e.g. NTSC-U v1.0 / Rev 0). Passing subsequent revisions (Rev A / v1.1) fails hash checks silently. Port wrappers must inspect cartridge header bytes (0x3B-0x3F) and implement zero-touch boot hydration from `/storage/*/ROMs/`. Redundant revisions must be pruned from MicroSD.
15. **Downstream Handheld Fork Discoverability & Community Release Prominence Law**: Handheld maintenance forks (`dmillerzx/*`) must configure complete GitHub topics, descriptive headers, and promote latest releases as `--latest` (`--prerelease=false`).
16. **Release Version & AppStream Metadata Atomic Synchronization Law**: Bumping `VERSION` across projects with packaging validation (e.g. `DKR-R`) requires atomically updating `<release version="X.Y.Z" date="YYYY-MM-DD">` in `packaging/linux/*.appdata.xml`. Verify locally with `python scripts/check.py --suite tooling`.
17. **Upstream `pull_request_target` Fork CI Triage Invariant**: Upstream GitHub Actions workflows triggered on `pull_request_target` (e.g. `AurelioB/BanjoRecomp-Android` PR #24 `validate-external`) fail with `Refusing to check out fork pull request code` due to GitHub Actions fork security policy. This is an expected upstream CI security posture, not an error with the PR changes. Never attempt to rewrite fork branch commits to "fix" upstream checkout rejections; monitor and validate via autonomous fork CI workflows (`Android APK`).
18. **Monolithic Provisioning Prohibition & User Setting Preservation Law**: The Retroid Pocket 5 is an actively configured, daily-driver handheld gaming console, never a blank-slate disposable test harness. Once initial zero-touch provisioning is complete, agents and automation tools MUST NEVER invoke monolithic provisioning (`setup_rp5.py --all` or `provision_all.ps1`) or broad configuration sweeps (`--hardware`) autonomously. Day-to-day operations must be strictly surgical, targeted, and non-destructive. User-defined preferences—including Quick Settings tile arrangements, fan profiles, controller layout modes, volume click sounds, and display adjustments—must never be overwritten or reverted back to stock baseline without explicit user request. If a system change is recommended, document it in repository configs and seek confirmation before modifying the device.

---

## 8. Markdown Clipboard Staging Protocol

When providing markdown intended for external copy/paste (GitHub, issues, PRs, Discord):
1. Stage directly into Windows clipboard via PowerShell: `Get-Content <file> -Raw | Set-Clipboard` or `.\\scripts\\stage_clipboard.ps1 -FilePath <file>`.
2. Ensure strict flush-left formatting (no leading 4-space indentation) so GitHub Markdown does not parse text as code blocks.

---

## 9. OLED Display Sleep Invariant (Burn-in Prevention)

Whenever finishing automation tasks, concluding a conversation turn, or awaiting user input:
1. **Inspect Wakefulness First**: Query `adb -s <serial> shell "dumpsys power | grep mWakefulness="`.
2. **Power Down Display If Awake**: Only execute `adb -s <serial> shell input keyevent 26` if `mWakefulness=Awake`. If already `mWakefulness=Dozing` or `Asleep`, do not toggle.
3. **Verify Sleep Status**: Execute `adb -s <serial> shell "dumpsys power | grep -E 'mHoldingDisplay|mWakefulness'"` to ensure `mHoldingDisplaySuspendBlocker=false` and `mWakefulness=Dozing`.

---

## 10. Autonomous High-Confidence Proceed & Review Presentation Protocol

When preparing proposals, architectural designs, or improvements:
1. **High-Confidence Autonomous Execution**: When confidence is very high (backed by deterministic testing, schema verification, and live hardware logs), proceed with applying changes autonomously without halting.
2. **Generate Styled HTML Review Page**: Build a self-contained, styled `.html` file with clean typography, diff highlighting, and clear sectioning (e.g. `docs/review/<topic>.html`).
3. **Clickable Link**: Always link using standard markdown `file:///` format.
4. **Enforce Anti-Hallucination Guardrails**: Adhere strictly to the 17 Laws of Schema Verification before committing changes.

---

## 11. GitHub Issue & Bug Report Governance (Human-in-the-Loop & Anti-AI Spam)

- **No Autonomous Upstream Submissions**: NEVER autonomously submit issues, bug reports, or feature requests to third-party upstream repositories via `gh issue create`. Autonomous creation is permitted ONLY on user personal forks and tracking repositories (`dmillerzx/*`).
- **Upstream Submission Approval**: All bug reports intended for external maintainers must be drafted locally (e.g. in `docs/community_reports/`), presented to the user, and staged to clipboard (`.\\scripts\\stage_clipboard.ps1`) for explicit user review and manual posting.
- **Permanent Screenshot Permalinks**: Stage bug screenshots into `docs/assets/screenshots/<name>.png`. Commit and push to `origin main` before submitting issues so images render via permanent raw GitHub URLs.
- **Strict Privacy Invariant**: NEVER leak, publish, or commit user real names, work directories, corporate file paths, or private hostnames. Scrub paths to generic forms.

---

## 12. Specialized Skills Reference Directory

For domain-specific runbooks, progressive skills are available in `.agents/skills/`:
- **Downstream Fork Governance & Releases**: [`.agents/skills/handheld-fork-governance/SKILL.md`](.agents/skills/handheld-fork-governance/SKILL.md)
- **ROM Packaging & Port Profiles**: [`.agents/skills/rom-and-port-staging/SKILL.md`](.agents/skills/rom-and-port-staging/SKILL.md)
- **Qualcomm Adreno 650 Drivers**: [`.agents/skills/adreno-gpu-drivers/SKILL.md`](.agents/skills/adreno-gpu-drivers/SKILL.md)
- **RP5 Hardware & OLED Display Sleep**: [`.agents/skills/rp5-device-control/SKILL.md`](.agents/skills/rp5-device-control/SKILL.md)
- **Workstation Tuning & Audio Shield**: [`.agents/skills/workstation-tuning/SKILL.md`](.agents/skills/workstation-tuning/SKILL.md)
- **YouTube Research & Setup Guides**: [`.agents/skills/youtube-research/SKILL.md`](.agents/skills/youtube-research/SKILL.md)
- **Binary Reverse Engineering (REA)**: [`.agents/skills/reverse-engineer-anything/SKILL.md`](.agents/skills/reverse-engineer-anything/SKILL.md)
