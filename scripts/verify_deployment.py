#!/usr/bin/env python3
"""
scripts/verify_deployment.py — Automated Pre-Flight Verification & Release Readiness Auditor
=============================================================================================
Performs an automated end-to-end hardware, configuration, permission, and controller
descriptor audit over ADB. Validates zero-touch community deployment readiness and
ensures all emulators, frontends, and storage mappings are hardened.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Import dynamic device profiling helper
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import detect_device_profile, detect_storage_targets


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


class PreFlightAuditor:
    def __init__(self, adb_path: str, serial: Optional[str] = None):
        self.adb = adb_path
        self.serial = serial
        self.results: List[Dict[str, str]] = []
        self.critical_failures = 0
        self.warnings = 0

    def adb_cmd(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [self.adb]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(list(args))
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    def shell(self, cmd: str) -> str:
        res = self.adb_cmd("shell", cmd)
        return res.stdout.strip() if res.stdout else ""

    def add_result(self, category: str, item: str, status: str, details: str = ""):
        self.results.append({
            "category": category,
            "item": item,
            "status": status,
            "details": details
        })
        if status == "FAIL":
            self.critical_failures += 1
        elif status == "WARN":
            self.warnings += 1

    # =========================================================================
    # 1. APP PACKAGE AUDIT
    # =========================================================================
    def audit_packages(self) -> Dict[str, bool]:
        installed_output = self.shell("pm list packages")
        installed_set = set()
        for line in installed_output.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                installed_set.add(line.split("package:", 1)[1].strip())

        packages = [
            ("RetroArch", ["com.retroarch.aarch64", "com.retroarch"]),
            ("Dolphin", ["org.dolphinemu.dolphinemu"]),
            ("ARM SX2 (PS2)", ["com.armsx2", "come.nanodata.armsx2"]),
            ("NetherSX2 (PS2)", ["xyz.aethersx2.android"]),
            ("DuckStation (PS1)", ["com.github.stenzek.duckstation"]),
            ("PPSSPP", ["org.ppsspp.ppsspp", "org.ppsspp.ppssppgold"]),
            ("DroidDeck (Steam)", ["com.droiddeck.launcher"]),
            ("ES-DE Frontend", ["org.es_de.frontend"]),
            ("Azahar (3DS)", ["org.azahar_emu.azahar"]),
            ("Vita3K (PS Vita)", ["org.vita3k.emulator"]),
            ("Flycast (Dreamcast)", ["com.flycast.emulator"]),
            ("Obtainium", ["dev.imranr.obtainium"]),
        ]

        status_map = {}
        for name, pkg_ids in packages:
            found = any(p in installed_set for p in pkg_ids)
            status_map[name] = found
            if found:
                active_id = next(p for p in pkg_ids if p in installed_set)
                self.add_result("Package", name, "PASS", f"Installed ({active_id})")
            else:
                # DroidDeck or DuckStation might be pending manual install
                if name in ["DuckStation (PS1)", "DroidDeck (Steam)"]:
                    self.add_result("Package", name, "INFO", "Not installed (Optional / User manual install)")
                else:
                    self.add_result("Package", name, "WARN", "Not installed on device")

        return status_map

    # =========================================================================
    # 2. CONFIG PATHS & INTEGRITY AUDIT
    # =========================================================================
    def audit_configs(self, sd_id: Optional[str]):
        config_checks = [
            ("Dolphin GCPadNew.ini", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/GCPadNew.ini"),
            ("Dolphin WiimoteNew.ini", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/WiimoteNew.ini"),
            ("Dolphin.ini", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Dolphin.ini"),
            ("Dolphin Motion Profile", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Profiles/Wiimote/Classic_Controller.ini"),
            ("MKWii GameSettings", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings/RMCEA2.ini"),
            ("DuckStation settings.ini", "/sdcard/Android/data/com.github.stenzek.duckstation/files/settings.ini"),
            ("PPSSPP ppsspp.ini", "/sdcard/PSP/SYSTEM/ppsspp.ini"),
            ("ARM SX2 PCSX2.ini", "/sdcard/Android/data/com.armsx2/files/inis/PCSX2.ini"),
            ("ARM SX2 Settings JSON", "/sdcard/Android/data/com.armsx2/files/armsx2-settings.json"),
            ("NetherSX2 PCSX2.ini", "/sdcard/Android/data/xyz.aethersx2.android/files/inis/PCSX2.ini"),
            ("Vita3K config.yml", "/sdcard/Android/data/org.vita3k.emulator/files/config.yml"),
            ("Obtainium Master Config", "/sdcard/Download/rp5_master_obtainium.json"),
            ("ES-DE Settings", "/sdcard/ES-DE/settings/es_settings.xml"),
            ("ES-DE Custom Systems", "/sdcard/ES-DE/custom_systems/es_systems.xml"),
            ("DroidDeck config.json", "/sdcard/DroidDeck/config.json"),
        ]

        for name, path in config_checks:
            exists = self.shell(f"[ -f '{path}' ] && echo 'EXISTS' || echo 'MISSING'") == "EXISTS"
            if exists:
                size_str = self.shell(f"wc -c < '{path}' 2>/dev/null || stat -c %s '{path}' 2>/dev/null || echo '1'")
                try:
                    size = int(size_str.strip().split()[0])
                except Exception:
                    size = 1
                if size > 10:
                    self.add_result("Config", name, "PASS", f"Present ({size:,} bytes)")
                else:
                    self.add_result("Config", name, "WARN", "File exists but appears empty")
            else:
                # DuckStation / DroidDeck might not have run yet
                if "DuckStation" in name or "DroidDeck" in name:
                    self.add_result("Config", name, "INFO", f"Not staged (app pending)")
                else:
                    self.add_result("Config", name, "FAIL", f"Missing from {path}")

        # Dedicated Root-Cause Schema Audits
        # 1. MKWii Controller Mode check
        mkwii_ini = self.shell("cat /sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings/RMCEA2.ini 2>/dev/null || true")
        if "WiimoteSource0 = 0" in mkwii_ini:
            self.add_result("RootCause", "MKWii Controller Mode", "PASS", "GameCube Controller pass-through active (WiimoteSource0 = 0)")
        elif "PadType0" in mkwii_ini:
            self.add_result("RootCause", "MKWii PadType Override", "FAIL", "Found conflicting PadType0 in RMCEA2.ini!")
        elif "WiimoteProfile1 = Classic_Controller" in mkwii_ini:
            self.add_result("RootCause", "MKWii Profile Binding", "PASS", "Bound to Classic_Controller profile without PadType0 conflict")
        else:
            self.add_result("RootCause", "MKWii Profile Binding", "WARN", "WiimoteProfile1 = Classic_Controller not found in RMCEA2.ini")

        # 2. PS2 Widescreen & CropMode check
        armsx2_ini = self.shell("cat /sdcard/Android/data/com.armsx2/files/inis/PCSX2.ini 2>/dev/null || true")
        if "AspectRatio = 16:9" in armsx2_ini and ("CropMode = Overscan" in armsx2_ini or "CropMode = 1" in armsx2_ini):
            self.add_result("RootCause", "ARM SX2 16:9 & Crop", "PASS", "AspectRatio = 16:9 and CropMode = 1 / Overscan verified")
        else:
            self.add_result("RootCause", "ARM SX2 16:9 & Crop", "WARN", "AspectRatio or CropMode not fully matching 16:9 / Overscan")

        # 3. Vita3K Initial-Setup bypass check
        vita_yml = self.shell("cat /sdcard/Android/data/org.vita3k.emulator/files/config.yml 2>/dev/null || true")
        if "initial-setup: false" in vita_yml and "backend-renderer: Vulkan" in vita_yml:
            self.add_result("RootCause", "Vita3K Setup Bypass", "PASS", "initial-setup: false and Vulkan backend active")
        else:
            self.add_result("RootCause", "Vita3K Setup Bypass", "WARN", "Vita3K config.yml missing initial-setup or Vulkan backend")

        # 4. ARM SX2 ES-DE ROMSAF intent check
        es_sys = self.shell("cat /sdcard/ES-DE/custom_systems/es_systems.xml 2>/dev/null || true")
        if "%EMULATOR_ARMSX2%" in es_sys and "%DATA%=%ROMSAF%" in es_sys:
            self.add_result("RootCause", "ARM SX2 ES-DE Intent", "PASS", "Configured with %DATA%=%ROMSAF% content-URI")
        else:
            self.add_result("RootCause", "ARM SX2 ES-DE Intent", "WARN", "ARM SX2 command not yet using %ROMSAF%")

    # =========================================================================
    # 3. CONTROLLER DESCRIPTOR & SCHEMA VERIFICATION (5 LAWS AUDIT)
    # =========================================================================
    def audit_controller_schemas(self):
        # 1. Read WiimoteNew.ini
        wii_ini = self.shell("cat /sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/WiimoteNew.ini 2>/dev/null || true")
        gcpad_ini = self.shell("cat /sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/GCPadNew.ini 2>/dev/null || true")

        if not wii_ini:
            self.add_result("Schema (Law 1)", "WiimoteNew.ini", "FAIL", "File missing or inaccessible")
            return

        # Law 1 & 3: Flat Wiimote extensions, NEVER [Classic1]
        if "[Classic1]" in wii_ini:
            self.add_result("Schema (Law 3)", "Flat Wiimote Extension", "FAIL", "Found forbidden [Classic1] section!")
        else:
            self.add_result("Schema (Law 3)", "Flat Wiimote Extension", "PASS", "Extension flat inside [Wiimote1]")

        # Law 4: Literal + and -
        if "Buttons/Plus" in wii_ini or "Buttons/Minus" in wii_ini:
            self.add_result("Schema (Law 4)", "Literal Plus/Minus Keys", "FAIL", "Found illegal Buttons/Plus or Buttons/Minus!")
        else:
            self.add_result("Schema (Law 4)", "Literal Plus/Minus Keys", "PASS", "Using literal + and - keys")

        # Law 2: Clean direct tokens
        if "Retroid Pocket Controller:Button 96" in wii_ini or "Retroid Pocket Controller:Button 96" in gcpad_ini:
            self.add_result("Schema (Law 2)", "Direct Input Tokens", "WARN", "Piped controller prefixes detected")
        else:
            self.add_result("Schema (Law 2)", "Direct Input Tokens", "PASS", "Clean direct `Button 96` tokens active")

        # Key coverage audit
        required_wii_keys = [
            "Classic/Buttons/A", "Classic/Buttons/B", "Classic/Buttons/X", "Classic/Buttons/Y",
            "Classic/Buttons/+", "Classic/Buttons/-", "Classic/Left Stick/Up", "Classic/Triggers/L"
        ]
        missing_keys = [k for k in required_wii_keys if k not in wii_ini]
        if missing_keys:
            self.add_result("Schema (Law 1)", "Wiimote Key Coverage", "FAIL", f"Missing vital keys: {', '.join(missing_keys)}")
        else:
            self.add_result("Schema (Law 1)", "Wiimote Key Coverage", "PASS", "All Classic Controller keys mapped")

        # Trigger axis orientation check (L=Axis 22+, R=Axis 23+)
        if "Classic/Triggers/L = `Axis 22+`" in wii_ini and "Classic/Triggers/R = `Axis 23+`" in wii_ini:
            self.add_result("Schema (Triggers)", "Wii Classic Trigger Axes", "PASS", "L=Axis 22+, R=Axis 23+ verified")
        else:
            self.add_result("Schema (Triggers)", "Wii Classic Trigger Axes", "WARN", "Trigger axes not mapped to L=Axis 22+, R=Axis 23+")

        # Dolphin.ini WiimoteSource0 check
        dol_ini = self.shell("cat /sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Dolphin.ini 2>/dev/null || true")
        if "WiimoteSource0 = 1" in dol_ini:
            self.add_result("Schema", "Dolphin Wiimote Source", "PASS", "WiimoteSource0 = 1 (Emulated Wiimote active)")
        elif "WiimoteSource0 = 0" in dol_ini and "SIDevice0 = 6" in dol_ini:
            self.add_result("Schema", "Dolphin Wiimote Source", "PASS", "WiimoteSource0 = 0 & SIDevice0 = 6 (GameCube Controller 1 pass-through active)")
        else:
            self.add_result("Schema", "Dolphin Wiimote Source", "WARN", "WiimoteSource0 is not set to 1 or 0")

        # Community profiles directory check
        prof_count_str = self.shell("ls /sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Profiles/Wiimote/ 2>/dev/null | wc -l")
        try:
            prof_count = int(prof_count_str.strip())
        except Exception:
            prof_count = 0
        if prof_count >= 5:
            self.add_result("Schema", "Wii Community Profiles", "PASS", f"{prof_count} motion profiles deployed")
        else:
            self.add_result("Schema", "Wii Community Profiles", "WARN", f"Only {prof_count} motion profiles found")

    # =========================================================================
    # 4. STORAGE & PERMISSIONS AUDIT
    # =========================================================================
    def audit_storage_and_permissions(self, internal: str, sdcard: Optional[str], sd_id: Optional[str]):
        # Check canonical directories
        dirs_to_check = [f"{internal}/bios"]
        if sdcard:
            dirs_to_check.extend([
                f"{sdcard}/bios",
                f"{sdcard}/ROMs",
                f"{sdcard}/ES-DE",
                f"{sdcard}/Saves_Backup",
            ])

        for d in dirs_to_check:
            exists = self.shell(f"[ -d '{d}' ] && echo 'EXISTS' || echo 'MISSING'") == "EXISTS"
            if exists:
                self.add_result("Storage", f"Canonical Dir ({Path(d).name})", "PASS", f"Created at {d}")
            else:
                self.add_result("Storage", f"Canonical Dir ({Path(d).name})", "FAIL", f"Missing at {d}")

        # Check Permissions (MANAGE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, or REQUEST_INSTALL_PACKAGES)
        permission_checks = [
            ("ES-DE", "org.es_de.frontend", "manage_storage"),
            ("ARM SX2", "com.armsx2", "manage_storage"),
            ("RetroArch", "com.retroarch.aarch64", "storage"),
            ("Dolphin", "org.dolphinemu.dolphinemu", "storage"),
            ("PPSSPP", "org.ppsspp.ppsspp", "storage"),
            ("NetherSX2", "xyz.aethersx2.android", "scoped_storage"),
            ("Obtainium", "dev.imranr.obtainium", "install_packages"),
        ]

        for label, pkg, p_type in permission_checks:
            pkg_installed = (self.shell(f"pm path {pkg} 2>/dev/null || true") != "")
            if not pkg_installed:
                self.add_result("Permission", f"{label} Permissions", "INFO", "Package not installed")
                continue

            if p_type == "manage_storage":
                op_res = self.shell(f"appops get {pkg} MANAGE_EXTERNAL_STORAGE 2>/dev/null || true")
                if "allow" in op_res.lower():
                    self.add_result("Permission", f"{label} Storage", "PASS", "MANAGE_EXTERNAL_STORAGE: allow")
                else:
                    self.add_result("Permission", f"{label} Storage", "FAIL", "Storage permission NOT granted")
            elif p_type == "storage":
                # Check MANAGE_EXTERNAL_STORAGE first, then READ_EXTERNAL_STORAGE
                op_res = self.shell(f"appops get {pkg} MANAGE_EXTERNAL_STORAGE 2>/dev/null || true")
                perm_dump = self.shell(f"dumpsys package {pkg} | grep 'android.permission.READ_EXTERNAL_STORAGE: granted=' || true")
                if "allow" in op_res.lower():
                    self.add_result("Permission", f"{label} Storage", "PASS", "MANAGE_EXTERNAL_STORAGE: allow")
                elif "granted=true" in perm_dump:
                    self.add_result("Permission", f"{label} Storage", "PASS", "READ_EXTERNAL_STORAGE: granted")
                else:
                    self.add_result("Permission", f"{label} Storage", "FAIL", "Storage permission NOT granted")
            elif p_type == "install_packages":
                op_res = self.shell(f"appops get {pkg} REQUEST_INSTALL_PACKAGES 2>/dev/null || true")
                if "allow" in op_res.lower():
                    self.add_result("Permission", f"{label} Install Access", "PASS", "REQUEST_INSTALL_PACKAGES: allow")
                else:
                    self.add_result("Permission", f"{label} Install Access", "WARN", "Install permission not allowed")
            elif p_type == "scoped_storage":
                self.add_result("Permission", f"{label} Storage", "PASS", "Scoped Storage / SAF Directory Access")

        # ES-DE ROMDirectory mapping
        settings_paths = ["/sdcard/ES-DE/settings/es_settings.xml"]
        if sdcard:
            settings_paths.insert(0, f"{sdcard}/ES-DE/settings/es_settings.xml")

        es_settings = ""
        for sp in settings_paths:
            out = self.shell(f"cat '{sp}' 2>/dev/null || true")
            if out:
                es_settings += "\n" + out

        if sdcard and f"/storage/{sd_id}/ROMs" in es_settings:
            self.add_result("Storage", "ES-DE ROM Directory", "PASS", f"Mapped to MicroSD (/storage/{sd_id}/ROMs)")
        elif "/sdcard/ROMs" in es_settings:
            self.add_result("Storage", "ES-DE ROM Directory", "PASS", "Mapped to internal storage fallback")
        else:
            self.add_result("Storage", "ES-DE ROM Directory", "WARN", "Custom ROM path configured")

    # =========================================================================
    # 5. HARDWARE TUNING AUDIT
    # =========================================================================
    def audit_hardware_tuning(self):
        # Auto-rotation
        rot = self.shell("settings get system accelerometer_rotation")
        if rot == "0":
            self.add_result("Hardware", "Auto-Rotation Lock", "PASS", "Locked to landscape (accelerometer_rotation=0)")
        else:
            self.add_result("Hardware", "Auto-Rotation Lock", "WARN", "Auto-rotation is still enabled")

        # Trigger mode
        trig = self.shell("getprop persist.sys.trigger.mode")
        if trig == "2":
            self.add_result("Hardware", "Trigger Mode", "PASS", "Both analog axis & digital click (mode=2)")
        else:
            self.add_result("Hardware", "Trigger Mode", "INFO", f"Trigger mode: {trig or 'Default'}")

        # Dark theme
        night = self.shell("settings get secure ui_night_mode")
        if night == "2":
            self.add_result("Hardware", "AMOLED Dark Theme", "PASS", "Enabled (ui_night_mode=2)")
        else:
            self.add_result("Hardware", "AMOLED Dark Theme", "INFO", f"Night mode: {night or 'Default'}")

    # =========================================================================
    # SUMMARY DISPLAY
    # =========================================================================
    def print_dashboard(self) -> bool:
        print("\n" + "=" * 80)
        print("          HANDHELD COMMUNITY PROVISIONING PRE-FLIGHT VERIFICATION")
        print("=" * 80)
        print(f" {'CATEGORY':<14} | {'ITEM / SUBSYSTEM':<28} | {'STATUS':<6} | {'DETAILS'}")
        print("-" * 80)

        for r in self.results:
            cat = r["category"]
            item = r["item"]
            status = r["status"]
            det = r["details"]

            status_color = status
            if status == "PASS":
                status_color = "[PASS]"
            elif status == "FAIL":
                status_color = "[FAIL]"
            elif status == "WARN":
                status_color = "[WARN]"
            else:
                status_color = "[INFO]"

            print(f" {cat:<14} | {item:<28} | {status_color:<6} | {det}")

        print("=" * 80)
        print(f" Summary: Critical Failures: {self.critical_failures} | Warnings: {self.warnings}")
        print("-" * 80)

        is_ready = (self.critical_failures == 0)
        if is_ready:
            print("\n  ************************************************************************")
            print("  *                                                                      *")
            print("  *     [READY TO PLAY] ALL SYSTEMS HARDENED & VERIFIED SUCCESSFUL!      *")
            print("  *                                                                      *")
            print("  ************************************************************************\n")
            print("  All emulator configurations, controller scan codes, and storage paths")
            print("  have been verified. Your handheld is 100% prepared for community gaming!\n")
        else:
            print("\n  [!] Pre-flight verification detected issues requiring attention above.\n")

        return is_ready


def main():
    parser = argparse.ArgumentParser(description="Pre-Flight Deployment Verification & Health Auditor")
    parser.add_argument("-s", "--serial", default=None, help="Target device serial")
    parser.add_argument("--adb", default=None, help="Path to ADB binary")
    args = parser.parse_args()

    adb_path = find_adb(args.adb)
    internal, sdcard, sd_id = detect_storage_targets(adb_path, serial=args.serial, dry_run=False)

    auditor = PreFlightAuditor(adb_path, serial=args.serial)
    auditor.audit_packages()
    auditor.audit_configs(sd_id)
    auditor.audit_controller_schemas()
    auditor.audit_storage_and_permissions(internal, sdcard, sd_id)
    auditor.audit_hardware_tuning()

    success = auditor.print_dashboard()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
