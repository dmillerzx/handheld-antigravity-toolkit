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


    # 1. DUCKSTATION (PS1)
    def configure_duckstation(self) -> None:
        scale = self.emulation.get("duckstation_resolution_scale", 5)
        print(f"\n[*] Configuring DuckStation (PS1 - {scale}x Vulkan & Low Latency Audio)...")
        content = f"""[Main]
AutoHideTouchscreenController = true
ConfirmPowerOff = false
FastBoot = true

[BIOS]
SearchDirectory = {self.bios_dir}

[Audio]
Backend = Cubeb
Sync = true

[Display]
OptimalFramePacing = true
ReduceInputLatency = true
ShowFPS = false
Force43For2D = true

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
        aspect = "16:9" if self.force_widescreen else "Auto 4:3/3:2"
        ws_patches = "true" if self.force_widescreen else "false"
        print(f"\n[*] Configuring NetherSX2 (PS2 - {scale}x Vulkan, SPU2 Interpolation, AspectRatio={aspect}, Crop=1, CropMode=Overscan & Widescreen={ws_patches})...")
        content = f"""[UI]
SettingsVersion = 1
OsdShowFPS = true
OsdShowSpeed = true

[General]
Bios = scph70012.bin
BiosDirectory = {self.bios_dir}
WarnAboutUnsafeSettings = false

[SPU2/Mixing]
Interpolation = 4
Latency = 1
SyncMode = 0

[EmuCore]
EnableFastBoot = true
FastBoot = true
EnableWideScreenPatches = {ws_patches}
EnableCheats = true

