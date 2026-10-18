import os
import re
import shutil
import subprocess
import sys
import time

ADB = shutil.which("adb") or "platform-tools/adb.exe"
SERIAL = os.environ.get("ANDROID_SERIAL")

def adb(args):
    cmd = [ADB] + (["-s", SERIAL] if SERIAL else []) + args
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

print("Tapping Second library dropdown at (1600, 542)...")
adb(["shell", "input", "tap", "1600", "542"])
time.sleep(1)

adb(["shell", "uiautomator", "dump", "/sdcard/dropdown.xml"])
xml = adb(["shell", "cat", "/sdcard/dropdown.xml"])
for m in re.finditer(r'<node\s+([^>]+)/>', xml):
    n = m.group(1)
    text_m = re.search(r'text="([^"]*)"', n)
    desc_m = re.search(r'content-desc="([^"]*)"', n)
    bounds_m = re.search(r'bounds="([^"]*)"', n)
    text = text_m.group(1) if text_m else ""
    desc = desc_m.group(1) if desc_m else ""
    bounds = bounds_m.group(1) if bounds_m else ""
    if text or desc:
        print(f"Text: '{text}' | Desc: '{desc}' | Bounds: {bounds}")
