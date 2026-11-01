#!/usr/bin/env python3
"""
stage_xbox_roms.py
Extracts HDD-ready Xbox 7z archives, packages them into sector-aligned trimmed XDVDFS (.iso)
via extract-xiso, and pushes them directly to the Retroid Pocket 5 MicroSD storage.
"""

import argparse
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
EXTRACT_XISO = WORKSPACE / "tools" / "extract-xiso" / "artifacts" / "extract-xiso.exe"
DOWNLOADS_BASE = Path(os.environ.get("USERPROFILE", "")) / "Downloads" / "XBOX.Collection.878.HDD.Ready"
STAGING_DIR = WORKSPACE / "scratch" / "xbox_staging"

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

GAMES_QUEUE = [
    # (relative_7z_path, target_iso_name)
    ("XBOX HDD ready (#-I) [20140930]/Gunvalkrye [!].7z", "Gunvalkyrie.iso"),
    ("XBOX HDD ready (#-I) [20140930]/Auto Modellista [!].7z", "Auto Modellista.iso"),
    ("XBOX HDD ready (J-Q) [20140930]/Kung Fu Chaos [!].7z", "Kung Fu Chaos.iso"),
    ("XBOX HDD ready (R-Z) [20140930]/SSX 3 [!].7z", "SSX 3.iso"),
    ("XBOX HDD ready (#-I) [20140930]/Amped 2 [!].7z", "Amped 2.iso"),
    ("XBOX HDD ready (#-I) [20140930]/ESPN NHL 2K5 [!].7z", "ESPN NHL 2K5.iso"),
    ("XBOX HDD ready (J-Q) [20140930]/Midnight Club 3 DUB Edition Remix [!].7z", "Midnight Club 3 - DUB Edition Remix.iso"),
    ("XBOX HDD ready (#-I) [20140930]/Halo 2 [!].7z", "Halo 2.iso"),
    ("XBOX HDD ready (R-Z) [20140930]/Sega GT Online [!].7z", "Sega GT Online.iso"),
]

def adb_cmd(serial: str, args):
    cmd = ["adb", "-s", serial] + args
    return subprocess.run(cmd, capture_output=True, text=True)

def find_xbe_root(directory: Path) -> Path:
    """Find directory containing default.xbe."""
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.lower() == "default.xbe":
                return Path(root)
    return None

def process_game(serial: str, remote_xbox_dir: str, archive_rel: str, iso_name: str, index: int, total: int):
    archive_path = DOWNLOADS_BASE / archive_rel
    if not archive_path.exists():
        print(f"[-] [{index}/{total}] Archive not found: {archive_path}")
        return False

    print(f"\n========================================================")
    print(f"[{index}/{total}] Processing: {iso_name}")
    print(f"Source: {archive_path.name} ({archive_path.stat().st_size / (1024*1024):.1f} MB)")
    print(f"========================================================")

    # 1. Check if already on device
    check = adb_cmd(serial, ["shell", f"[ -f '{remote_xbox_dir}/{iso_name}' ] && echo EXISTS || echo MISSING"])
    if "EXISTS" in check.stdout:
        print(f"[!] {iso_name} already exists on device. Skipping.")
        return True

    # 2. Prepare clean staging dir
    extract_target = STAGING_DIR / f"temp_{index}"
    if extract_target.exists():
        shutil.rmtree(extract_target, ignore_errors=True)
    extract_target.mkdir(parents=True, exist_ok=True)

    local_iso = STAGING_DIR / iso_name
    if local_iso.exists():
        local_iso.unlink()

    # 3. Extract 7z archive using bsdtar
    t0 = time.time()
    print(f"[*] Step 1: Extracting {archive_path.name}...")
    res = subprocess.run(["tar", "-xf", str(archive_path), "-C", str(extract_target)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[-] Tar extraction error: {res.stderr}")
        shutil.rmtree(extract_target, ignore_errors=True)
        return False
    print(f"[+] Extracted in {time.time() - t0:.1f}s")

    # 4. Locate default.xbe root
    xbe_dir = find_xbe_root(extract_target)
    if not xbe_dir:
        print(f"[-] Could not find default.xbe in extracted contents!")
        shutil.rmtree(extract_target, ignore_errors=True)
        return False
    print(f"[+] Located game root: {xbe_dir}")

    # 5. Create sector-aligned trimmed XDVDFS (.iso) via extract-xiso
    t1 = time.time()
    print(f"[*] Step 2: Packaging trimmed XDVDFS ISO via extract-xiso...")
    cmd_xiso = [str(EXTRACT_XISO), "-c", str(xbe_dir), str(local_iso)]
    res_xiso = subprocess.run(cmd_xiso, capture_output=True, text=True)
    if res_xiso.returncode != 0 or not local_iso.exists() or local_iso.stat().st_size == 0:
        print(f"[-] extract-xiso failed! {res_xiso.stderr}\n{res_xiso.stdout}")
        shutil.rmtree(extract_target, ignore_errors=True)
        return False

    iso_size_mb = local_iso.stat().st_size / (1024 * 1024)
    print(f"[+] Created {iso_name} ({iso_size_mb:.1f} MB) in {time.time() - t1:.1f}s")

    # Clean extracted folder immediately to save local disk space
    shutil.rmtree(extract_target, ignore_errors=True)

    # 6. Push ISO to RP5 MicroSD over ADB
    t2 = time.time()
    remote_path = f"{remote_xbox_dir}/{iso_name}"
    print(f"[*] Step 3: Pushing {iso_name} to RP5 MicroSD ({remote_path})...")
    push_res = subprocess.run(["adb", "-s", serial, "push", str(local_iso), remote_path], capture_output=True, text=True)
    if push_res.returncode != 0:
        print(f"[-] adb push failed! {push_res.stderr}")
        return False

    rate = (iso_size_mb / max(1.0, time.time() - t2))
    print(f"[+] Pushed in {time.time() - t2:.1f}s (~{rate:.1f} MB/s)")

    # 7. Clean local ISO
    local_iso.unlink()

    # 8. Verify remote file
    verify = adb_cmd(serial, ["shell", f"ls -l '{remote_path}'"])
    print(f"[+] Remote verification: {verify.stdout.strip()}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Batch stage Xbox 7z HDD games to trimmed XDVDFS ISO on RP5")
    parser.add_argument("--serial", "-s", default=None, help="ADB device serial")
    parser.add_argument("--sd-id", default=None, help="MicroSD card UUID")
    args = parser.parse_args()

    serial = args.serial or get_device_serial()
    sd_id = args.sd_id or get_micro_sd_id(serial)
    remote_xbox_dir = f"/storage/{sd_id}/ROMs/xbox"

    print(f"Target Device: {serial}")
    print(f"Target Storage: {remote_xbox_dir}")

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    total = len(GAMES_QUEUE)
    success = 0
    t_start = time.time()

    print(f"Starting batch Xbox game staging: {total} games queued.")
    for idx, (archive, iso_name) in enumerate(GAMES_QUEUE, start=1):
        if process_game(serial, remote_xbox_dir, archive, iso_name, idx, total):
            success += 1
        else:
            print(f"[-] Failed processing {iso_name}")

    # Final cleanup of staging dir
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR, ignore_errors=True)

    print("\n========================================================")
    print(f"Batch Staging Complete: {success}/{total} games staged successfully.")
    print(f"Total time elapsed: {(time.time() - t_start)/60:.1f} minutes")
    print("========================================================")

if __name__ == "__main__":
    main()
