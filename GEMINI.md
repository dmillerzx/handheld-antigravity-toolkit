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
| **Turnip Drivers** | Stage Mesa Turnip GPU drivers (turnip_v24.3.0_R9v2 baseline, TurnipZ-0.3.0 SD865, Turnip-24.1.0 R18 a6xx) in `/sdcard/Download/drivers/` (No Adreno 7xx-only builds) | `adb shell "ls -la /sdcard/Download/drivers"` |
| **Hardware Tuning** | Lockscreen disabled, overlay hidden, auto-rotate disabled (`accelerometer_rotation 0`), Smart fan mode (`fan_mode 4`), Xbox layout, Both triggers (`persist.sys.trigger.mode 2`) | `adb shell "getprop persist.sys.trigger.mode; settings get system fan_mode"` |
| **DroidDeck & Steam** | Stage DroidDeck 720p/FSR profile, env overrides, libraryfolders.vdf, and Sony Vita firmware | `adb shell "cat /sdcard/DroidDeck/config.json"` |
| **RetroArch 2D Engine** | Deploy Vulkan, Ozone, 48ms OpenSLES, Genesis Model 1 LPF, GBA 5.5kHz DSP, mGBA LCD grid | `adb shell "ls -la /storage/<SD_ID>/RetroArch/filters/audio"` |
| **2D/Arcade Cores** | Fetch & stage 11 designated cores and frontend assets | `adb shell "ls -la /storage/<SD_ID>/RetroArch/cores"` |
| **Standalone 3D Profiles** | Inject tuned Vulkan/audio profiles into DuckStation, NetherSX2 (16:9 Overscan), ARM SX2 (16:9 Overscan, Disable Readbacks, %DATA%=%ROMSAF%), Dolphin (global GFX.ini AspectRatio=0 Auto, SIDevice0=6 standard GC controller, WiimoteSource0=1, WiimoteProfile1=Classic_Controller, analog triggers L=Axis 22+ R=Axis 23+, no broken PadType0 overrides), PPSSPP, Flycast, Azahar, Vita3K (initial-setup: false, Vulkan backend, pref-path) | `adb shell "cat /sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Dolphin.ini"` |
| **Universal Patches** | Stage 4,700+ PS2 pnach cheats & 550 GameCube per-game profiles in patches/gcn/ smartly merged with upstream Dolphin GameSettings (Video_Settings AspectRatio=1, Gecko_Enabled) | `adb shell "ls /sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings"` |
| **Save Backup Sync** | Mirror saves, savestates, and memory cards to `/storage/<SD_ID>/Saves_Backup/latest/` | `adb shell "ls -la /storage/<SD_ID>/Saves_Backup/latest"` |
| **Permissions** | Grant `MANAGE_EXTERNAL_STORAGE` across all emulators and frontends | `adb shell "appops get <package> MANAGE_EXTERNAL_STORAGE"` |
| **Native Port Profiles** | Stage Perfect Dark (`com.perfectdark.port`) XBLA Duty Calls profile (`StickCButtons=0`, Style 8 "Ext", `MouseAimMode=1`, `CrosshairSway=0`, Lookspring OFF, `CK_8000` crouch), Super Mario 64 ALO touchless/BetterCamera/ZL multi-bind, Sonic Mania RSDKv5, GoldenEye root files + gunbarrel 007 adaptive icon (backup `/sdcard/Android/data/com.sunjaycy.goldeneye/files/` before reinstall), CannonBall OutRun | `adb shell "cat /sdcard/Android/data/com.perfectdark.port/files/pd.ini"` |
| **LibUltraShip Ports** | Verify `baserom.us.z64` extraction generates `*.o2r` (SoH, 2S2H, Starship, PaperBoat), touch overlay disabled (`Enabled=0`), backend ID 1 OpenGL, ES-DE `.app` registered | `adb shell "ls -l /sdcard/Android/data/dev.net64.paperboat/files/pm64.o2r"` |
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

