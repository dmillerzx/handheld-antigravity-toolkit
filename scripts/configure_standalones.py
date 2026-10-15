#!/usr/bin/env python3
"""
scripts/configure_standalones.py — Dynamic 3D Emulator Profiling Engine
========================================================================
Injects optimized configurations, controller mappings, Vulkan rendering
profiles, and audio settings headlessly across DuckStation, NetherSX2,
Dolphin, PPSSPP, Flycast, Azahar, and Vita3K based on dynamic device profiles.
"""

import argparse
import configparser
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Import dynamic device profiling helper
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import detect_device_profile, detect_storage_targets, load_profile_by_id


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


class StandaloneConfigurator:
    def __init__(
        self,
        adb_path: str,
        serial: Optional[str] = None,
        sd_id: Optional[str] = None,
        profile: Optional[Dict] = None,
        dry_run: bool = False
    ):
        self.adb = adb_path
        self.serial = serial
        self.dry_run = dry_run
        self.profile = profile or {}
        self.sd_id = sd_id
        self.bios_dir = f"/storage/{self.sd_id}/bios" if self.sd_id else "/sdcard/bios"
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rp_standalones_"))

        # Profile extraction
        self.emulation = self.profile.get("emulation", {})
        self.soc = self.profile.get("soc", {})
        self.controls = self.profile.get("controls", {})
        self.force_widescreen = self.emulation.get("force_widescreen", True)
        self.supports_turnip = self.soc.get("supports_turnip", False) and str(self.soc.get("gpu_family", "")).startswith("adreno")

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

    def push_file(self, local_path: Path, remote_path: str) -> None:
        parent = str(Path(remote_path).parent).replace("\\", "/")
        self.shell(f"mkdir -p '{parent}'", check=False)
        print(f"    -> Pushing {local_path.name} -> {remote_path}")
        self.adb_cmd("push", str(local_path), remote_path)

    # 1. DUCKSTATION (PS1)
    def configure_duckstation(self) -> None:
        scale = self.emulation.get("duckstation_resolution_scale", 5)
        print(f"\n[*] Configuring DuckStation (PS1 - {scale}x Vulkan & Low Latency Audio)...")
        content = f"""[Main]
AutoHideTouchscreenController = true
ConfirmPowerOff = false

[BIOS]
SearchDirectory = {self.bios_dir}

[Audio]
Backend = Cubeb
BufferSize = 20
Resampler = Gaussian
Sync = true

[Display]
OptimalFramePacing = true
ReduceInputLatency = true
ShowFPS = false

[GPU]
Renderer = Vulkan
ResolutionScale = {scale}
PGXPEnable = true
PGXPTextureCorrection = true
PGXPColorCorrection = true
TextureFilter = Nearest
ChromaSmoothing = true

[Pad1]
Type = AnalogController
AnalogDPadInDigitalMode = true

[Touchscreen]
ControllerView = None
"""
        local_cfg = self.temp_dir / "duckstation_settings.ini"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/com.github.stenzek.duckstation/files/settings.ini")
        self.push_file(local_cfg, "/sdcard/duckstation/settings.ini")

    # 2. NETHERSX2 (PS2)
    def configure_nethersx2(self) -> None:
        scale = self.emulation.get("nethersx2_upscale_multiplier", 2.25)
        aspect = "1" if self.force_widescreen else "0"
        ws_patches = "true" if self.force_widescreen else "false"
        print(f"\n[*] Configuring NetherSX2 (PS2 - {scale}x Vulkan, SPU2 Interpolation & Widescreen={ws_patches})...")
        content = f"""[General]
Bios = scph70012.bin
BiosDirectory = {self.bios_dir}
WarnAboutUnsafeSettings = false

[SPU2/Mixing]
Interpolation = 4
Latency = 1
SyncMode = 0

[EmuCore/GS]
Renderer = Vulkan
UpscaleMultiplier = {scale}
AspectRatio = {aspect}
EnableWideScreenPatches = {ws_patches}
EnableCheats = true
ThreadedPresentation = true
Hacks = 1

[Touchscreen]
ControllerView = None
"""
        local_cfg = self.temp_dir / "PCSX2.ini"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/xyz.aethersx2.android/files/inis/PCSX2.ini")

    # 3. DOLPHIN (GameCube / Wii)
    def configure_dolphin(self) -> None:
        scale = self.emulation.get("dolphin_internal_resolution", 2.5)
        print(f"\n[*] Configuring Dolphin (GC/Wii - {scale}x Vulkan, Controller & DSP Audio)...")
        # Dolphin.ini (GC & Wii Virtual Console Setup)
        wii_widescreen = "True" if self.force_widescreen else "False"
        dolphin_ini = f"""[Core]
GFXBackend = Vulkan
Fastmem = True
DualCore = True
EnableCheats = True
CPUThread = True
WiimoteEnableGCControllers = True

[DSP]
Backend = OpenSLES
DSPThread = True
Volume = 100
WASAPIDevice = default

[Interface]
ConfirmStop = False
ShowToolbar = False

[Wii]
Enable = True
Widescreen = {wii_widescreen}
ProgressiveScan = True
Language = 1
PAL60 = True

[Android]
JoystickRelCenter = False
ShowInputOverlay = False
"""
        # GFX.ini (Graphics & Performance)
        aspect_ratio = 1 if self.force_widescreen else 0
        gfx_ini = f"""[Settings]
Backend = Vulkan
InternalResolution = {scale}
AspectRatio = {aspect_ratio}
WideScreenHack = False
WaitForShadersBeforeStarting = False
VSync = True
ShaderCompilationMode = 2

[Enhancements]
ArbitraryMipmapDetection = True
ForceTrueColor = True
MaxAnisotropy = 2

[Hacks]
FastDepthCalc = True
DeferEFBCopies = True
"""
        # GCPadNew.ini (Controller mapping)
        gcpad_ini = """[GCPad1]
Device = Android/1/Retroid Pocket Controller
Buttons/A = `Button 96`
Buttons/B = `Button 97`
Buttons/X = `Button 99`
Buttons/Y = `Button 100`
Buttons/Z = `Button 103`
Buttons/Start = `Button 108`
Main Stick/Up = `Axis 1-`
Main Stick/Down = `Axis 1+`
Main Stick/Left = `Axis 0-`
Main Stick/Right = `Axis 0+`
Main Stick/Modifier = `Shift`
Main Stick/Modifier/Range = 50.000000
C-Stick/Up = `Axis 14-`
C-Stick/Down = `Axis 14+`
C-Stick/Left = `Axis 11-`
C-Stick/Right = `Axis 11+`
C-Stick/Modifier = `Control`
C-Stick/Modifier/Range = 50.000000
D-Pad/Up = `Hat 0N` | `Button 19`
D-Pad/Down = `Hat 0S` | `Button 20`
D-Pad/Left = `Hat 0W` | `Button 21`
D-Pad/Right = `Hat 0E` | `Button 22`
Triggers/L = `Axis 23+` | `Button 104`
Triggers/R = `Axis 22+` | `Button 105`
Triggers/Threshold = 50.000000
Triggers/L-Analog = `Axis 23+`
Triggers/R-Analog = `Axis 22+`
"""
        # WiimoteNew.ini (Classic controller mapped)
        wiimote_ini = """[Wiimote1]
Device = Android/1/Retroid Pocket Controller
Source = 1
Extension = Classic
Buttons/A = `Button 96`
Buttons/B = `Button 97`
Buttons/1 = `Button 99`
Buttons/2 = `Button 100`
Buttons/- = `Button 109`
Buttons/+ = `Button 108`
D-Pad/Up = `Hat 0N` | `Button 19`
D-Pad/Down = `Hat 0S` | `Button 20`
D-Pad/Left = `Hat 0W` | `Button 21`
D-Pad/Right = `Hat 0E` | `Button 22`
[Classic1]
Device = Android/1/Retroid Pocket Controller
Buttons/A = `Button 96`
Buttons/B = `Button 97`
Buttons/X = `Button 99`
Buttons/Y = `Button 100`
Buttons/ZL = `Button 102`
Buttons/ZR = `Button 103`
Buttons/Plus = `Button 108`
Buttons/Minus = `Button 109`
Left Stick/Up = `Axis 1-`
Left Stick/Down = `Axis 1+`
Left Stick/Left = `Axis 0-`
Left Stick/Right = `Axis 0+`
Right Stick/Up = `Axis 14-`
Right Stick/Down = `Axis 14+`
Right Stick/Left = `Axis 11-`
Right Stick/Right = `Axis 11+`
D-Pad/Up = `Hat 0N` | `Button 19`
D-Pad/Down = `Hat 0S` | `Button 20`
D-Pad/Left = `Hat 0W` | `Button 21`
D-Pad/Right = `Hat 0E` | `Button 22`
Triggers/L = `Axis 23+` | `Button 104`
Triggers/R = `Axis 22+` | `Button 105`
Triggers/Threshold = 50.000000
"""
        hotkeys_ini = """[Hotkeys]
Device = Android/1/Retroid Pocket Controller
General/Toggle Pause = F10
General/Stop = Escape
"""
        freelook_ini = """[FreeLook1]
Device = Android/1/Retroid Pocket Controller
"""
        f_dol = self.temp_dir / "Dolphin.ini"
        f_dol.write_text(dolphin_ini, encoding="utf-8")
        f_gfx = self.temp_dir / "GFX.ini"
        f_gfx.write_text(gfx_ini, encoding="utf-8")
        f_pad = self.temp_dir / "GCPadNew.ini"
        f_pad.write_text(gcpad_ini, encoding="utf-8")
        f_wii = self.temp_dir / "WiimoteNew.ini"
        f_wii.write_text(wiimote_ini, encoding="utf-8")
        f_hot = self.temp_dir / "Hotkeys.ini"
        f_hot.write_text(hotkeys_ini, encoding="utf-8")
        f_hot2 = self.temp_dir / "HotKey.ini"
        f_hot2.write_text(hotkeys_ini, encoding="utf-8")
        f_free = self.temp_dir / "FreeLookController.ini"
        f_free.write_text(freelook_ini, encoding="utf-8")

        for f in [f_dol, f_gfx, f_pad, f_wii, f_hot, f_hot2, f_free]:
            self.push_file(f, f"/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/{f.name}")
            self.push_file(f, f"/sdcard/dolphin-emu/Config/{f.name}")

    # 4. PPSSPP (PSP)
    def configure_ppsspp(self) -> None:
        scale = self.emulation.get("ppsspp_resolution_scale", 4)
        print(f"\n[*] Configuring PPSSPP (PSP - {scale}x Vulkan & Low Latency)...")
        content = f"""[Audio]
AudioLatency = 0
AudioResampler = True
GlobalVolume = 10

[Graphics]
GraphicsBackend = 3
InternalResolution = {scale}
AutoFrameskip = False
FrameSkip = 0
AnisotropyLevel = 16
BufferMode = 1
ShowTouchControls = False
FullScreen = True
VSyncInterval = 1

[Control]
ShowTouchControls = False
"""
        local_cfg = self.temp_dir / "ppsspp.ini"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/PSP/SYSTEM/ppsspp.ini")
        self.push_file(local_cfg, "/sdcard/Android/data/org.ppsspp.ppsspp/files/PSP/SYSTEM/ppsspp.ini")

    # 5. FLYCAST (Dreamcast)
    def configure_flycast(self) -> None:
        scale = self.emulation.get("flycast_res_scale", 2)
        ws = 1 if self.force_widescreen else 0
        print(f"\n[*] Configuring Flycast (Dreamcast - {scale}x Vulkan, Widescreen={ws} & AICA DSP Audio)...")
        content = f"""[aica]
AutoLatency = yes
BufferSize = 2822
DSPEnabled = yes
GlobalVolume = 100

[rend]
rend = 2
res_scale = {scale}
widescreen = {ws}
cable = 0
Fog = 1
Vsync = 1
"""
        local_cfg = self.temp_dir / "emu.cfg"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/com.flycast.emulator/files/emu.cfg")
        self.push_file(local_cfg, "/sdcard/Flycast/emu.cfg")

    # 6. AZAHAR (3DS)
    def configure_azahar(self) -> None:
        scale = self.emulation.get("azahar_resolution_factor", 3)
        turnip_line = "custom_driver = /sdcard/Download/drivers/Turnip_v26.0.0_R8.zip\n" if self.supports_turnip else ""
        driver_desc = "Mesa Turnip Driver" if self.supports_turnip else "System Vulkan Driver"
        print(f"\n[*] Configuring Azahar (3DS - {scale}x Vulkan, Async Shaders & {driver_desc})...")
        content = f"""[Renderer]
graphics_api = 1
resolution_factor = {scale}
async_shader_compilation = true
{turnip_line}use_disk_shader_cache = true
use_vsync_new = true

[Layout]
layout_option = 0
swap_screen = false

[Audio]
output_engine = 0
"""
        local_cfg = self.temp_dir / "azahar_config.ini"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/org.azahar_emu.azahar/files/config/config.ini")

        # Check bios/ for aes_keys.txt and copy to sysdata/
        bios_keys = list((WORKSPACE_ROOT / "bios").rglob("*aes_keys*.txt"))
        if bios_keys:
            print(f"    -> Staging 3DS AES keys from {bios_keys[0]}...")
            self.push_file(bios_keys[0], "/sdcard/Android/data/org.azahar_emu.azahar/files/sysdata/aes_keys.txt")
        else:
            self.shell("mkdir -p /sdcard/Android/data/org.azahar_emu.azahar/files/sysdata", check=False)

    # 7. VITA3K (PS Vita)
    def configure_vita3k(self) -> None:
        scale = self.emulation.get("vita3k_resolution_multiplier", 2)
        turnip_line = "custom-driver: /sdcard/Download/drivers/Turnip_v26.0.0_R8.zip\n" if self.supports_turnip else ""
        driver_desc = "Mesa Turnip Driver" if self.supports_turnip else "System Vulkan Driver"
        print(f"\n[*] Configuring Vita3K (PS Vita - {scale}x Vulkan & {driver_desc})...")
        content = f"""backend: Vulkan
resolution-multiplier: {scale}
{turnip_line}vsync: true
fullscreen: true
"""
        local_cfg = self.temp_dir / "config.yml"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/org.vita3k.emulator/files/vita/config.yml")
        self.push_file(local_cfg, "/sdcard/Android/data/org.vita3k.emulator/files/config.yml")

    # 8. ES-DE STANDALONE EMULATOR ROUTING
    def configure_esde_routing(self) -> None:
        print("\n[*] Locking down ES-DE standalone routing for all 3D systems...")
        source_systems = WORKSPACE_ROOT / "configs" / "es_systems.xml"
        source_settings = WORKSPACE_ROOT / "configs" / "es_settings.xml"

        target_rom_dir = f"/storage/{self.sd_id}/ROMs" if self.sd_id else "/sdcard/ROMs"

        # 1. Deploy custom_systems/es_systems.xml
        if source_systems.exists():
            self.push_file(source_systems, "/sdcard/ES-DE/custom_systems/es_systems.xml")
            if self.sd_id:
                self.push_file(source_systems, f"/storage/{self.sd_id}/ES-DE/custom_systems/es_systems.xml")

        # 2. Deploy es_settings.xml with verified AlternativeEmulator keys & dynamic ROMDirectory
        if source_settings.exists():
            content = source_settings.read_text(encoding="utf-8")
            content_mod = re.sub(
                r'<string\s+name="ROMDirectory"\s+value="[^"]*"',
                f'<string name="ROMDirectory" value="{target_rom_dir}"',
                content
            )
            local_settings = self.temp_dir / "es_settings.xml"
            local_settings.write_text(content_mod, encoding="utf-8")
            self.push_file(local_settings, "/sdcard/ES-DE/settings/es_settings.xml")
            if self.sd_id:
                self.push_file(local_settings, f"/storage/{self.sd_id}/ES-DE/settings/es_settings.xml")
        print("    [OK] ES-DE custom_systems & AlternativeEmulator mappings locked down.")

    def run_all(self) -> None:
        print(f"\n[Standalone 3D Profiler] Active Profile: {self.profile.get('name', 'Unknown')}")
        print(f"[Standalone 3D Profiler] MicroSD Root   : {f'/storage/{self.sd_id}' if self.sd_id else 'None (/sdcard/ fallback)'}")
        print(f"[Standalone 3D Profiler] Widescreen Fix : {self.force_widescreen}")
        print(f"[Standalone 3D Profiler] Turnip Support : {self.supports_turnip}")
        self.configure_duckstation()
        self.configure_nethersx2()
        self.configure_dolphin()
        self.configure_ppsspp()
        self.configure_flycast()
        self.configure_azahar()
        self.configure_vita3k()
        self.configure_esde_routing()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        print("\n========================================================================")
        print("   All Standalone 3D Emulators & ES-DE Routing Successfully Configured!")
        print("========================================================================")


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone 3D Emulator Configurator with Dynamic Hardware Profiles")
    parser.add_argument("-s", "--serial", default=None, help="Target device serial")
    parser.add_argument("--sd-id", default=None, help="MicroSD volume UUID (auto-detected if omitted)")
    parser.add_argument("--profile", default=None, help="Override device profile ID (rp5, rp_mini, rp4_pro, odin2, generic)")
    parser.add_argument("--adb", default=None, help="Path to ADB binary")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without execution")
    args = parser.parse_args()

    adb_path = find_adb(args.adb)

    # Dynamic storage detection
    internal_root, sd_root, detected_sd_id = detect_storage_targets(adb_path, serial=args.serial, dry_run=args.dry_run)
    sd_id = args.sd_id or detected_sd_id

    # Dynamic profile detection
    profile, model_name = detect_device_profile(adb_path, serial=args.serial, override_id=args.profile, dry_run=args.dry_run)

    configurator = StandaloneConfigurator(
        adb_path=adb_path,
        serial=args.serial,
        sd_id=sd_id,
        profile=profile,
        dry_run=args.dry_run
    )
    configurator.run_all()


if __name__ == "__main__":
    main()
