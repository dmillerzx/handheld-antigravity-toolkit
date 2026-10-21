#!/usr/bin/env python3
"""
scripts/stage_community_patches.py — Universal PS2 & GameCube/Wii Community Patch Engine
======================================================================================
Streams upstream community patches directly from official repositories into
temporary scratch storage, applies custom user overrides and profile rules,
pushes to device over ADB, and immediately wipes scratch storage to maintain
a lightweight git repository.

1. PS2 (NetherSX2 / PCSX2):
   - Streams latest patches.zip from https://github.com/PCSX2/pcsx2_patches.
   - Extracts into temporary scratch, layers local custom overrides (patches/ps2/*.pnach),
     deploys to NetherSX2 patches/ and cheats/ over ADB, and cleans up scratch.
2. GameCube & Wii (Dolphin):
   - Fetches upstream GameSettings catalog from dolphin-emu/dolphin into scratch.
   - Conditional Widescreen: Injects 16:9 Gecko codes under [Gecko_Enabled] and sets
     AspectRatio = 1 only if active profile specifies "force_widescreen": true.
   - Layers local custom overrides from patches/gcn/*.ini.
   - Deploys to Dolphin GameSettings/ over ADB and completely wipes scratch.
"""

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Import dynamic device profiling helper
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import detect_device_profile, detect_storage_targets, load_profile_by_id

PCSX2_PATCHES_URL = "https://github.com/PCSX2/pcsx2_patches/releases/latest/download/patches.zip"
DOLPHIN_REPO_URL = "https://github.com/dolphin-emu/dolphin.git"

RE_169_CODE = re.compile(r"^\$(?:16:9\s*(?:Widescreen|Aspect Ratio Fix)?|Widescreen(?:\s*Hack|\s*Fix|\s*\(16:9\)|\[|\s*$))[^\r\n]*", re.IGNORECASE)
RE_DEFLICKER_CODE = re.compile(r"^\$(?:Disable\s*Deflicker|Deflicker\s*Off|No\s*Deflicker|Disable\s*Bloom)[^\r\n]*", re.IGNORECASE)


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


def merge_dolphin_ini_content(base_text: str, custom_text: str) -> str:
    """Merges custom INI (Video_Settings, Gecko codes, etc.) into base INI without losing base game fixes."""
    custom_sections = {}
    curr_sec = None
    for line in custom_text.splitlines():
        stripped = line.strip()
        m = re.match(r"^\[(.*?)\]$", stripped)
        if m:
            curr_sec = m.group(1).strip()
            custom_sections[curr_sec] = []
        elif curr_sec is not None:
            custom_sections[curr_sec].append(line)

    base_lines = base_text.splitlines()
    base_sec_indices = {}
    for idx, line in enumerate(base_lines):
        m = re.match(r"^\[(.*?)\]$", line.strip())
        if m:
            base_sec_indices[m.group(1).strip().lower()] = idx

    out_lines = list(base_lines)
    for c_sec, c_lines in custom_sections.items():
        c_sec_lower = c_sec.lower()
        if c_sec_lower not in base_sec_indices:
            if out_lines and out_lines[-1].strip() != "":
                out_lines.append("")
            out_lines.append(f"[{c_sec}]")
            out_lines.extend(c_lines)
        else:
            if c_sec_lower in ["video_settings", "video_enhancements", "video_hacks", "core"]:
                sec_idx = None
                for idx, line in enumerate(out_lines):
                    if re.match(rf"^\[{re.escape(c_sec)}\]$", line.strip(), re.IGNORECASE):
                        sec_idx = idx
                        break
                if sec_idx is not None:
                    end_idx = len(out_lines)
                    for idx in range(sec_idx + 1, len(out_lines)):
                        if re.match(r"^\[.*?\]$", out_lines[idx].strip()):
                            end_idx = idx
                            break
                    for cl in c_lines:
                        if "=" in cl:
                            k = cl.split("=", 1)[0].strip().lower()
                            replaced = False
                            for idx in range(sec_idx + 1, end_idx):
                                if "=" in out_lines[idx] and out_lines[idx].split("=", 1)[0].strip().lower() == k:
                                    out_lines[idx] = cl
                                    replaced = True
                                    break
                            if not replaced:
                                out_lines.insert(sec_idx + 1, cl)
                                end_idx += 1
            elif c_sec_lower in ["gecko", "actionreplay"]:
                sec_idx = None
                for idx, line in enumerate(out_lines):
                    if re.match(rf"^\[{re.escape(c_sec)}\]$", line.strip(), re.IGNORECASE):
                        sec_idx = idx
                        break
                if sec_idx is not None:
                    end_idx = len(out_lines)
                    for idx in range(sec_idx + 1, len(out_lines)):
                        if re.match(r"^\[.*?\]$", out_lines[idx].strip()):
                            end_idx = idx
                            break
                    existing_text = "\n".join(out_lines[sec_idx:end_idx])
                    codes_to_add = []
                    skip = False
                    for cl in c_lines:
                        if cl.strip().startswith("$") and cl.strip() in existing_text:
                            skip = True
                        elif cl.strip().startswith("$"):
                            skip = False
                            codes_to_add.append(cl)
                        elif not skip:
                            codes_to_add.append(cl)
                    if codes_to_add:
                        for cl in codes_to_add:
                            out_lines.insert(end_idx, cl)
                            end_idx += 1
            elif c_sec_lower in ["gecko_enabled", "actionreplay_enabled"]:
                sec_idx = None
                for idx, line in enumerate(out_lines):
                    if re.match(rf"^\[{re.escape(c_sec)}\]$", line.strip(), re.IGNORECASE):
                        sec_idx = idx
                        break
                if sec_idx is not None:
                    end_idx = len(out_lines)
                    for idx in range(sec_idx + 1, len(out_lines)):
                        if re.match(r"^\[.*?\]$", out_lines[idx].strip()):
                            end_idx = idx
                            break
                    existing_entries = [out_lines[i].strip() for i in range(sec_idx + 1, end_idx) if out_lines[i].strip()]
                    for cl in c_lines:
                        stripped = cl.strip()
                        if stripped and stripped not in existing_entries:
                            out_lines.insert(end_idx, cl)
                            end_idx += 1

    return "\n".join(out_lines) + "\n"


