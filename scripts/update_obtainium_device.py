import json
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

serial = "ff152647"
app_data_remote = "/sdcard/Android/data/dev.imranr.obtainium/files/app_data"
local_dir = "scratch/obtainium_update"
os.makedirs(local_dir, exist_ok=True)

print("1. Force-stopping Obtainium...")
subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", "am", "force-stop", "dev.imranr.obtainium"], check=True)

print("2. Pulling current app_data files...")
res = subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", f"ls {app_data_remote}/*.json"], capture_output=True, text=True)
remote_files = [f.strip() for f in res.stdout.splitlines() if f.strip().endswith(".json")]

for rf in remote_files:
    fname = os.path.basename(rf)
    subprocess.run(["platform-tools/adb.exe", "-s", serial, "pull", rf, os.path.join(local_dir, fname)], check=True)

print(f"Pulled {len(remote_files)} files to {local_dir}")

# 3. Remove PPSSPP
ppsspp_file = os.path.join(local_dir, "org.ppsspp.ppsspp.json")
if os.path.exists(ppsspp_file):
    os.remove(ppsspp_file)
    print("Removed org.ppsspp.ppsspp.json locally")
subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", f"rm -f {app_data_remote}/org.ppsspp.ppsspp.json"])
print("Removed org.ppsspp.ppsspp.json from device")

# 4. Update Obtainium
obtainium_file = os.path.join(local_dir, "dev.imranr.obtainium.json")
if os.path.exists(obtainium_file):
    with open(obtainium_file, "r", encoding="utf-8") as f:
        d = json.load(f)
    s = json.loads(d.get("additionalSettings", "{}"))
    s["apkFilterRegEx"] = "^app-arm64-v8a-release\\.apk$"
    d["additionalSettings"] = json.dumps(s)
    with open(obtainium_file, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    print("Updated dev.imranr.obtainium.json")

# 5. Update Vita3K
vita3k_file = os.path.join(local_dir, "org.vita3k.emulator.json")
if os.path.exists(vita3k_file):
    with open(vita3k_file, "r", encoding="utf-8") as f:
        d = json.load(f)
    d["url"] = "https://github.com/Vita3K/Vita3K"
    s = json.loads(d.get("additionalSettings", "{}"))
    s["filterReleaseTitlesByRegEx"] = "continuous"
    s["apkFilterRegEx"] = "android-latest\\.apk$"
    s["useLatestAssetDateAsReleaseDate"] = True
    s["sortMethodChoice"] = "date"
    d["additionalSettings"] = json.dumps(s)
    with open(vita3k_file, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    print("Updated org.vita3k.emulator.json")

# 6. Update Azahar
azahar_file = os.path.join(local_dir, "org.azahar_emu.azahar.json")
if os.path.exists(azahar_file):
    with open(azahar_file, "r", encoding="utf-8") as f:
        d = json.load(f)
    s = json.loads(d.get("additionalSettings", "{}"))
    s["apkFilterRegEx"] = "azahar-android-vanilla.*\\.apk$"
    d["additionalSettings"] = json.dumps(s)
    with open(azahar_file, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    print("Updated org.azahar_emu.azahar.json")

# 7. Add / Update ARM SX2
armsx2_file = os.path.join(local_dir, "com.armsx2.json")
armsx2_settings = {
    "includePrereleases": False,
    "fallbackToOlderReleases": True,
    "filterReleaseTitlesByRegEx": "",
    "filterReleaseNotesByRegEx": "",
    "verifyLatestTag": False,
    "sortMethodChoice": "date",
    "useLatestAssetDateAsReleaseDate": False,
    "releaseTitleAsVersion": False,
    "trackOnly": False,
    "versionExtractionRegEx": "",
    "matchGroupToUse": "",
    "versionDetection": True,
    "releaseDateAsVersion": False,
    "useVersionCodeAsOSVersion": False,
    "apkFilterRegEx": "a13-armv8.2-sdk33|a13.*apk",
    "invertAPKFilter": False,
    "autoApkFilterByArch": True,
    "minimumUpdateAgeDays": "",
    "appName": "ARM SX2",
    "appAuthor": "ARMSX2",
    "shizukuPretendToBeGooglePlay": False,
    "allowInsecure": False,
    "allowedSigningCertHashes": "",
    "exemptFromBackgroundUpdates": False,
    "skipUpdateNotifications": False,
    "about": "PlayStation 2 Emulator (ARM SX2 Community Fork)",
    "refreshBeforeDownload": False,
    "includeZips": False,
    "zippedApkFilterRegEx": "",
    "includeTarballs": False,
    "tarballedApkFilterRegEx": "",
    "GHReqPrefix": ""
}
armsx2_data = {
    "id": "com.armsx2",
    "url": "https://github.com/ARMSX2/ARMSX2",
    "author": "ARMSX2",
    "name": "ARM SX2",
    "installedVersion": "2.8.3",
    "latestVersion": "2.8.3",
    "apkUrls": "[]",
    "otherAssetUrls": "[]",
    "preferredApkIndex": 0,
    "additionalSettings": json.dumps(armsx2_settings),
    "lastUpdateCheck": int(time.time() * 1000000),
    "pinned": False,
    "categories": ["Emulator"],
    "releaseDate": 0,
    "changeLog": "",
    "releaseUrl": None,
    "overrideSource": "GitHub",
    "allowIdChange": False,
    "pendingRepoRenameUrl": None
}
with open(armsx2_file, "w", encoding="utf-8") as f:
    json.dump(armsx2_data, f, indent=2)
print("Created com.armsx2.json")

# 8. Push all updated files to device
for fname in os.listdir(local_dir):
    if fname.endswith(".json"):
        lpath = os.path.join(local_dir, fname)
        subprocess.run(["platform-tools/adb.exe", "-s", serial, "push", lpath, f"{app_data_remote}/{fname}"], check=True)
print("Pushed all updated JSONs to device")

# 9. Launch Obtainium
print("Launching Obtainium...")
subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", "monkey -p dev.imranr.obtainium -c android.intent.category.LAUNCHER 1"], check=True)
time.sleep(3)

# 10. Navigate to Settings and Trigger Export
print("Navigating to Settings -> Import/export...")
subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", "input tap 720 108"]) # Settings gear
time.sleep(1)
subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", "input tap 960 240"]) # Import/export option
time.sleep(1)
print("Tapping Obtainium export...")
subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", "input tap 960 375"]) # Obtainium export
time.sleep(2)

print("Export triggered! Searching for newest export file...")
res = subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", "ls -lat /storage/EEEF-F762/Downloads/obtainium*"], capture_output=True, text=True)
lines = [l.strip() for l in res.stdout.splitlines() if "obtainium-export" in l]
if lines:
    latest_export_remote = lines[0].split()[-1]
    print(f"Latest export file on device: {latest_export_remote}")
    subprocess.run(["platform-tools/adb.exe", "-s", serial, "pull", latest_export_remote, "configs/obtainium_export.json"], check=True)
    print("Pulled and updated configs/obtainium_export.json")
else:
    print("No export file found!")
