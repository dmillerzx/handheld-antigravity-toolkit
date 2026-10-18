import subprocess
import re
import time

ADB = r"C:\Users\dmill\Documents\AntigravityWorkingDir\platform-tools\adb.exe"
SERIAL = "ff152647"

def adb(args):
    return subprocess.run([ADB, "-s", SERIAL] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

print("Tapping RP5 at (900, 620)...")
adb(["shell", "input", "tap", "900", "620"])
time.sleep(2)
adb(["shell", "uiautomator", "dump", "/sdcard/sd_browse.xml"])
xml = adb(["shell", "cat", "/sdcard/sd_browse.xml"])
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
