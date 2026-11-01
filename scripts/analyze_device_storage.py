#!/usr/bin/env python3
"""
analyze_device_storage.py
Provides a detailed breakdown of internal storage and external MicroSD storage on the RP5.
"""

import subprocess
import sys
from pathlib import Path

def get_device_serial() -> str:
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = [line.strip() for line in res.stdout.strip().splitlines()[1:] if line.strip() and not line.startswith("*")]
    devices = [l.split()[0] for l in lines if "\tdevice" in l]
    if not devices:
        raise RuntimeError("No authorized ADB device found.")
    return devices[0]

def get_micro_sd_id(serial: str) -> str:
    res = subprocess.run(["adb", "-s", serial, "shell", "ls", "/storage"], capture_output=True, text=True)
    for entry in res.stdout.split():
        if len(entry) == 9 and entry[4] == "-":
            return entry
    raise RuntimeError("Could not discover MicroSD card UUID under /storage.")

SERIAL = get_device_serial()
SD_ID = get_micro_sd_id(SERIAL)

def adb(cmd: str) -> str:
    res = subprocess.run(["adb", "-s", SERIAL, "shell", cmd], capture_output=True, text=True)
    return res.stdout.strip()

def format_kb(kb: int) -> str:
    if kb >= 1024 * 1024:
        return f"{kb / (1024 * 1024):.2f} GB"
    elif kb >= 1024:
        return f"{kb / 1024:.1f} MB"
    else:
        return f"{kb} KB"

def parse_du(du_output: str):
    items = []
    for line in du_output.splitlines():
        parts = line.strip().split("\t")
        if len(parts) == 2:
            try:
                kb = int(parts[0])
                path = parts[1]
                items.append((kb, path))
            except ValueError:
                pass
    items.sort(key=lambda x: x[0], reverse=True)
    return items

def main():
    print("==================================================")
    print("RETROID POCKET 5 STORAGE AUDIT & USAGE BREAKDOWN")
    print("==================================================\n")

    # 1. High-level disk stats
    df_out = adb("df -h /data /sdcard /storage/" + SD_ID)
    print("--- High-Level Filesystem Usage ---")
    print(df_out)
    print()

    # 2. dumpsys diskstats
    diskstats = adb("dumpsys diskstats")
    print("--- Android System Diskstats Summary ---")
    for line in diskstats.splitlines():
        line_s = line.strip()
        if any(line_s.startswith(k) for k in [
            "Data-Free", "App Size", "App Data Size", "Photos Size",
            "Videos Size", "Audio Size", "Downloads Size", "System Size"
        ]):
            print(f"  {line_s}")
    print()

    # 3. External MicroSD Top-Level
    print(f"--- External MicroSD (/storage/{SD_ID}) Top-Level Directories ---")
    sd_top = parse_du(adb(f"du -k -d 1 /storage/{SD_ID} 2>/dev/null"))
    for kb, path in sd_top:
        name = Path(path).name or path
        print(f"  {format_kb(kb):>10}  {name}")
    print()

    # 4. External MicroSD ROMs by System
    print(f"--- External MicroSD ROMs by System (/storage/{SD_ID}/ROMs) ---")
    roms_breakdown = parse_du(adb(f"du -k -d 1 /storage/{SD_ID}/ROMs 2>/dev/null"))
    for kb, path in roms_breakdown:
        name = Path(path).name
        if name != "ROMs":
            print(f"  {format_kb(kb):>10}  {name}")
    print()

    # 5. Internal Storage Top-Level (/storage/emulated/0)
    print("--- Internal User Storage (/sdcard) Top-Level Directories ---")
    internal_top = parse_du(adb("du -k -d 1 /storage/emulated/0 2>/dev/null"))
    for kb, path in internal_top:
        name = Path(path).name or path
        print(f"  {format_kb(kb):>10}  {name}")
    print()

    # 6. Internal Android/data by App
    print("--- Internal Android/data Top Space Consumers ---")
    data_apps = parse_du(adb("du -k -d 1 /storage/emulated/0/Android/data 2>/dev/null"))
    for kb, path in data_apps[:15]:
        name = Path(path).name
        if name != "data":
            print(f"  {format_kb(kb):>10}  {name}")
    print()

    # 7. Internal Android/obb by App
    print("--- Internal Android/obb Top Space Consumers ---")
    obb_apps = parse_du(adb("du -k -d 1 /storage/emulated/0/Android/obb 2>/dev/null"))
    for kb, path in obb_apps[:10]:
        name = Path(path).name
        if name != "obb":
            print(f"  {format_kb(kb):>10}  {name}")
    print()

    # 8. ES-DE Media Breakdown on MicroSD
    print(f"--- ES-DE Frontend Data Breakdown (/storage/{SD_ID}/ES-DE) ---")
    esde_breakdown = parse_du(adb(f"du -k -d 1 /storage/{SD_ID}/ES-DE 2>/dev/null"))
    for kb, path in esde_breakdown:
        name = Path(path).name
        if name != "ES-DE":
            print(f"  {format_kb(kb):>10}  {name}")
    print()

    # 9. Top 10 largest files on MicroSD
    print("--- Top 10 Largest Individual Files on MicroSD ---")
    top_sd_files = adb(f"find /storage/{SD_ID}/ROMs -type f -exec ls -s {{}} + 2>/dev/null | sort -nr | head -n 10")
    for line in top_sd_files.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            try:
                kb = int(parts[0])
                name = Path(parts[1]).name
                print(f"  {format_kb(kb):>10}  {name}")
            except ValueError:
                pass
    print()

if __name__ == "__main__":
    main()
