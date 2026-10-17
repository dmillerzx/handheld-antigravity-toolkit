#!/usr/bin/env python3
"""
scripts/sync_all_saves.py — Dynamic Save, Memory Card & State Backup & Restore Pipeline
======================================================================================
Systematically mirrors all active saves, memory cards, and savestates across
RetroArch, Dolphin, ARM SX2, NetherSX2, DuckStation, PPSSPP, Azahar, Flycast, and Vita3K into:
  1. MicroSD (or internal): /storage/<SD_ID>/Saves_Backup/latest/
  2. Timestamped on-device archive: /storage/<SD_ID>/Saves_Backup/archive/<timestamp>/
  3. Local PC backup: backups/saves/latest/ and backups/saves/archive/<timestamp>/

Supports bidirectional restore (--restore) to recover saves from latest or any archive.
"""

import argparse
import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Import dynamic device profiling helper
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import detect_storage_targets

EMULATOR_PACKAGES = [
    "org.dolphinemu.dolphinemu",
    "com.armsx2",
    "xyz.aethersx2.android",
    "com.github.stenzek.duckstation",
    "org.ppsspp.ppsspp",
    "org.azahar_emu.azahar",
    "com.flycast.emulator",
    "org.vita3k.emulator",
    "com.retroarch.aarch64",
]

SAVE_TARGETS = [
    # (Platform/Emulator Key, Label, Source Path, Subfolder in Backup)
    ("retroarch", "RetroArch (MicroSD Saves)", "{sd_prefix}/RetroArch/saves", "retroarch/saves"),
    ("retroarch", "RetroArch (MicroSD States)", "{sd_prefix}/RetroArch/states", "retroarch/states"),
    ("retroarch", "RetroArch (Internal Saves)", "/sdcard/RetroArch/saves", "retroarch/internal_saves"),
    ("retroarch", "RetroArch (Internal States)", "/sdcard/RetroArch/states", "retroarch/internal_states"),
    ("retroarch", "RetroArch (App Data Saves)", "/sdcard/Android/data/com.retroarch.aarch64/files/saves", "retroarch/app_saves"),
    ("dolphin", "Dolphin (GameCube Memcards)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GC", "dolphin/GC"),
    ("dolphin", "Dolphin (Savestates)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/StateSaves", "dolphin/StateSaves"),
    ("dolphin", "Dolphin (Wii Saves)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Wii", "dolphin/Wii"),
    ("armsx2", "ARM SX2 (PS2 Memcards)", "/sdcard/Android/data/com.armsx2/files/memcards", "armsx2/memcards"),
    ("armsx2", "ARM SX2 (Savestates)", "/sdcard/Android/data/com.armsx2/files/sstates", "armsx2/sstates"),
    ("nethersx2", "NetherSX2 (PS2 Memcards)", "/sdcard/Android/data/xyz.aethersx2.android/files/memcards", "nethersx2/memcards"),
    ("nethersx2", "NetherSX2 (Savestates)", "/sdcard/Android/data/xyz.aethersx2.android/files/sstates", "nethersx2/sstates"),
    ("duckstation", "DuckStation (PS1 Memcards)", "/sdcard/Android/data/com.github.stenzek.duckstation/files/memcards", "duckstation/memcards"),
    ("duckstation", "DuckStation (Savestates)", "/sdcard/Android/data/com.github.stenzek.duckstation/files/savestates", "duckstation/savestates"),
    ("duckstation", "DuckStation (Root Memcards)", "/sdcard/duckstation/memcards", "duckstation/root_memcards"),
    ("ppsspp", "PPSSPP (Root SAVEDATA)", "/sdcard/PSP/SAVEDATA", "ppsspp/SAVEDATA"),
    ("ppsspp", "PPSSPP (Root States)", "/sdcard/PSP/PPSSPP_STATE", "ppsspp/PPSSPP_STATE"),
    ("ppsspp", "PPSSPP (App Data SAVEDATA)", "/sdcard/Android/data/org.ppsspp.ppsspp/files/PSP/SAVEDATA", "ppsspp/app_SAVEDATA"),
    ("azahar", "Azahar (3DS SDMC)", "/sdcard/Android/data/org.azahar_emu.azahar/files/sdmc", "azahar/sdmc"),
    ("azahar", "Azahar (Savestates)", "/sdcard/Android/data/org.azahar_emu.azahar/files/states", "azahar/states"),
    ("flycast", "Flycast (Root Saves/VMU)", "/sdcard/Flycast", "flycast/Flycast"),
    ("flycast", "Flycast (App Data Files)", "/sdcard/Android/data/com.flycast.emulator/files", "flycast/app_files"),
    ("vita3k", "Vita3K (PS Vita Savedata)", "/sdcard/Android/data/org.vita3k.emulator/files/vita/ux0/user/00/savedata", "vita3k/savedata"),
]


