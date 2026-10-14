#!/usr/bin/env python3
"""
Automated Standalone 3D Emulator Configuration Script for Retroid Pocket 5 (RP5)
--------------------------------------------------------------------------------
Injects tuned configurations, controller mappings, Vulkan rendering profiles,
and audio settings headlessly across DuckStation, NetherSX2, Dolphin, PPSSPP,
Flycast, Azahar, and Vita3K.
"""

import argparse
import configparser
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SERIAL = "ff152647"
DEFAULT_SD_ID = "EEEF-F762"


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
    def __init__(self, adb_path: str, serial: str = DEFAULT_SERIAL, sd_id: str = DEFAULT_SD_ID, dry_run: bool = False):
        self.adb = adb_path
        self.serial = serial
        self.sd_id = sd_id
        self.dry_run = dry_run
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rp5_standalones_"))

    def adb_cmd(self, *args, check: bool = True) -> subprocess.CompletedProcess:
        cmd = [self.adb, "-s", self.serial] + list(args)
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
        print("\n[*] Configuring DuckStation (PS1 - 1080p Vulkan & Low Latency Audio)...")
        content = f"""[Main]
AutoHideTouchscreenController = true
ConfirmPowerOff = false

[BIOS]
SearchDirectory = /storage/{self.sd_id}/bios

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
ResolutionScale = 5
PGXPEnable = true
PGXPTextureCorrection = true
PGXPColorCorrection = true
TextureFilter = Nearest
ChromaSmoothing = true

[Pad1]
Type = AnalogController
AnalogDPadInDigitalMode = true
"""
        local_cfg = self.temp_dir / "duckstation_settings.ini"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/com.github.stenzek.duckstation/files/settings.ini")
        self.push_file(local_cfg, "/sdcard/duckstation/settings.ini")

    # 2. NETHERSX2 (PS2)
    def configure_nethersx2(self) -> None:
        print("\n[*] Configuring NetherSX2 (PS2 - 1080p Vulkan, SPU2 Interpolation & Widescreen)...")
        content = f"""[General]
Bios = scph70012.bin
BiosDirectory = /storage/{self.sd_id}/bios
WarnAboutUnsafeSettings = false

[SPU2/Mixing]
Interpolation = 4
Latency = 1
SyncMode = 0

[EmuCore/GS]
Renderer = Vulkan
UpscaleMultiplier = 2.25
AspectRatio = 1
EnableWideScreenPatches = true
EnableCheats = true
ThreadedPresentation = true
Hacks = 1
"""
        local_cfg = self.temp_dir / "PCSX2.ini"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/xyz.aethersx2.android/files/inis/PCSX2.ini")

    # 3. DOLPHIN (GameCube / Wii)
    def configure_dolphin(self) -> None:
        print("\n[*] Configuring Dolphin (GC/Wii - 2.5x 1080p Vulkan, Controls & DSP Audio)...")
        # Dolphin.ini
        dolphin_ini = """[Core]
Fastmem = True
DualCore = True
EnableCheats = True
CPUThread = True

[DSP]
Backend = OpenSLES
DSPThread = True
Volume = 100
WASAPIDevice = default

[Interface]
ConfirmStop = False
ShowToolbar = False
"""
        # GFX.ini
        gfx_ini = """[Settings]
Backend = Vulkan
InternalResolution = 2.5
AspectRatio = 0
WideScreenHack = False
WaitForShadersBeforeStarting = True
VSync = True
ShaderCompilationMode = 2

[Enhancements]
ArbitraryMipmapDetection = True
ForceTrueColor = True
MaxAnisotropy = 2
"""
        # GCPadNew.ini (Standard RP5 Controller mapping with analog triggers)
        gcpad_ini = """[GCPad1]
Device = Android/0/Retroid Pocket Controller
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
D-Pad/Up = `Hat 0N`
D-Pad/Down = `Hat 0S`
D-Pad/Left = `Hat 0W`
D-Pad/Right = `Hat 0E`
Triggers/L = `Axis 23+`
Triggers/R = `Axis 22+`
Triggers/Threshold = 90.000000
Triggers/L-Analog = `Axis 23+`
Triggers/R-Analog = `Axis 22+`
"""
        # WiimoteNew.ini (Classic controller mapped to RP5)
        wiimote_ini = """[Wiimote1]
Device = Android/0/Retroid Pocket Controller
Source = 1
Extension = Classic
[Classic1]
Device = Android/0/Retroid Pocket Controller
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
D-Pad/Up = `Hat 0N`
D-Pad/Down = `Hat 0S`
D-Pad/Left = `Hat 0W`
D-Pad/Right = `Hat 0E`
Triggers/L = `Axis 23+`
Triggers/R = `Axis 22+`
Triggers/Threshold = 90.000000
"""
        f_dol = self.temp_dir / "Dolphin.ini"
        f_dol.write_text(dolphin_ini, encoding="utf-8")
        f_gfx = self.temp_dir / "GFX.ini"
        f_gfx.write_text(gfx_ini, encoding="utf-8")
        f_pad = self.temp_dir / "GCPadNew.ini"
        f_pad.write_text(gcpad_ini, encoding="utf-8")
        f_wii = self.temp_dir / "WiimoteNew.ini"
        f_wii.write_text(wiimote_ini, encoding="utf-8")

        for f in [f_dol, f_gfx, f_pad, f_wii]:
            self.push_file(f, f"/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/{f.name}")
            self.push_file(f, f"/sdcard/dolphin-emu/Config/{f.name}")

    # 4. PPSSPP (PSP)
    def configure_ppsspp(self) -> None:
        print("\n[*] Configuring PPSSPP (PSP - 4x 1080p Vulkan, 16x Anisotropy & Low Latency)...")
        content = """[Audio]
AudioLatency = 0
AudioResampler = True
GlobalVolume = 10

[Graphics]
GraphicsBackend = 3
InternalResolution = 4
AutoFrameskip = False
FrameSkip = 0
AnisotropyLevel = 16
BufferMode = 1
ShowTouchControls = False
FullScreen = True
VSyncInterval = 1
"""
        local_cfg = self.temp_dir / "ppsspp.ini"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/PSP/SYSTEM/ppsspp.ini")
        self.push_file(local_cfg, "/sdcard/Android/data/org.ppsspp.ppsspp/files/PSP/SYSTEM/ppsspp.ini")

    # 5. FLYCAST (Dreamcast)
    def configure_flycast(self) -> None:
        print("\n[*] Configuring Flycast (Dreamcast - 2x 1080p Vulkan, 16:9 & AICA DSP Audio)...")
        content = """[aica]
AutoLatency = yes
BufferSize = 2822
DSPEnabled = yes
GlobalVolume = 100

[rend]
rend = 2
res_scale = 2
widescreen = 1
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
        print("\n[*] Configuring Azahar (3DS - 3x 1200p Vulkan, Async Shaders & Mesa Turnip Driver)...")
        content = """[Renderer]
