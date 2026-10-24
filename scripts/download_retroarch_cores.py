#!/usr/bin/env python3
"""
Automated RetroArch Core & Asset Provisioning Script for Retroid Pocket 5 (RP5)
-----------------------------------------------------------------------------
Downloads and provisions designated 2D/Arcade cores (Mesen, Snes9x, Gambatte,
mGBA, Genesis Plus GX, PicoDrive, Beetle PCE Fast, Beetle NeoPop, Beetle Cygne,
FBNeo, Stella) and frontend assets (Info, Autoconfig, Slang Shaders) headlessly
over ADB. Strictly excludes 3D platform cores (handled by standalone emulators).
"""

import argparse
import io
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Import dynamic device profiling helper
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import detect_storage_targets, get_connected_serial

BUILDBOT_BASE = "https://buildbot.libretro.com/nightly/android/latest/arm64-v8a/"
ASSETS_BASE = "https://buildbot.libretro.com/assets/frontend/"

DESIGNATED_2D_CORES = [
    ("mesen_libretro_android.so.zip", "NES / Famicom (Mesen)"),
    ("snes9x_libretro_android.so.zip", "SNES / Super Famicom (Snes9x)"),
    ("gambatte_libretro_android.so.zip", "Game Boy / Game Boy Color (Gambatte)"),
    ("mgba_libretro_android.so.zip", "Game Boy Advance (mGBA)"),
    ("genesis_plus_gx_libretro_android.so.zip", "Sega Genesis / Mega Drive (Genesis Plus GX)"),
    ("picodrive_libretro_android.so.zip", "Sega Master System / Genesis / 32X (PicoDrive)"),
    ("mednafen_pce_fast_libretro_android.so.zip", "PC Engine / TurboGrafx-16 (Beetle PCE Fast)"),
    ("mednafen_ngp_libretro_android.so.zip", "Neo Geo Pocket / Color (Beetle NeoPop)"),
    ("mednafen_wswan_libretro_android.so.zip", "WonderSwan / Color (Beetle Cygne)"),
    ("fbneo_libretro_android.so.zip", "Arcade / Neo Geo (FinalBurn Neo)"),
    ("stella_libretro_android.so.zip", "Atari 2600 (Stella)"),
    ("cannonball_libretro_android.so.zip", "OutRun Arcade (CannonBall)"),
]

