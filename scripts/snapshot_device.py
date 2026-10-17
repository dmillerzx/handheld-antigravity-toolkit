#!/usr/bin/env python3
"""
scripts/snapshot_device.py — Hardware Configuration Snapshot & Restore Engine
=============================================================================
Captures complete, reproducible configuration snapshots from a live Retroid Pocket 5
(or other Android handheld) into timestamped directories under snapshots/<timestamp>/.
Provides bidirectional restoration (--restore) to reinstall a known golden baseline.

Coverage:
- Dolphin: Config/ and GameSettings/
- ARM SX2: inis/, gamesettings/, patches/, cheats/
- NetherSX2: inis/, gamesettings/, patches/, cheats/
- RetroArch: App retroarch.cfg, core options, filters, and SD config/
- ES-DE: settings/
- Obtainium: files/app_data/ (all tracked apps and update manifests)
- DuckStation: settings.ini, gamesettings/, inputprofiles/
- PPSSPP: PSP/SYSTEM/ (ppsspp.ini, controls.ini)
- Flycast: emu.cfg
- Azahar: files/config/
- Vita3K: files/vita/config.yml
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ADB = WORKSPACE_ROOT / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
SNAPSHOTS_ROOT = WORKSPACE_ROOT / "snapshots"

# Ensure device_profile can be imported
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import detect_storage_targets  # type: ignore


def get_connected_serial(adb_path: Path) -> str:
    try:
        out = subprocess.check_output([str(adb_path), "devices"], text=True)
        lines = [line.strip() for line in out.splitlines() if line.strip() and not line.startswith("List of devices")]
        if lines:
            return lines[0].split()[0]
    except Exception:
        pass
    return ""

# All packages to force stop before pulling or restoring
MANAGED_PACKAGES = [
    "org.dolphinemu.dolphinemu",
    "com.armsx2",
    "xyz.aethersx2.android",
    "com.retroarch.aarch64",
    "org.es_de.frontend",
    "dev.imranr.obtainium",
    "com.github.stenzek.duckstation",
    "org.ppsspp.ppsspp",
    "com.flycast.emulator",
    "org.azahar_emu.azahar",
    "org.vita3k.emulator",
    "com.magneticchen.daijishou",
]


class SnapshotEngine:
    def __init__(self, adb_path: Path, serial: Optional[str] = None, dry_run: bool = False):
        self.adb = str(adb_path)
        self.dry_run = dry_run
        self.serial = serial or get_connected_serial(adb_path)
        if not self.serial and not dry_run:
            raise RuntimeError("No ADB device detected. Connect device and enable USB debugging.")

        _, _, self.sd_id = detect_storage_targets(self.adb, self.serial, dry_run=self.dry_run)

    def adb_cmd(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        if self.dry_run:
            print(f"[DRY-RUN] ADB: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)

    def force_stop_all(self) -> None:
        print("[*] Force-stopping emulators and frontends on device...")
        for pkg in MANAGED_PACKAGES:
            self.adb_cmd("shell", "am", "force-stop", pkg)

    def remote_exists(self, remote_path: str) -> bool:
        if self.dry_run:
            return True
        res = self.adb_cmd("shell", f"[ -e '{remote_path}' ] && echo 'EXISTS'")
        return "EXISTS" in res.stdout

    def pull_remote_target(self, remote_path: str, local_dest: Path) -> bool:
        if not self.remote_exists(remote_path):
            return False
        local_dest.parent.mkdir(parents=True, exist_ok=True)
        res = self.adb_cmd("pull", remote_path, str(local_dest))
        return res.returncode == 0

    def push_local_target(self, local_path: Path, remote_dest: str) -> bool:
        if not local_path.exists():
            return False
        # Create remote parent dir
        remote_parent = remote_dest.rsplit("/", 1)[0]
        self.adb_cmd("shell", f"mkdir -p '{remote_parent}'")
        res = self.adb_cmd("push", str(local_path), remote_dest)
        return res.returncode == 0

    def get_snapshot_targets(self) -> List[Dict[str, str]]:
        targets = [
            # Dolphin
            {"name": "dolphin_config", "remote": "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config", "rel_local": "dolphin/Config"},
            {"name": "dolphin_gamesettings", "remote": "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings", "rel_local": "dolphin/GameSettings"},
            # ARM SX2
            {"name": "armsx2_inis", "remote": "/sdcard/Android/data/com.armsx2/files/inis", "rel_local": "armsx2/inis"},
            {"name": "armsx2_gamesettings", "remote": "/sdcard/Android/data/com.armsx2/files/gamesettings", "rel_local": "armsx2/gamesettings"},
            {"name": "armsx2_patches", "remote": "/sdcard/Android/data/com.armsx2/files/patches", "rel_local": "armsx2/patches"},
            {"name": "armsx2_cheats", "remote": "/sdcard/Android/data/com.armsx2/files/cheats", "rel_local": "armsx2/cheats"},
            # NetherSX2
            {"name": "nethersx2_inis", "remote": "/sdcard/Android/data/xyz.aethersx2.android/files/inis", "rel_local": "nethersx2/inis"},
            {"name": "nethersx2_gamesettings", "remote": "/sdcard/Android/data/xyz.aethersx2.android/files/gamesettings", "rel_local": "nethersx2/gamesettings"},
            {"name": "nethersx2_patches", "remote": "/sdcard/Android/data/xyz.aethersx2.android/files/patches", "rel_local": "nethersx2/patches"},
            {"name": "nethersx2_cheats", "remote": "/sdcard/Android/data/xyz.aethersx2.android/files/cheats", "rel_local": "nethersx2/cheats"},
            # RetroArch
            {"name": "retroarch_cfg", "remote": "/sdcard/Android/data/com.retroarch.aarch64/files/retroarch.cfg", "rel_local": "retroarch/retroarch.cfg"},
            {"name": "retroarch_core_options", "remote": "/sdcard/Android/data/com.retroarch.aarch64/files/retroarch-core-options.cfg", "rel_local": "retroarch/retroarch-core-options.cfg"},
            {"name": "retroarch_app_config", "remote": "/sdcard/Android/data/com.retroarch.aarch64/files/config", "rel_local": "retroarch/config"},
            # ES-DE
            {"name": "esde_settings", "remote": "/sdcard/ES-DE/settings", "rel_local": "esde/settings"},
            # Obtainium
            {"name": "obtainium_apps", "remote": "/sdcard/Android/data/dev.imranr.obtainium/files/app_data", "rel_local": "obtainium/app_data"},
            # DuckStation
            {"name": "duckstation_settings", "remote": "/sdcard/Android/data/com.github.stenzek.duckstation/files/settings.ini", "rel_local": "duckstation/settings.ini"},
            {"name": "duckstation_gamesettings", "remote": "/sdcard/Android/data/com.github.stenzek.duckstation/files/gamesettings", "rel_local": "duckstation/gamesettings"},
            {"name": "duckstation_inputprofiles", "remote": "/sdcard/Android/data/com.github.stenzek.duckstation/files/inputprofiles", "rel_local": "duckstation/inputprofiles"},
            # PPSSPP
            {"name": "ppsspp_system", "remote": "/sdcard/PSP/SYSTEM", "rel_local": "ppsspp/SYSTEM"},
            # Flycast
            {"name": "flycast_cfg", "remote": "/sdcard/Android/data/com.flycast.emulator/files/emu.cfg", "rel_local": "flycast/emu.cfg"},
            # Azahar
            {"name": "azahar_config", "remote": "/sdcard/Android/data/org.azahar_emu.azahar/files/config", "rel_local": "azahar/config"},
            # Vita3K
            {"name": "vita3k_cfg", "remote": "/sdcard/Android/data/org.vita3k.emulator/files/vita/config.yml", "rel_local": "vita3k/config.yml"},
        ]

        if self.sd_id:
            targets.append({
                "name": "retroarch_sd_config",
                "remote": f"/storage/{self.sd_id}/RetroArch/config",
                "rel_local": "retroarch_sd/config",
            })

        return targets

    def create_snapshot(self, output_dir: Optional[Path] = None) -> Path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_dir = output_dir or (SNAPSHOTS_ROOT / timestamp)
        target_dir.mkdir(parents=True, exist_ok=True)

        print("\n=======================================================")
        print(f"[*] Creating Device Snapshot: {timestamp}")
        print(f"[*] Serial: {self.serial}")
        print(f"[*] MicroSD UUID: {self.sd_id or 'None'}")
        print(f"[*] Target Directory: {target_dir}")
        print("=======================================================\n")

        self.force_stop_all()

        manifest = {
            "timestamp": timestamp,
            "created_at": datetime.datetime.now().isoformat(),
            "device_serial": self.serial,
            "sd_id": self.sd_id,
            "targets": [],
        }

        results = []
        for target in self.get_snapshot_targets():
            name = target["name"]
            remote = target["remote"]
            rel_local = target["rel_local"]
            dest = target_dir / rel_local

            if self.pull_remote_target(remote, dest):
                results.append((name, remote, "OK", str(dest.relative_to(target_dir))))
                manifest["targets"].append({
                    "name": name,
                    "remote": remote,
                    "rel_local": rel_local,
                    "status": "CAPTURED",
                })
            else:
                results.append((name, remote, "SKIPPED", "Remote target not found or empty"))

        # Write manifest
        manifest_file = target_dir / "snapshot_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # Update snapshots/latest mirror
        latest_dir = SNAPSHOTS_ROOT / "latest"
        try:
            if latest_dir.exists():
                shutil.rmtree(latest_dir)
            shutil.copytree(target_dir, latest_dir)
        except Exception as e:
            print(f"[!] Warning: Could not update snapshots/latest mirror: {e}")

        # Summary Table
        print(f"\n{'Target':<26} | {'Status':<8} | {'Destination / Reason'}")
        print("-" * 80)
        for name, _, status, detail in results:
            print(f"{name:<26} | {status:<8} | {detail}")
        print("-" * 80)
        print(f"\n[SUCCESS] Snapshot created successfully at: {target_dir}")
        print(f"[*] Mirrored to: {latest_dir}\n")
        return target_dir

    def restore_snapshot(self, snapshot_dir: Path) -> bool:
        if not snapshot_dir.is_dir():
            # Check relative to SNAPSHOTS_ROOT
            candidate = SNAPSHOTS_ROOT / snapshot_dir
            if candidate.is_dir():
                snapshot_dir = candidate
            else:
                print(f"[ERROR] Snapshot directory not found: {snapshot_dir}")
                return False

        manifest_file = snapshot_dir / "snapshot_manifest.json"
        if not manifest_file.exists():
            print(f"[ERROR] Snapshot manifest missing: {manifest_file}")
            return False

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        print("\n=======================================================")
        print(f"[*] Restoring Device Snapshot: {snapshot_dir.name}")
        print(f"[*] Manifest Timestamp: {manifest.get('timestamp')}")
        print(f"[*] Target Serial: {self.serial}")
        print("=======================================================\n")

        self.force_stop_all()

        results = []
        all_ok = True
        for target in manifest.get("targets", []):
            name = target["name"]
            remote = target["remote"]
            rel_local = target["rel_local"]
            src = snapshot_dir / rel_local

            # Adjust MicroSD remote path if SD UUID differs
            if "/storage/" in remote and self.sd_id:
                parts = remote.split("/")
                # parts: ['', 'storage', '<SD_ID>', ...]
                if len(parts) > 2 and parts[1] == "storage":
                    remote = f"/storage/{self.sd_id}/" + "/".join(parts[3:])

            if not src.exists():
                results.append((name, remote, "MISSING", f"Local file not found: {src}"))
                all_ok = False
                continue

            if self.push_local_target(src, remote):
                results.append((name, remote, "RESTORED", f"Pushed to {remote}"))
            else:
                results.append((name, remote, "FAILED", f"Push failed to {remote}"))
                all_ok = False

        print(f"\n{'Target':<26} | {'Status':<10} | {'Details'}")
        print("-" * 80)
        for name, _, status, detail in results:
            print(f"{name:<26} | {status:<10} | {detail}")
        print("-" * 80)

        if all_ok:
            print(f"\n[SUCCESS] Snapshot restoration complete for {snapshot_dir.name}\n")
        else:
            print(f"\n[WARNING] One or more targets failed to restore.\n")

        return all_ok


def main():
    parser = argparse.ArgumentParser(description="Retroid Pocket 5 Configuration Snapshot & Restore Utility")
    parser.add_argument("--adb", default=str(DEFAULT_ADB), help="Path to ADB executable")
    parser.add_argument("--serial", "-s", default="", help="Target device serial (auto-detects if omitted)")
    parser.add_argument("--restore", metavar="DIR", help="Restore configurations from a snapshot directory (e.g. latest or 20261017_034500)")
    parser.add_argument("--output-dir", help="Explicit destination directory for snapshot capture")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without modifying files")

    args = parser.parse_args()
    adb_path = Path(args.adb)

    engine = SnapshotEngine(adb_path, serial=args.serial or None, dry_run=args.dry_run)

    if args.restore:
        ok = engine.restore_snapshot(Path(args.restore))
        sys.exit(0 if ok else 1)
    else:
        out_dir = Path(args.output_dir) if args.output_dir else None
        engine.create_snapshot(out_dir)
        sys.exit(0)


if __name__ == "__main__":
    main()
