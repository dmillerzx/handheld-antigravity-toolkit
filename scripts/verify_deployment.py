#!/usr/bin/env python3
"""
verify_deployment.py — Hardware Deployment & Configuration Verifier
==================================================================
Compares parsed key/value pairs between on-device configurations and
repository source-of-truth files.

Normalizes:
- Quoted/unquoted key names and backticks: `Button A` == Button A, `Select` == Select
- Float / numeric formatting: 50. == 50.000000 == 50
- Case-insensitive booleans: true == True
- Unordered sections and keys
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ADB = WORKSPACE_ROOT / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
DEFAULT_SERIAL = "ff152647"

DOLPHIN_PKG = "org.dolphinemu.dolphinemu"
ARMSX2_PKG = "com.armsx2"


def normalize_val(v: str) -> Any:
    v = v.strip()
    # Strip backticks from individual tokens: `Button A` -> Button A
    v = re.sub(r"`([^`]+)`", r"\1", v)
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    # Numeric normalization: 50. -> 50.0, 50.000000 -> 50.0
    if re.match(r"^-?\d+(\.\d*)?$", v):
        try:
            return float(v)
        except ValueError:
            pass
    return v


def parse_ini(text: str) -> Dict[str, Dict[str, Any]]:
    sections: Dict[str, Dict[str, Any]] = {}
    current_sec = ""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";") or line.startswith("//"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_sec = line[1:-1].strip()
            if current_sec not in sections:
                sections[current_sec] = {}
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            # Keys themselves might have backticks stripped if any
            k = re.sub(r"`([^`]+)`", r"\1", k)
            norm_v = normalize_val(v)
            sec_dict = sections.setdefault(current_sec, {})
            if k in sec_dict:
                if not isinstance(sec_dict[k], list):
                    sec_dict[k] = [sec_dict[k]]
                sec_dict[k].append(norm_v)
            else:
                sec_dict[k] = norm_v
        else:
            # Unkeyed lines (e.g. Gecko codes, pnach lines)
            sections.setdefault(current_sec, {})[line] = True
    return sections


def diff_parsed(device_dict: Dict[str, Dict[str, Any]], repo_dict: Dict[str, Dict[str, Any]]) -> List[str]:
    diffs = []
    all_secs = sorted(set(device_dict.keys()) | set(repo_dict.keys()))
    for sec in all_secs:
        if sec not in device_dict:
            diffs.append(f"Missing section [{sec}] on device")
            continue
        if sec not in repo_dict:
            diffs.append(f"Extra section [{sec}] on device")
            continue
        dev_k = device_dict[sec]
        repo_k = repo_dict[sec]
        all_k = sorted(set(dev_k.keys()) | set(repo_k.keys()))
        for k in all_k:
            if k not in dev_k:
                diffs.append(f"[{sec}] Missing key '{k}' on device (repo has '{repo_k[k]}')")
            elif k not in repo_k:
                diffs.append(f"[{sec}] Extra key '{k}' on device ('{dev_k[k]}')")
            else:
                v_dev = dev_k[k]
                v_repo = repo_k[k]
                if isinstance(v_dev, list) or isinstance(v_repo, list):
                    l_dev = v_dev if isinstance(v_dev, list) else [v_dev]
                    l_repo = v_repo if isinstance(v_repo, list) else [v_repo]
                    if sorted([str(x) for x in l_dev]) != sorted([str(x) for x in l_repo]):
                        diffs.append(f"[{sec}] Key '{k}' list mismatch: device={l_dev} vs repo={l_repo}")
                elif v_dev != v_repo:
                    diffs.append(f"[{sec}] Key '{k}' mismatch: device='{v_dev}' vs repo='{v_repo}'")
    return diffs


class DeploymentVerifier:
    def __init__(self, adb_path: Path, serial: str):
        self.adb = str(adb_path)
        self.serial = serial
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rp5_verify_"))

    def run_cmd(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

    def force_stop(self, pkg: str) -> None:
        self.run_cmd("shell", "am", "force-stop", pkg)

    def pull_file(self, remote_path: str) -> Path:
        local_target = self.temp_dir / Path(remote_path).name
        # Use counter if filename exists
        idx = 1
        while local_target.exists():
            local_target = self.temp_dir / f"{Path(remote_path).stem}_{idx}{Path(remote_path).suffix}"
            idx += 1
        res = self.run_cmd("pull", remote_path, str(local_target))
        if res.returncode != 0 or not local_target.exists():
            return None
        return local_target

    def verify(self) -> bool:
        print(f"\n=======================================================")
        print(f"[*] Starting Hardware Deployment Verification")
        print(f"[*] Device Serial: {self.serial}")
        print(f"=======================================================\n")

        # 1. Force stop emulators to ensure disk writeback
        print("[*] Force-stopping emulators on device...")
        self.force_stop(DOLPHIN_PKG)
        self.force_stop(ARMSX2_PKG)

        # File definitions: (Emulator, Remote Path, Repo Path)
        verifications: List[Tuple[str, str, Path]] = [
            # Dolphin Controllers
            ("Dolphin", f"/sdcard/Android/data/{DOLPHIN_PKG}/files/Config/GCPadNew.ini", WORKSPACE_ROOT / "configs" / "dolphin" / "GCPadNew.ini"),
            ("Dolphin", f"/sdcard/Android/data/{DOLPHIN_PKG}/files/Config/WiimoteNew.ini", WORKSPACE_ROOT / "configs" / "dolphin" / "WiimoteNew.ini"),
            ("Dolphin", f"/sdcard/Android/data/{DOLPHIN_PKG}/files/Config/Profiles/GCPad/Standard_Controller.ini", WORKSPACE_ROOT / "configs" / "dolphin" / "profiles" / "GCPad" / "Standard_Controller.ini"),
            ("Dolphin", f"/sdcard/Android/data/{DOLPHIN_PKG}/files/Config/Profiles/Wiimote/Classic_Controller.ini", WORKSPACE_ROOT / "configs" / "dolphin" / "profiles" / "Wiimote" / "Classic_Controller.ini"),
            # Dolphin GameSettings
            ("Dolphin", f"/sdcard/Android/data/{DOLPHIN_PKG}/files/GameSettings/RMC.ini", WORKSPACE_ROOT / "patches" / "wii" / "RMC.ini"),
            ("Dolphin", f"/sdcard/Android/data/{DOLPHIN_PKG}/files/GameSettings/RMCE01.ini", WORKSPACE_ROOT / "patches" / "wii" / "RMCE01.ini"),
            ("Dolphin", f"/sdcard/Android/data/{DOLPHIN_PKG}/files/GameSettings/RMCEA2.ini", WORKSPACE_ROOT / "patches" / "wii" / "RMCEA2.ini"),
            # ARM SX2 Patches & Settings
            ("ARM SX2", f"/sdcard/Android/data/{ARMSX2_PKG}/files/patches/646B2E29.pnach", WORKSPACE_ROOT / "patches" / "ps2" / "646B2E29.pnach"),
            ("ARM SX2", f"/sdcard/Android/data/{ARMSX2_PKG}/files/gamesettings/646B2E29.ini", WORKSPACE_ROOT / "patches" / "ps2" / "646B2E29.ini"),
        ]

        results = []
        all_passed = True

        for emu, remote_path, repo_file in verifications:
            fname = Path(remote_path).name
            if not repo_file.exists():
                results.append((emu, fname, "FAIL", f"Repo file missing: {repo_file}"))
                all_passed = False
                continue

            local_pulled = self.pull_file(remote_path)
            if not local_pulled or not local_pulled.exists():
                results.append((emu, fname, "FAIL", f"Remote file not found on device: {remote_path}"))
                all_passed = False
                continue

            try:
                dev_text = local_pulled.read_text(encoding="utf-8", errors="replace")
                repo_text = repo_file.read_text(encoding="utf-8", errors="replace")

                dev_parsed = parse_ini(dev_text)
                repo_parsed = parse_ini(repo_text)

                diffs = diff_parsed(dev_parsed, repo_parsed)
                if not diffs:
                    results.append((emu, fname, "PASS", "Key-value match"))
                else:
                    results.append((emu, fname, "FAIL", "; ".join(diffs[:2])))
                    all_passed = False
            except Exception as e:
                results.append((emu, fname, "FAIL", str(e)))
                all_passed = False

        # Output results table
        print(f"{'Emulator':<10} | {'Config / Patch File':<28} | {'Status':<6} | {'Details'}")
        print("-" * 80)
        for emu, fname, status, details in results:
            print(f"{emu:<10} | {fname:<28} | {status:<6} | {details}")
        print("-" * 80)

        if all_passed:
            print("\n[SUCCESS] All deployed configurations match the repository source of truth exactly!\n")
        else:
            print("\n[ERROR] One or more configuration mismatches detected.\n")

        return all_passed


def main():
    parser = argparse.ArgumentParser(description="Verify on-device configurations against repository source of truth.")
    parser.add_argument("--adb", default=str(DEFAULT_ADB), help="Path to adb executable")
    parser.add_argument("--serial", "-s", default=DEFAULT_SERIAL, help="Target device serial")
    args = parser.parse_args()

    verifier = DeploymentVerifier(Path(args.adb), args.serial)
    success = verifier.verify()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
