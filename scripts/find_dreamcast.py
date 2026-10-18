import os
import shutil
import subprocess
import sys

ADB = shutil.which("adb") or "platform-tools/adb.exe"
SERIAL = os.environ.get("ANDROID_SERIAL")

cmd = [ADB] + (["-s", SERIAL] if SERIAL else []) + ["shell", "find /storage/<SD_ID>/ -iname '*arcade*racing*' -o -iname '*road*trip*'"]
res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, errors="ignore")
print(res.stdout)
