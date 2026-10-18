import subprocess
import time

ADB = r"C:\Users\dmill\Documents\AntigravityWorkingDir\platform-tools\adb.exe"
SERIAL = "ff152647"

def adb(args):
    return subprocess.run([ADB, "-s", SERIAL] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

print("Tapping BROWSE FOR ROM... at (340, 750)...")
adb(["shell", "input", "tap", "340", "750"])
time.sleep(2)

print("Taking screenshot...")
adb(["shell", "screencap", "-p", "/sdcard/dkrr_tap.png"])
subprocess.run([ADB, "-s", SERIAL, "pull", "/sdcard/dkrr_tap.png", r"C:\Users\dmill\.gemini\antigravity-cli\brain\62e808dd-2d7f-4695-99e0-b96a52085cf3\dkrr_tap.png"])
print("Done!")