## 11. Autonomous High-Confidence Proceed & Review Presentation Protocol

When preparing proposals, architectural designs, or improvements (such as `/learn` proposals or system refactors):
1. **High-Confidence Autonomous Execution**: When confidence in a recommendation, refinement, or `/learn` proposal is very high (backed by deterministic testing, schema verification, and live hardware logs), proceed with applying the changes autonomously without halting to wait for user confirmation. For all `/learn` invocations with high conviction, implement the changes automatically and only ask for confirmation if genuinely unsure or facing ambiguous tradeoffs.
2. **Always generate a self-contained HTML review page**: Build a modern, styled `.html` file with clean typography, diff highlighting, and clear sectioning (e.g. `docs/review/<topic>.html`) to serve as an audit trail.
3. **Provide clickable `file://` link**: Always link to the `.html` file using standard markdown `file:///` format for immediate user visibility.
4. **Enforce Anti-Hallucination Guardrails**: Adhere strictly to the 5 Laws of Schema Verification (never invent INI keys, inspect actual emulator source or device mappings, clean direct tokens, verify live on hardware) before committing changes.

---

## 12. GitHub Issue & Bug Report Governance (Human-in-the-Loop & Anti-AI Spam)

- **No Autonomous Upstream Submissions**: NEVER autonomously submit issues, bug reports, or feature requests to third-party upstream repositories (e.g., `rt64/rt64`, `HarbourMasters/*`, etc.) via `gh issue create`. Autonomous creation is permitted ONLY on the user's personal forks and tracking repositories (`dmillerzx/*`).
- **Upstream Submission Approval**: All bug reports or communications intended for external upstream maintainers must be drafted locally (e.g. in `docs/community_reports/`), presented to the user, and staged to clipboard (`.\scripts\stage_clipboard.ps1`) for explicit user review and manual posting.
- **No AI-Generated Report Templates**: When drafting bug reports for external maintainers, NEVER use standard LLM templates (e.g. "Root Cause Analysis", "Suggested Fixes for Developers", bold didactic bullet lists). Keep reports concise, human, and focused purely on concrete reproduction steps, raw stack traces, and targeted context. Always verify whether upstream actually supports the target platform before raising platform-specific issues.
- **Permanent Screenshot Permalinks**: Stage bug screenshots into `docs/assets/screenshots/<name>.png`. Ensure `.gitignore` anchors `/assets/` at root so `docs/assets/` is tracked. Commit and push to `origin main` before submitting the issue so images render via permanent raw GitHub URLs.
- **Strict Personal Privacy & PII Protection Invariant**: NEVER leak, publish, commit, or stage the user's real name, email, physical address, or any personally identifiable information (PII) into README files, commit messages, licenses, PRs, issues, or documentation. Strictly use the public GitHub handle (`dmillerzx`) or generic terms ("community contributor", "maintainer").
- **Cross-Link Synchronization**: Document issue URLs in `WORKQUEUE.md` and `CLAUDE.md`, and update local tracking issues (e.g. `dmillerzx/handheld-antigravity-toolkit#1`) for cross-agent awareness.

---

## 13. Token Efficiency, Reasoning Effort & Multi-Pool Quota Architecture

To avoid premature throttling under the 5-hour rolling rate limits and preserve high-velocity responsiveness:

1. **Reasoning Effort Invariant (`Medium` Baseline)**:
   - Always default to `Medium` (or `Low`) reasoning effort for procedural execution, ADB tasks, script authoring, and INI configuration.
   - `High` reasoning effort spends 2,500–5,000 hidden thinking tokens on every single tool step. It is prohibited for routine execution and permitted only during initial decompilation analysis or on explicit user request.
2. **Proactive Reasoning & Model Escalation Gate**:
   - If a requested task (e.g. deep C++ NDK decompilation, complex multi-file architectural refactoring, elusive race conditions, or low-level SPIR-V/Vulkan shader debugging) would benefit significantly from `High` reasoning effort or a more capable model (e.g. `Claude 3.5 Sonnet` or `Gemini Pro`), the agent MUST pause immediately, explain the technical justification, and prompt the user to make the switch in the chat UI before proceeding with execution.
