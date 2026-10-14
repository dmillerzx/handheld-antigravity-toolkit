#!/usr/bin/env python3
"""
scripts/stage_community_patches.py — Universal PS2 & GameCube/Wii Community Patch Engine
======================================================================================
Automates downloading, parsing, curating, and deploying:
1. PS2 (NetherSX2 / PCSX2):
   - Downloads official pcsx2_patches master archive (3,500+ widescreen/60fps .pnach cheats).
   - Unpacks into local patches/ps2/ staging directory.
   - Pushes complete collection to both NetherSX2 patches/ and cheats/ directories.
2. GameCube & Wii (Dolphin):
   - Pulls master GameSettings from upstream dolphin-emu/dolphin (Data/Sys/GameSettings/).
   - Parses [Gecko] blocks, detects all 16:9 widescreen codes, injects them into
     [Gecko_Enabled], and sets [Video_Settings] AspectRatio = 1.
   - Merges curated custom Gecko patches from patches/gcn/*.ini.
   - Pushes full curated catalog to Dolphin GameSettings/.
"""

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SERIAL = "ff152647"

PCSX2_PATCHES_URL = "https://github.com/PCSX2/pcsx2_patches/releases/latest/download/patches.zip"
DOLPHIN_REPO_URL = "https://github.com/dolphin-emu/dolphin.git"

RE_169_CODE = re.compile(r"^\$(16:9\s*(?:Widescreen|Aspect Ratio Fix)[^\r\n]*)", re.IGNORECASE)


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
        if c.is_file():
            return str(c)
    raise FileNotFoundError("Could not find ADB binary.")