[EmuCore/GS]
Renderer = Vulkan
UpscaleMultiplier = {scale}
AspectRatio = {aspect}
Crop = 1
CropMode = Overscan
HardwareDownloadMode = 0
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

        # Deploy GT4, OutRun 2006, and native widescreen per-game profiles
        widescreen_games = [
            # Gran Turismo 4 / Spec II
            "646B2E29.ini", "SCUS-97436_646B2E29.ini", "SLUS-97436.ini", "SCUS-97436.ini", "SCUS-97328.ini", "SCES-51719.ini", "SCPS-17001.ini",
            # Burnout 3: Takedown (NTSC-U & PAL)
            "C74D7614.ini", "SLUS-21050.ini", "SLUS-21050_C74D7614.ini", "SLES-52585.ini",
            # Black (NTSC-U & PAL)
            "C2B0A956.ini", "SLUS-21376.ini", "SLES-53886.ini",
        ]
        gt4_ini_content = f"""[EmuCore/GS]
AspectRatio = {aspect}
Crop = 1
CropMode = Overscan
HardwareDownloadMode = 1
UpscaleMultiplier = {scale}
EnableWideScreenPatches = {ws_patches}
EnableCheats = true
"""
        gt4_cfg = self.temp_dir / "gt4_nethersx2_gamesettings.ini"
        gt4_cfg.write_text(gt4_ini_content, encoding="utf-8")
        for g_id in widescreen_games:
            self.push_file(gt4_cfg, f"/sdcard/Android/data/xyz.aethersx2.android/files/gamesettings/{g_id}")

        # OutRun 2006: Coast 2 Coast (NTSC-U & PAL) - 60 FPS Speedhack + GS profile
        outrun_games = [
            "38C16493.ini", "SLUS-21274.ini", "SLUS-21274_38C16493.ini", "F3FD313E.ini", "SLES-53998.ini", "SLES-53998_F3FD313E.ini",
        ]
        outrun_scale = 1.5
        outrun_ini_content = f"""[EmuCore/Speedhacks]
EECycleRate = 0
EECycleSkip = 1
vuThread = true
vu1Instant = true
WaitLoop = true
IntcStat = true
vuFlagHack = true
fastCDVD = true

[EmuCore/GS]
AspectRatio = {aspect}
Crop = 1
CropMode = Overscan
HWDownloadMode = 1
HardwareDownloadMode = 1
HWSpinCPUForReadbacks = true
UpscaleMultiplier = {outrun_scale}
accurate_blending_unit = 0
UserHacks = 1
UserHacks_AutoFlush = 0
UserHacks_AutoFlushLevel = 0
SkipDuplicateFrames = true
ThreadedPresentation = true
EnableWideScreenPatches = {ws_patches}
EnableCheats = true
"""
        outrun_cfg = self.temp_dir / "outrun_nethersx2_gamesettings.ini"
        outrun_cfg.write_text(outrun_ini_content, encoding="utf-8")
        for g_id in outrun_games:
            self.push_file(outrun_cfg, f"/sdcard/Android/data/xyz.aethersx2.android/files/gamesettings/{g_id}")

        # Deploy Retroid Pocket 5 calibrated input profile
        input_prof = WORKSPACE_ROOT / "configs" / "nethersx2_rp5_inputprofile.ini"
        if input_prof.exists():
            self.push_file(input_prof, "/sdcard/Android/data/xyz.aethersx2.android/files/inputprofiles/RP5r.ini")

        # Stage BIOS into NetherSX2 internal directory
        self.shell("mkdir -p /sdcard/Android/data/xyz.aethersx2.android/files/bios")
        self.shell("cp /sdcard/bios/*.bin /sdcard/Android/data/xyz.aethersx2.android/files/bios/ 2>/dev/null || true")

    # 2b. ARM SX2 (PS2 - Primary Standalone)
    def configure_armsx2(self) -> None:
        scale = self.emulation.get("armsx2_upscale_multiplier", 2.0)
        aspect = "16:9" if self.force_widescreen else "Auto 4:3/3:2"
        self.shell("am force-stop com.armsx2", check=False)
        ws_patches = "true" if self.force_widescreen else "false"
        print(f"\n[*] Configuring ARM SX2 (PS2 Primary - {scale}x Vulkan, AspectRatio={aspect}, Crop=1, CropMode=Overscan, Disable Readbacks & Widescreen={ws_patches})...")

        # 1. Generate PCSX2-Android.ini
        pcsx2_ini_content = f"""[UI]
SettingsVersion = 1
OsdShowFPS = true
OsdShowSpeed = true

[Folders]
Bios = {self.bios_dir}
Snapshots = snaps
Savestates = sstates
MemoryCards = memcards
Logs = logs
Cheats = cheats
Patches = patches
UserResources = resources
Cache = cache
Textures = textures
InputProfiles = inputprofiles

[EmuCore]
EnablePatches = true
EnableCheats = true
EnableWideScreenPatches = {ws_patches}
EnableNoInterlacingPatches = true
EnableFastBoot = true
WarnAboutUnsafeSettings = false

[EmuCore/GS]
Renderer = Vulkan
UpscaleMultiplier = {scale}
AspectRatio = {aspect}
Crop = 1
CropMode = Overscan
HardwareDownloadMode = 0
EnableWideScreenPatches = {ws_patches}
EnableCheats = true
ThreadedPresentation = true
Hacks = 1

[Touchscreen]
ControllerView = None

[TouchscreenController]
Opacity = 0
"""
        local_ini = self.temp_dir / "armsx2_PCSX2-Android.ini"
        local_ini.write_text(pcsx2_ini_content, encoding="utf-8")
        self.push_file(local_ini, "/sdcard/Android/data/com.armsx2/files/PCSX2-Android.ini")
        self.push_file(local_ini, "/sdcard/Android/data/com.armsx2/files/inis/PCSX2.ini")

        # 2. Generate/update armsx2-settings.json
        existing_json = self.shell("cat /sdcard/Android/data/com.armsx2/files/armsx2-settings.json 2>/dev/null || true")
        import json
        settings_data = {}
        if existing_json and existing_json.startswith("{"):
            try:
                settings_data = json.loads(existing_json)
            except Exception:
                settings_data = {}

        if "global" not in settings_data:
            settings_data["global"] = {}
        g = settings_data["global"]
        g["renderer"] = "vulkan"
        g["upscaleFloat"] = float(scale)
        g["aspectRatio"] = 1 if self.force_widescreen else 0
        g["enableWideScreenPatches"] = (ws_patches == "true")
        g["enableNoInterlacingPatches"] = True
        g["enableCheats"] = True
        g["enableFastBoot"] = True
        g["hardwareDownloadMode"] = 0  # Accurate (GT4 per-game override uses 1)
        g["antiBlur"] = True
        g["accurateBlendingUnit"] = 1
        g["memoryCardSlot1Filename"] = "mcd001.ps2"
        g["memoryCardSlot2Filename"] = "mcd002.ps2"
        g["touchControllerOpacity"] = 0

        local_json = self.temp_dir / "armsx2-settings.json"
        local_json.write_text(json.dumps(settings_data, indent=2), encoding="utf-8")
        self.push_file(local_json, "/sdcard/Android/data/com.armsx2/files/armsx2-settings.json")

        # 3. Deploy Retroid Pocket 5 calibrated input profile
        input_prof = WORKSPACE_ROOT / "configs" / "nethersx2_rp5_inputprofile.ini"
        if input_prof.exists():
            self.push_file(input_prof, "/sdcard/Android/data/com.armsx2/files/inputprofiles/RP5r.ini")

        # 4. Deploy GT4, OutRun 2006, and native widescreen per-game profiles
        widescreen_games = [
            # Gran Turismo 4 / Spec II
            "646B2E29.ini", "SCUS-97436_646B2E29.ini", "SLUS-97436.ini", "SCUS-97436.ini", "SCUS-97328.ini", "SCES-51719.ini", "SCPS-17001.ini",
            # Burnout 3: Takedown (NTSC-U & PAL)
            "C74D7614.ini", "SLUS-21050.ini", "SLUS-21050_C74D7614.ini", "SLES-52585.ini",
            # Black (NTSC-U & PAL)
            "C2B0A956.ini", "SLUS-21376.ini", "SLES-53886.ini",
        ]
        gt4_ini_content = f"""[EmuCore/GS]
AspectRatio = {aspect}
Crop = 1
CropMode = Overscan
HardwareDownloadMode = 1
UpscaleMultiplier = {scale}
EnableWideScreenPatches = {ws_patches}
EnableCheats = true
"""
        gt4_cfg = self.temp_dir / "gt4_armsx2_gamesettings.ini"
        gt4_cfg.write_text(gt4_ini_content, encoding="utf-8")
        for g_id in widescreen_games:
            self.push_file(gt4_cfg, f"/sdcard/Android/data/com.armsx2/files/gamesettings/{g_id}")

        # OutRun 2006: Coast 2 Coast (NTSC-U & PAL) - 60 FPS Speedhack + GS profile
        outrun_games = [
            "38C16493.ini", "SLUS-21274.ini", "SLUS-21274_38C16493.ini", "F3FD313E.ini", "SLES-53998.ini", "SLES-53998_F3FD313E.ini",
        ]
        outrun_scale = 1.5
        outrun_ini_content = f"""[EmuCore/Speedhacks]
EECycleRate = 0
EECycleSkip = 1
vuThread = true
vu1Instant = true
WaitLoop = true
IntcStat = true
vuFlagHack = true
fastCDVD = true

[EmuCore/GS]
AspectRatio = {aspect}
Crop = 1
CropMode = Overscan
HWDownloadMode = 1
HardwareDownloadMode = 1
HWSpinCPUForReadbacks = true
UpscaleMultiplier = {outrun_scale}
accurate_blending_unit = 0
UserHacks = 1
UserHacks_AutoFlush = 0
UserHacks_AutoFlushLevel = 0
SkipDuplicateFrames = true
ThreadedPresentation = true
EnableWideScreenPatches = {ws_patches}
EnableCheats = true
"""
        outrun_cfg = self.temp_dir / "outrun_armsx2_gamesettings.ini"
        outrun_cfg.write_text(outrun_ini_content, encoding="utf-8")
        for g_id in outrun_games:
            self.push_file(outrun_cfg, f"/sdcard/Android/data/com.armsx2/files/gamesettings/{g_id}")

        # 5. Stage BIOS into ARM SX2 internal directory
        self.shell("mkdir -p /sdcard/Android/data/com.armsx2/files/bios", check=False)
        self.shell("cp /sdcard/bios/*.bin /sdcard/Android/data/com.armsx2/files/bios/ 2>/dev/null || true", check=False)
        if self.sd_id:
            self.shell(f"cp /storage/{self.sd_id}/bios/*.bin /sdcard/Android/data/com.armsx2/files/bios/ 2>/dev/null || true", check=False)

        # 6. Bi-directional Memory Card Mirroring between NetherSX2 and ARM SX2
        self.shell("mkdir -p /sdcard/Android/data/com.armsx2/files/memcards", check=False)
        self.shell("mkdir -p /sdcard/Android/data/xyz.aethersx2.android/files/memcards", check=False)
        # NetherSX2 -> ARM SX2
        self.shell("cp -n /sdcard/Android/data/xyz.aethersx2.android/files/memcards/* /sdcard/Android/data/com.armsx2/files/memcards/ 2>/dev/null || true", check=False)
        # Ensure lowercase mcd001.ps2 / mcd002.ps2 exist for ARM SX2
        self.shell("cp /sdcard/Android/data/com.armsx2/files/memcards/Mcd001.ps2 /sdcard/Android/data/com.armsx2/files/memcards/mcd001.ps2 2>/dev/null || true", check=False)
        self.shell("cp /sdcard/Android/data/com.armsx2/files/memcards/Mcd002.ps2 /sdcard/Android/data/com.armsx2/files/memcards/mcd002.ps2 2>/dev/null || true", check=False)

        # 7. Disable all onscreen touch controls (RP5 has physical integrated controls)
        touch_json_path = "/sdcard/Android/data/com.armsx2/files/inputprofiles/Default.touch.json"
        raw_touch = self.shell(f"cat '{touch_json_path}' 2>/dev/null || true")
        if raw_touch and raw_touch.startswith("{"):
            try:
                touch_data = json.loads(raw_touch)
                if "layout" in touch_data and "buttons" in touch_data["layout"]:
                    for btn in touch_data["layout"]["buttons"]:
                        btn["on"] = False
                    local_touch = self.temp_dir / "Default.touch.json"
                    local_touch.write_text(json.dumps(touch_data, indent=2), encoding="utf-8")
                    self.push_file(local_touch, touch_json_path)
            except Exception:
                pass

    # 3. DOLPHIN (GameCube / Wii)
    def configure_dolphin(self) -> None:
        self.shell("am force-stop org.dolphinemu.dolphinemu", check=False)
        scale = self.emulation.get("dolphin_internal_resolution", 2.5)
        print(f"\n[*] Configuring Dolphin (GC/Wii - {scale}x Vulkan, AspectRatio=Auto [0], Controller & DSP Audio)...")
        # Dolphin.ini (GC & Wii Virtual Console Setup)
        wii_widescreen = "True" if self.force_widescreen else "False"
        dolphin_ini = f"""[Core]
GFXBackend = Vulkan
Fastmem = True
DualCore = True
EnableCheats = True
CPUThread = True
FallbackRegion = 1
WiimoteEnableGCControllers = True
SIDevice0 = 6
SIDevice1 = 0
SIDevice2 = 0
SIDevice3 = 0
SlotA = 1
SlotB = 255

[DSP]
Backend = OpenSLES
DSPThread = True
Volume = 100
WASAPIDevice = default

[Interface]
ConfirmStop = False
ShowToolbar = False
UsePanicHandlers = False

[Wii]
Enable = True
Widescreen = {wii_widescreen}
ProgressiveScan = True
Language = 1
PAL60 = True

[Android]
JoystickRelCenter = False
ShowInputOverlay = False

[Analytics]
Enabled = False
PermissionAsked = True
"""
        # GFX.ini (Graphics & Performance)
        # Global AspectRatio = 0 (Auto): Keeps unpatched games pillarboxed 4:3,
        # while per-game GameSettings INIs inject [Video_Settings] AspectRatio = 1
        # specifically for widescreen patched or native widescreen titles.
        aspect_ratio = 0
        gfx_ini = f"""[Settings]
Backend = Vulkan
InternalResolution = {scale}
AspectRatio = {aspect_ratio}
WideScreenHack = False
WaitForShadersBeforeStarting = True
VSync = True
ShaderCompilationMode = 2

[Enhancements]
ArbitraryMipmapDetection = True
ForceTrueColor = True
MaxAnisotropy = 2

[Hacks]
FastDepthCalc = True
DeferEFBCopies = True
EFBAccessEnable = False
BBoxEnable = False
"""
        ctrl_dev = "Android/1/Xbox Wireless Controller"

        # Require authoritative Dolphin controller config files (no inline string fallbacks)
        cfg_gcpad = WORKSPACE_ROOT / "configs" / "dolphin" / "GCPadNew.ini"
        if not cfg_gcpad.exists():
            raise FileNotFoundError(f"Missing required Dolphin config: {cfg_gcpad}")
        cfg_wiimote = WORKSPACE_ROOT / "configs" / "dolphin" / "WiimoteNew.ini"
        if not cfg_wiimote.exists():
            raise FileNotFoundError(f"Missing required Dolphin config: {cfg_wiimote}")

        hotkeys_ini = f"""[Hotkeys]
Device = {ctrl_dev}
General/Toggle Pause = `Button L3` & `Button R3`
General/Stop = Escape
"""
        freelook_ini = f"""[FreeLook1]
Device = {ctrl_dev}
"""
        f_dol = self.temp_dir / "Dolphin.ini"
        f_dol.write_text(dolphin_ini, encoding="utf-8")
        f_gfx = self.temp_dir / "GFX.ini"
        f_gfx.write_text(gfx_ini, encoding="utf-8")
        f_hot = self.temp_dir / "Hotkeys.ini"
        f_hot.write_text(hotkeys_ini, encoding="utf-8")
        f_hot2 = self.temp_dir / "HotKey.ini"
        f_hot2.write_text(hotkeys_ini, encoding="utf-8")
        f_free = self.temp_dir / "FreeLookController.ini"
        f_free.write_text(freelook_ini, encoding="utf-8")

        for remote_base in ["/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config", "/sdcard/dolphin-emu/Config"]:
            self.push_file(f_dol, f"{remote_base}/Dolphin.ini")
            self.push_file(f_gfx, f"{remote_base}/GFX.ini")
            # Preserve user controller mappings if already configured on-device
            has_gcpad = self.shell(f"[ -f '{remote_base}/GCPadNew.ini' ] && echo 1 || echo 0", check=False).strip()
            if has_gcpad != "1":
                self.push_file(cfg_gcpad, f"{remote_base}/GCPadNew.ini")
            has_wiimote = self.shell(f"[ -f '{remote_base}/WiimoteNew.ini' ] && echo 1 || echo 0", check=False).strip()
            if has_wiimote != "1":
                self.push_file(cfg_wiimote, f"{remote_base}/WiimoteNew.ini")
            self.push_file(f_hot, f"{remote_base}/Hotkeys.ini")
            self.push_file(f_hot2, f"{remote_base}/HotKey.ini")
            self.push_file(f_free, f"{remote_base}/FreeLookController.ini")

        # Deploy Android-native Wii & GCPad community profiles (unchanged from repo)
        profiles_dir = WORKSPACE_ROOT / "configs" / "dolphin" / "profiles"
        if not profiles_dir.exists():
            raise FileNotFoundError(f"Missing required Dolphin profiles directory: {profiles_dir}")
        for prof_file in profiles_dir.rglob("*.ini"):
            rel_path = prof_file.relative_to(profiles_dir)
            remote_sub = str(rel_path.parent).replace("\\", "/")
            self.push_file(prof_file, f"/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Config/Profiles/{remote_sub}/{prof_file.name}")
            self.push_file(prof_file, f"/sdcard/dolphin-emu/Config/Profiles/{remote_sub}/{prof_file.name}")

        # Deploy tuned Mario Kart Wii GameSettings overrides
        for rmc_name in ["RMCE01.ini", "RMC.ini", "RMCP01.ini", "RMCJ01.ini", "RMCEA2.ini", "RMCK01.ini"]:
            local_rmc = WORKSPACE_ROOT / "patches" / "wii" / rmc_name
            if local_rmc.exists():
                self.push_file(local_rmc, f"/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GameSettings/{rmc_name}")
                self.push_file(local_rmc, f"/sdcard/dolphin-emu/GameSettings/{rmc_name}")

    # 4. PPSSPP (PSP)
    def configure_ppsspp(self) -> None:
        scale = self.emulation.get("ppsspp_resolution_scale", 4)
        print(f"\n[*] Configuring PPSSPP (PSP - {scale}x Vulkan & Low Latency)...")
        psp_dir = f"/storage/{self.sd_id}/ROMs/psp" if self.sd_id else "/sdcard/PSP"
        content = f"""[General]
FirstRun = False
RunCount = 1
CurrentDirectory = {psp_dir}

[Sound]
GameVolume = 100

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

[CPU]
FastMemory = True
IOTimingMethod = 0

[System]
FastMemory = True
"""
        local_cfg = self.temp_dir / "ppsspp.ini"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/PSP/SYSTEM/ppsspp.ini")
        self.push_file(local_cfg, "/sdcard/Android/data/org.ppsspp.ppsspp/files/PSP/SYSTEM/ppsspp.ini")
        if self.sd_id:
            self.push_file(local_cfg, f"/storage/{self.sd_id}/PSP/SYSTEM/ppsspp.ini")

    # 5. FLYCAST (Dreamcast)
    def configure_flycast(self) -> None:
        scale = self.emulation.get("flycast_res_scale", 2)
        ws = 1 if self.force_widescreen else 0
        print(f"\n[*] Configuring Flycast (Dreamcast - {scale}x Vulkan, Widescreen={ws} & AICA DSP Audio)...")
        content = f"""[audio]
backend = auto

[config]
aica.AutoLatency = yes
aica.BufferSize = 2822
aica.DSPEnabled = yes
aica.Volume = 100

[rend]
rend = 2
res_scale = {scale}
widescreen = {ws}
cable = 0
Fog = 1
Vsync = 1

[input]
VirtualGamepad = 0
"""
        local_cfg = self.temp_dir / "emu.cfg"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/com.flycast.emulator/files/emu.cfg")
        self.push_file(local_cfg, "/sdcard/Flycast/emu.cfg")

    # 6. AZAHAR (3DS)
    def configure_azahar(self) -> None:
        scale = self.emulation.get("azahar_resolution_factor", 3)
        turnip_line = "custom_driver = /sdcard/Download/drivers/turnip_v24.3.0_R9v2.zip\n" if self.supports_turnip else ""
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
        driver_desc = "Mesa Turnip Driver" if self.supports_turnip else "System Vulkan Driver"
        print(f"\n[*] Configuring Vita3K (PS Vita - {scale}x Vulkan & {driver_desc})...")
        self.shell("am force-stop org.vita3k.emulator", check=False)
        cfg_source = WORKSPACE_ROOT / "configs" / "vita3k" / "config.yml"
        if cfg_source.exists():
            content = cfg_source.read_text(encoding="utf-8")
        else:
            content = f"""initial-setup: false
pref-path: "/storage/emulated/0/Android/data/org.vita3k.emulator/files/vita"
backend-renderer: Vulkan
resolution-multiplier: {scale}
vsync: true
fullscreen: true
show-touch-controls: false
gui-controllers-overlay: false
overlay-opacity: 0
overlay-scale: 1.0
show-gui: true
"""
        local_cfg = self.temp_dir / "config.yml"
        local_cfg.write_text(content, encoding="utf-8")
        self.push_file(local_cfg, "/sdcard/Android/data/org.vita3k.emulator/files/vita/config.yml")
        self.push_file(local_cfg, "/sdcard/Android/data/org.vita3k.emulator/files/config.yml")

    # 8. ES-DE STANDALONE EMULATOR ROUTING
    def configure_esde_routing(self) -> None:
        print("\n[*] Locking down ES-DE standalone routing for all 3D systems...")
        self.shell("am force-stop org.es_de.frontend", check=False)
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
        self.configure_armsx2()
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