3. **Automated Turn-25 Compaction Alarm (`/compact`)**:
   - Antigravity transmits the cumulative transcript on every interaction. To prevent multi-megabyte context bloat and quadratic token burn, the agent tracks conversation length and proactively prepends a high-visibility alert banner (`> [!IMPORTANT] Context Compaction Gate (Turn 25 Reached)`) advising the user to type `/compact` before sending their next prompt.
4. **Strict Compound One-Flow Execution**:
   - Group related inspections, mutations, and verification into a single compound execution pass per turn (or unified PowerShell scratch scripts). Strictly eliminate serialized `thought -> tool -> thought -> tool` exploratory micro-turns.
5. **Output Silencing & Lean Receipts**:
   - Never dump voluminous raw terminal/ADB outputs (e.g. `dumpsys`, full `logcat`, recursive directory trees, long test logs) directly into stdout, which permanently bloats `transcript.jsonl`. Pipe or filter outputs (`Select-Object -First 20`, `grep`), or redirect full logs to scratch files (`scratch/<name>.log`), reporting only concise exit codes and summaries.
6. **Multi-Model Quota Balancing**:
   - Antigravity isolates quotas into three distinct pools:
     - **Gemini Models** (`gemini-3.8-flash`, `gemini-pro`)
     - **Claude and GPT Models** (`claude-sonnet-5-5`, `claude-opus-5-5`, `gpt-oss-120b`)
     - **Gemini 4 Argon** (`gemini-4-argon`)
   - When one pool's 5-hour limit approaches depletion, immediately offer to route workloads to `claude-sonnet-5-5-medium` or `gemini-4-argon`, which maintain completely independent 100% capacity buckets.

---

## 14. Host Workstation Optimization & Shell Execution Invariants

1. **Dell Precision Service Boundary Law**: Always preserve `DPMService` (Dell Peripheral Manager / `DDPM.Subagent`) to protect external monitor input switching and USB-C hub peripheral controls. Set `DellTechHub` and `DellClientManagementService` to `Manual` (or `Disabled`) and kill child subagents to eliminate ~1.3 GB of idle memory bloat.
2. **Audio Shield Watchdog**: The scheduled task `MaxxAudioShield_AntiDistortion` locks Waves/Realtek services to `Start = 4` (Disabled) on boot and logon as `SYSTEM`, ensuring Peace Equalizer APO and RNNoise AI microphone filtering run with zero Realtek driver compression or distortion.
3. **OneNote Tray & Phone Link Suppression**: Office Click-to-Run must be prevented from restoring `Send to OneNote.lnk` on logon via `HKCU:\Software\Microsoft\Office\16.0\OneNote\Options\Other\EnableMemoryTrayMenuItem = 0`. Windows Phone Link background permissions must remain disabled (`Disabled = 1`, `EnableMmx = 0`).
4. **PowerShell Scratch File Execution Invariant**: When running complex PowerShell commands via agent CLI tools, never nest double-quoted script blocks or unescaped variables inside `-Command "..."`. Always stage multi-line scripts to `<appDataDir>\brain\<conversation-id>/scratch/<name>.ps1` and execute with `-File` for 100% deterministic, uncorrupted parsing.

---

## 15. GPU Driver Architecture & Native Port Rendering Invariant

1. **Adreno 650 Driver Hierarchy**: The Retroid Pocket 5 features a Qualcomm Snapdragon 865 (SM8250 / Kona) with an Adreno 650 GPU (`a6xx` family). Supported drivers:
   - `turnip_v24.3.0_R9v2.zip`: Gold-standard general baseline (Azahar 3DS, DroidDeck DXVK).
   - `TurnipZ-0.3.0.zip`: SD865-tailored Mesa 27.0-devel branch (highest Switch/heavy Vulkan FPS, Unreal Engine color fixes).
   - `Turnip-24.1.0.adpkg_R18.a6xx.zip`: Dedicated `a6xx` depth clearing & tessellation fix.
   - Qualcomm Kona Stock Driver (`com.qualcomm.qti.gpudrivers.kona.api30`): Built-in system driver; default for PS2, Dolphin baseline, and native Android ports.
