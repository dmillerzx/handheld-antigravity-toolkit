---
name: rp5-device-control
description: >-
  Deterministic hardware and UI interaction runbook for the Retroid Pocket 5 (RP5).
  Covers OLED display sleep management, UIAutomator XML element interaction (scripts/android_ui.py),
  and kernel evdev controller injection (/dev/input/event8) inside gamescope/PRoot containers.
---

# Retroid Pocket 5 Device Control Skill

This skill provides deterministic commands and protocols for interacting with physical RP5 hardware, preventing screen burn-in, automating Android UI elements without coordinate guessing, and injecting gamepad input into containers.

---

## 1. OLED Display Sleep Management (Burn-in Prevention)

The Retroid Pocket 5 features a 5.5-inch 1080p AMOLED display. To prevent burn-in, the screen must always be powered down when work finishes or when waiting on user input.

### Check Screen State:
```powershell
.\platform-tools\adb.exe -s <SERIAL> shell "dumpsys power | grep -E 'mHoldingDisplay|mWakefulness'"
```
* **Asleep / Safe**: `mWakefulness=Dozing` or `mWakefulness=Asleep`, and `mHoldingDisplaySuspendBlocker=false`.
* **Awake**: `mHoldingDisplaySuspendBlocker=true`.

### Power Down the Screen:
```powershell
.\platform-tools\adb.exe -s <SERIAL> shell "input keyevent 26"
```
Always verify with `dumpsys power` that `mHoldingDisplaySuspendBlocker=false`.

---

## 2. Deterministic Android UI Automation (`scripts/android_ui.py`)

Do not guess pixel coordinates. Use `scripts/android_ui.py` to parse UIAutomator XML hierarchies and calculate exact bounding-box centroids:

```powershell
# 1. Dump visible hierarchy with text, IDs, and bounding boxes
python scripts/android_ui.py --dump

# 2. Click elements by exact text or substring
python scripts/android_ui.py --click-text "Play Steam"
python scripts/android_ui.py --click-contains "Compatibility"

# 3. Deterministically pick files in Android DocumentsUI / SAF pickers
python scripts/android_ui.py --select-file "oot.otr"

# 4. Tap specific centroid and immediately re-dump hierarchy
python scripts/android_ui.py --tap-and-dump 500 500
```

---

## 3. Container & Gamescope Input: Kernel Evdev Injection

Inside containerized environments (DroidDeck, Steam Big Picture, Wine/Proton, Gamescope, Xwayland), standard Android `input tap` commands often fail to reach game surfaces. Use direct Linux kernel input injection via the RP5's controller event node:

* **Input Node**: `/dev/input/event8` (`Xbox Wireless Controller`)
* **Button A (South / Confirm)**:
  ```bash
  sendevent /dev/input/event8 1 304 1; sendevent /dev/input/event8 0 0 0; sleep 0.15; sendevent /dev/input/event8 1 304 0; sendevent /dev/input/event8 0 0 0
  ```
* **Button B (East / Back)**:
  ```bash
  sendevent /dev/input/event8 1 305 1; sendevent /dev/input/event8 0 0 0; sleep 0.15; sendevent /dev/input/event8 1 305 0; sendevent /dev/input/event8 0 0 0
  ```
* **D-Pad Left**:
  ```bash
  sendevent /dev/input/event8 3 16 -1; sendevent /dev/input/event8 0 0 0; sleep 0.1; sendevent /dev/input/event8 3 16 0; sendevent /dev/input/event8 0 0 0
  ```
* **D-Pad Right**:
  ```bash
  sendevent /dev/input/event8 3 16 1; sendevent /dev/input/event8 0 0 0; sleep 0.1; sendevent /dev/input/event8 3 16 0; sendevent /dev/input/event8 0 0 0
  ```
* **D-Pad Down**:
  ```bash
  sendevent /dev/input/event8 3 17 1; sendevent /dev/input/event8 0 0 0; sleep 0.1; sendevent /dev/input/event8 3 17 0; sendevent /dev/input/event8 0 0 0
  ```
* **D-Pad Up**:
  ```bash
  sendevent /dev/input/event8 3 17 -1; sendevent /dev/input/event8 0 0 0; sleep 0.1; sendevent /dev/input/event8 3 17 0; sendevent /dev/input/event8 0 0 0
  ```

---

## 4. Frontend Launch & Dynamic Linker Diagnostics

When a title launched from ES-DE results in an immediate black screen or drops back to the frontend:

1. **Query Linker & App Activity Logs Immediately**:
   ```powershell
   adb -s <serial> shell "logcat -d | grep -iE 'RetroActivity|linker|dlopen|fatal|signal 11' | tail -n 40"
   ```

2. **Diagnose Missing vs. Inaccessible Core**:
   * `dlopen failed: library ".../cores/<core>.so" not found`: The core has not been downloaded inside RetroArch's internal storage (`/data/user/0/com.retroarch.aarch64/cores/`). Direct the user to **Online Updater ➔ Core Downloader** inside RetroArch.
   * `dlopen failed: library ... is not accessible for the namespace: [name="classloader-namespace"]`: ES-DE or an intent passed a path pointing to external storage (`/sdcard/` or `/storage/<SD_ID>/`). The core path in `es_systems.xml` must point to `/data/user/0/com.retroarch.aarch64/cores/<core>.so` and the binary must be installed via RetroArch's internal downloader.

---

## 5. Flutter Accessibility Limitations & Android DocumentsUI SAF Selection

### A. The Flutter SurfaceView `null root node` Phenomenon
Flutter-based Android applications (such as Obtainium `dev.imranr.obtainium`) render their entire UI via Skia/Impeller onto a single hardware `SurfaceView`.
- **UIAutomator Limitation**: Running `uiautomator dump` or `python scripts/android_ui.py --dump` frequently returns:
  ```text
  ERROR: null root node returned by UiTestAutomationBridge
  ```
  This occurs because Flutter does not populate native Android `AccessibilityNodeInfo` trees unless an assistive service (like TalkBack) is active or specific semantic flags are enabled.
- **Deterministic Workaround**:
  1. Do not loop or block waiting for an XML hierarchy dump in Flutter apps.
  2. Use calibrated physical coordinate taps (`input tap X Y`) or hardware navigation keys:
     - Settings gear: `input tap 1010 140`
     - Floating Action Button / Add: `input tap 980 980`
     - Menu items: use `input keyevent 20` (DPAD_DOWN) and `input keyevent 66` (ENTER).

### B. DocumentsUI (SAF) MediaStore Indexing Gate
When automating import/export operations that launch the Android Storage Access Framework picker (`com.google.android.documentsui`):
1. **Pushing Files via ADB**: Files pushed directly to `/sdcard/Download/` or `/storage/<SD_ID>/Downloads/` are invisible to DocumentsUI search queries and "Recent" views until indexed by the Android MediaStore.
2. **Deterministic MediaScanner Broadcast**: Immediately after pushing files intended for SAF file pickers, invoke:
   ```powershell
   adb -s <serial> shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file:///sdcard/Download/<file>"
   ```
3. **DocumentsUI Keyboard/DPAD Navigation**:
   - Focus the file list or search bar using `input keyevent 20` (DPAD_DOWN).
   - Confirm selection using `input keyevent 66` (ENTER) or tap the prominent "USE THIS FOLDER" / "SELECT" button.
   - If importing into Obtainium, pre-synchronizing existing export files located in canonical paths (e.g. `/storage/<SD_ID>/Downloads/obtainium-export.json`) ensures deterministic 1-click restoration.


