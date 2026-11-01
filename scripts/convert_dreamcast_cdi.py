#!/usr/bin/env python3
"""
convert_dreamcast_cdi.py
Two-step Dreamcast CDI to CHD converter:
1. Extracts DiscJuggler .cdi tracks via tools/cdirip/cdirip.exe
2. Synthesizes multi-session CUE sheet (REM SESSION, audio/mode2 mapping)
3. Encodes to lossless CHD via tools/chdman/chdman.exe (FLAC audio + LZMA data)
4. Pushes .chd to RP5 MicroSD, verifies, and removes obsolete .cdi
"""

import os
import re
import sys
import shutil
import subprocess
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
CHDMAN = WORKSPACE / "tools" / "chdman" / "chdman.exe"
CDIRIP = WORKSPACE / "tools" / "cdirip" / "cdirip.exe"
STAGING_DIR = WORKSPACE / "scratch" / "dc_staging"

def get_adb_command() -> str:
    local_adb = WORKSPACE / "platform-tools" / "adb.exe"
    if local_adb.exists():
        return str(local_adb)
    return "adb"

def get_device_serial(adb_cmd: str) -> str:
    res = subprocess.run([adb_cmd, "devices"], capture_output=True, text=True)
    lines = [line.strip() for line in res.stdout.strip().splitlines()[1:] if line.strip() and not line.startswith("*")]
    devices = [l.split()[0] for l in lines if "\tdevice" in l]
    if not devices:
        raise RuntimeError("No authorized ADB device found.")
    return devices[0]

def get_micro_sd_id(adb_cmd: str, serial: str) -> str:
    res = subprocess.run([adb_cmd, "-s", serial, "shell", "ls", "/storage"], capture_output=True, text=True)
    for entry in res.stdout.split():
        if len(entry) == 9 and entry[4] == "-":
            return entry
    raise RuntimeError("Could not discover MicroSD card UUID under /storage.")

def build_multisession_cue(extracted_dir: Path) -> Path:
    files = sorted(os.listdir(extracted_dir))
    pattern = re.compile(r"^s(\d+)t(\d+)\.(wav|bin|iso|raw)$", re.IGNORECASE)
    track_files = []
    for f in files:
        m = pattern.match(f)
        if m:
            sess = int(m.group(1))
            trk = int(m.group(2))
            ext = m.group(3).lower()
            track_files.append((sess, trk, ext, f))

    if not track_files:
        raise RuntimeError(f"No tracks extracted by cdirip in {extracted_dir}")

    track_files.sort(key=lambda x: (x[0], x[1]))

    cue_lines = []
    current_sess = None
    for sess, trk, ext, fname in track_files:
        if sess != current_sess:
            current_sess = sess
            cue_lines.append(f"REM SESSION {sess}")

        if ext == "wav":
            cue_lines.append(f'FILE "{fname}" WAVE')
            cue_lines.append(f"  TRACK {trk:02d} AUDIO")
            cue_lines.append("    INDEX 01 00:00:00")
        elif ext == "bin":
            cue_lines.append(f'FILE "{fname}" BINARY')
            cue_lines.append(f"  TRACK {trk:02d} MODE2/2336")
            cue_lines.append("    INDEX 01 00:00:00")
        elif ext == "iso":
            cue_lines.append(f'FILE "{fname}" BINARY')
            cue_lines.append(f"  TRACK {trk:02d} MODE1/2048")
            cue_lines.append("    INDEX 01 00:00:00")
        elif ext == "raw":
            cue_lines.append(f'FILE "{fname}" BINARY')
            cue_lines.append(f"  TRACK {trk:02d} AUDIO")
            cue_lines.append("    INDEX 01 00:00:00")

    cue_path = extracted_dir / "multisession.cue"
    with open(cue_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cue_lines) + "\n")

    return cue_path