2. **Native Port Boundary**: Native Android ports (Perfect Dark, SM64 ALO, Banjo, SoH, Sonic Mania, etc.) and direct OS bounded emulators (ARM SX2, NetherSX2, PPSSPP, Flycast, DuckStation) bind directly to `/system/lib64/libvulkan.so` and execute natively on Qualcomm hardware with zero translation overhead. Do not attempt to inject Turnip ZIPs into native ports.
3. **Adreno 6xx Invariant**: Never stage Adreno 7xx-only (`vulkan.ad07xx.so`) driver archives as primary drivers on the RP5. Always verify `meta.json` inside driver ZIPs.

---

## 16. Controller Configuration Preservation Invariant

Automated provisioning scripts (`setup_rp5.py`, `configure_standalones.py`, `provision_all.ps1`) must **never** unconditionally overwrite existing emulator controller mappings on the device:
1. **Dolphin Controller Guard**: Always check if `GCPadNew.ini` or `WiimoteNew.ini` exists on-device before pushing. If present, skip deploying controller templates to preserve user-calibrated physical button assignments and stick deadzones.
2. **RetroArch & Standalone Pads**: Input profiles in NetherSX2, ARM SX2, DuckStation, and PPSSPP must respect user-calibrated files once created.

---

## 17. Architecture-Driven Platform Routing Heuristic

When a title exists across multiple platforms (e.g. PS2, GameCube, PSP, Native PC):
1. **Bespoke Console Titles**: Titles engineered natively for the PS2 architecture (e.g., *Gran Turismo 4*, *God of War*, *Devil May Cry 3*) run at a locked 60 FPS at 2.0x 1080p on the Snapdragon 865.
2. **PC/Xbox-Ported Outliers**: Titles originally engineered for PC/Xbox architectures (DirectX 8/9 with programmable shaders, e.g., *OutRun 2006: Coast 2 Coast*) fight the PS2 hardware, triggering excessive `autoFlush` stalls and single-threaded Emotion Engine bottlenecks.
3. **Preferred Routing**: For these outlier titles, prioritize:
   - **PSP (PPSSPP)**: Rendered at 4x Native (1080p) with emulated CPU clock unlocked to `444 MHz` for a locked 60 FPS presentation.
   - **GameCube (Dolphin)**: 2.5x 1080p with Gecko widescreen patches.
   - **Native PC (DroidDeck / Wine)**: Once 32-bit x86 DX9 translation stabilizes under FEX.

---

## 18. Community Project Orphan Takeover & Deep Engineering Session Boundary

