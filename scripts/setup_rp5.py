#!/usr/bin/env python3
"""
setup_rp5.py — Dynamic Automated Android Handheld Provisioning Engine
====================================================================
Handles automated zero-touch provisioning, Android 12/13 performance tweaks,
canonical directory scaffolding, dynamic device hardware profiling, GPU driver
staging with GPU guards, and AppOps MANAGE_EXTERNAL_STORAGE grants.

Supports Retroid Pocket 5, Retroid Pocket Mini, Retroid Pocket 4 Pro,
AYN Odin 2, and generic Android handhelds via dynamic JSON device profiles.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Import dynamic device profiling helper
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import (
    detect_device_profile,
    detect_storage_targets,
    list_available_profiles,
    load_profile_by_id,
)

# Fallback Obtainium configuration if configs/rp5_master_obtainium.json is missing
DEFAULT_OBTAINIUM_PATH = WORKSPACE_ROOT / "configs" / "rp5_master_obtainium.json"
DEFAULT_ESDE_CONFIG_PATH = WORKSPACE_ROOT / "configs" / "es_settings.xml"
DEFAULT_DRIVERS_PATH = WORKSPACE_ROOT / "drivers"

# Key emulator & frontend packages that benefit from MANAGE_EXTERNAL_STORAGE
TARGET_PACKAGES = [
    ("dev.imranr.obtainium", "Obtainium App Updater"),
    ("org.es_de.frontend", "ES-DE Frontend"),
    ("com.retroarch.aarch64", "RetroArch (64-bit)"),
    ("com.armsx2", "ARM SX2 (PS2)"),
    ("come.nanodata.armsx2", "ARM SX2 (PS2, alternate package ID)"),
    ("xyz.aethersx2.android", "NetherSX2 / AetherSX2 (PS2)"),
    ("org.ppsspp.ppsspp", "PPSSPP"),
    ("org.azahar_emu.azahar", "Azahar (3DS)"),
    ("org.vita3k.emulator", "Vita3K (PS Vita)"),
    ("com.flycast.emulator", "Flycast (Dreamcast)"),
    ("com.magneticchen.daijishou", "Daijisho Frontend"),
    ("org.dolphinemu.dolphinemu", "Dolphin Emulator (GameCube/Wii)"),
    ("com.github.stenzek.duckstation", "DuckStation (PS1)"),
    ("com.droiddeck.launcher", "DroidDeck Launcher (Steam)"),
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
    ("eu.pokemmo.client", "PokeMMO Client"),
    ("org.eukaryot.sonic3air", "Sonic 3 A.I.R."),
    ("org.stjr.srb2", "Sonic Robo Blast 2"),
    ("com.fexed.spacecadetpinball", "Space Cadet 3D Pinball"),
    ("com.unofficial.balatro", "Balatro (Native Mobile)"),
    ("com.example.megamanxregenesis", "Mega Man X Regenesis"),
    ("org.godotengine.rockmanx816bitdemakemod", "Mega Man X8 16-bit Demake"),
    ("com.dishii.soh", "Ship of Harkinian (OOT)"),
    ("com.dishii.mm", "2 Ship 2 Harkinian (MM)"),
    ("com.starship.android", "Star Fox 64 (Starship)"),
    ("com.dishii.zelda3", "Zelda 3 (A Link to the Past)"),
    ("com.izzy.kart", "Mario Kart 64 (SpaghettiKart)"),
    ("com.perfectdark.port", "Perfect Dark"),
    ("com.sunjaycy.goldeneye", "GoldenEye 007 (Recomp)"),
    ("io.github.thatguymcd.dkrr.preview", "Diddy Kong Racing (DKR-R)"),
]

# Additional AppOps granted beyond MANAGE_EXTERNAL_STORAGE
EXTRA_APPOPS = {
    "dev.imranr.obtainium": ["REQUEST_INSTALL_PACKAGES"],
    "com.droiddeck.launcher": ["READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE", "REQUEST_INSTALL_PACKAGES"],
}

INTERNAL_ROOT = "/sdcard"
INTERNAL_DIRS = ["bios"]
SD_DIRS = ["bios", "ROMs", "ES-DE"]


class RP5Provisioner:
    def __init__(
        self,
        adb_path: str,
        serial: Optional[str] = None,
        profile: Optional[Dict] = None,
        dry_run: bool = False
    ):
        self.adb = adb_path
        self.serial = serial
        self.dry_run = dry_run
        self.profile = profile or {}
        self.device_model: Optional[str] = None
        self.sd_id: Optional[str] = None
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rp_provision_"))

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
            return False, "No ADB devices detected. Connect your handheld via USB or Wi-Fi.", devices

        if self.serial:
            match = next((d for d in devices if d["serial"] == self.serial), None)
            if not match:
                return False, f"Device with serial '{self.serial}' not found in attached devices.", devices
            if match["status"] == "unauthorized":
                return False, f"Device '{self.serial}' is UNAUTHORIZED. Unlock screen and tap 'Always allow from this computer'.", devices
            return True, f"Device '{self.serial}' connected and authorized.", devices

        authorized = [d for d in devices if d["status"] == "device"]
        unauthorized = [d for d in devices if d["status"] == "unauthorized"]

        if authorized:
            chosen = authorized[0]
            self.serial = chosen["serial"]
            return True, f"Connected to {chosen['serial']} ({chosen['extra']}).", devices
        elif unauthorized:
            return False, f"Device '{unauthorized[0]['serial']}' is UNAUTHORIZED. Unlock the screen and accept USB Debugging.", devices
        else:
            return False, f"Device found in status '{devices[0]['status']}'. Ensure USB debugging is active.", devices

    def query_device_specs(self) -> dict:
        """Inspects device properties to confirm hardware specs."""
        if self.dry_run:
            return {"model": "Handheld [DRY RUN]", "android_version": "13", "sdk": "33"}
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
        print("\n[*] [1/4] Applying Android 12/13 Phantom Process Killer bypass...")
        self.shell("/system/bin/device_config set_sync_disabled_for_tests persistent", check=False)
        self.shell("/system/bin/device_config put activity_manager max_phantom_processes 2147483647", check=False)
        self.shell("settings put global settings_enable_monitor_phantom_procs false", check=False)

        if not self.dry_run:
            val = self.shell("/system/bin/device_config get activity_manager max_phantom_processes", check=False)
            print(f"    -> max_phantom_processes configured to: {val or '2147483647'}")
        else:
            print("    -> [DRY RUN] Set max_phantom_processes=2147483647 and disabled monitor.")

    def discover_storage_targets(self) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Dynamically discovers internal storage (/sdcard) and mounted external MicroSD cards.
        Uses canonical FAT32/exFAT UUID format: ^[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$
        """
        return detect_storage_targets(self.adb, serial=self.serial, dry_run=self.dry_run)

    def scaffold_directories(self) -> None:
        """Creates canonical storage hierarchy: /sdcard/bios and /storage/<SD_ID>/{bios,ROMs,ES-DE}."""
        print("\n[*] [2/4] Scaffolding canonical storage folder structure...")
        internal, sdcard, self.sd_id = self.discover_storage_targets()

        print(f"    -> Internal storage: {internal}")
        if sdcard:
            print(f"    -> External MicroSD detected: {sdcard} (UUID: {self.sd_id})")
        else:
            print("    -> Notice: No external MicroSD card detected. Initializing internal fallback.")

        targets = [(internal, INTERNAL_DIRS)]
        if sdcard:
            targets.append((sdcard, SD_DIRS))
        else:
            # Fallback if no MicroSD is present: scaffold ROMs & ES-DE on internal storage
            targets.append((internal, ["ROMs", "ES-DE"]))

        for target, subdirs in targets:
            print(f"    Scaffolding {', '.join(subdirs)} on {target}...")
            mkdir_cmd = " && ".join([f"mkdir -p '{target}/{subdir}'" for subdir in subdirs])
            self.shell(mkdir_cmd, check=False)

        print("    -> Storage scaffolding complete.")

    def stage_obtainium_config(self, custom_path: Optional[Path] = None) -> None:
        """Pushes master obtainium configuration for 1-click batch emulator downloads."""
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

    def stage_esde_config(self, custom_path: Optional[Path] = None) -> None:
        """Pushes headless es_settings.xml pre-configured dynamically with canonical ROMDirectory."""
        print("\n[*] Staging headless ES-DE configuration with dynamic ROM path...")
        source_xml = custom_path or DEFAULT_ESDE_CONFIG_PATH
        if not source_xml.exists():
            print(f"    [!] Notice: ES-DE config not found at {source_xml}. Skipping.")
            return

        internal, sdcard, sd_id = self.discover_storage_targets()
        content = source_xml.read_text(encoding="utf-8")

        # Dynamically replace ROMDirectory value
        target_rom_dir = f"/storage/{sd_id}/ROMs" if sd_id else "/sdcard/ROMs"
        content_mod = re.sub(
            r'<string\s+name="ROMDirectory"\s+value="[^"]*"',
            f'<string name="ROMDirectory" value="{target_rom_dir}"',
            content
        )

        tmp_xml = self.temp_dir / "es_settings.xml"
        tmp_xml.write_text(content_mod, encoding="utf-8")

        dest_internal = f"{internal}/ES-DE/settings/es_settings.xml"
        self.shell(f"mkdir -p '{internal}/ES-DE/settings'", check=False)
        print(f"    Pushing dynamic {source_xml.name} -> {dest_internal} (ROMDirectory={target_rom_dir})")
        self.run_cmd("push", str(tmp_xml), dest_internal)

        if sdcard:
            dest_sd = f"{sdcard}/ES-DE/settings/es_settings.xml"
            self.shell(f"mkdir -p '{sdcard}/ES-DE/settings'", check=False)
            print(f"    Pushing dynamic {source_xml.name} -> {dest_sd}")
            self.run_cmd("push", str(tmp_xml), dest_sd)
        print("    -> Headless ES-DE configuration staged successfully.")

        # Stage custom_systems/es_systems.xml and es_find_rules.xml (Force Standalone 3D Emulators & Custom Rules)
        source_systems = WORKSPACE_ROOT / "configs" / "es_systems.xml"
        source_find_rules = WORKSPACE_ROOT / "configs" / "es_find_rules.xml"
        if source_systems.exists():
            dest_sys_internal = f"{internal}/ES-DE/custom_systems/es_systems.xml"
            self.shell(f"mkdir -p '{internal}/ES-DE/custom_systems'", check=False)
            print(f"    Pushing {source_systems.name} -> {dest_sys_internal}")
            self.run_cmd("push", str(source_systems), dest_sys_internal)
            if sdcard:
                dest_sys_sd = f"{sdcard}/ES-DE/custom_systems/es_systems.xml"
                self.shell(f"mkdir -p '{sdcard}/ES-DE/custom_systems'", check=False)
                print(f"    Pushing {source_systems.name} -> {dest_sys_sd}")
                self.run_cmd("push", str(source_systems), dest_sys_sd)

        if source_find_rules.exists():
            dest_rules_internal = f"{internal}/ES-DE/custom_systems/es_find_rules.xml"
            self.shell(f"mkdir -p '{internal}/ES-DE/custom_systems'", check=False)
            print(f"    Pushing {source_find_rules.name} -> {dest_rules_internal}")
            self.run_cmd("push", str(source_find_rules), dest_rules_internal)
            if sdcard:
                dest_rules_sd = f"{sdcard}/ES-DE/custom_systems/es_find_rules.xml"
                self.shell(f"mkdir -p '{sdcard}/ES-DE/custom_systems'", check=False)
                print(f"    Pushing {source_find_rules.name} -> {dest_rules_sd}")
                self.run_cmd("push", str(source_find_rules), dest_rules_sd)
            print("    -> ES-DE custom_systems standalone emulator overrides & find rules deployed.")

    def stage_turnip_drivers(self, drivers_dir: Optional[Path] = None) -> None:
        """
        Pushes staged Mesa Turnip GPU drivers from local drivers/ to /sdcard/Download/drivers/.
        GPU GUARD: Strictly skipped if device profile indicates a non-Adreno GPU (e.g. Mali).
        """
        soc = self.profile.get("soc", {})
        gpu_family = str(soc.get("gpu_family", "generic")).lower()
        supports_turnip = soc.get("supports_turnip", False) and gpu_family.startswith("adreno")

        if not supports_turnip:
            print(f"\n[*] [GPU GUARD] Device GPU ({soc.get('gpu_model', 'Non-Adreno')}) does not support Turnip drivers. Skipping Mesa driver staging.")
            return

        print("\n[*] Staging Mesa Turnip Adreno GPU drivers...")
        src_dir = drivers_dir or DEFAULT_DRIVERS_PATH
        if not src_dir.exists():
            print(f"    [!] Notice: Local drivers directory {src_dir} does not exist. Skipping.")
            return

        zips = list(src_dir.glob("*.zip"))
        if not zips:
            print("    [!] Notice: No driver .zip archives found in drivers/ staging folder. Skipping.")
            return

        remote_drivers_dir = "/sdcard/Download/drivers"
        self.shell(f"mkdir -p '{remote_drivers_dir}'", check=False)
        print(f"    Found {len(zips)} driver archive(s). Pushing to {remote_drivers_dir}...")
        for z in zips:
            print(f"    -> Pushing {z.name}...")
            self.run_cmd("push", str(z), f"{remote_drivers_dir}/{z.name}")
        print("    -> Mesa Turnip drivers staged successfully.")

    def tune_retroid_hardware(self) -> None:
        """Applies hardware tuning, disables lock screen, and optimizes trigger/gamepad defaults."""
        print("\n[*] Applying handheld hardware & system tuning...")
        # 1. Disable Android lock screen
        self.shell("locksettings set-disabled true", check=False)

        # 2. Disable on-screen floating game assistant icon overlay
        self.shell("settings put system is_show_floatingIcon 0", check=False)

        # 3. Disable accelerometer screen auto-rotation (Retro Game Corps guideline: lock to landscape)
        print("    -> Disabling screen auto-rotation (locking orientation to landscape)...")
        self.shell("settings put system accelerometer_rotation 0", check=False)
        self.shell("settings put system user_rotation 0", check=False)

        # 4. Disable UI touch and lockscreen audio click sounds
        print("    -> Disabling touch clicks and lockscreen sound effects...")
        self.shell("settings put system sound_effects_enabled 0", check=False)
        self.shell("settings put system lockscreen_sounds_enabled 0", check=False)

        # 5. Enable System Dark Theme (AMOLED battery & contrast optimization)
        print("    -> Enforcing System Dark Theme for AMOLED display...")
        self.shell("cmd uimode night yes", check=False)
        self.shell("settings put secure ui_night_mode 2", check=False)

        # 6. Ensure screen timeout does not interrupt scraping / downloads (10 min / 600,000ms)
        self.shell("settings put system screen_off_timeout 600000", check=False)

        # 7. Whitelist emulators and frontends from Android Doze background throttling
        print("    -> Whitelisting frontends & emulators from Android Doze power throttling...")
        for pkg in ["org.es_de.frontend", "com.retroarch.aarch64", "com.droiddeck.launcher"]:
            self.shell(f"dumpsys deviceidle whitelist +{pkg}", check=False)

        controls = self.profile.get("controls", {})
        gamepad_type = controls.get("gamepad_type", 0)
        trigger_mode = controls.get("trigger_mode", 2)

        # 8. Gamepad layout
        print(f"    -> Setting gamepad controller style (persist.sys.gamepad.type={gamepad_type})...")
        self.shell(f"setprop persist.sys.gamepad.type {gamepad_type}", check=False)

        # 9. Trigger mode
        print(f"    -> Setting trigger mode (persist.sys.trigger.mode={trigger_mode})...")
        self.shell(f"setprop persist.sys.trigger.mode {trigger_mode}", check=False)

        # 10. Power / end button behavior (2 = sleep/wake)
        self.shell("settings put system end_button_behavior 2", check=False)

        # 11. Enable Do Not Disturb (Russ & Joey recommendation: silence popups from hijacking input/focus)
        print("    -> Activating Do Not Disturb (zen_mode=1) to prevent notification focus loss...")
        self.shell("settings put global zen_mode 1", check=False)

        print("    -> System and hardware tuning complete.")

    def stage_droiddeck(self) -> None:
        """Deploys dynamic DroidDeck config and scaffolds prefix/Steam library directories."""
        print("\n[*] Staging DroidDeck configuration and storage structure...")
        internal, sdcard, sd_id = self.discover_storage_targets()

        self.shell("mkdir -p /sdcard/DroidDeck/prefixes/default", check=False)
        self.shell("mkdir -p /sdcard/Android/data/com.droiddeck.launcher/files", check=False)

        steam_target = f"/storage/{sd_id}/Games/Steam" if sd_id else "/sdcard/Games/Steam"
        if sdcard:
            self.shell(f"mkdir -p '{steam_target}'", check=False)

        cfg_source = WORKSPACE_ROOT / "configs" / "droiddeck_config.json"
        if cfg_source.exists():
            cfg_content = cfg_source.read_text(encoding="utf-8")
            cfg_content = re.sub(r'/storage/[^"]+/Games/Steam', steam_target, cfg_content)
            tmp_cfg = self.temp_dir / "droiddeck_config.json"
            tmp_cfg.write_text(cfg_content, encoding="utf-8")

            print(f"    -> Pushing DroidDeck config (Steam library -> {steam_target})...")
            self.run_cmd("push", str(tmp_cfg), "/sdcard/DroidDeck/config.json")
            self.run_cmd("push", str(tmp_cfg), "/sdcard/DroidDeck/settings.json")
            self.run_cmd("push", str(tmp_cfg), "/sdcard/Android/data/com.droiddeck.launcher/files/config.json")
            self.run_cmd("push", str(tmp_cfg), "/sdcard/Android/data/com.droiddeck.launcher/files/settings.json")

        vdf_source = WORKSPACE_ROOT / "configs" / "libraryfolders.vdf"
        if vdf_source.exists():
            vdf_content = vdf_source.read_text(encoding="utf-8")
            vdf_content = re.sub(r'/storage/[^"]+/Games/Steam', steam_target, vdf_content)
            tmp_vdf = self.temp_dir / "libraryfolders.vdf"
            tmp_vdf.write_text(vdf_content, encoding="utf-8")

            remote_vdf_dir = "/sdcard/DroidDeck/prefixes/default/drive_c/Program Files (x86)/Steam/config"
            self.shell(f"mkdir -p '{remote_vdf_dir}'", check=False)
            print(f"    -> Pre-seeding libraryfolders.vdf with dynamic mount: {steam_target}")
            self.run_cmd("push", str(tmp_vdf), f"{remote_vdf_dir}/libraryfolders.vdf")

        vita_firmware_sources = [
            WORKSPACE_ROOT / "scratch" / "PSP2UPDAT.PUP",
            WORKSPACE_ROOT / "bios" / "PSP2UPDAT.PUP",
        ]
        for vfw in vita_firmware_sources:
            if vfw.exists():
                print(f"    -> Staging Sony PS Vita OS Firmware ({vfw.name}) to /sdcard/Download/vita3k/...")
                self.shell("mkdir -p /sdcard/Download/vita3k", check=False)
                self.run_cmd("push", str(vfw), "/sdcard/Download/vita3k/PSP2UPDAT.PUP")
                break
        print("    -> DroidDeck and PS Vita firmware staging complete.")

    def stage_retroarch_engine(self) -> None:
        """Deploys ultra-low latency RetroArch configurations and low-pass audio filters."""
        print("\n[*] Staging Ultra-Low Latency RetroArch 2D engine & low-pass audio filters...")
        internal, sdcard, sd_id = self.discover_storage_targets()
        ra_base = f"/storage/{sd_id}/RetroArch" if sd_id else "/sdcard/RetroArch"

        ra_cfgs = WORKSPACE_ROOT / "configs" / "retroarch"
        if not ra_cfgs.exists():
            print("    [!] RetroArch configs directory not found. Skipping.")
            return

        internal_ra = "/sdcard/Android/data/com.retroarch.aarch64/files"
        self.shell(f"mkdir -p '{internal_ra}' '{ra_base}/config' '{ra_base}/filters/audio' '{ra_base}/shaders'", check=False)

        def patch_and_push(src: Path, dest_internal: str, dest_sd: Optional[str] = None):
            if not src.exists():
                return
            txt = src.read_text(encoding="utf-8", errors="replace")
            # Replace any hardcoded SD_ID or EEEF-F762 with dynamic sd_id or /sdcard
            if sd_id:
                txt = txt.replace("<SD_ID>", sd_id).replace("EEEF-F762", sd_id)
            else:
                txt = txt.replace("/storage/<SD_ID>/RetroArch", "/sdcard/RetroArch")
                txt = txt.replace("/storage/EEEF-F762/RetroArch", "/sdcard/RetroArch")
                txt = txt.replace("/storage/<SD_ID>/bios", "/sdcard/bios")
                txt = txt.replace("/storage/EEEF-F762/bios", "/sdcard/bios")
            tmp_f = self.temp_dir / src.name
            tmp_f.write_text(txt, encoding="utf-8")
            self.run_cmd("push", str(tmp_f), dest_internal)
            if dest_sd and sdcard:
                self.run_cmd("push", str(tmp_f), dest_sd)

        main_cfg = ra_cfgs / "retroarch.cfg"
        patch_and_push(main_cfg, f"{internal_ra}/retroarch.cfg", f"{ra_base}/config/retroarch.cfg")

        core_opts = ra_cfgs / "retroarch-core-options.cfg"
        patch_and_push(core_opts, f"{internal_ra}/retroarch-core-options.cfg", f"{ra_base}/config/retroarch-core-options.cfg")

        gba_dsp = ra_cfgs / "filters" / "audio" / "gba_lowpass.dsp"
        if gba_dsp.exists():
            self.shell(f"mkdir -p '{internal_ra}/filters/audio' '{ra_base}/filters/audio'", check=False)
            self.run_cmd("push", str(gba_dsp), f"{internal_ra}/filters/audio/gba_lowpass.dsp")
            if sdcard:
                self.run_cmd("push", str(gba_dsp), f"{ra_base}/filters/audio/gba_lowpass.dsp")

        mgba_cfg = ra_cfgs / "config" / "mGBA" / "mGBA.cfg"
        mgba_slangp = ra_cfgs / "config" / "mGBA" / "mGBA.slangp"
        if mgba_cfg.exists():
            self.shell(f"mkdir -p '{internal_ra}/config/mGBA' '{ra_base}/config/mGBA'", check=False)
            patch_and_push(mgba_cfg, f"{internal_ra}/config/mGBA/mGBA.cfg", f"{ra_base}/config/mGBA/mGBA.cfg")
        if mgba_slangp.exists():
            patch_and_push(mgba_slangp, f"{internal_ra}/config/mGBA/mGBA.slangp", f"{ra_base}/config/mGBA/mGBA.slangp")

        print("    -> RetroArch 2D engine & low-pass audio filters staged successfully.")

    def stage_widescreen_patches(self) -> None:
        """Executes stage_community_patches.py with dynamic profile."""
        script = WORKSPACE_ROOT / "scripts" / "stage_community_patches.py"
        if script.exists():
            print("\n[*] Deploying Universal PS2 & GameCube/Wii Community Patches...")
            cmd = [sys.executable, str(script), "--adb", self.adb]
            if self.serial:
                cmd.extend(["-s", self.serial])
            if self.profile.get("device_id"):
                cmd.extend(["--profile", self.profile["device_id"]])
            if self.sd_id:
                cmd.extend(["--sd-id", self.sd_id])
            if self.dry_run:
                cmd.append("--dry-run")
            subprocess.run(cmd, check=False)
        else:
            print("    [!] stage_community_patches.py not found. Skipping.")

    def run_standalone_config(self) -> None:
        """Executes configure_standalones.py with dynamic profile."""
        script = WORKSPACE_ROOT / "scripts" / "configure_standalones.py"
        if script.exists():
            print("\n[*] Injecting Standalone 3D Emulator Profiles...")
            cmd = [sys.executable, str(script), "--adb", self.adb]
            if self.serial:
                cmd.extend(["-s", self.serial])
            if self.profile.get("device_id"):
                cmd.extend(["--profile", self.profile["device_id"]])
            if self.sd_id:
                cmd.extend(["--sd-id", self.sd_id])
            if self.dry_run:
                cmd.append("--dry-run")
            subprocess.run(cmd, check=False)

    def run_retroarch_core_download(self) -> None:
        """Executes download_retroarch_cores.py."""
        script = WORKSPACE_ROOT / "scripts" / "download_retroarch_cores.py"
        if script.exists():
            print("\n[*] Provisioning RetroArch 2D/Arcade Cores & Assets...")
            cmd = [sys.executable, str(script), "--adb", self.adb]
            if self.serial:
                cmd.extend(["-s", self.serial])
            if self.dry_run:
                cmd.append("--dry-run")
            res = subprocess.run(cmd, check=False)
            if res.returncode != 0:
                print(f"\n[!] ERROR: download_retroarch_cores.py failed with returncode {res.returncode}")
                raise RuntimeError("RetroArch core and asset provisioning failed")

    def run_save_sync(self) -> None:
        """Executes sync_all_saves.py with dynamic storage detection."""
        script = WORKSPACE_ROOT / "scripts" / "sync_all_saves.py"
        if script.exists():
            print("\n[*] Executing Automated Save & State Backup Pipeline...")
            cmd = [sys.executable, str(script), "--adb", self.adb]
            if self.serial:
                cmd.extend(["-s", self.serial])
            if self.sd_id:
                cmd.extend(["--sd-id", self.sd_id])
            if self.dry_run:
                cmd.append("--dry-run")
            subprocess.run(cmd, check=False)

    def run_preflight_verification(self) -> None:
        """Executes verify_deployment.py to audit all subsystems post-provisioning."""
        script = WORKSPACE_ROOT / "scripts" / "verify_deployment.py"
        if script.exists():
            print("\n[*] Executing Automated Pre-Flight Deployment Verification...")
            cmd = [sys.executable, str(script), "--adb", self.adb]
            if self.serial:
                cmd.extend(["-s", self.serial])
            subprocess.run(cmd, check=False)

    def provision_all(self, apks_dir: Optional[Path] = None) -> None:
        """Runs the complete end-to-end community provisioning pipeline."""
        print("\n" + "=" * 72)
        print(f"   Starting Complete Zero-Touch Community Provisioning Pipeline")
        print(f"   Device Profile: {self.profile.get('name', 'Generic')}")
        print("=" * 72)
        self.unlock_phantom_process_killer()
        self.scaffold_directories()
        self.stage_obtainium_config()
        self.stage_esde_config()
        self.stage_turnip_drivers()
        self.tune_retroid_hardware()
        if apks_dir and apks_dir.exists():
            self.install_local_apks(apks_dir)
        self.grant_storage_permissions()
        self.stage_droiddeck()
        self.stage_retroarch_engine()
        self.stage_widescreen_patches()
        self.run_standalone_config()
        self.run_retroarch_core_download()
        self.run_save_sync()
        self.run_preflight_verification()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

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
                self.shell(f"pm grant {pkg} android.permission.READ_EXTERNAL_STORAGE 2>/dev/null || true", check=False)
                self.shell(f"pm grant {pkg} android.permission.WRITE_EXTERNAL_STORAGE 2>/dev/null || true", check=False)
                for extra_op in EXTRA_APPOPS.get(pkg, []):
                    print(f"    -> Granting {extra_op} to {label} ({pkg})...")
                    self.shell(f"appops set {pkg} {extra_op} allow", check=False)
                granted_count += 1

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
    which_adb = shutil.which("adb")
    if which_adb:
        return which_adb

    local_candidates = [
        WORKSPACE_ROOT / "platform-tools" / ("adb.exe" if sys.platform == "win32" else "adb"),
        WORKSPACE_ROOT.parent / "platform-tools" / ("adb.exe" if sys.platform == "win32" else "adb"),
    ]
    for cand in local_candidates:
        if cand.is_file():
            return str(cand)

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            sdk_adb = Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
            if sdk_adb.is_file():
                return str(sdk_adb)

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dynamic Automated ADB Provisioner with Hardware Profiles.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--serial", "-s", help="Target specific ADB device serial number.")
    parser.add_argument("--profile", help="Hardware profile ID (rp5, rp_mini, rp4_pro, odin2, generic).")
    parser.add_argument("--adb", help="Explicit path to adb binary.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate commands without modifying device.")
    parser.add_argument("--status", action="store_true", help="Check device connection and print hardware specs.")
    parser.add_argument("--skip-phantom", action="store_true", help="Skip Android 13 phantom process killer unlocks.")
    parser.add_argument("--skip-scaffold", action="store_true", help="Skip directory scaffolding on storage.")
    parser.add_argument("--skip-obtainium", action="store_true", help="Skip pushing rp5_master_obtainium.json.")
    parser.add_argument("--skip-esde", action="store_true", help="Skip staging headless ES-DE es_settings.xml.")
    parser.add_argument("--skip-drivers", action="store_true", help="Skip staging Mesa Turnip GPU drivers.")
    parser.add_argument("--skip-tuning", action="store_true", help="Skip Retroid OS hardware & system tuning.")
    parser.add_argument("--skip-permissions", action="store_true", help="Skip granting MANAGE_EXTERNAL_STORAGE.")
    parser.add_argument("--install-apks", action="store_true", help="Install any .apk files staged in apks/ folder.")
    parser.add_argument("--all", action="store_true", help="Execute complete zero-touch community provisioning pipeline.")
    args = parser.parse_args()

    print("=" * 72)
    print("   Automated Handheld Community Provisioning Pipeline")
    print("=" * 72)

    adb_bin = args.adb or find_adb()
    if not adb_bin:
        print("[ERROR] Could not locate 'adb' in PATH or local workspace directories.")
        print("Please install Android platform-tools or run with --adb <path_to_adb>.")
        return 1

    print(f"ADB Binary: {adb_bin}")

    # Dynamic hardware profiling & detection
    profile, model_name = detect_device_profile(adb_bin, serial=args.serial, override_id=args.profile, dry_run=args.dry_run)
    print(f"Detected Hardware  : {model_name}")
    print(f"Loaded Profile     : {profile.get('name', 'Generic')} (ID: {profile.get('device_id', 'unknown')})")

    provisioner = RP5Provisioner(adb_bin, serial=args.serial, profile=profile, dry_run=args.dry_run)
    is_connected, msg, device_list = provisioner.check_connection()

    print(f"Connection Status  : {msg}")

    if not is_connected and not args.dry_run:
        print("\n[!] Setup paused: Handheld is not ready.")
        print("    Troubleshooting steps:")
        print("    1. Connect device via USB-C to this computer.")
        print("    2. On device: Settings -> System -> Developer Options -> Enable 'USB Debugging'.")
        print("    3. When prompted on screen: Check 'Always allow from this computer' and tap 'Allow'.")
        print("    4. Re-run: python scripts/setup_rp5.py")
        return 2

    specs = provisioner.query_device_specs()
    print("\n--- Device Information ---")
    for k, v in specs.items():
        print(f"  {k:18}: {v}")
    print("--------------------------")

    if args.status:
        return 0

    if args.all:
        provisioner.provision_all(apks_dir=WORKSPACE_ROOT / "apks")
        print("\n" + "=" * 72)
        print("   Complete Handheld Community Provisioning Finished!")
        print("=" * 72)
        return 0

    if not args.skip_phantom:
        provisioner.unlock_phantom_process_killer()
    if not args.skip_scaffold:
        provisioner.scaffold_directories()
    if not args.skip_obtainium:
        provisioner.stage_obtainium_config()
    if not args.skip_esde:
        provisioner.stage_esde_config()
    if not args.skip_drivers:
        provisioner.stage_turnip_drivers()
    if not args.skip_tuning:
        provisioner.tune_retroid_hardware()
    if args.install_apks:
        provisioner.install_local_apks(WORKSPACE_ROOT / "apks")
    if not args.skip_permissions:
        provisioner.grant_storage_permissions()

    print("\n" + "=" * 72)
    print("   Provisioning Sequence Complete!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
