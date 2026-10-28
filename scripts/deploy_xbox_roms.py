import argparse
import glob
import os
import shutil
import subprocess
import sys

def detect_device(serial: str = None) -> str:
    if serial:
        return serial
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = [line.strip() for line in res.stdout.strip().splitlines()[1:] if line.strip()]
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            return parts[0]
    return ""

def detect_sd_id(serial: str) -> str:
    cmd = ["adb"]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["shell", "ls -d /storage/????-???? 2>/dev/null"])
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in res.stdout.strip().splitlines():
        line = line.strip()
        if line.startswith("/storage/"):
            return os.path.basename(line)
    return ""
EXTRACT_XISO = os.path.abspath("tools/extract-xiso/artifacts/extract-xiso.exe")
SCRATCH_DIR = os.path.abspath("scratch/xbox_batch")

# Mapping from source 7z archive name to clean canonical game title
GAME_NAMES = {
    "Bloody Roar Extreme [!].7z": "Bloody Roar Extreme.iso",
    "Castlevania - Curse of Darkness [!].7z": "Castlevania - Curse of Darkness.iso",
    "Crazy taxi 3 [!].7z": "Crazy Taxi 3 - High Roller.iso",
    "Crimson skies [!].7z": "Crimson Skies - High Road to Revenge.iso",
    "Dead Or Alive Extreme Beach Volleyball [!].7z": "Dead or Alive Xtreme Beach Volleyball.iso",
    "Jet Set Radio Future [!].7z": "Jet Set Radio Future.iso",
    "Marvel Vs Capcom 2 [!].7z": "Marvel vs. Capcom 2.iso",
    "NBA Jam [!].7z": "NBA Jam.iso",
    "OutRun 2006 - Coast 2 Coast [!].7z": "OutRun 2006 - Coast 2 Coast.iso",
    "SSX Tricky [!].7z": "SSX Tricky.iso",
    "Top Spin [!].7z": "Top Spin.iso",
}

def get_remote_files(serial: str, remote_dir: str):
    cmd = ["adb"]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["shell", f"ls '{remote_dir}' 2>/dev/null"])
    res = subprocess.run(cmd, capture_output=True, text=True)
    return [f.strip() for f in res.stdout.strip().splitlines() if f.strip()]

def main():
    parser = argparse.ArgumentParser(description="Automated Xbox ROM Repackaging & Deployment Pipeline")
    parser.add_argument("--serial", "-s", default="", help="Target ADB device serial")
    parser.add_argument("--sd-id", default="", help="External MicroSD UUID (e.g. XXXX-XXXX)")
    args = parser.parse_args()

    serial = detect_device(args.serial)
    if not serial:
        print("Error: No ADB device detected.")
        sys.exit(1)

    sd_id = args.sd_id or detect_sd_id(serial)
    if not sd_id:
        print("Error: Could not detect external MicroSD card UUID.")
        sys.exit(1)

    remote_dir = f"/storage/{sd_id}/ROMs/xbox/"
    print(f"Target Device: {serial}")
    print(f"Target SD Storage: {remote_dir}")

    if not os.path.isfile(EXTRACT_XISO):
        print(f"Error: extract-xiso not found at {EXTRACT_XISO}")
        sys.exit(1)

    existing_remote = get_remote_files(serial, remote_dir)
    print(f"Currently on RP5 MicroSD: {existing_remote}")

    os.makedirs(SCRATCH_DIR, exist_ok=True)
    archives = sorted(glob.glob("roms/xbox/*.7z"))

    for arch in archives:
        base = os.path.basename(arch)
        target_name = GAME_NAMES.get(base, base.replace("[!]", "").replace(".7z", ".iso").strip())
        print(f"\n=======================================================")
        print(f"Processing: {base} -> {target_name}")
        print(f"=======================================================")

        if target_name in existing_remote:
            print(f"Skipping {target_name} (already on device)")
            continue

        work_extract = os.path.join(SCRATCH_DIR, "extracted")
        if os.path.exists(work_extract):
            shutil.rmtree(work_extract)
        os.makedirs(work_extract, exist_ok=True)

        print(f"1. Unpacking {base} via tar...")
        res = subprocess.run(["tar.exe", "-xf", arch, "-C", work_extract])
        if res.returncode != 0:
            print(f"Failed to unpack {base}")
            continue

        # Locate default.xbe
        xbe_folder = None
        for root, dirs, files in os.walk(work_extract):
            if any(f.lower() == "default.xbe" for f in files):
                xbe_folder = root
                break

        if not xbe_folder:
            print(f"Error: default.xbe not found in {base}!")
            shutil.rmtree(work_extract, ignore_errors=True)
            continue

        print(f"Found game root: {xbe_folder}")
        target_iso = os.path.join(SCRATCH_DIR, target_name)
        if os.path.exists(target_iso):
            os.remove(target_iso)

        print(f"2. Building XDVDFS ISO: {target_iso}...")
        res = subprocess.run([EXTRACT_XISO, "-c", xbe_folder, target_iso])
        if res.returncode != 0:
            print(f"Failed to create XISO for {base}")
            shutil.rmtree(work_extract, ignore_errors=True)
            continue

        iso_size_mb = os.path.getsize(target_iso) / (1024 * 1024)
        print(f"Created XISO successfully ({iso_size_mb:.2f} MB)")

        print("3. Pushing to RP5 MicroSD card...")
        push_cmd = ["adb"]
        if serial:
            push_cmd.extend(["-s", serial])
        push_cmd.extend(["push", target_iso, remote_dir])
        res = subprocess.run(push_cmd)
        if res.returncode != 0:
            print(f"Failed to push {target_iso} to device!")
            continue

        # Cleanup scratch space for this title
        print("4. Cleaning up local scratch space...")
        shutil.rmtree(work_extract, ignore_errors=True)
        if os.path.exists(target_iso):
            os.remove(target_iso)
        existing_remote.append(target_name)
        print(f"Finished {target_name} successfully!")

    print("\nAll Xbox ROMs processed!")

if __name__ == "__main__":
    main()