1. **Orphan Takeover Protocol**: When an upstream open-source maintainer announces departure or ends platform support (e.g. ThatGuyMcd on DKR-R Android), verify licensing (MIT/GPL), autonomously establish community continuity via `gh repo fork <owner>/<repo> --clone=false` under the user's account (`dmillerzx`), and post empathetic, technically accurate feedback explaining the hardware root cause.
2. **Shared-Engine Triage Strategy**: When multiple ports share the same underlying engine (e.g. N64Recomp + RT64 across DKR-R and Banjo Recomp), solve the bug on the orphaned project first, then backport or submit upstream PRs to active maintainers.
3. **Session Boundary & Reasoning Elevation Invariant**: Transitioning from high-level triage/planning to deep C++ Android NDK builds, CMake scripting, or Vulkan shader debugging MUST occur in a fresh session to eliminate transcript bloat and prevent quadratic token inflation. Explicitly prompt the user to switch to a high-reasoning model (`Claude 3.5 Sonnet` or `Gemini Pro`) with `High` thinking effort before commencing native decompilation/patching work.
4. **Continuous Upstream Synchronization**: When maintaining an orphaned or downstream handheld fork (e.g., DKR-R Android on `dmillerzx/DKR-R`), continuously track and rebase against `upstream/main` and upstream release tags. Downstream branches must never lag behind upstream bugfixes and engine enhancements (`ahead_by: N, behind_by: 0`).
5. **Community Standalone Release Obligation**: Handheld console users cannot compile C++ Android NDK code on-device. Whenever an upstream sync or downstream platform fix completes, package standalone signed APKs (`Package-Android-Preview.ps1`) and publish them to GitHub Releases with verified SHA-256 checksums and controller mapping instructions.
6. **Android CMake Library Target Boundary**: Never invoke default build targets in hybrid C++/Android projects. Default targets compile desktop host tests (e.g. `DKRMipmapLoadingTests`), which fail due to native window type mismatches. Always build the specific Android shared library target (e.g. `DKRPortGame` / `libDKR-R.so`).
7. **CI Host Test Flake Isolation**: Host test failures on unrelated platforms (e.g. WebRTC socket timing on GitHub Actions macOS VMs) must be recognized as platform-specific CI flakes and isolated from blocking Android release delivery.
8. **Downstream Fork Branch Protection Prohibition**: Never configure GitHub branch protection rules or require mandatory passing status checks on downstream maintenance forks (`dmillerzx/*`). Upstream test flakes on unrelated OS targets (e.g., macOS VM WebRTC socket timeouts) block handheld Android PR merges, and branch protection obstructs zero-friction fast-forward rebasing against upstream release tags.
9. **Pattern-Guard Baseline Indexing & Transition-Layer PR Invariant**: In repositories enforcing architectural pattern guards (e.g., `scripts/pattern_guard.py` rule `PG013`), newly staged dependency or platform patches must be sorted alphabetically into `architecture/pattern-guard-baseline.txt`. Accompanying pull requests must be explicitly tagged with the `transition-layer` label (`gh pr edit <PR> --add-label transition-layer`) so CI diff checks accept baseline expansion.
10. **Local Python Linter Preflight (`ruff`)**: Before pushing commits modifying Python contract tests, build tools, or packaging scripts in repos enforcing automated linting, always execute `ruff check` and `ruff format --check` locally to eliminate CI turnaround cycles.

---

## 19. Android 13 Dynamic Linker Classloader Namespace Invariant (RetroArch Cores)

On Android 10+ and strictly on Android 13 (Retroid OS on RP5), the Android dynamic linker restricts native library loading via `classloader-namespace`:
- **Permitted Paths**: `permitted_paths="/data:/mnt/expand:/data/user/0/com.retroarch.aarch64"`.
- **External Storage Prohibition**: RetroArch cannot `dlopen()` any `.so` dynamic library located on `/sdcard/`, `/storage/emulated/0/`, or external MicroSD (`/storage/<SD_ID>/RetroArch/cores/`). Attempts to pass external core paths fail with:
  `dlopen failed: library "..." is not accessible for the namespace: [name="classloader-namespace"]`
- **Non-Root Write Boundary**: Unrooted ADB shell cannot write to `/data/user/0/com.retroarch.aarch64/cores/` (`Permission denied`), and `run-as` is unavailable on non-debuggable production builds.
- **Operational Requirement**:
  1. **Assets vs. Cores**: Frontend assets (Shaders, Joypad Autoconfig, Info files) can and should be staged to `/storage/<SD_ID>/RetroArch/`.
  2. **Core Acquisition**: Executable `.so` cores **must** be downloaded directly inside RetroArch via **Online Updater ➔ Core Downloader**. Provisioning scripts and agents must not assume pushing `.so` binaries to external storage provides a functional core.
  3. **Standalone N64 Routing**: If an in-app core download is not preferred, route N64 to standalone Mupen64Plus FZ (`org.mupen64plusae.v3.fzurita`) in `es_settings.xml`.








