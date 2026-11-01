#!/usr/bin/env python3
"""
fix_n64_roms.py
Inspects .n64 files in RP5 ROMs/n64, byte-swaps .v64 / .n64 to native big-endian .z64,
and renames already big-endian .n64 files to .z64.
"""

import subprocess
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

def byteswap_v64_to_z64(data: bytearray) -> bytearray:
    # Doctor V64 (37 80 40 12) -> Big Endian (80 37 12 40)
    # Swap adjacent bytes
    data[0::2], data[1::2] = data[1::2], data[0::2]
    return data

def main():
    serial = get_device_serial()
    sd_id = get_micro_sd_id(serial)
    n64_dir = f"/storage/{sd_id}/ROMs/n64"
    staging_dir = Path(__file__).resolve().parent.parent / "scratch" / "n64_fix"
    staging_dir.mkdir(parents=True, exist_ok=True)

    res = subprocess.run(["adb", "-s", serial, "shell", f"ls '{n64_dir}'"], capture_output=True, text=True)
    n64_files = [f.strip() for f in res.stdout.splitlines() if f.strip().endswith(".n64")]

    print(f"Found {len(n64_files)} .n64 files to process:")
    for fname in n64_files:
        remote_path = f"{n64_dir}/{fname}"
        cmd_head = ["adb", "-s", serial, "shell", f"head -c 4 '{remote_path}' | xxd -p"]
        magic = subprocess.run(cmd_head, capture_output=True, text=True).stdout.strip().replace("\n", "").replace("\r", "")

        stem = fname[:-4]
        target_z64 = f"{stem}.z64"
        remote_target = f"{n64_dir}/{target_z64}"

        if magic.startswith("80371240"):
            print(f"[+] {fname} is already native big-endian. Renaming to {target_z64}...")
            subprocess.run(["adb", "-s", serial, "shell", f"mv '{remote_path}' '{remote_target}'"], check=True)
        elif magic.startswith("37804012"):
            print(f"[*] {fname} is byte-swapped (.v64). Pulling and converting to {target_z64}...")
            local_in = staging_dir / fname
            local_out = staging_dir / target_z64
            subprocess.run(["adb", "-s", serial, "pull", remote_path, str(local_in)], check=True)
            
            ba = bytearray(local_in.read_bytes())
            byteswap_v64_to_z64(ba)
            local_out.write_bytes(ba)
            
            # Push back
            subprocess.run(["adb", "-s", serial, "push", str(local_out), remote_target], check=True)
            # Remove old remote .n64
            subprocess.run(["adb", "-s", serial, "shell", f"rm '{remote_path}'"], check=True)
            
            local_in.unlink()
            local_out.unlink()
            print(f"[+] Converted and replaced with {target_z64}")
        else:
            print(f"[-] Unknown magic {magic} for {fname}. Skipping.")

    print("\nAll N64 files standardized to native big-endian .z64!")

if __name__ == "__main__":
    main()
