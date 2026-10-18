import subprocess
import time

ADB = r"C:\Users\dmill\Documents\AntigravityWorkingDir\platform-tools\adb.exe"
SERIAL = "ff152647"

def adb(args):
    return subprocess.run([ADB, "-s", SERIAL] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

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
subprocess.run([ADB, "-s", SERIAL, "pull", "/sdcard/steam_launching.png", r"C:\Users\dmill\.gemini\antigravity-cli\brain\62e808dd-2d7f-4695-99e0-b96a52085cf3\steam_launching.png"])
print("Captured steam_launching.png")