def find_git() -> str:
    git_which = shutil.which("git")
    if git_which:
        return git_which
    candidates = [
        Path(r"C:\Program Files\Git\cmd\git.exe"),
        Path(r"C:\Program Files\Git\bin\git.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return "git"


class CommunityPatchEngine:
    def __init__(self, adb_path: str, serial: str = DEFAULT_SERIAL, dry_run: bool = False):
        self.adb = adb_path
        self.serial = serial
        self.dry_run = dry_run
        self.scratch_dir = WORKSPACE_ROOT / "scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        self.ps2_local_dir = WORKSPACE_ROOT / "patches" / "ps2"
        self.ps2_local_dir.mkdir(parents=True, exist_ok=True)
        self.gcn_local_dir = WORKSPACE_ROOT / "patches" / "gcn"
        self.gcn_local_dir.mkdir(parents=True, exist_ok=True)

    def adb_cmd(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        cmd = [self.adb, "-s", self.serial] + list(args)
        if self.dry_run:
            print(f"[DRY-RUN] {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        try:
            return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] ADB command failed: {' '.join(cmd)}")
            print(f"       Stderr: {e.stderr.strip() if e.stderr else ''}")
            raise

    def shell(self, cmd: str, check: bool = False) -> str:
        res = self.adb_cmd("shell", cmd, check=check)
        return res.stdout.strip() if res.stdout else ""

    # =========================================================================
    # PS2 (NetherSX2 / PCSX2) PATCH ENGINE
    # =========================================================================
    def stage_ps2_patches(self) -> int:
        """Downloads, unpacks, and stages PCSX2 master .pnach patches."""
        print("\n[*] [1/2] Processing PS2 (NetherSX2 / PCSX2) Master Community Patches...")

        # 1. Check if local patches/ps2 already has pnach files or download
        existing_pnach = list(self.ps2_local_dir.glob("*.pnach"))
        zip_target = self.scratch_dir / "pcsx2_patches.zip"

        if len(existing_pnach) < 1000:
            print(f"    -> Downloading master patches archive from {PCSX2_PATCHES_URL}...")
            req = urllib.request.Request(PCSX2_PATCHES_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(zip_target, "wb") as f:
                f.write(data)
            print(f"    -> Downloaded {len(data)} bytes. Unpacking to {self.ps2_local_dir}...")

            with zipfile.ZipFile(zip_target, "r") as z:
                for member in z.namelist():
                    if member.endswith(".pnach"):
                        content = z.read(member)
                        out_name = os.path.basename(member)
                        with open(self.ps2_local_dir / out_name, "wb") as f:
                            f.write(content)

            existing_pnach = list(self.ps2_local_dir.glob("*.pnach"))

        print(f"    -> Staged {len(existing_pnach)} .pnach patches in local {self.ps2_local_dir.name}/.")

        # 2. Package into tarball for fast ADB deployment
        tar_path = self.scratch_dir / "ps2_patches.tar.gz"
        print(f"    -> Packaging {len(existing_pnach)} patches into {tar_path.name}...")
        with tarfile.open(tar_path, "w:gz") as tar:
            for pnach in existing_pnach:
                tar.add(pnach, arcname=pnach.name)

        # 3. Push and unpack over ADB to NetherSX2 patches/ and cheats/
        remote_tar = "/sdcard/Download/ps2_patches.tar.gz"
        remote_patches_dir = "/sdcard/Android/data/xyz.aethersx2.android/files/patches"
        remote_cheats_dir = "/sdcard/Android/data/xyz.aethersx2.android/files/cheats"

        print(f"    -> Deploying patches to NetherSX2 ({remote_patches_dir} and {remote_cheats_dir})...")
        self.adb_cmd("push", str(tar_path), remote_tar)

        extract_cmd = (
            f"mkdir -p '{remote_patches_dir}' '{remote_cheats_dir}' && "
            f"tar -xzf '{remote_tar}' -C '{remote_patches_dir}/' && "
            f"tar -xzf '{remote_tar}' -C '{remote_cheats_dir}/' && "
            f"rm '{remote_tar}'"
        )
        self.shell(extract_cmd, check=False)
        print(f"    [OK] Successfully deployed {len(existing_pnach)} PS2 patches to NetherSX2.")
        return len(existing_pnach)

    # =========================================================================
    # GAMECUBE & WII (DOLPHIN) PATCH ENGINE
    # =========================================================================
    def stage_dolphin_gamesettings(self) -> int:
        """Pulls upstream Dolphin GameSettings, injects 16:9 widescreen Gecko codes, and deploys."""
        print("\n[*] [2/2] Processing GameCube & Wii (Dolphin) Master GameSettings & Widescreen Patches...")

        # 1. Fetch upstream Dolphin GameSettings via sparse-checkout
        git_bin = find_git()
        dolphin_sparse_dir = self.scratch_dir / "dolphin_temp"
        source_gamesettings = dolphin_sparse_dir / "Data" / "Sys" / "GameSettings"

        if not source_gamesettings.exists() or len(list(source_gamesettings.glob("*.ini"))) < 1000:
            print("    -> Pulling master GameSettings from upstream dolphin-emu/dolphin...")
            if dolphin_sparse_dir.exists():
                shutil.rmtree(dolphin_sparse_dir, ignore_errors=True)

            # Clone with blob filter and sparse checkout
            clone_cmd = [git_bin, "clone", "--filter=blob:none", "--no-checkout", "--depth", "1", DOLPHIN_REPO_URL, str(dolphin_sparse_dir)]
            subprocess.run(clone_cmd, capture_output=True, text=True, check=True)
            subprocess.run([git_bin, "-C", str(dolphin_sparse_dir), "sparse-checkout", "set", "Data/Sys/GameSettings"], capture_output=True, text=True, check=True)
            subprocess.run([git_bin, "-C", str(dolphin_sparse_dir), "checkout"], capture_output=True, text=True, check=True)

        all_inis = list(source_gamesettings.glob("*.ini"))
        print(f"    -> Found {len(all_inis)} upstream Dolphin GameSettings INI files.")

        # 2. Curate and inject 16:9 Gecko codes
        curated_dir = self.scratch_dir / "curated_dolphin_gamesettings"
        curated_dir.mkdir(parents=True, exist_ok=True)
        widescreen_injected_count = 0

        for ini_path in all_inis:
            content = ini_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            in_gecko = False
            widescreen_codes = []

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    in_gecko = (stripped.lower() == "[gecko]")
                elif in_gecko and stripped.startswith("$"):
                    if RE_169_CODE.match(stripped) or ("16:9" in stripped and "widescreen" in stripped.lower()):
                        widescreen_codes.append(stripped)

            if widescreen_codes:
                widescreen_injected_count += 1
                selected_code = widescreen_codes[0]
                for c in widescreen_codes:
                    if "normal hud" in c.lower() or c.strip() == "$16:9 Widescreen":
                        selected_code = c
                        break

                new_lines = []
                has_video_settings = False
                has_gecko_enabled = False
                in_video_settings = False
                in_gecko_enabled = False
                aspect_ratio_set = False
                code_enabled = False

                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("[") and stripped.endswith("]"):
                        sec = stripped.lower()
                        if in_video_settings and not aspect_ratio_set:
                            new_lines.append("AspectRatio = 1")
                            aspect_ratio_set = True
                        if in_gecko_enabled and not code_enabled:
                            new_lines.append(selected_code)
                            code_enabled = True

                        in_video_settings = (sec == "[video_settings]")
                        in_gecko_enabled = (sec == "[gecko_enabled]")
                        if in_video_settings:
                            has_video_settings = True
                        if in_gecko_enabled:
                            has_gecko_enabled = True
                        new_lines.append(line)
                    else:
                        if in_video_settings and stripped.startswith("AspectRatio"):
                            new_lines.append("AspectRatio = 1")
                            aspect_ratio_set = True
                        elif in_gecko_enabled and stripped == selected_code:
                            new_lines.append(line)
                            code_enabled = True
                        else:
                            new_lines.append(line)

                if in_video_settings and not aspect_ratio_set:
                    new_lines.append("AspectRatio = 1")
                    aspect_ratio_set = True
                if in_gecko_enabled and not code_enabled:
                    new_lines.append(selected_code)
                    code_enabled = True

                if not has_video_settings:
                    new_lines.extend(["", "[Video_Settings]", "AspectRatio = 1"])
                if not has_gecko_enabled:
                    new_lines.extend(["", "[Gecko_Enabled]", selected_code])

                final_content = "\n".join(new_lines) + "\n"
            else:
                final_content = content

            (curated_dir / ini_path.name).write_text(final_content, encoding="utf-8")

        # 3. Merge custom local patches from patches/gcn/*.ini
        custom_gcn = list(self.gcn_local_dir.glob("*.ini"))
        for custom_ini in custom_gcn:
            print(f"    -> Merging custom Gecko patch: {custom_ini.name}...")
            shutil.copy2(custom_ini, curated_dir / custom_ini.name)

        print(f"    -> Curation complete: {len(all_inis)} total INIs ({widescreen_injected_count} with active 16:9 Gecko widescreen).")

        # 4. Package into tarball and push to Dolphin GameSettings
        tar_path = self.scratch_dir / "dolphin_gamesettings.tar.gz"
        print(f"    -> Packaging {len(all_inis)} curated GameSettings into {tar_path.name}...")
        with tarfile.open(tar_path, "w:gz") as tar:
            for ini_file in curated_dir.glob("*.ini"):
                tar.add(ini_file, arcname=ini_file.name)

        remote_tar = "/sdcard/Download/dolphin_gamesettings.tar.gz"
        remote_gamesettings = "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings"

        print(f"    -> Deploying curated GameSettings catalog to {remote_gamesettings}...")
        self.adb_cmd("push", str(tar_path), remote_tar)

        extract_cmd = (
            f"mkdir -p '{remote_gamesettings}' && "
            f"tar -xzf '{remote_tar}' -C '{remote_gamesettings}/' && "
            f"rm '{remote_tar}'"
        )
        self.shell(extract_cmd, check=False)
        print(f"    [OK] Successfully deployed {len(all_inis)} GameSettings to Dolphin.")
        return len(all_inis)

    def run_all(self, skip_ps2: bool = False, skip_dolphin: bool = False) -> Tuple[int, int]:
        ps2_count = 0
        dolphin_count = 0
        if not skip_ps2:
            ps2_count = self.stage_ps2_patches()
        if not skip_dolphin:
            dolphin_count = self.stage_dolphin_gamesettings()

        print("\n" + "=" * 72)
        print("   Universal Community Patch Deployment Complete!")
        print(f"   * PS2 (NetherSX2) .pnach Cheats Deployed : {ps2_count}")
        print(f"   * Dolphin GameSettings Deployed         : {dolphin_count}")
        print("=" * 72)
        return ps2_count, dolphin_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal PS2 & GameCube/Wii Community Patch Engine for RP5")
    parser.add_argument("-s", "--serial", default=DEFAULT_SERIAL, help="Target device serial")
    parser.add_argument("--adb", default=None, help="Path to ADB binary")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands without modifying device")
    parser.add_argument("--skip-ps2", action="store_true", help="Skip PS2 PCSX2 patches")
    parser.add_argument("--skip-dolphin", action="store_true", help="Skip Dolphin GameSettings patches")
    args = parser.parse_args()

    adb_path = find_adb(args.adb)
    engine = CommunityPatchEngine(adb_path=adb_path, serial=args.serial, dry_run=args.dry_run)
    engine.run_all(skip_ps2=args.skip_ps2, skip_dolphin=args.skip_dolphin)


if __name__ == "__main__":
    main()