CORE_ASSETS = [
    ("info.zip", "Core Info Files"),
    ("autoconfig.zip", "Joypad Autoconfig Profiles"),
    ("shaders_slang.zip", "Slang Shaders Suite"),
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


class RetroArchProvisioner:
    def __init__(self, adb_path: str, serial: Optional[str] = None, dry_run: bool = False):
        self.adb = adb_path
        self.serial = serial or get_connected_serial(adb_path)
        self.dry_run = dry_run
        self.staging_dir = WORKSPACE_ROOT / "scratch" / "retroarch_staging"
        self.staging_dir.mkdir(parents=True, exist_ok=True)

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

    def download_file(self, url: str, target_path: Path) -> bool:
        """Downloads a file if not already cached."""
        if target_path.exists() and target_path.stat().st_size > 0:
            print(f"    [OK] Using cached {target_path.name}")
            return True
        print(f"    -> Downloading {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(target_path, "wb") as f:
                f.write(data)
            print(f"    [OK] Downloaded {target_path.name} ({len(data)} bytes)")
            return True
        except Exception as e:
            print(f"    [!] Failed to download {url}: {e}")
            return False

    def fetch_designated_cores(self) -> List[Path]:
        """Downloads the 11 designated 2D/Arcade core zip archives."""
        print("\n[*] Fetching designated 2D/Arcade core suite from Libretro Buildbot...")
        cores_dir = self.staging_dir / "cores"
        cores_dir.mkdir(parents=True, exist_ok=True)
        staged_cores = []

        for zip_name, display_name in DESIGNATED_2D_CORES:
            url = BUILDBOT_BASE + zip_name
            target_zip = cores_dir / zip_name
            if self.download_file(url, target_zip):
                # Extract the .so
                try:
                    with zipfile.ZipFile(target_zip, "r") as z:
                        for item in z.namelist():
                            if item.endswith(".so"):
                                so_path = cores_dir / item
                                with open(so_path, "wb") as f:
                                    f.write(z.read(item))
                                staged_cores.append(so_path)
                except Exception as e:
                    print(f"    [!] Error unpacking {zip_name}: {e}")

        print(f"    -> Successfully staged {len(staged_cores)} 2D/Arcade cores.")
        return staged_cores

    def fetch_assets(self) -> None:
        """Downloads core info, joypad autoconfigs, and slang shaders."""
        print("\n[*] Fetching RetroArch frontend assets (Info, Autoconfig, Slang Shaders)...")
        assets_dir = self.staging_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        for zip_name, display_name in CORE_ASSETS:
            url = ASSETS_BASE + zip_name
            target_zip = assets_dir / zip_name
            self.download_file(url, target_zip)

    def deploy_to_device(self, sd_card_id: Optional[str] = None) -> None:
        """Pushes staged cores and assets to canonical MicroSD and internal paths."""
        print("\n[*] Deploying cores and assets to device storage...")
        internal_root, sd_root, detected_sd_id = detect_storage_targets(self.adb, serial=self.serial, dry_run=self.dry_run)
        resolved_sd_id = sd_card_id or detected_sd_id

        # 1. Push cores
        cores_dir = self.staging_dir / "cores"
        remote_sd_cores = f"/storage/{resolved_sd_id}/RetroArch/cores" if resolved_sd_id else "/sdcard/RetroArch/cores"
        remote_internal_cores = "/sdcard/Android/data/com.retroarch.aarch64/files/cores"
        remote_download_cores = "/sdcard/Download/retroarch_cores"

        self.shell(f"mkdir -p '{remote_sd_cores}' '{remote_internal_cores}' '{remote_download_cores}'", check=False)

        so_files = list(cores_dir.glob("*.so"))
        print(f"    -> Pushing {len(so_files)} core(s) to MicroSD and internal storage...")
        for so in so_files:
            self.adb_cmd("push", str(so), f"{remote_sd_cores}/{so.name}")
            self.adb_cmd("push", str(so), f"{remote_internal_cores}/{so.name}")
            self.adb_cmd("push", str(so), f"{remote_download_cores}/{so.name}")

        # 2. Extract and push Info and Autoconfig assets
        assets_dir = self.staging_dir / "assets"
        target_ra = f"/storage/{resolved_sd_id}/RetroArch" if resolved_sd_id else "/sdcard/RetroArch"
        info_zip = assets_dir / "info.zip"
        if info_zip.exists():
            print("    -> Deploying Core Info Files...")
            self.adb_cmd("push", str(info_zip), f"{target_ra}/info.zip")
            self.shell(f"mkdir -p '{target_ra}/info'; unzip -q -o '{target_ra}/info.zip' -d '{target_ra}/info/' && rm '{target_ra}/info.zip'", check=False)
            self.shell(f"mkdir -p /sdcard/Android/data/com.retroarch.aarch64/files/info; cp -r '{target_ra}/info/'* /sdcard/Android/data/com.retroarch.aarch64/files/info/", check=False)

        autoconfig_zip = assets_dir / "autoconfig.zip"
        if autoconfig_zip.exists():
            print("    -> Deploying Joypad Autoconfig Profiles...")
            self.adb_cmd("push", str(autoconfig_zip), f"{target_ra}/autoconfig.zip")
            self.shell(f"mkdir -p '{target_ra}/autoconfig'; unzip -q -o '{target_ra}/autoconfig.zip' -d '{target_ra}/autoconfig/' && rm '{target_ra}/autoconfig.zip'", check=False)
            self.shell(f"mkdir -p /sdcard/Android/data/com.retroarch.aarch64/files/autoconfig; cp -r '{target_ra}/autoconfig/'* /sdcard/Android/data/com.retroarch.aarch64/files/autoconfig/", check=False)

        shaders_zip = assets_dir / "shaders_slang.zip"
        if shaders_zip.exists():
            print("    -> Deploying Slang Shaders Suite...")
            self.adb_cmd("push", str(shaders_zip), f"{target_ra}/shaders/shaders_slang.zip")
            self.shell(f"mkdir -p '{target_ra}/shaders' && cd '{target_ra}/shaders' && unzip -q -o shaders_slang.zip && rm shaders_slang.zip", check=False)

        print("    [OK] RetroArch cores and frontend assets successfully deployed.")

    def trigger_online_updater_ui(self) -> None:
        """Launches RetroArch and triggers Online Updater components via ADB."""
        print("\n[*] Triggering RetroArch Online Updater sequence via ADB...")
        self.shell("am force-stop com.retroarch.aarch64", check=False)
        time.sleep(1)
        self.shell("am start -n com.retroarch.aarch64/com.retroarch.browser.mainmenu.MainMenuActivity", check=False)
        time.sleep(3)

        # In Ozone UI on 1920x1080:
        # Tap Main Menu left tab at (150, 195)
        self.shell("input tap 150 195", check=False)
        time.sleep(0.5)

        # Tap Online Updater in right list at (600, 750)
        print("    -> Navigating to Online Updater...")
        self.shell("input tap 600 750", check=False)
        time.sleep(1.5)

        # In Online Updater:
        # Tap Update Core Info Files at (600, 320)
        print("    -> Updating Core Info Files in-app...")
        self.shell("input tap 600 320", check=False)
        time.sleep(2)

        # Tap Update Controller Profiles at (600, 600)
        print("    -> Updating Controller Profiles in-app...")
        self.shell("input tap 600 600", check=False)
        time.sleep(2)

        # Return to home
        self.shell("input keyevent 4; input keyevent 4; input keyevent 3", check=False)
        print("    [OK] Online Updater sequence executed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="RetroArch Cores & Assets Provisioner for RP5")
    parser.add_argument("-s", "--serial", default=None, help="Target device serial (auto-detects if omitted)")
    parser.add_argument("--adb", default=None, help="Path to ADB binary")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading from buildbot if cached")
    parser.add_argument("--skip-ui", action="store_true", help="Skip ADB UI interaction")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands without execution")
    args = parser.parse_args()

    adb_path = find_adb(args.adb)
    target_serial = args.serial or get_connected_serial(adb_path)
    provisioner = RetroArchProvisioner(adb_path=adb_path, serial=target_serial, dry_run=args.dry_run)

    if not args.skip_download:
        provisioner.fetch_designated_cores()
        provisioner.fetch_assets()

    provisioner.deploy_to_device()

    if not args.skip_ui:
        provisioner.trigger_online_updater_ui()

    print("\n========================================================================")
    print("   RetroArch 2D Engine & Asset Provisioning Complete!")
    print("========================================================================")


if __name__ == "__main__":
    main()
