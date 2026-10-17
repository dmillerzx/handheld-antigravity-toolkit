#!/usr/bin/env python3
"""
scripts/inspect_save_paths.py — Diagnostic Scanner for Emulator Saves & States
=============================================================================
Dynamically queries all on-device save, savestate, and memory card directories
across internal storage and external MicroSD storage.
"""

import os
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import detect_storage_targets, get_connected_serial  # type: ignore

sys.stdout.reconfigure(encoding="utf-8")

adb_bin = WORKSPACE_ROOT / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
serial = get_connected_serial(adb_bin)
_, _, sd_id = detect_storage_targets(str(adb_bin), serial=serial)

targets = []

if sd_id:
    targets.extend([
        ("RetroArch (MicroSD Saves)", f"/storage/{sd_id}/RetroArch/saves"),
        ("RetroArch (MicroSD States)", f"/storage/{sd_id}/RetroArch/states"),
    ])

targets.extend([
    ("RetroArch (Internal Root Saves)", "/sdcard/RetroArch/saves"),
    ("RetroArch (Internal Root States)", "/sdcard/RetroArch/states"),
    ("RetroArch (App Data Saves)", "/sdcard/Android/data/com.retroarch.aarch64/files/saves"),
    ("RetroArch (App Data States)", "/sdcard/Android/data/com.retroarch.aarch64/files/states"),
    ("Dolphin (GC Memcards)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GC"),
    ("Dolphin (StateSaves)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/StateSaves"),
    ("Dolphin (Wii Saves)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Wii"),
    ("ARM SX2 (Memcards)", "/sdcard/Android/data/com.armsx2/files/memcards"),
    ("ARM SX2 (Savestates)", "/sdcard/Android/data/com.armsx2/files/sstates"),
    ("NetherSX2 (Memcards)", "/sdcard/Android/data/xyz.aethersx2.android/files/memcards"),
    ("NetherSX2 (Savestates)", "/sdcard/Android/data/xyz.aethersx2.android/files/sstates"),
    ("DuckStation (App Data Memcards)", "/sdcard/Android/data/com.github.stenzek.duckstation/files/memcards"),
    ("DuckStation (App Data Savestates)", "/sdcard/Android/data/com.github.stenzek.duckstation/files/savestates"),
    ("DuckStation (Internal Root)", "/sdcard/duckstation/memcards"),
    ("PPSSPP (Root SAVEDATA)", "/sdcard/PSP/SAVEDATA"),
    ("PPSSPP (Root States)", "/sdcard/PSP/PPSSPP_STATE"),
    ("PPSSPP (App Data SAVEDATA)", "/sdcard/Android/data/org.ppsspp.ppsspp/files/PSP/SAVEDATA"),
    ("Azahar (App Data SDMC)", "/sdcard/Android/data/org.azahar_emu.azahar/files/sdmc"),
    ("Azahar (App Data States)", "/sdcard/Android/data/org.azahar_emu.azahar/files/states"),
    ("Flycast (Root Saves/VMU)", "/sdcard/Flycast"),
    ("Flycast (App Data)", "/sdcard/Android/data/com.flycast.emulator/files"),
    ("Vita3K (Savedata)", "/sdcard/Android/data/org.vita3k.emulator/files/vita/ux0/user/00/savedata"),
])

print("=" * 100)
print(f"Device Serial: {serial or 'None'} | MicroSD: {sd_id or 'None'}")
print(f"{'Target Name':<35} | {'Status / File Count':<25} | {'Path'}")
print("=" * 100)

for name, path in targets:
    cmd = [str(adb_bin)]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["shell", f"if [ -d '{path}' ]; then find '{path}' -type f | wc -l; else echo 'NOT_FOUND'; fi"])
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = res.stdout.strip()
    if out == "NOT_FOUND":
        status = "Not Found"
    elif out == "0":
        status = "0 files (empty dir)"
    else:
        status = f"{out} file(s)"
    print(f"{name:<35} | {status:<25} | {path}")

print("=" * 100)
