# Project Status & Task Ledger

*Last Updated: 2026-10-18 12:40 EDT*
*Device: Retroid Pocket 5 (`<SERIAL>`) | Host: Windows 11*
*Branch: `main` | Tracking: `origin/main`*

---

## 📊 Complete Task Ledger (Notes #6, #7, #8)

| # | Task Description | Source | Status | Evidence / Reference |
|---|---|---|---|---|
| **P0.1** | Make GitHub repository private | Note #6 | ⏳ **Waiting for Doug** | User action (GitHub Settings ➔ Danger Zone) |
| **P0.2** | Remove copyrighted video transcripts from `notes/` & update `CREDITS.md` | Note #6 | ✅ **Done & Pushed** | Commit [`7af289f`](https://github.com/.../handheld-antigravity-toolkit/commit/7af289f) |
| **P0.3** | Scrub device serial (`<SERIAL>`), MicroSD UUID (`<SD_ID>`) & user paths from repo | Note #6 | ⏳ **In Progress** | Reopened; active scrub across docs & scripts, pre-commit leak check hook |
| **P0.4** | Remove hardcoded Python paths from PowerShell runner scripts | Note #6 | ✅ **Done & Pushed** | Commit [`bfffbc2`](https://github.com/.../handheld-antigravity-toolkit/commit/bfffbc2) |
| **P0.5** | Delete redundant and divergent `configs/templates/` directory | Note #6 | ✅ **Done & Pushed** | Commit [`7af289f`](https://github.com/.../handheld-antigravity-toolkit/commit/7af289f) |
| **P1.1** | Discover MicroSD volume UUID dynamically at runtime | Note #6 | ✅ **Done & Pushed** | Commit [`c91236d`](https://github.com/.../handheld-antigravity-toolkit/commit/c91236d) |
| **P1.2** | Back up saves to on-device timestamped archives & `latest/` mirror | Note #6 | ✅ **Done & Pushed** | Commit [`c91236d`](https://github.com/.../handheld-antigravity-toolkit/commit/c91236d) |
| **P1.3** | Sync backup mirror to local PC (`backups/saves/`) & gitignore `backups/` | Note #6 | ✅ **Done & Pushed** | Commit [`c91236d`](https://github.com/.../handheld-antigravity-toolkit/commit/c91236d) |
| **P1.4** | Implement bidirectional save restore CLI (`--restore`, `--restore-target`) | Note #6 | ✅ **Done & Pushed** | Commit [`c91236d`](https://github.com/.../handheld-antigravity-toolkit/commit/c91236d) |
| **P1.5** | End-to-end save restore test with game verification (GT4 / ARM SX2 memcard) | Notes #6 & #8 | 🔄 **Step B.2** | Verified restore byte-for-byte; pending user in-game load confirmation |
| **P2.1** | Build `scripts/snapshot_device.py` (`am force-stop`, pulls 23 targets, `--restore`) | Note #6 | ✅ **Done & Pushed** | Commit [`4be842e`](https://github.com/.../handheld-antigravity-toolkit/commit/4be842e) |
| **P2.2** | Capture golden hardware configuration snapshot from live device | Note #6 | ✅ **Done Locally** | `snapshots/20261016_234208/`, `snapshots/latest/` (gitignored in [`4be842e`](https://github.com/.../handheld-antigravity-toolkit/commit/4be842e)) |
| **P2.3** | Smart key-value `verify_deployment.py` (parsed INI, XML, JSON, `%ROM%` check) | Note #6 | ✅ **Done & Pushed** | Commit [`4be842e`](https://github.com/.../handheld-antigravity-toolkit/commit/4be842e) |
| **P3.1** | Fix `download_retroarch_cores.py` unimported `DEFAULT_SERIAL` & loud failure | Note #6 | ✅ **Done & Pushed** | Commit [`4be842e`](https://github.com/.../handheld-antigravity-toolkit/commit/4be842e) |
| **P3.2** | Add `armsx2_upscale_multiplier` to all device profiles in `profiles/*.json` | Note #6 | ✅ **Done & Pushed** | Commit [`4be842e`](https://github.com/.../handheld-antigravity-toolkit/commit/4be842e) |
| **P3.3** | Purge inline fallback strings (`gcpad_ini`, `wiimote_ini`) in `configure_standalones.py` | Note #6 | ✅ **Done & Pushed** | Commit [`4be842e`](https://github.com/.../handheld-antigravity-toolkit/commit/4be842e) |
| **P3.4** | Deploy captured Dolphin profiles untouched without rewriting `Device = ` | Note #6 | ✅ **Done & Pushed** | Commit [`4be842e`](https://github.com/.../handheld-antigravity-toolkit/commit/4be842e) |
| **P3.5** | Remove redundant `WiimoteSource0..3` from `Dolphin.ini [Core]` | Note #6 | ✅ **Done & Pushed** | Commit [`4be842e`](https://github.com/.../handheld-antigravity-toolkit/commit/4be842e) |
| **P3.6** | Rewrite `README.md` to match tested RP5 environment, snapshot, and save tools | Note #6 | ✅ **Done & Pushed** | Commit [`4b62140`](https://github.com/.../handheld-antigravity-toolkit/commit/4b62140) |
| **OB.1** | Remove PPSSPP from Obtainium (Google Play / web distribution) | Note #7 | ✅ **Done & Pushed** | Commits [`43e9f97`](https://github.com/.../handheld-antigravity-toolkit/commit/43e9f97), [`6d4a6cd`](https://github.com/.../handheld-antigravity-toolkit/commit/6d4a6cd) |
| **OB.2** | Switch Vita3K to `Vita3K/Vita3K` continuous CI release | Note #7 | ✅ **Done & Pushed** | Commits [`43e9f97`](https://github.com/.../handheld-antigravity-toolkit/commit/43e9f97), [`6d4a6cd`](https://github.com/.../handheld-antigravity-toolkit/commit/6d4a6cd) |
| **OB.3** | Set ARM SX2 to stable 2.8.3 (`includePrereleases: false`) | Note #7 | ✅ **Done & Pushed** | Commits [`43e9f97`](https://github.com/.../handheld-antigravity-toolkit/commit/43e9f97), [`6d4a6cd`](https://github.com/.../handheld-antigravity-toolkit/commit/6d4a6cd) |
| **OB.4** | Pin Obtainium APK regex to `^app-arm64-v8a-release\.apk$` | Note #7 | ✅ **Done & Pushed** | Commits [`43e9f97`](https://github.com/.../handheld-antigravity-toolkit/commit/43e9f97), [`6d4a6cd`](https://github.com/.../handheld-antigravity-toolkit/commit/6d4a6cd) |
| **OB.5** | Pin Azahar APK regex to `azahar-android-vanilla.*\.apk$` | Note #7 | ✅ **Done & Pushed** | Commits [`43e9f97`](https://github.com/.../handheld-antigravity-toolkit/commit/43e9f97), [`6d4a6cd`](https://github.com/.../handheld-antigravity-toolkit/commit/6d4a6cd) |
| **OB.6** | Keep Daijishō in catalog per Doug's confirmation | Note #7 | ✅ **Done & Pushed** | Commits [`43e9f97`](https://github.com/.../handheld-antigravity-toolkit/commit/43e9f97), [`6d4a6cd`](https://github.com/.../handheld-antigravity-toolkit/commit/6d4a6cd) |
| **OB.7** | Verify RetroArch Libretro buildbot stable HTML scraper intermediate links | Note #7 | ✅ **Done & Pushed** | Commits [`43e9f97`](https://github.com/.../handheld-antigravity-toolkit/commit/43e9f97), [`6d4a6cd`](https://github.com/.../handheld-antigravity-toolkit/commit/6d4a6cd) |
| **OB.8** | Export verified on-device configs to `configs/obtainium_export.json` & sync master | Note #7 | ✅ **Done & Pushed** | Commits [`43e9f97`](https://github.com/.../handheld-antigravity-toolkit/commit/43e9f97), [`6d4a6cd`](https://github.com/.../handheld-antigravity-toolkit/commit/6d4a6cd) |
| **B.1** | Fix Vita3K Obtainium update tracking (`Vita3K-builds`) & capture working config | Note #8 | ✅ **Done & Pushed** | Commit [`e8bbef3`](https://github.com/.../handheld-antigravity-toolkit/commit/e8bbef3) |
| **B.2** | Live save restore test with game confirmation | Note #8 | 🔄 **Step B.2** | Full backup created (`20261017_081954`); ready for user save selection & restore |
| **B.3** | Replace remaining `<SD_ID>` in `configs/` (`es_settings.xml`, mGBA, DroidDeck, etc.) & update `inspect_save_paths.py` | Note #8 | ✅ **Done & Pushed** | Commit [`1d6235e`](https://github.com/.../handheld-antigravity-toolkit/commit/1d6235e) |
| **B.4** | Phase 4 Device Improvements (RetroArch hotkeys, standalones, drivers, etc.) | Notes #6 & #8 | ✅ **Done & Pushed** | Commits [`1d6235e`](https://github.com/.../handheld-antigravity-toolkit/commit/1d6235e), [`e8bbef3`](https://github.com/.../handheld-antigravity-toolkit/commit/e8bbef3) |
| **B.5** | Write `notes/FINDINGS.md` (plain-language community findings from testing) | Notes #6 & #8 | ✅ **Done & Pushed** | Commit [`1d6235e`](https://github.com/.../handheld-antigravity-toolkit/commit/1d6235e) |
| **C.1** | Write `docs/RELEASE_PLAN.md` (automation taxonomy, RJNY comparison, OS unification, v0.2 capture mode) | Note #8 | ✅ **Done & Pushed** | Commit [`1d6235e`](https://github.com/.../handheld-antigravity-toolkit/commit/1d6235e) |

---

## 🔍 Current Git Working Tree

- **HEAD Commit**: `e8bbef3` (*feat(emulators): deploy verified Vita3K config & Obtainium builds tracking, update Dolphin 3x profile, and scope PS2 readbacks*)
- **Status vs `origin/main`**: Up to date (no unpushed commits)
- **Local Unstaged Changes**: None (clean working tree)

