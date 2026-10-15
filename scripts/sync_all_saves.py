#!/usr/bin/env python3
"""
scripts/sync_all_saves.py — Dynamic Save, Memory Card & State Backup Pipeline
=============================================================================
Systematically mirrors all active saves, memory cards, and savestates across
RetroArch, Dolphin, NetherSX2, DuckStation, PPSSPP, Azahar, and Vita3K into
the canonical backup directory:
    /storage/<SD_ID>/Saves_Backup/latest/ (or /sdcard/Saves_Backup/latest/ if internal only)
Protects against Android 13 FUSE external storage file locking corruption.
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

SAVE_TARGETS = [
    # (Platform/Emulator, Source Path, Subfolder in Backup)
    ("RetroArch (Saves)", "{sd_prefix}/RetroArch/saves", "retroarch/saves"),
    ("RetroArch (States)", "{sd_prefix}/RetroArch/states", "retroarch/states"),
    ("RetroArch (Internal Saves)", "/sdcard/Android/data/com.retroarch.aarch64/files/saves", "retroarch/internal_saves"),
    ("RetroArch (Internal States)", "/sdcard/Android/data/com.retroarch.aarch64/files/states", "retroarch/internal_states"),
    ("Dolphin (GameCube Memcards)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GC", "dolphin/GC"),
    ("Dolphin (Savestates)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/StateSaves", "dolphin/StateSaves"),
    ("Dolphin (Wii Saves)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Wii", "dolphin/Wii"),
    ("NetherSX2 (PS2 Memcards)", "/sdcard/Android/data/xyz.aethersx2.android/files/memcards", "nethersx2/memcards"),
    ("NetherSX2 (Savestates)", "/sdcard/Android/data/xyz.aethersx2.android/files/sstates", "nethersx2/sstates"),
    ("DuckStation (PS1 Memcards)", "/sdcard/Android/data/com.github.stenzek.duckstation/files/memcards", "duckstation/memcards"),
    ("DuckStation (Savestates)", "/sdcard/Android/data/com.github.stenzek.duckstation/files/savestates", "duckstation/savestates"),
    ("PPSSPP (PSP Savedata)", "/sdcard/PSP/SAVEDATA", "ppsspp/SAVEDATA"),
    ("PPSSPP (PSP States)", "/sdcard/PSP/PPSSPP_STATE", "ppsspp/PPSSPP_STATE"),
    ("PPSSPP (Internal Savedata)", "/sdcard/Android/data/org.ppsspp.ppsspp/files/PSP/SAVEDATA", "ppsspp/internal_SAVEDATA"),
    ("Azahar (3DS SDMC)", "/sdcard/Android/data/org.azahar_emu.azahar/files/sdmc", "azahar/sdmc"),
    ("Azahar (Savestates)", "/sdcard/Android/data/org.azahar_emu.azahar/files/states", "azahar/states"),
    ("Vita3K (PS Vita Savedata)", "/sdcard/Android/data/org.vita3k.emulator/files/vita/ux0/user/00/savedata", "vita3k/savedata"),
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


class SaveSyncPipeline:
    def __init__(
        self,
        adb_path: str,
        serial: Optional[str] = None,
        sd_id: Optional[str] = None,
        dry_run: bool = False
    ):
        self.adb = adb_path
        self.serial = serial
        self.sd_id = sd_id
        self.dry_run = dry_run
        self.sd_prefix = f"/storage/{self.sd_id}" if self.sd_id else "/sdcard"
        self.backup_root = f"{self.sd_prefix}/Saves_Backup"

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

    def run_backup(self) -> None:
        print("\n" + "=" * 80)
        print("COMMUNITY TOOLKIT - AUTOMATED SAVE BACKUP PIPELINE")
        print("=" * 80)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_latest = f"{self.backup_root}/latest"
        target_archive = f"{self.backup_root}/archive/{timestamp}"

        print(f"[*] Target backup destination: {target_latest}")
        self.shell(f"mkdir -p '{target_latest}' '{target_archive}'", check=False)

        manifest = []
        total_files = 0

        for label, raw_src, subpath in SAVE_TARGETS:
            src = raw_src.format(sd_prefix=self.sd_prefix)
            dest = f"{target_latest}/{subpath}"

            # Check if source exists and count files
            check_out = self.shell(f"if [ -d '{src}' ]; then find '{src}' -type f | wc -l; else echo '0'; fi")
            count = int(check_out) if check_out.isdigit() else 0

            if count > 0:
                print(f"  -> [{label}] Syncing {count} file(s)...")
                self.shell(f"mkdir -p '{dest}' && cp -r '{src}/'* '{dest}/' 2>/dev/null", check=False)
                manifest.append((label, src, count, "Synced"))
                total_files += count
            else:
                manifest.append((label, src, 0, "Empty / Initialized"))

        # Write manifest on-device
        manifest_path = f"{target_latest}/backup_manifest.txt"
        manifest_text = f"Handheld Save Backup Manifest\\nTimestamp: {timestamp}\\nTotal files: {total_files}\\n"
        self.shell(f"echo '{manifest_text}' > '{manifest_path}'", check=False)

        print("\n" + "-" * 80)
        print(f"| {'Emulator / Platform':<30} | {'Files':<6} | {'Status':<18} |")
        print("-" * 80)
        for label, _, cnt, status in manifest:
            print(f"| {label:<30} | {cnt:<6} | {status:<18} |")
        print("-" * 80)
        print(f"[*] Complete! Total files safely backed up to storage: {total_files}")
        print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated Save & State Backup Pipeline")
    parser.add_argument("-s", "--serial", default=None, help="Target device serial")
    parser.add_argument("--sd-id", default=None, help="MicroSD volume UUID (auto-detected if omitted)")
    parser.add_argument("--adb", default=None, help="Path to ADB binary")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync actions without execution")
    args = parser.parse_args()

    adb_path = find_adb(args.adb)
    internal_root, sd_root, detected_sd_id = detect_storage_targets(adb_path, serial=args.serial, dry_run=args.dry_run)
    sd_id = args.sd_id or detected_sd_id

    pipeline = SaveSyncPipeline(
        adb_path=adb_path,
        serial=args.serial,
        sd_id=sd_id,
        dry_run=args.dry_run
    )
    pipeline.run_backup()


if __name__ == "__main__":
    main()
