import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")

adb_bin = shutil.which("adb") or "platform-tools/adb.exe"
serial = os.environ.get("ANDROID_SERIAL")
for arg in sys.argv[1:]:
    if arg.startswith("--serial="):
        serial = arg.split("=", 1)[1]
    elif arg == "--serial" and sys.argv.index(arg) + 1 < len(sys.argv):
        serial = sys.argv[sys.argv.index(arg) + 1]

cmd = [adb_bin]
if serial:
    cmd.extend(["-s", serial])
cmd.extend(["shell", "cat", "/sdcard/azahar_dump_real.xml"])

res = subprocess.run(cmd, capture_output=True, text=True)
if not res.stdout.strip():
    print("No dump found or adb failed.")
    sys.exit(0)

try:
    root = ET.fromstring(res.stdout)
    for node in root.iter("node"):
        cd = node.attrib.get("content-desc", "").replace("\n", " ")
        text = node.attrib.get("text", "").replace("\n", " ")
        bounds = node.attrib.get("bounds", "")
        cls = node.attrib.get("class", "").split(".")[-1]
        if cd or text:
            print(f"{bounds} [{cls}]: text='{text}' desc='{cd}'")
except Exception as e:
    print(f"Error parsing XML: {e}")
