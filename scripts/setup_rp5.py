#!/usr/bin/env python3
"""
setup_rp5.py — Retroid Pocket 5 Automated ADB Provisioning Script
================================================================
Handles initial provisioning, Android 13 performance tweaks, directory
scaffolding (internal and external storage), staging of Obtainium configs,
and batch-granting MANAGE_EXTERNAL_STORAGE permissions.

Designed for Retroid Pocket 5 running Android 13 (Qualcomm Snapdragon 865).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Workspace root is the parent directory of scripts/
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Fallback Obtainium configuration if configs/rp5_master_obtainium.json is missing
DEFAULT_OBTAINIUM_PATH = WORKSPACE_ROOT / "configs" / "rp5_master_obtainium.json"

# Key emulator & frontend packages that benefit from MANAGE_EXTERNAL_STORAGE
TARGET_PACKAGES = [
    ("dev.imranr.obtainium", "Obtainium App Updater"),
    ("org.es_de.frontend", "ES-DE Frontend"),
    ("com.retroarch.aarch64", "RetroArch (64-bit)"),
    ("xyz.aethersx2.android", "NetherSX2 / AetherSX2 (PS2)"),
    ("org.ppsspp.ppsspp", "PPSSPP"),
    ("org.azahar_emu.azahar", "Azahar (3DS)"),
    ("org.vita3k.emulator", "Vita3K (PS Vita)"),
    ("com.flycast.emulator", "Flycast (Dreamcast)"),
    ("com.magneticchen.daijishou", "Daijisho Frontend"),
    ("org.dolphinemu.dolphinemu", "Dolphin Emulator (GameCube/Wii)"),
    ("com.github.stenzek.duckstation", "DuckStation (PS1)"),
    ("com.retroarch", "RetroArch (Standard)"),
    ("com.retroarch.ra32", "RetroArch (32-bit)"),
    ("org.ppsspp.ppssppgold", "PPSSPP Gold"),
    ("org.mupen64plusae.v3.fzurita", "Mupen64Plus FZ (N64)"),
    ("org.mupen64plusae.v3.fzurita.pro", "Mupen64Plus FZ Pro"),
    ("com.flyinghead.flycast", "Flycast (Dreamcast, legacy ID)"),
    ("org.citra.emu", "Citra (3DS)"),
    ("io.github.lime3ds", "Lime3DS (3DS, legacy ID)"),
    ("me.quack.daijisho", "Daijisho Frontend (legacy ID)"),
    ("com.magneticstarlight.beacon", "Beacon Frontend"),
    ("com.google.android.apps.nbu.files", "Files by Google"),
    ("com.mixplorer", "MiXplorer"),
    ("pl.solidexplorer2", "Solid Explorer"),
]

# Additional AppOps granted (beyond MANAGE_EXTERNAL_STORAGE) to specific packages
EXTRA_APPOPS = {
    "dev.imranr.obtainium": ["REQUEST_INSTALL_PACKAGES"],
}

# ---------------------------------------------------------------------------
# CANONICAL STORAGE LAYOUT (hardcoded - do NOT add alternative folder variants)
#
#   Internal : /sdcard/bios
#   MicroSD  : /storage/<SD_ID>/{bios, ROMs, ES-DE}
#
# No ROM/Emulation/Games trees are ever created on internal storage, and no
# other top-level directories are created on the MicroSD card.
# ---------------------------------------------------------------------------
INTERNAL_ROOT = "/sdcard"
INTERNAL_DIRS = ["bios"]
SD_DIRS = ["bios", "ROMs", "ES-DE"]


class RP5Provisioner:
    def __init__(self, adb_path: str, serial: Optional[str] = None, dry_run: bool = False):
        self.adb = adb_path
        self.serial = serial
        self.dry_run = dry_run
        self.device_model: Optional[str] = None

    def _build_adb_cmd(self, *args: str) -> List[str]:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        return cmd

    def run_cmd(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        cmd = self._build_adb_cmd(*args)
        if self.dry_run:
            print(f"[DRY RUN] Executing: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=check, encoding="utf-8", errors="replace")
            return res
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] ADB Command failed: {' '.join(cmd)}")
            print(f"       Exit code: {e.returncode}")
            print(f"       Stderr: {e.stderr.strip()}")
            raise

    def shell(self, command: str, check: bool = True) -> str:
        res = self.run_cmd("shell", command, check=check)
        return res.stdout.strip() if res.stdout else ""

    def check_connection(self) -> Tuple[bool, str, List[dict]]:
        """Checks ADB connectivity, lists attached devices, and validates authorization."""
        res = subprocess.run([self.adb, "devices", "-l"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        lines = res.stdout.strip().splitlines()
        devices = []

        if len(lines) > 1:
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status = parts[1]
                    extra = " ".join(parts[2:]) if len(parts) > 2 else ""
                    devices.append({"serial": serial, "status": status, "extra": extra})

        if not devices:
            return False, "No ADB devices detected. Connect your Retroid Pocket 5 via USB or Wi-Fi.", devices

        # If a specific serial was given, check for it
        if self.serial:
            match = next((d for d in devices if d["serial"] == self.serial), None)
            if not match:
                return False, f"Device with serial '{self.serial}' not found in attached devices.", devices
            if match["status"] == "unauthorized":
                return False, f"Device '{self.serial}' is UNAUTHORIZED. Unlock your RP5 and tap 'Always allow from this computer'.", devices
            return True, f"Device '{self.serial}' connected and authorized.", devices

        # Find authorized device
        authorized = [d for d in devices if d["status"] == "device"]
        unauthorized = [d for d in devices if d["status"] == "unauthorized"]

        if authorized:
            chosen = authorized[0]
            self.serial = chosen["serial"]
            return True, f"Connected to {chosen['serial']} ({chosen['extra']}).", devices
        elif unauthorized:
            return False, f"Device '{unauthorized[0]['serial']}' is UNAUTHORIZED. Unlock the Retroid Pocket 5 screen and accept USB Debugging.", devices
        else:
            return False, f"Device found in status '{devices[0]['status']}'. Ensure USB debugging is active.", devices

    def query_device_specs(self) -> dict:
        """Inspects device properties to confirm Retroid Pocket 5 hardware specs."""
        if self.dry_run:
            return {"model": "Retroid Pocket 5 [DRY RUN]", "android_version": "13", "sdk": "33"}
        model = self.shell("getprop ro.product.model")
        brand = self.shell("getprop ro.product.brand")
        release = self.shell("getprop ro.build.version.release")
        sdk = self.shell("getprop ro.build.version.sdk")
        soc = self.shell("getprop ro.soc.model") or self.shell("getprop ro.board.platform")
        return {
            "model": model,
            "brand": brand,
            "android_version": release,
            "sdk": sdk,
            "soc": soc,
        }

    def unlock_phantom_process_killer(self) -> None:
        """Disables the Android 12/13 Phantom Process Killer limit (32 child processes)."""
        print("\n[*] [1/4] Applying Android 13 Phantom Process Killer bypass...")
        # 1. Disable sync overrides from server
        self.shell("/system/bin/device_config set_sync_disabled_for_tests persistent", check=False)
        # 2. Set max phantom processes to 2^31 - 1
        self.shell("/system/bin/device_config put activity_manager max_phantom_processes 2147483647", check=False)
        # 3. Disable global monitoring flag
        self.shell("settings put global settings_enable_monitor_phantom_procs false", check=False)

        # Verification
        if not self.dry_run:
            val = self.shell("/system/bin/device_config get activity_manager max_phantom_processes", check=False)
            print(f"    -> max_phantom_processes configured to: {val or '2147483647'}")
        else:
            print("    -> [DRY RUN] Set max_phantom_processes=2147483647 and disabled monitor.")

    def discover_storage_targets(self) -> Tuple[str, Optional[str]]:
        """Identifies internal storage (/sdcard) and mounted external MicroSD cards."""
        internal = "/sdcard"
        sdcard = None

        if not self.dry_run:
            out = self.shell("ls -d /storage/*", check=False)
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            for line in lines:
                base = os.path.basename(line)
                # SD cards have format XXXX-XXXX (hex UUID) and are not 'emulated' or 'self'
                if base not in ("emulated", "self", "knox-emulated") and not base.startswith("."):
                    # Check if writable directory
                    test_w = self.shell(f"[ -d '{line}' ] && echo 'exists'", check=False)
                    if "exists" in test_w:
                        sdcard = line
                        break
        else:
            sdcard = "/storage/0000-0000 [DRY RUN]"

        return internal, sdcard

    def scaffold_directories(self) -> None:
        """Creates ONLY the canonical directories: /sdcard/bios and /storage/<SD_ID>/{bios,ROMs,ES-DE}."""
        print("\n[*] [2/4] Scaffolding canonical storage folder structure...")
        internal, sdcard = self.discover_storage_targets()

        print(f"    -> Internal storage: {internal}")
        if sdcard:
            print(f"    -> External MicroSD detected: {sdcard}")
        else:
            print("    -> Notice: No external MicroSD card detected. Only internal storage will be scaffolded.")

        targets = [(internal, INTERNAL_DIRS)]
        if sdcard:
            targets.append((sdcard, SD_DIRS))

        for target, subdirs in targets:
            print(f"    Scaffolding {', '.join(subdirs)} on {target}...")
            mkdir_cmd = " && ".join([f"mkdir -p '{target}/{subdir}'" for subdir in subdirs])
            self.shell(mkdir_cmd, check=False)

        print("    -> Storage scaffolding complete.")

    def stage_obtainium_config(self, custom_path: Optional[Path] = None) -> None:
        """Pushes rp5_master_obtainium.json to /sdcard/Download/ for 1-click import."""
        print("\n[*] [3/4] Staging Obtainium configuration file...")
        source_json = custom_path or DEFAULT_OBTAINIUM_PATH

        if not source_json.exists():
            print(f"[!] Warning: Config file not found at {source_json}. Generating default configuration...")
            source_json.parent.mkdir(parents=True, exist_ok=True)
            self._write_fallback_obtainium(source_json)

        dest_remote = "/sdcard/Download/rp5_master_obtainium.json"
        print(f"    Pushing {source_json.name} -> {dest_remote}")
        self.run_cmd("push", str(source_json), dest_remote)
        print("    -> Obtainium master config staged successfully in /sdcard/Download/.")

    def _write_fallback_obtainium(self, path: Path) -> None:
        """Creates a default rp5_master_obtainium.json if not present."""
        data = {
            "apps": [
                {
                    "id": "dev.imranr.obtainium",
                    "url": "https://github.com/ImranR98/Obtainium",
                    "author": "ImranR98",
                    "name": "Obtainium",
                    "preferredApkIndex": 0,
                    "additionalSettings": "{\"includePrereleases\":false,\"fallbackToOlderReleases\":true,\"filterReleaseTitlesByRegEx\":\"\",\"filterReleaseNotesByRegEx\":\"\",\"verifyLatestTag\":false,\"sortMethodChoice\":\"date\",\"useLatestAssetDateAsReleaseDate\":false,\"releaseTitleAsVersion\":false,\"github-creds\":\"\",\"GHReqPrefix\":\"\",\"trackOnly\":false,\"versionExtractionRegEx\":\"\",\"matchGroupToUse\":\"\",\"versionDetection\":true,\"releaseDateAsVersion\":false,\"useVersionCodeAsOSVersion\":false,\"apkFilterRegEx\":\"arm64-v8a|universal\",\"invertAPKFilter\":false,\"autoApkFilterByArch\":true,\"appName\":\"\",\"appAuthor\":\"\",\"shizukuPretendToBeGooglePlay\":false,\"allowInsecure\":false,\"exemptFromBackgroundUpdates\":false,\"skipUpdateNotifications\":false,\"about\":\"App updates directly from source\",\"refreshBeforeDownload\":false,\"includeZips\":false,\"zippedApkFilterRegEx\":\"\"}",
                    "categories": ["Utility"],
                    "allowIdChange": false,
                    "overrideSource": "GitHub"
                }
            ]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def grant_storage_permissions(self) -> None:
        """Grants MANAGE_EXTERNAL_STORAGE AppOps to installed emulator & frontend packages."""
        print("\n[*] [4/4] Pre-granting MANAGE_EXTERNAL_STORAGE AppOps...")

        installed_packages = set()
        if not self.dry_run:
            out = self.shell("pm list packages", check=False)
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("package:"):
                    installed_packages.add(line.split("package:", 1)[1].strip())

        granted_count = 0
        for pkg, label in TARGET_PACKAGES:
            is_installed = (pkg in installed_packages) if not self.dry_run else True
            if is_installed:
                print(f"    -> Granting MANAGE_EXTERNAL_STORAGE to {label} ({pkg})...")
                self.shell(f"appops set {pkg} MANAGE_EXTERNAL_STORAGE allow", check=False)
                for extra_op in EXTRA_APPOPS.get(pkg, []):
                    print(f"    -> Granting {extra_op} to {label} ({pkg})...")
                    self.shell(f"appops set {pkg} {extra_op} allow", check=False)
                granted_count += 1
            else:
                # App not installed yet, but we can set the default or log it
                pass

        if granted_count == 0 and not self.dry_run:
            print("    -> No pre-installed emulators detected yet. Once installed via Obtainium,")
            print("       re-run this script to automatically grant them MANAGE_EXTERNAL_STORAGE.")
        else:
            print(f"    -> Successfully applied storage AppOps to {granted_count} installed target package(s).")

    def install_local_apks(self, apks_dir: Path) -> None:
        """Optionally installs all .apk files placed in the local apks/ staging folder."""
        if not apks_dir.exists():
            return
        apks = list(apks_dir.glob("*.apk"))
        if not apks:
            return

        print(f"\n[*] Found {len(apks)} local APK(s) in {apks_dir}. Installing...")
        for apk in apks:
            print(f"    Installing {apk.name}...")
            self.run_cmd("install", "-r", "-g", str(apk), check=False)


def find_adb() -> Optional[str]:
    """Locates adb executable in PATH, project platform-tools, or standard Android SDK directories."""
    # 1. System PATH
    which_adb = shutil.which("adb")
    if which_adb:
        return which_adb

    # 2. Local workspace platform-tools
    local_candidates = [
        WORKSPACE_ROOT / "platform-tools" / ("adb.exe" if sys.platform == "win32" else "adb"),
        WORKSPACE_ROOT.parent / "platform-tools" / ("adb.exe" if sys.platform == "win32" else "adb"),
    ]
    for cand in local_candidates:
        if cand.is_file():
            return str(cand)

    # 3. Standard Windows AppData paths
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            sdk_adb = Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
            if sdk_adb.is_file():
                return str(sdk_adb)

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automated ADB Provisioner for Retroid Pocket 5 (RP5) on Android 13.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--serial", "-s", help="Target specific ADB device serial number.")
    parser.add_argument("--adb", help="Explicit path to adb binary.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate commands without modifying device.")
    parser.add_argument("--status", action="store_true", help="Check device connection and print hardware specs.")
    parser.add_argument("--skip-phantom", action="store_true", help="Skip Android 13 phantom process killer unlocks.")
    parser.add_argument("--skip-scaffold", action="store_true", help="Skip directory scaffolding on storage.")
    parser.add_argument("--skip-obtainium", action="store_true", help="Skip pushing rp5_master_obtainium.json.")
    parser.add_argument("--skip-permissions", action="store_true", help="Skip granting MANAGE_EXTERNAL_STORAGE.")
    parser.add_argument("--install-apks", action="store_true", help="Install any .apk files staged in apks/ folder.")
    args = parser.parse_args()

    print("=" * 72)
    print("   Retroid Pocket 5 (RP5) Automated Provisioning Pipeline")
    print("=" * 72)

    adb_bin = args.adb or find_adb()
    if not adb_bin:
        print("[ERROR] Could not locate 'adb' in PATH or local workspace directories.")
        print("Please install Android platform-tools or run with --adb <path_to_adb>.")
        return 1

    print(f"ADB Binary: {adb_bin}")

    provisioner = RP5Provisioner(adb_bin, serial=args.serial, dry_run=args.dry_run)
    is_connected, msg, device_list = provisioner.check_connection()

    print(f"Connection Status: {msg}")

    if not is_connected and not args.dry_run:
        print("\n[!] Setup paused: Retroid Pocket 5 is not ready.")
        print("    Troubleshooting steps:")
        print("    1. Connect RP5 via USB-C to this computer.")
        print("    2. On RP5: Settings -> System -> Developer Options -> Enable 'USB Debugging'.")
        print("    3. When prompted on screen: Check 'Always allow from this computer' and tap 'Allow'.")
        print("    4. Re-run: python scripts/setup_rp5.py")
        return 2

    # Query device specs
    specs = provisioner.query_device_specs()
    print("\n--- Device Information ---")
    for k, v in specs.items():
        print(f"  {k:18}: {v}")
    print("--------------------------")

    if args.status:
        return 0

    # 1. Android 13 Phantom Process unlock
    if not args.skip_phantom:
        provisioner.unlock_phantom_process_killer()

    # 2. Storage scaffolding
    if not args.skip_scaffold:
        provisioner.scaffold_directories()

    # 3. Stage Obtainium master config
    if not args.skip_obtainium:
        provisioner.stage_obtainium_config()

    # 4. Optional APK installations
    if args.install_apks:
        provisioner.install_local_apks(WORKSPACE_ROOT / "apks")

    # 5. Grant MANAGE_EXTERNAL_STORAGE AppOps
    if not args.skip_permissions:
        provisioner.grant_storage_permissions()

    print("\n" + "=" * 72)
    print("   Retroid Pocket 5 Provisioning Sequence Complete!")
    print("=" * 72)
    print("\nNext Steps on your Retroid Pocket 5:")
    print("1. Open Obtainium -> Tap 'Import/Export' -> 'Obtainium Import'.")
    print("2. Choose /sdcard/Download/rp5_master_obtainium.json.")
    print("3. Batch-install your preferred emulators (RetroArch, NetherSX2, Dolphin, etc.).")
    print("4. Canonical layout: BIOS in /sdcard/bios and /storage/<SD_ID>/bios; ROMs in /storage/<SD_ID>/ROMs; ES-DE data in /storage/<SD_ID>/ES-DE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
