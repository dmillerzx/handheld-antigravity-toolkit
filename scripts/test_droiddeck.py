import subprocess
import re

ADB = r"C:\Users\dmill\Documents\AntigravityWorkingDir\platform-tools\adb.exe"
SERIAL = "ff152647"

def run_adb(args):
    cmd = [ADB, "-s", SERIAL] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
    return res.stdout

print("Dumping UI hierarchy...")
run_adb(["shell", "uiautomator", "dump", "/sdcard/dd_dump.xml"])
xml = run_adb(["shell", "cat", "/sdcard/dd_dump.xml"])

nodes = re.findall(r'<node\s+([^>]+)/>', xml)
print(f"Found {len(nodes)} nodes.")
for n in nodes:
    text_m = re.search(r'text="([^"]*)"', n)
    desc_m = re.search(r'content-desc="([^"]*)"', n)
    bounds_m = re.search(r'bounds="([^"]*)"', n)
    text = text_m.group(1) if text_m else ""
    desc = desc_m.group(1) if desc_m else ""
    bounds = bounds_m.group(1) if bounds_m else ""
    if text or desc:
        print(f"Text: '{text}' | Desc: '{desc}' | Bounds: {bounds}")
