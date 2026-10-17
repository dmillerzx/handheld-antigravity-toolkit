# Technical Findings & Architectural Truths: Retroid Pocket 5 Emulation

*This document was compiled through AI-assisted pair programming and empirically verified on a single Retroid Pocket 5 (Qualcomm Snapdragon 865, Android 13). It documents low-level emulator behaviors, configuration schemas, and Android integration facts discovered during live hardware provisioning and testing.*

---

## 1. Dolphin Emulator on Android (Controllers & GameSettings)

### A. Button Token Syntax (`Android.cpp`)
* **Fact**: Dolphin on Android resolves button and axis identifiers strictly via the `KEYCODE_NAMES` mapping table defined in `Source/Core/InputCommon/ControllerInterface/Android/Android.cpp` (upstream Dolphin master).
* **The Numeric Scan-Code Pitfall**: Numeric tokens (such as `Button 96`, `Button 97`, `Axis 22+`) **do not exist** in Dolphin's Android input parser. When written into INIs, Dolphin treats them as unbound tokens or drops them upon saving.
* **Why Older Guides Fail**: Older forum posts, Reddit threads, and community controller packs that reference `Button 96` predate Dolphin's native Android input subsystem overhaul. Modern Dolphin Android requires literal, clean string tokens under an active `Device = ` definition (e.g. `Button A`, `Button B`, `Classic/Buttons/A`).

### B. GameSettings INI Parsing (`GameConfigLoader.cpp`)
* **Fact**: Per-game control overrides are parsed in `Source/Core/Core/ConfigLoaders/GameConfigLoader.cpp`.
* **Valid Keys Under `[Controls]`**:
  - `PadType0` through `PadType3`
  - `WiimoteSource0` through `WiimoteSource3`
  - `PadProfile1` through `PadProfile4`
  - `WiimoteProfile1` through `WiimoteProfile4`
* **Ignored Keys**: `SIDevice0` placed under `[Controls]` in a game INI is **completely ignored** by the loader.
* **Wii Remote Source Architecture**: The Wii Remote source itself lives in `WiimoteNew.ini` under `[Wiimote1] Source`. Binding `WiimoteProfile1 = Classic_Controller` and ensuring `WiimoteSource0 = 1` in the game INI binds the Classic Controller profile directly without corrupting dropdown indices in the GUI.

---

## 2. PlayStation 2: PCSX2, NetherSX2 & ARM SX2

### A. Per-Game Settings & Patch Discovery
* **Upstream PCSX2 Spec**: Per-game settings files are named `SERIAL_CRC.ini` (`VMManager.cpp`) and patches are named `SERIAL_CRC.pnach` (`Patch.cpp`).
* **ARM SX2 Hardware Reality**: On live hardware, ARM SX2 actively discovers and loads patches by **CRC alone** (e.g., `646B2E29.pnach`), verified directly in `emulog.txt`. Deploying patches indexed by CRC guarantees 16:9 widescreen and 60fps code execution regardless of regional serial variations.
* **Gran Turismo 4 Performance Fix**: Gran Turismo 4 experiences severe framerate drops during night races and tunnel sequences on Snapdragon/Adreno hardware because the engine polls the GPU synchronously for ambient brightness. Setting `HardwareDownloadMode = 1` (Disable GS Readbacks) completely eliminates this stutter without visual degradation.

### B. ARM SX2 Distribution & Package Naming
* **Package Split**:
  - Stable releases (e.g., v2.8.3) install as package ID: `com.armsx2`.
  - Nightly automated CI builds install as a completely separate package: `com.armsx2.nightly`.
* **Obtainium Tracking Impact**: Tracking the nightly branch while expecting package `com.armsx2` causes Obtainium package-mismatch errors (#183). Stable releases must be pinned with prereleases disabled (`includePrereleases: false`) to ensure uninterrupted updates.

---

## 3. Android Process Lifecycle & Storage Persistence

### A. The In-Memory Overwrite Rule
* **Fact**: Android emulators (RetroArch, Dolphin, NetherSX2, ARM SX2, DuckStation) hold their configuration state in memory while running or suspended in the background.
* **The Pitfall**: Pushing a modified `.ini` or `.cfg` over ADB while the emulator is active results in silent failure—the emulator overwrites the pushed file with its in-memory state when exiting or switching activities.
* **The Rule**: Always issue `am force-stop <package>` before pulling or pushing any configuration file.

### B. Deterministic Configuration via Hardware Pulls
* **The Rule of Ground Truth**: Emulators frequently re-order INI sections, alter floating-point formatting (`50.` vs `50.000000`), or unquote tokens on save. Hand-crafting text files often leads to syntax incompatibilities.
* **The Reliable Method**:
  1. Set the option directly on the handheld screen once.
  2. Force-stop the app via ADB (`am force-stop <package>`).
  3. Pull the written file over ADB and inspect the exact tokens parsed by the native engine.
  4. Commit that exact file into version control.
