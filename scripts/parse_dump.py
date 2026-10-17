import xml.etree.ElementTree as ET
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

res = subprocess.run(["platform-tools/adb.exe", "-s", "ff152647", "shell", "cat", "/sdcard/azahar_dump_real.xml"], capture_output=True, text=True)
root = ET.fromstring(res.stdout)
for node in root.iter("node"):
    cd = node.attrib.get("content-desc", "").replace("\n", " ")
    text = node.attrib.get("text", "").replace("\n", " ")
    bounds = node.attrib.get("bounds", "")
    cls = node.attrib.get("class", "").split(".")[-1]
    if cd or text:
        print(f"{bounds} [{cls}]: text='{text}' desc='{cd}'")
