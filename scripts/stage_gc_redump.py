#!/usr/bin/env python3
"""
stage_gc_redump.py
Extracts clean Redump GameCube ISOs from 7z downloads, converts them to
1:1 lossless .rvz with dolphin-tool (zstd / 128KB chunking), and pushes to RP5.
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
DOWNLOADS = Path(os.environ.get("USERPROFILE", "")) / "Downloads"
STAGING_DIR = WORKSPACE / "scratch" / "gc_staging"

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

TARGET_GAMES = [
    ("Kirby Air Ride (USA).7z", "Kirby Air Ride (USA).rvz"),
    ("Mario Golf - Toadstool Tour (USA).7z", "Mario Golf - Toadstool Tour (USA).rvz"),
    ("Mario Kart - Double Dash (USA).7z", "Mario Kart - Double Dash!! (USA).rvz"),
]

def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    serial = get_device_serial()
    sd_id = get_micro_sd_id(serial)
    gc_remote_dir = f"/storage/{sd_id}/ROMs/gc"
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Target Device: {serial}")
    print(f"Target Directory: {gc_remote_dir}\n")

    for archive_name, target_rvz_name in TARGET_GAMES:
        archive_path = DOWNLOADS / archive_name
        if not archive_path.exists():
            print(f"[-] Archive not found: {archive_path}")
            continue

        print("==================================================")
        print(f"Processing: {target_rvz_name}")
        print(f"Source: {archive_name} ({archive_path.stat().st_size / (1024*1024):.1f} MB)")
        print("==================================================")

        temp_extract = STAGING_DIR / "temp"
        temp_extract.mkdir(parents=True, exist_ok=True)

        # 1. Extract ISO
        t0 = time.time()
        print(f"[*] Step 1: Extracting {archive_name}...")
        res = subprocess.run(["tar", "-xf", str(archive_path), "-C", str(temp_extract)], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[-] Tar extraction failed: {res.stderr}")
            shutil.rmtree(temp_extract, ignore_errors=True)
            continue
        print(f"[+] Extracted in {time.time() - t0:.1f}s")

        # Find the .iso file
        iso_files = list(temp_extract.glob("*.iso"))
        if not iso_files:
            print(f"[-] No .iso found in extracted contents!")
            shutil.rmtree(temp_extract, ignore_errors=True)
            continue
        extracted_iso = iso_files[0]
        print(f"[+] Found ISO: {extracted_iso.name} ({extracted_iso.stat().st_size / (1024*1024):.1f} MB)")

        # 2. Convert to RVZ via dolphin-tool
        t1 = time.time()
        local_rvz = STAGING_DIR / target_rvz_name
        if local_rvz.exists():
            local_rvz.unlink()

        print(f"[*] Step 2: Converting to 1:1 lossless RVZ (zstd lvl 5, 128KB blocks)...")
        convert_cmd = [
            "npx", "dolphin-tool", "convert",
            "-i", str(extracted_iso),
            "-o", str(local_rvz),
            "-f", "rvz",
            "-c", "zstd",
            "-l", "5",
            "-b", "131072",
        ]
        res_conv = subprocess.run(convert_cmd, capture_output=True, text=True, shell=True)
        if res_conv.returncode != 0 or not local_rvz.exists():
            print(f"[-] dolphin-tool failed: {res_conv.stderr}\n{res_conv.stdout}")
            shutil.rmtree(temp_extract, ignore_errors=True)
            continue

        rvz_mb = local_rvz.stat().st_size / (1024*1024)
        print(f"[+] Created {target_rvz_name} ({rvz_mb:.1f} MB) in {time.time() - t1:.1f}s")

        # Cleanup extracted raw ISO immediately
        shutil.rmtree(temp_extract, ignore_errors=True)

        # 3. Push to RP5 over ADB
        t2 = time.time()
        remote_path = f"{gc_remote_dir}/{target_rvz_name}"
        print(f"[*] Step 3: Pushing {target_rvz_name} to RP5...")
        push_res = subprocess.run(["adb", "-s", serial, "push", str(local_rvz), remote_path], capture_output=True, text=True)
        if push_res.returncode != 0:
            print(f"[-] ADB push failed: {push_res.stderr}")
            continue

        rate = rvz_mb / max(1.0, time.time() - t2)
        print(f"[+] Pushed in {time.time() - t2:.1f}s (~{rate:.1f} MB/s)")

        # Cleanup local RVZ
        local_rvz.unlink()

        # Remote verification
        verify = subprocess.run(["adb", "-s", serial, "shell", f"ls -lh '{remote_path}'"], capture_output=True, text=True)
        print(f"[+] Verified: {verify.stdout.strip()}\n")

    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
    print("==================================================")
    print("GameCube Redump 1:1 Replacement Complete!")
    print("==================================================")

if __name__ == "__main__":
    main()
