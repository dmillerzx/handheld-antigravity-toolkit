#!/usr/bin/env python3
"""
Automated CannonBall (OutRun Arcade 60FPS Widescreen) Deployer for Retroid Pocket 5
----------------------------------------------------------------------------------
Provisions Chris White's CannonBall arcade OutRun engine for RetroArch:
1. Downloads cannonball_libretro_android.so core from Libretro buildbot
2. Downloads CannonBall.zip engine assets into RetroArch/system/cannonball/
3. Downloads OutRun Revision B arcade ROMs into RetroArch/system/cannonball/roms/
4. Deploys 60FPS, widescreen, and high-res rendering configuration into Cannonball.opt
5. Creates launcher entry in ROMs/ports/CannonBall - OutRun.game
"""

import os
import sys
import ssl
import shutil
import zipfile
import urllib.request
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Import dynamic device profiling helper
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))
from device_profile import detect_storage_targets, get_connected_serial

ctx = ssl._create_unverified_context()

CORE_URL = "https://buildbot.libretro.com/nightly/android/latest/arm64-v8a/cannonball_libretro_android.so.zip"
ASSETS_URL = "https://buildbot.libretro.com/assets/cores/Cannonball/CannonBall.zip"
ROMS_URL = "https://archive.org/download/arcade_outrun/outrun.zip"

def deploy_cannonball(serial: str = None) -> bool:
    print("\n[*] Deploying CannonBall: OutRun (60 FPS Widescreen C++ Engine)...")
    temp_dir = WORKSPACE_ROOT / "scratch" / "_cannonball_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    adb_bin = str(WORKSPACE_ROOT / "platform-tools" / "adb.exe")
    adb_cmd = [adb_bin]
    if serial:
        adb_cmd.extend(["-s", serial])
        
    internal, sdcard, sd_id = detect_storage_targets(adb_bin, serial=serial)
    target_base = sdcard or internal
    if not target_base:
        print("    [!] ERROR: No accessible storage detected.")
        return False
        
    try:
        # 1. Download Core
        print("    -> Downloading Cannonball Libretro Core (arm64-v8a)...")
        core_zip = temp_dir / "core.zip"
        req = urllib.request.Request(CORE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as resp, open(core_zip, 'wb') as f:
            f.write(resp.read())
            
        with zipfile.ZipFile(core_zip, 'r') as z:
            z.extractall(temp_dir)
            
        core_so = temp_dir / "cannonball_libretro_android.so"
        dest_core = f"{target_base}/RetroArch/cores/cannonball_libretro_android.so"
        subprocess.check_call(adb_cmd + ['push', str(core_so), dest_core])
        print("       [OK] Core deployed to RetroArch/cores/")
        
        # 2. Download Engine Assets
        print("    -> Downloading CannonBall engine assets...")
        assets_zip = temp_dir / "assets.zip"
        req = urllib.request.Request(ASSETS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as resp, open(assets_zip, 'wb') as f:
            f.write(resp.read())
            
        assets_extract = temp_dir / "cannonball_system"
        with zipfile.ZipFile(assets_zip, 'r') as z:
            z.extractall(assets_extract)
            
        # 3. Download OutRun Revision B Arcade ROMs
        print("    -> Downloading OutRun Revision B arcade ROMs...")
        roms_zip = temp_dir / "outrun.zip"
        req = urllib.request.Request(ROMS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as resp, open(roms_zip, 'wb') as f:
            f.write(resp.read())
            
        roms_target = assets_extract / "roms"
        roms_target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(roms_zip, 'r') as z:
            z.extractall(roms_target)
            
        # Push system directory
        print("    -> Staging assets & ROMs to RetroArch/system/cannonball/...")
        subprocess.check_call(adb_cmd + ['shell', f'mkdir -p "{target_base}/RetroArch/system/cannonball"'])
        subprocess.check_call(adb_cmd + ['push', str(assets_extract) + "/.", f"{target_base}/RetroArch/system/cannonball/"])
        
        # 4. Create launcher .game and .app
        launcher_game = temp_dir / "CannonBall - OutRun.game"
        launcher_game.write_text("CannonBall OutRun Arcade 60FPS Widescreen\n", encoding="utf-8")
        subprocess.check_call(adb_cmd + ['push', str(launcher_game), f"{target_base}/ROMs/ports/CannonBall - OutRun.game"])
        subprocess.check_call(adb_cmd + ['push', str(launcher_game), f"{target_base}/RetroArch/system/cannonball/CannonBall.game"])
        
        # 5. Core options for 60fps & widescreen
        opt_content = """cannonball_fps = "60"
cannonball_widescreen = "enabled"
cannonball_hires = "enabled"
cannonball_gear = "manual"
cannonball_cd_music = "disabled"
cannonball_time = "normal"
cannonball_traffic = "normal"
"""
        opt_file = temp_dir / "Cannonball.opt"
        opt_file.write_text(opt_content, encoding="utf-8")
        subprocess.check_call(adb_cmd + ['shell', f'mkdir -p "{target_base}/RetroArch/config/Cannonball"'])
        subprocess.check_call(adb_cmd + ['push', str(opt_file), f"{target_base}/RetroArch/config/Cannonball/Cannonball.opt"])
        
        print("    [+] CannonBall OutRun 60FPS Widescreen deployed successfully!")
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    serial = get_connected_serial()
    deploy_cannonball(serial)