def convert_single_cdi(adb_cmd: str, serial: str, remote_cdi_path: str, remote_dir: str):
    fname = Path(remote_cdi_path).name
    stem = Path(remote_cdi_path).stem
    target_chd = f"{stem}.chd"
    remote_chd_path = f"{remote_dir}/{target_chd}"

    print("=" * 60)
    print(f"Processing: {fname} -> {target_chd}")
    print("=" * 60)

    # Check if target CHD already exists on device
    check_res = subprocess.run([adb_cmd, "-s", serial, "shell", f"ls '{remote_chd_path}' 2>/dev/null"], capture_output=True, text=True)
    if remote_chd_path in check_res.stdout:
        print(f"[!] Remote CHD already exists: {remote_chd_path}")
        print(f"[*] Removing redundant remote CDI: {fname}...")
        subprocess.run([adb_cmd, "-s", serial, "shell", f"rm '{remote_cdi_path}'"], check=True)
        print("[+] Done.")
        return

    work_dir = STAGING_DIR / stem
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    local_cdi = work_dir / fname
    out_dir = work_dir / "extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    local_chd = work_dir / target_chd

    try:
        # Step 1: Pull CDI
        t0 = time.time()
        print(f"[*] Step 1: Pulling {fname} from RP5...")
        pull_res = subprocess.run([adb_cmd, "-s", serial, "pull", remote_cdi_path, str(local_cdi)], capture_output=True, text=True)
        if pull_res.returncode != 0 or not local_cdi.exists():
            print(f"[-] Pull failed: {pull_res.stderr}")
            return
        cdi_mb = local_cdi.stat().st_size / (1024 * 1024)
        print(f"[+] Pulled {cdi_mb:.1f} MB in {time.time() - t0:.1f}s")

        # Step 2: Extract tracks via cdirip
        t1 = time.time()
        print("[*] Step 2: Unpacking DiscJuggler tracks with cdirip...")
        rip_res = subprocess.run([str(CDIRIP), str(local_cdi), str(out_dir), "-bin"], capture_output=True, text=True)
        if rip_res.returncode != 0:
            print(f"[-] cdirip failed with return code {rip_res.returncode}:\n{rip_res.stderr}")
            return
        print(f"[+] Extracted in {time.time() - t1:.1f}s")

        # Free local CDI file immediately to save disk
        local_cdi.unlink(missing_ok=True)

        # Step 3: Build multi-session CUE
        cue_path = build_multisession_cue(out_dir)

        # Step 4: Encode to CHD via chdman createcd
        t2 = time.time()
        print(f"[*] Step 3: Compressing to lossless CHD ({target_chd})...")
        cmd_chd = [str(CHDMAN), "createcd", "-i", str(cue_path), "-o", str(local_chd), "-f"]
        chd_res = subprocess.run(cmd_chd, capture_output=True, text=True, cwd=str(out_dir))
        if chd_res.returncode != 0 or not local_chd.exists():
            print(f"[-] chdman failed with return code {chd_res.returncode}:\n{chd_res.stderr}\n{chd_res.stdout}")
            return
        chd_mb = local_chd.stat().st_size / (1024 * 1024)
        ratio = (1.0 - (chd_mb / max(0.1, cdi_mb))) * 100
        print(f"[+] Created {target_chd} ({chd_mb:.1f} MB, {ratio:.1f}% space savings) in {time.time() - t2:.1f}s")

        # Step 5: Push CHD to device
        t3 = time.time()
        print(f"[*] Step 4: Pushing {target_chd} to RP5...")
        push_res = subprocess.run([adb_cmd, "-s", serial, "push", str(local_chd), remote_chd_path], capture_output=True, text=True)
        if push_res.returncode != 0:
            print(f"[-] Push failed: {push_res.stderr}")
            return
        print(f"[+] Pushed in {time.time() - t3:.1f}s")

        # Step 6: Verify remote CHD exists and delete old CDI
        verify_res = subprocess.run([adb_cmd, "-s", serial, "shell", f"ls -l '{remote_chd_path}'"], capture_output=True, text=True)
        if remote_chd_path in verify_res.stdout:
            print(f"[*] Step 5: Verified remote CHD. Removing obsolete CDI: {fname}...")
            subprocess.run([adb_cmd, "-s", serial, "shell", f"rm '{remote_cdi_path}'"], check=True)
            print(f"[+] Successfully converted and removed {fname}!")
        else:
            print(f"[-] Verification failed for {remote_chd_path}, preserving {fname}")

    finally:
        # Cleanup local scratch files
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)

def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    adb_cmd = get_adb_command()
    serial = get_device_serial(adb_cmd)
    sd_id = get_micro_sd_id(adb_cmd, serial)
    dc_remote_dir = f"/storage/{sd_id}/ROMs/dreamcast"
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Target Device: {serial}")
    print(f"MicroSD UUID: {sd_id}")
    print(f"Dreamcast Directory: {dc_remote_dir}")

    # Discover remaining .cdi files
    res = subprocess.run([adb_cmd, "-s", serial, "shell", f"ls '{dc_remote_dir}'/*.cdi 2>/dev/null"], capture_output=True, text=True)
    cdi_remote_paths = [line.strip() for line in res.stdout.splitlines() if line.strip() and line.strip().endswith(".cdi")]

    print(f"Found {len(cdi_remote_paths)} Dreamcast .cdi file(s) to process:\n")
    for p in cdi_remote_paths:
        print(f" - {Path(p).name}")
    print()

    for p in cdi_remote_paths:
        convert_single_cdi(adb_cmd, serial, p, dc_remote_dir)

    print("\n==================================================")
    print("All Dreamcast conversions completed successfully!")
    print("==================================================")

if __name__ == "__main__":
    main()
