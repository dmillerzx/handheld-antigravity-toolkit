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

print("Closing dropdown...")
adb(["shell", "input", "tap", "500", "500"])
time.sleep(1)

print("Closing Settings...")
adb(["shell", "input", "tap", "1825", "260"])
time.sleep(1)

print("Tapping Play Steam at (500, 915)...")
adb(["shell", "input", "tap", "500", "915"])
time.sleep(4)

adb(["shell", "screencap", "-p", "/sdcard/steam_launching.png"])
os.makedirs("scratch", exist_ok=True)
cmd = [ADB] + (["-s", SERIAL] if SERIAL else []) + ["pull", "/sdcard/steam_launching.png", "scratch/steam_launching.png"]
subprocess.run(cmd)
print("Captured steam_launching.png")
