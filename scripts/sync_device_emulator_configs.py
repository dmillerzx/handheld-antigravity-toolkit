#!/usr/bin/env python3
"""
sync_device_emulator_configs.py — Device-to-Host Emulator Configuration Scanner & Backup

Scans the connected Android handheld (RP5) for live emulator configurations
and controller calibrations (PPSSPP, Dolphin, ARM SX2, NetherSX2, DuckStation),
backing them up locally and ensuring host defaults never clobber on-device user customizations.
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def find_adb(explicit_path: Optional[str] = None) -> str:
    if explicit_path and Path(explicit_path).exists():
        return explicit_path
    local_pt = WORKSPACE_ROOT / "platform-tools" / ("adb.exe" if sys.platform == "win32" else "adb")
    if local_pt.exists():
        return str(local_pt)
    which_adb = shutil.which("adb")
    if which_adb:
        return which_adb
    raise FileNotFoundError("Could not find 'adb' binary.")


def get_first_connected_device(adb: str) -> Optional[str]:
    try:
        res = subprocess.run([adb, "devices"], capture_output=True, text=True, check=True)
        for line in res.stdout.splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                return parts[0]
    except Exception:
        pass
    return None


class DeviceConfigScanner:
    def __init__(self, adb: str, serial: Optional[str] = None) -> None:
        self.adb = adb
        self.serial = serial or get_first_connected_device(adb)
        if not self.serial:
            raise RuntimeError("No authorized ADB device connected.")

        self.backup_dir = WORKSPACE_ROOT / "configs" / "backups" / "latest"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def adb_cmd(self, *args) -> subprocess.CompletedProcess:
        cmd = [self.adb, "-s", self.serial] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def file_exists_on_device(self, remote_path: str) -> bool:
        res = self.adb_cmd("shell", f"[ -f '{remote_path}' ] && echo 1 || echo 0")
        return res.stdout.strip() == "1"

    def pull_file(self, remote_path: str, local_path: Path) -> bool:
        if not self.file_exists_on_device(remote_path):
            return False
        local_path.parent.mkdir(parents=True, exist_ok=True)
        res = self.adb_cmd("pull", remote_path, str(local_path))
        return res.returncode == 0

    def sync(self) -> None:
        print(f"[*] Scanning device ({self.serial}) for live emulator configurations & user calibrations...\n")

        targets = [
            # PPSSPP
            {
                "name": "PPSSPP Config",
                "remote": "/sdcard/PSP/SYSTEM/ppsspp.ini",
                "local_backup": self.backup_dir / "ppsspp" / "ppsspp.ini",
                "repo_sync": WORKSPACE_ROOT / "configs" / "backups" / "ppsspp_baseline_20261027" / "ppsspp.ini",
            },
            {
                "name": "PPSSPP Controls",
                "remote": "/sdcard/PSP/SYSTEM/controls.ini",
                "local_backup": self.backup_dir / "ppsspp" / "controls.ini",
                "repo_sync": None,
            },
            # Dolphin
            {
                "name": "Dolphin GC Pad (GCPadNew.ini)",
                "remote": "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/GCPadNew.ini",
                "local_backup": self.backup_dir / "dolphin" / "GCPadNew.ini",
                "repo_sync": WORKSPACE_ROOT / "configs" / "dolphin" / "GCPadNew.ini",
            },
            {
                "name": "Dolphin Wiimote (WiimoteNew.ini)",
                "remote": "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/WiimoteNew.ini",
                "local_backup": self.backup_dir / "dolphin" / "WiimoteNew.ini",
                "repo_sync": WORKSPACE_ROOT / "configs" / "dolphin" / "WiimoteNew.ini",
            },
            {
                "name": "Dolphin Master Config (Dolphin.ini)",
                "remote": "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Dolphin.ini",
                "local_backup": self.backup_dir / "dolphin" / "Dolphin.ini",
                "repo_sync": None,
            },
            {
                "name": "Dolphin Graphics Config (GFX.ini)",
                "remote": "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/GFX.ini",
                "local_backup": self.backup_dir / "dolphin" / "GFX.ini",
                "repo_sync": None,
            },
            # ARM SX2
            {
                "name": "ARM SX2 Controller Calibration (RP5r.ini)",
                "remote": "/sdcard/Android/data/com.armsx2/files/inputprofiles/RP5r.ini",
                "local_backup": self.backup_dir / "armsx2" / "RP5r.ini",
                "repo_sync": None,
            },
            {
                "name": "ARM SX2 Core Settings (armsx2-settings.json)",
                "remote": "/sdcard/Android/data/com.armsx2/files/armsx2-settings.json",
                "local_backup": self.backup_dir / "armsx2" / "armsx2-settings.json",
                "repo_sync": None,
            },
            {
                "name": "ARM SX2 Core INI (PCSX2-Android.ini)",
                "remote": "/sdcard/Android/data/com.armsx2/files/PCSX2-Android.ini",
                "local_backup": self.backup_dir / "armsx2" / "PCSX2-Android.ini",
                "repo_sync": None,
            },
            # NetherSX2
            {
                "name": "NetherSX2 Controller Calibration (RP5r.ini)",
                "remote": "/sdcard/Android/data/xyz.aethersx2.android/files/inputprofiles/RP5r.ini",
                "local_backup": self.backup_dir / "nethersx2" / "RP5r.ini",
                "repo_sync": None,
            },
            # DuckStation
            {
                "name": "DuckStation Config (settings.ini)",
                "remote": "/sdcard/Android/data/com.github.stenzek.duckstation/files/settings.ini",
                "local_backup": self.backup_dir / "duckstation" / "settings.ini",
                "repo_sync": None,
            },
        ]

        synced_count = 0
        for item in targets:
            remote = item["remote"]
            backup = item["local_backup"]
            repo_sync = item["repo_sync"]
            name = item["name"]

            if self.pull_file(remote, backup):
                synced_count += 1
                print(f"  [+] Pulled {name}:")
                print(f"      Remote: {remote}")
                print(f"      Backup: {backup.relative_to(WORKSPACE_ROOT)}")
                if repo_sync:
                    repo_sync.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, repo_sync)
                    print(f"      Synced to repo baseline: {repo_sync.relative_to(WORKSPACE_ROOT)}")
            else:
                print(f"  [-] Skipped {name} (not found on device)")

        # Create timestamp metadata
        meta_file = self.backup_dir / "scan_metadata.txt"
        meta_file.write_text(
            f"Device Serial: {self.serial}\n"
            f"Last Synced: {datetime.now().isoformat()}\n"
            f"Total Configs Synced: {synced_count}\n",
            encoding="utf-8"
        )
        print(f"\n[OK] Successfully scanned and backed up {synced_count} live emulator configurations.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Device-to-Host Emulator Configuration Scanner & Backup")
    parser.add_argument("-s", "--serial", default=None, help="Target device serial")
    parser.add_argument("--adb", default=None, help="Explicit path to adb binary")
    args = parser.parse_args()

    adb = find_adb(args.adb)
    scanner = DeviceConfigScanner(adb=adb, serial=args.serial)
    scanner.sync()


if __name__ == "__main__":
    main()
