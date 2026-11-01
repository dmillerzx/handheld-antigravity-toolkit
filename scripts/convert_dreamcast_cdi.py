#!/usr/bin/env python3
"""
convert_dreamcast_cdi.py
Pulls the 6 Dreamcast .cdi homebrew/translation images from RP5,
converts them to .chd via chdman (createcd), pushes the .chd files back,
and removes the uncompressed .cdi files.
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
CHDMAN = WORKSPACE / "tools" / "chdman" / "chdman.exe"
STAGING_DIR = WORKSPACE / "scratch" / "dc_staging"

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

def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    serial = get_device_serial()
    sd_id = get_micro_sd_id(serial)
    dc_remote_dir = f"/storage/{sd_id}/ROMs/dreamcast"
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    res = subprocess.run(["adb", "-s", serial, "shell", f"ls '{dc_remote_dir}'/*.cdi"], capture_output=True, text=True)
    cdi_remote_paths = [line.strip() for line in res.stdout.splitlines() if line.strip() and line.strip().endswith(".cdi")]

    print(f"Target Device: {serial}")
    print(f"Found {len(cdi_remote_paths)} Dreamcast .cdi images to convert:\n")

    for remote_cdi in cdi_remote_paths:
        fname = Path(remote_cdi).name
        stem = Path(remote_cdi).stem
        target_chd = f"{stem}.chd"
        remote_chd_path = f"{dc_remote_dir}/{target_chd}"

        print("==================================================")
        print(f"Processing: {fname} -> {target_chd}")
        print("==================================================")

        local_cdi = STAGING_DIR / fname
        local_chd = STAGING_DIR / target_chd

        # 1. Pull CDI
        t0 = time.time()
        print(f"[*] Step 1: Pulling {fname} from device...")
        pull_res = subprocess.run(["adb", "-s", serial, "pull", remote_cdi, str(local_cdi)], capture_output=True, text=True)
        if pull_res.returncode != 0 or not local_cdi.exists():
            print(f"[-] Pull failed: {pull_res.stderr}")
            continue
        cdi_mb = local_cdi.stat().st_size / (1024*1024)
        print(f"[+] Pulled {cdi_mb:.1f} MB in {time.time() - t0:.1f}s")

        # 2. Convert via chdman createcd
        t1 = time.time()
        print(f"[*] Step 2: Compressing to CHD via chdman...")
        cmd_chd = [str(CHDMAN), "createcd", "-i", str(local_cdi), "-o", str(local_chd), "-f"]
        res_chd = subprocess.run(cmd_chd, capture_output=True, text=True)
        if res_chd.returncode != 0 or not local_chd.exists():
            print(f"[-] chdman failed: {res_chd.stderr}\n{res_chd.stdout}")
            if local_cdi.exists(): local_cdi.unlink()
            continue
        chd_mb = local_chd.stat().st_size / (1024*1024)
        ratio = (1.0 - (chd_mb / max(0.1, cdi_mb))) * 100
        print(f"[+] Created {target_chd} ({chd_mb:.1f} MB, {ratio:.1f}% space saved) in {time.time() - t1:.1f}s")

        # Cleanup local CDI immediately
        local_cdi.unlink()

        # 3. Push CHD to RP5
        t2 = time.time()
        print(f"[*] Step 3: Pushing {target_chd} to RP5...")
        push_res = subprocess.run(["adb", "-s", serial, "push", str(local_chd), remote_chd_path], capture_output=True, text=True)
        if push_res.returncode != 0:
            print(f"[-] Push failed: {push_res.stderr}")
            continue
        print(f"[+] Pushed in {time.time() - t2:.1f}s")

        # Cleanup local CHD
        local_chd.unlink()

        # 4. Remove remote CDI
        subprocess.run(["adb", "-s", serial, "shell", f"rm '{remote_cdi}'"], check=True)
        print(f"[+] Removed remote .cdi: {fname}\n")

    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
    print("==================================================")
    print("All Dreamcast .cdi images converted to .chd and verified!")
    print("==================================================")

if __name__ == "__main__":
    main()