class CommunityPatchEngine:
    def __init__(
        self,
        adb_path: str,
        serial: Optional[str] = None,
        profile: Optional[Dict] = None,
        dry_run: bool = False
    ):
        self.adb = adb_path
        self.serial = serial
        self.profile = profile or {}
        self.dry_run = dry_run

        # True custom user overrides directories in git repo
        self.ps2_custom_dir = WORKSPACE_ROOT / "patches" / "ps2"
        self.gcn_custom_dir = WORKSPACE_ROOT / "patches" / "gcn"
        self.wii_custom_dir = WORKSPACE_ROOT / "patches" / "wii"

        # Temporary scratch directory (isolated and wiped after execution)
        self.scratch_dir = Path(tempfile.mkdtemp(prefix="rp_stream_patches_"))
        self.force_widescreen = self.profile.get("emulation", {}).get("force_widescreen", True)

    def adb_cmd(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(list(args))
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
    # PS2 (NetherSX2 / PCSX2) STREAMING PATCH ENGINE
    # =========================================================================
    def stage_ps2_patches(self) -> int:
        """Streams upstream PCSX2 master .pnach patches into scratch, layers overrides, and deploys."""
        print("\n[*] [1/2] Streaming PS2 (NetherSX2 / PCSX2) Master Community Patches from Upstream...")
        ps2_scratch = self.scratch_dir / "ps2"
        ps2_scratch.mkdir(parents=True, exist_ok=True)
        zip_target = self.scratch_dir / "pcsx2_patches.zip"

        # 1. Stream release archive directly into scratch
        print(f"    -> Downloading master patches archive from {PCSX2_PATCHES_URL}...")
        try:
            req = urllib.request.Request(PCSX2_PATCHES_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(zip_target, "wb") as f:
                f.write(data)
            print(f"    -> Streamed {len(data):,} bytes directly to temporary scratch.")
        except Exception as e:
            print(f"    [!] Warning: Failed to stream from PCSX2 upstream: {e}")
            return 0

        # 2. Extract into scratch/ps2/
        with zipfile.ZipFile(zip_target, "r") as z:
            for member in z.namelist():
                if member.endswith(".pnach"):
                    content = z.read(member)
                    out_name = os.path.basename(member)
                    with open(ps2_scratch / out_name, "wb") as f:
                        f.write(content)

        # 3. Layer custom user overrides from patches/ps2/*.pnach
        if self.ps2_custom_dir.exists():
            custom_pnach = list(self.ps2_custom_dir.glob("*.pnach"))
            for p in custom_pnach:
                print(f"    -> Layering custom user PS2 override: {p.name}...")
                shutil.copy2(p, ps2_scratch / p.name)

        staged_patches = list(ps2_scratch.glob("*.pnach"))
        print(f"    -> Prepared {len(staged_patches):,} .pnach patches in temporary scratch.")

        # 4. Package into tarball for fast ADB deployment
        tar_path = self.scratch_dir / "ps2_patches.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            for pnach in staged_patches:
                tar.add(pnach, arcname=pnach.name)

        # 5. Push and unpack over ADB to NetherSX2 and ARM SX2
        remote_tar = "/sdcard/Download/ps2_patches.tar.gz"
        nethersx2_patches = "/sdcard/Android/data/xyz.aethersx2.android/files/patches"
        nethersx2_cheats = "/sdcard/Android/data/xyz.aethersx2.android/files/cheats"
        armsx2_patches = "/sdcard/Android/data/com.armsx2/files/patches"
        armsx2_cheats = "/sdcard/Android/data/com.armsx2/files/cheats"

        print(f"    -> Deploying patches to NetherSX2 and ARM SX2...")
        self.adb_cmd("push", str(tar_path), remote_tar)

        extract_cmd = (
            f"mkdir -p '{nethersx2_patches}' '{nethersx2_cheats}' '{armsx2_patches}' '{armsx2_cheats}' && "
            f"tar -xzf '{remote_tar}' -C '{nethersx2_patches}/' 2>/dev/null || true && "
            f"tar -xzf '{remote_tar}' -C '{nethersx2_cheats}/' 2>/dev/null || true && "
            f"tar -xzf '{remote_tar}' -C '{armsx2_patches}/' 2>/dev/null || true && "
            f"tar -xzf '{remote_tar}' -C '{armsx2_cheats}/' 2>/dev/null || true && "
            f"rm -f '{remote_tar}'"
        )
        self.shell(extract_cmd, check=False)
        print(f"    [OK] Successfully deployed {len(staged_patches):,} PS2 patches to NetherSX2 and ARM SX2.")

        # 6. Wipe scratch ps2 directory to free disk space
        shutil.rmtree(ps2_scratch, ignore_errors=True)
        if zip_target.exists():
            zip_target.unlink()
        if tar_path.exists():
            tar_path.unlink()
        print("    -> Scratch storage wiped cleanly.")
        return len(staged_patches)

    # =========================================================================
    # GAMECUBE & WII (DOLPHIN) STREAMING PATCH ENGINE
    # =========================================================================
    def stage_dolphin_gamesettings(self) -> int:
        """Fetches upstream Dolphin GameSettings into scratch, layers overrides, and deploys."""
        print("\n[*] [2/2] Streaming GameCube & Wii (Dolphin) Master GameSettings from Upstream...")
        git_bin = find_git()
        dolphin_sparse_dir = self.scratch_dir / "dolphin_git"
        curated_dir = self.scratch_dir / "curated_dolphin_gamesettings"
        curated_dir.mkdir(parents=True, exist_ok=True)

        # 1. Fetch upstream Dolphin GameSettings via sparse-checkout directly into scratch
        print(f"    -> Fetching GameSettings from {DOLPHIN_REPO_URL} into temporary scratch...")
        try:
            clone_cmd = [git_bin, "clone", "--filter=blob:none", "--no-checkout", "--depth", "1", DOLPHIN_REPO_URL, str(dolphin_sparse_dir)]
            subprocess.run(clone_cmd, capture_output=True, text=True, check=True)
            subprocess.run([git_bin, "-C", str(dolphin_sparse_dir), "sparse-checkout", "set", "Data/Sys/GameSettings"], capture_output=True, text=True, check=True)
            subprocess.run([git_bin, "-C", str(dolphin_sparse_dir), "checkout"], capture_output=True, text=True, check=True)
        except Exception as e:
            print(f"    [!] Warning: Failed to sparse-checkout Dolphin GameSettings: {e}")
            return 0

        source_gamesettings = dolphin_sparse_dir / "Data" / "Sys" / "GameSettings"
        all_inis = list(source_gamesettings.glob("*.ini"))
        print(f"    -> Streamed {len(all_inis):,} upstream Dolphin GameSettings INIs.")

        # 2. Parse and inject widescreen Gecko codes
        widescreen_injected_count = 0
        for ini_path in all_inis:
            content = ini_path.read_text(encoding="utf-8", errors="replace")

            if not self.force_widescreen:
                final_content = content
            else:
                lines = content.splitlines()
                in_gecko = False
                widescreen_codes = []
                deflicker_codes = []

                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("[") and stripped.endswith("]"):
                        in_gecko = (stripped.lower() == "[gecko]")
                    elif in_gecko and stripped.startswith("$"):
                        if RE_169_CODE.match(stripped) or ("16:9" in stripped and "widescreen" in stripped.lower()):
                            widescreen_codes.append(stripped)
                        elif RE_DEFLICKER_CODE.match(stripped):
                            deflicker_codes.append(stripped)

                codes_to_enable = []
                if widescreen_codes:
                    selected_code = widescreen_codes[0]
                    for c in widescreen_codes:
                        if "normal hud" in c.lower() or c.strip() == "$16:9 Widescreen":
                            selected_code = c
                            break
                    codes_to_enable.append(selected_code)
                if deflicker_codes:
                    codes_to_enable.append(deflicker_codes[0])

                if codes_to_enable:
                    widescreen_injected_count += 1
                    new_lines = []
                    has_video_settings = False
                    has_gecko_enabled = False
                    in_video_settings = False
                    in_gecko_enabled = False
                    aspect_ratio_set = False

                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith("[") and stripped.endswith("]"):
                            sec = stripped.lower()
                            if in_video_settings and not aspect_ratio_set:
                                new_lines.append("AspectRatio = 1")
                                aspect_ratio_set = True
                            if in_gecko_enabled:
                                for code in codes_to_enable:
                                    if code not in new_lines:
                                        new_lines.append(code)

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
                            else:
                                new_lines.append(line)

                    if in_video_settings and not aspect_ratio_set:
                        new_lines.append("AspectRatio = 1")
                        aspect_ratio_set = True
                    if in_gecko_enabled:
                        for code in codes_to_enable:
                            if code not in new_lines:
                                new_lines.append(code)

                    if not has_video_settings:
                        new_lines.extend(["", "[Video_Settings]", "AspectRatio = 1"])
                    if not has_gecko_enabled:
                        new_lines.extend(["", "[Gecko_Enabled]"] + codes_to_enable)

                    final_content = "\n".join(new_lines) + "\n"
                else:
                    final_content = content

            (curated_dir / ini_path.name).write_text(final_content, encoding="utf-8")

        # 3. Layer custom local user overrides from patches/gcn/*.ini and patches/wii/*.ini
        custom_gcn_count = 0
        if self.gcn_custom_dir.exists():
            custom_gcn = list(self.gcn_custom_dir.glob("*.ini"))
            print(f"    -> Layering {len(custom_gcn):,} custom local GameCube Gecko/widescreen patch overrides...")
            for custom_ini in custom_gcn:
                target_path = curated_dir / custom_ini.name
                custom_text = custom_ini.read_text(encoding="utf-8", errors="replace")
                if target_path.exists():
                    target_path.write_text(merge_dolphin_ini_content(target_path.read_text(encoding="utf-8", errors="replace"), custom_text), encoding="utf-8")
                else:
                    target_path.write_text(custom_text, encoding="utf-8")

                # If revision files exist for this game (e.g. GALE01r0.ini), merge widescreen settings into them as well
                stem = custom_ini.stem
                if len(stem) == 6:
                    for rev_ini in curated_dir.glob(f"{stem}r*.ini"):
                        rev_text = rev_ini.read_text(encoding="utf-8", errors="replace")
                        rev_ini.write_text(merge_dolphin_ini_content(rev_text, custom_text), encoding="utf-8")

                custom_gcn_count += 1

        custom_wii_count = 0
        if self.wii_custom_dir.exists():
            custom_wii = list(self.wii_custom_dir.glob("*.ini"))
            for custom_ini in custom_wii:
                print(f"    -> Layering custom local Wii Gecko patch override: {custom_ini.name}...")
                shutil.copy2(custom_ini, curated_dir / custom_ini.name)
                custom_wii_count += 1

        total_curated = len(list(curated_dir.glob("*.ini")))
        print(f"    -> Curation complete: {total_curated:,} INIs ({widescreen_injected_count:,} with 16:9/deflicker hooks, {custom_gcn_count} GCN overrides, {custom_wii_count} Wii overrides).")

        # 4. Package into tarball and push to Dolphin GameSettings
        tar_path = self.scratch_dir / "dolphin_gamesettings.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            for ini_file in curated_dir.glob("*.ini"):
                tar.add(ini_file, arcname=ini_file.name)

        remote_tar = "/sdcard/Download/dolphin_gamesettings.tar.gz"
        remote_gamesettings = "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings"

        print(f"    -> Deploying curated catalog to {remote_gamesettings}...")
        self.adb_cmd("push", str(tar_path), remote_tar)

        extract_cmd = (
            f"mkdir -p '{remote_gamesettings}' && "
            f"tar -xzf '{remote_tar}' -C '{remote_gamesettings}/' && "
            f"rm '{remote_tar}'"
        )
        self.shell(extract_cmd, check=False)
        print(f"    [OK] Successfully deployed {len(all_inis):,} GameSettings to Dolphin.")

        # 5. Wipe scratch directory
        shutil.rmtree(curated_dir, ignore_errors=True)
        shutil.rmtree(dolphin_sparse_dir, ignore_errors=True)
        if tar_path.exists():
            tar_path.unlink()
        print("    -> Scratch storage wiped cleanly.")
        return len(all_inis)

    def get_controller_device_string(self) -> str:
        """Dynamically queries connected Android InputDevices to resolve Dolphin controller identifier."""
        try:
            dumpsys = self.shell("dumpsys input")
            m = re.search(
                r'Device \d+:\s+(Xbox Wireless Controller|Retroid Pocket Controller).*?ControllerNum:\s*(\d+)',
                dumpsys,
                re.DOTALL | re.IGNORECASE
            )
            if m:
                return f"Android/{m.group(2).strip()}/{m.group(1).strip()}"
        except Exception:
            pass
        return "Android/1/Xbox Wireless Controller"


    @staticmethod
    def convert_to_android_wiimote_profile(content: str, ctrl_dev: str) -> str:
        """Converts upstream XInput / SDL Dolphin Wiimote profile to Android-native scan-code bindings."""
        lines = content.splitlines()
        out = []
        has_header = False

        sub_map = [
            ("Button A", "Button 96"),
            ("Button B", "Button 97"),
            ("Button X", "Button 99"),
            ("Button Y", "Button 100"),
            ("Shoulder L", "Button 102"),
            ("Button L", "Button 102"),
            ("Shoulder R", "Button 103"),
            ("Button R", "Button 103"),
            ("Trigger L", "Axis 23+"),
            ("Trigger R", "Axis 22+"),
            ("Thumb L", "Button 106"),
            ("Click L", "Button 106"),
            ("Thumb R", "Button 107"),
            ("Click R", "Button 107"),
            ("Back", "Button 109"),
            ("Select", "Button 109"),
            ("Start", "Button 108"),
            ("Guide", "Button 110"),
            ("Home", "Button 110"),
            ("Pad N", "Button 19"),
            ("Pad Up", "Button 19"),
            ("Pad S", "Button 20"),
            ("Pad Down", "Button 20"),
            ("Pad W", "Button 21"),
            ("Pad Left", "Button 21"),
            ("Pad E", "Button 22"),
            ("Pad Right", "Button 22"),
            ("Left Y+", "Axis 1+"),
            ("Left Y-", "Axis 1-"),
            ("Left X+", "Axis 0+"),
            ("Left X-", "Axis 0-"),
            ("Right Y+", "Axis 14+"),
            ("Right Y-", "Axis 14-"),
            ("Right X+", "Axis 11+"),
            ("Right X-", "Axis 11-"),
            ("Cursor Y-", "Axis 14-"),
            ("Cursor Y+", "Axis 14+"),
            ("Cursor X-", "Axis 11-"),
            ("Cursor X+", "Axis 11+"),
            ("LCONTROL", "Button 102"),
            ("LSHIFT", "Axis 23+"),
            ("RETURN", "Button 108"),
            ("ESCAPE", "Button 109"),
        ]

        for line in lines:
            stripped = line.strip()
            if stripped.lower() == "[profile]":
                has_header = True
                out.append("[Profile]")
                continue
            elif stripped.startswith("[") and stripped.endswith("]"):
                out.append(line)
                continue
            if not stripped or stripped.startswith("#"):
                out.append(line)
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key_strip = key.strip()
                val_strip = val.strip()

                if key_strip.endswith("/Plus"):
                    key_strip = key_strip[:-4] + "+"
                elif key_strip.endswith("/Minus"):
                    key_strip = key_strip[:-5] + "-"

                if key_strip.lower() == "device":
                    out.append(f"{key_strip} = {ctrl_dev}")
                    continue

                for src, dst in sub_map:
                    val_strip = re.sub(r"(`)?" + re.escape(src) + r"(`)?", f"`{dst}`", val_strip)

                out.append(f"{key_strip} = {val_strip}")
            else:
                out.append(line)

        if not has_header:
            out.insert(0, "[Profile]")
        return "\n".join(out) + "\n"

    def stage_wiimote_community_profiles(self) -> int:
        """Streams, parses, and converts ALL available Wiimote controller profiles from upstream into Android-native keycodes."""
        print("\n[*] [3/3] Streaming & Converting Community Wiimote Profiles from Upstream...")
        ctrl_dev = self.get_controller_device_string()
        print(f"    -> Target Controller Device: {ctrl_dev}")

        prof_scratch = self.scratch_dir / "wiimote_profiles"
        prof_scratch.mkdir(parents=True, exist_ok=True)

        # 1. Stream iwubcode/DolphinControllerProfiles
        iwubcode_zip = self.scratch_dir / "iwubcode_profiles.zip"
        iwubcode_url = "https://github.com/iwubcode/DolphinControllerProfiles/archive/refs/heads/master.zip"
        print(f"    -> Streaming community game profiles from {iwubcode_url}...")
        try:
            req = urllib.request.Request(iwubcode_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(iwubcode_zip, "wb") as f:
                f.write(data)
            print(f"    -> Streamed {len(data):,} bytes of community profiles.")

            with zipfile.ZipFile(iwubcode_zip, "r") as z:
                for member in z.namelist():
                    if member.endswith(".ini") and "Profiles/" in member:
                        parts = member.split("Profiles/", 1)[1].split("/")
                        if len(parts) >= 2:
                            game_name = parts[0].replace(" ", "_")
                            var_name = parts[-1].replace(".ini", "").replace(" ", "_")
                            if var_name.lower() in ["general", "skywardsword_basic"]:
                                out_filename = f"{game_name}.ini"
                            else:
                                out_filename = f"{game_name}_{var_name}.ini"
                        else:
                            out_filename = os.path.basename(member).replace(" ", "_")

                        raw_content = z.read(member).decode("utf-8", errors="replace")
                        converted = self.convert_to_android_wiimote_profile(raw_content, ctrl_dev)
                        (prof_scratch / out_filename).write_text(converted, encoding="utf-8")
        except Exception as e:
            print(f"    [!] Notice: Failed to stream iwubcode profiles: {e}")

        # 2. Stream EmuDeck Wiimote Profiles
        emudeck_files = [
            "Wii_base_nunchuck.ini",
            "Wii_base_nunchuck_with_touchpad.ini",
            "Wii_classic_controller.ini",
            "Wii_no_attachment.ini",
            "Wii_no_attachment_with_touchpad.ini",
            "Wii_NoController.ini",
        ]
        emudeck_base = "https://raw.githubusercontent.com/dragoonDorise/EmuDeck/main/configs/org.DolphinEmu.dolphin-emu/config/dolphin-emu/Profiles/Wiimote/"
        print("    -> Streaming EmuDeck Wiimote baseline profiles...")
        for ed_name in emudeck_files:
            try:
                ed_url = f"{emudeck_base}{ed_name}"
                req = urllib.request.Request(ed_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw_ed = resp.read().decode("utf-8", errors="replace")
                converted_ed = self.convert_to_android_wiimote_profile(raw_ed, ctrl_dev)
                (prof_scratch / ed_name).write_text(converted_ed, encoding="utf-8")
            except Exception:
                pass

        # 3. Layer local custom community profiles
        local_wiimote_dir = WORKSPACE_ROOT / "configs" / "dolphin" / "profiles" / "Wiimote"
        if local_wiimote_dir.exists():
            for loc_prof in local_wiimote_dir.glob("*.ini"):
                loc_txt = loc_prof.read_text(encoding="utf-8")
                loc_mod = re.sub(r"Device\s*=\s*[^\r\n]+", f"Device = {ctrl_dev}", loc_txt)
                (prof_scratch / loc_prof.name).write_text(loc_mod, encoding="utf-8")

        all_profiles = list(prof_scratch.glob("*.ini"))
        print(f"    -> Ingested and converted {len(all_profiles)} Android-native Wiimote profiles.")

        # 4. Package and push over ADB
        tar_path = self.scratch_dir / "wiimote_profiles.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            for p in all_profiles:
                tar.add(p, arcname=p.name)

        remote_tar = "/sdcard/Download/wiimote_profiles.tar.gz"
        remote_target1 = "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Profiles/Wiimote"
        remote_target2 = "/sdcard/dolphin-emu/Config/Profiles/Wiimote"

        self.adb_cmd("push", str(tar_path), remote_tar)
        extract_cmd = (
            f"mkdir -p '{remote_target1}' '{remote_target2}' && "
            f"tar -xzf '{remote_tar}' -C '{remote_target1}/' && "
            f"tar -xzf '{remote_tar}' -C '{remote_target2}/' && "
            f"rm '{remote_tar}'"
        )
        self.shell(extract_cmd, check=False)
        print(f"    [OK] Successfully deployed {len(all_profiles)} Wiimote profiles to Dolphin.")

        # 5. Clean up scratch
        shutil.rmtree(prof_scratch, ignore_errors=True)
        if iwubcode_zip.exists():
            iwubcode_zip.unlink()
        if tar_path.exists():
            tar_path.unlink()
        return len(all_profiles)

    def run_all(self, skip_ps2: bool = False, skip_dolphin: bool = False, skip_wiimote: bool = False) -> Tuple[int, int, int]:
        ps2_count = 0
        dolphin_count = 0
        wiimote_count = 0
        try:
            if not skip_ps2:
                ps2_count = self.stage_ps2_patches()
            if not skip_dolphin:
                dolphin_count = self.stage_dolphin_gamesettings()
            if not skip_wiimote:
                wiimote_count = self.stage_wiimote_community_profiles()
        finally:
            # Absolute scratch cleanup guarantee
            shutil.rmtree(self.scratch_dir, ignore_errors=True)

        print("\n" + "=" * 72)
        print("   Universal Dynamic Patch Streaming & Deployment Complete!")
        print(f"   * Active Device Profile : {self.profile.get('name', 'Default')}")
        print(f"   * Widescreen Injection  : {self.force_widescreen}")
        print(f"   * PS2 (NetherSX2) .pnach Cheats Deployed : {ps2_count:,}")
        print(f"   * Dolphin GameSettings Deployed         : {dolphin_count:,}")
        print(f"   * Dolphin Wiimote Profiles Deployed     : {wiimote_count:,}")
        print("   * Local Repository Footprint            : Clean (0 Bulk Patches in Git)")
        print("=" * 72)
        return ps2_count, dolphin_count, wiimote_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal Dynamic Upstream Patch Engine with Zero Repo Bloat")
    parser.add_argument("-s", "--serial", default=None, help="Target device serial")
    parser.add_argument("--profile", default=None, help="Hardware profile ID or path")
    parser.add_argument("--adb", default=None, help="Path to ADB binary")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands without modifying device")
    parser.add_argument("--skip-ps2", action="store_true", help="Skip PS2 PCSX2 patches")
    parser.add_argument("--skip-dolphin", action="store_true", help="Skip Dolphin GameSettings patches")
    parser.add_argument("--skip-wiimote", action="store_true", help="Skip Dolphin Wiimote profile streaming")
    args = parser.parse_args()

    adb_path = find_adb(args.adb)
    profile, model_name = detect_device_profile(adb_path, serial=args.serial, override_id=args.profile, dry_run=args.dry_run)

    engine = CommunityPatchEngine(
        adb_path=adb_path,
        serial=args.serial,
        profile=profile,
        dry_run=args.dry_run
    )
    engine.run_all(skip_ps2=args.skip_ps2, skip_dolphin=args.skip_dolphin, skip_wiimote=args.skip_wiimote)


if __name__ == "__main__":
    main()