def find_adb(explicit_path: Optional[str] = None) -> str:
    if explicit_path and Path(explicit_path).exists():
        return explicit_path
    adb_which = shutil.which("adb")
    if adb_which:
        return adb_which
    candidates = [
        WORKSPACE_ROOT / "platform-tools" / ("adb.exe" if sys.platform == "win32" else "adb"),
        WORKSPACE_ROOT.parent / "platform-tools" / ("adb.exe" if sys.platform == "win32" else "adb"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise FileNotFoundError("Could not find ADB binary.")


def get_first_connected_device(adb_path: str) -> Optional[str]:
    res = subprocess.run([adb_path, "devices"], capture_output=True, text=True, errors="replace")
    for line in res.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("*") and not line.startswith("List of"):
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                return parts[0]
    return None


class SaveSyncPipeline:
    def __init__(
        self,
        adb_path: str,
        serial: Optional[str] = None,
        sd_id: Optional[str] = None,
        dry_run: bool = False,
        pull_to_pc: bool = True
    ):
        self.adb = adb_path
        self.serial = serial or get_first_connected_device(adb_path)
        self.sd_id = sd_id
        self.dry_run = dry_run
        self.pull_to_pc = pull_to_pc
        self.sd_prefix = f"/storage/{self.sd_id}" if self.sd_id else "/sdcard"
        self.backup_root = f"{self.sd_prefix}/Saves_Backup"
        self.pc_backup_root = WORKSPACE_ROOT / "backups" / "saves"

    def adb_cmd(self, *args, check: bool = True) -> subprocess.CompletedProcess:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(list(args))
        if self.dry_run:
            print(f"[DRY-RUN] {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)

    def shell(self, cmd: str, check: bool = False) -> str:
        res = self.adb_cmd("shell", cmd, check=check)
        return res.stdout.strip() if res.stdout else ""

    def flush_emulators(self) -> None:
        """Force-stop active emulators so memory cards and savedata flush cleanly."""
        print("[*] Flushing active emulator memory cards (force-stopping background instances)...")
        for pkg in EMULATOR_PACKAGES:
            self.shell(f"am force-stop {pkg}", check=False)

    def run_backup(self) -> None:
        print("\n" + "=" * 90)
        print("HANDHELD SAVE & MEMORY CARD BACKUP PIPELINE")
        print("=" * 90)
        print(f"[*] Target Serial : {self.serial or 'Default'}")
        print(f"[*] Storage UUID  : {self.sd_id or 'Internal (/sdcard)'}")
        print(f"[*] On-Device Dest: {self.backup_root}")
        print(f"[*] Local PC Dest : {self.pc_backup_root}")

        self.flush_emulators()

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_latest = f"{self.backup_root}/latest"
        target_archive = f"{self.backup_root}/archive/{timestamp}"

        print(f"\n[*] Creating on-device directories:")
        print(f"    -> Latest : {target_latest}")
        print(f"    -> Archive: {target_archive}")
        self.shell(f"mkdir -p '{target_latest}' '{target_archive}'", check=False)

        manifest = []
        total_files = 0

        print(f"\n[*] Scanning and backing up active save folders...")
        for key, label, raw_src, subpath in SAVE_TARGETS:
            src = raw_src.format(sd_prefix=self.sd_prefix)
            dest_latest = f"{target_latest}/{subpath}"
            dest_archive = f"{target_archive}/{subpath}"

            check_out = self.shell(f"if [ -d '{src}' ]; then find '{src}' -type f | wc -l; else echo '0'; fi")
            count = int(check_out) if check_out.isdigit() else 0

            if count > 0:
                print(f"  -> [{label}] Backing up {count} file(s)...")
                # Copy to both latest and timestamped archive
                self.shell(f"mkdir -p '{dest_latest}' '{dest_archive}' && cp -r '{src}/'* '{dest_latest}/' 2>/dev/null && cp -r '{src}/'* '{dest_archive}/' 2>/dev/null", check=False)
                manifest.append((label, src, count, "Backed Up"))
                total_files += count
            else:
                manifest.append((label, src, 0, "Empty / Initialized"))

        # Write manifest on-device
        manifest_text = f"Handheld Save Backup Manifest\nTimestamp: {timestamp}\nTotal Files: {total_files}\nDevice Serial: {self.serial}\n"
        manifest_text += "-" * 60 + "\n"
        for label, src, cnt, status in manifest:
            manifest_text += f"{label:<35} | {cnt:<5} | {status} | {src}\n"

        self.shell(f"echo '{manifest_text}' > '{target_latest}/backup_manifest.txt'", check=False)
        self.shell(f"echo '{manifest_text}' > '{target_archive}/backup_manifest.txt'", check=False)

        # Pull to Local PC
        if self.pull_to_pc and not self.dry_run:
            print(f"\n[*] Pulling backup mirror to Local PC ({self.pc_backup_root})...")
            pc_latest = self.pc_backup_root / "latest"
            pc_archive = self.pc_backup_root / "archive" / timestamp
            pc_latest.mkdir(parents=True, exist_ok=True)
            pc_archive.mkdir(parents=True, exist_ok=True)

            pull_res = self.adb_cmd("pull", f"{target_latest}/.", str(pc_latest))
            if Path(pc_latest).exists():
                shutil.copytree(pc_latest, pc_archive, dirs_exist_ok=True)
                print(f"    -> PC Latest Backup : {pc_latest}")
                print(f"    -> PC Archive Backup: {pc_archive}")

        print("\n" + "-" * 90)
        print(f"| {'Emulator / Platform':<35} | {'Files':<6} | {'Status':<18} |")
        print("-" * 90)
        for label, _, cnt, status in manifest:
            print(f"| {label:<35} | {cnt:<6} | {status:<18} |")
        print("-" * 90)
        print(f"[*] Complete! Total files safely backed up to device & PC: {total_files}")
        print("=" * 90)

    def run_restore(self, from_source: str = "latest", target_emulator: str = "all") -> None:
        print("\n" + "=" * 90)
        print("HANDHELD SAVE & MEMORY CARD RESTORE PIPELINE")
        print("=" * 90)
        print(f"[*] Target Serial   : {self.serial or 'Default'}")
        print(f"[*] Restore Source  : {from_source}")
        print(f"[*] Target Emulator : {target_emulator}")

        self.flush_emulators()

        if from_source == "latest":
            source_dir = f"{self.backup_root}/latest"
        else:
            source_dir = f"{self.backup_root}/archive/{from_source}"

        # Verify source directory exists on device
        dir_check = self.shell(f"if [ -d '{source_dir}' ]; then echo 'EXISTS'; else echo 'MISSING'; fi")
        if dir_check != "EXISTS":
            print(f"[!] Error: Source backup directory does not exist on device: {source_dir}")
            # Check local PC fallback
            local_fallback = self.pc_backup_root / from_source
            if local_fallback.exists():
                print(f"[*] Found local PC backup at {local_fallback}. Pushing to device first...")
                self.adb_cmd("push", str(local_fallback), source_dir)
            else:
                print(f"[!] Cannot restore. Neither on-device nor PC backup was found for: {from_source}")
                return

        print(f"[*] Restoring from: {source_dir}")
        restored_count = 0

        for key, label, raw_src, subpath in SAVE_TARGETS:
            if target_emulator != "all" and target_emulator.lower() != key.lower():
                continue

            src_folder = f"{source_dir}/{subpath}"
            dest_folder = raw_src.format(sd_prefix=self.sd_prefix)

            # Check if source backup has files
            check_out = self.shell(f"if [ -d '{src_folder}' ]; then find '{src_folder}' -type f | wc -l; else echo '0'; fi")
            count = int(check_out) if check_out.isdigit() else 0

            if count > 0:
                print(f"  -> Restoring [{label}] ({count} file(s)) -> {dest_folder}")
                self.shell(f"mkdir -p '{dest_folder}' && cp -r '{src_folder}/'* '{dest_folder}/'", check=False)
                restored_count += count

        print("\n" + "-" * 90)
        print(f"[*] Restore complete! Total restored files: {restored_count}")
        print("=" * 90)


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated Save & State Backup and Restore Pipeline")
    parser.add_argument("-s", "--serial", default=None, help="Target device serial")
    parser.add_argument("--sd-id", default=None, help="MicroSD volume UUID (auto-detected if omitted)")
    parser.add_argument("--adb", default=None, help="Path to ADB binary")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync actions without execution")
    parser.add_argument("--no-pc", action="store_true", help="Skip pulling backup mirror to local PC")
    parser.add_argument("--restore", action="store_true", help="Execute save restore instead of backup")
    parser.add_argument("--restore-from", default="latest", help="Restore from 'latest' or a timestamp under archive/")
    parser.add_argument("--restore-target", default="all", help="Target emulator key ('all', 'dolphin', 'armsx2', 'retroarch', etc.)")
    args = parser.parse_args()

    adb_path = find_adb(args.adb)
    internal_root, sd_root, detected_sd_id = detect_storage_targets(adb_path, serial=args.serial, dry_run=args.dry_run)
    sd_id = args.sd_id or detected_sd_id

    pipeline = SaveSyncPipeline(
        adb_path=adb_path,
        serial=args.serial,
        sd_id=sd_id,
        dry_run=args.dry_run,
        pull_to_pc=not args.no_pc
    )

    if args.restore:
        pipeline.run_restore(from_source=args.restore_from, target_emulator=args.restore_target)
    else:
        pipeline.run_backup()


if __name__ == "__main__":
    main()
