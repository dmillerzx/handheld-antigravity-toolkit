import os
import shutil
import subprocess
import sys
import time

ADB = shutil.which("adb") or "platform-tools/adb.exe"
SERIAL = os.environ.get("ANDROID_SERIAL")

def adb(args):
    cmd = [ADB] + (["-s", SERIAL] if SERIAL else []) + args
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

print("Tapping BROWSE FOR ROM... at (340, 750)...")
adb(["shell", "input", "tap", "340", "750"])
time.sleep(2)

print("Taking screenshot...")
adb(["shell", "screencap", "-p", "/sdcard/dkrr_tap.png"])
os.makedirs("scratch", exist_ok=True)
cmd = [ADB] + (["-s", SERIAL] if SERIAL else []) + ["pull", "/sdcard/dkrr_tap.png", "scratch/dkrr_tap.png"]
subprocess.run(cmd)
print("Done!")