graphics_api = 1
resolution_factor = 3
async_shader_compilation = true
custom_driver = /sdcard/Download/drivers/Turnip_v26.0.0_R8.zip
use_disk_shader_cache = true
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
        print("\n[*] Configuring Vita3K (PS Vita - 2x 1080p Vulkan & Mesa Turnip Driver)...")
        content = """backend: Vulkan
resolution-multiplier: 2
custom-driver: /sdcard/Download/drivers/Turnip_v26.0.0_R8.zip
vsync: true
fullscreen: true
"""
        local_cfg = self.temp_dir / "config.yml"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/org.vita3k.emulator/files/vita/config.yml")
        self.push_file(local_cfg, "/sdcard/Android/data/org.vita3k.emulator/files/config.yml")

    def run_all(self) -> None:
        self.configure_duckstation()
        self.configure_nethersx2()
        self.configure_dolphin()
        self.configure_ppsspp()
        self.configure_flycast()
        self.configure_azahar()
        self.configure_vita3k()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        print("\n========================================================================")
        print("   All Standalone 3D Emulators Successfully Configured!")
        print("========================================================================")


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone 3D Emulator Configurator for RP5")
    parser.add_argument("-s", "--serial", default=DEFAULT_SERIAL, help="Target device serial")
    parser.add_argument("--sd-id", default=DEFAULT_SD_ID, help="MicroSD volume UUID")
    parser.add_argument("--adb", default=None, help="Path to ADB binary")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without execution")
    args = parser.parse_args()

    adb_path = find_adb(args.adb)
    configurator = StandaloneConfigurator(adb_path=adb_path, serial=args.serial, sd_id=args.sd_id, dry_run=args.dry_run)
    configurator.run_all()


if __name__ == "__main__":
    main()
