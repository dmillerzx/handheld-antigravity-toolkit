import json
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

adb_bin = shutil.which("adb") or "platform-tools/adb.exe"
serial = os.environ.get("ANDROID_SERIAL")
for arg in sys.argv[1:]:
    if arg.startswith("--serial="):
        serial = arg.split("=", 1)[1]
    elif arg == "--serial" and sys.argv.index(arg) + 1 < len(sys.argv):
        serial = sys.argv[sys.argv.index(arg) + 1]

if not serial:
    try:
        from device_profile import get_connected_serial
        serial = get_connected_serial(adb_bin)
    except Exception:
        serial = None

def adb_cmd(*args):
    cmd = [adb_bin]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)
    return cmd

app_data_remote = "/sdcard/Android/data/dev.imranr.obtainium/files/app_data"
local_dir = "scratch/obtainium_update"
os.makedirs(local_dir, exist_ok=True)

print("1. Force-stopping Obtainium...")
subprocess.run(adb_cmd("shell", "am", "force-stop", "dev.imranr.obtainium"), check=True)

# 2. Fix Vita3K
vita3k_file = os.path.join(local_dir, "org.vita3k.emulator.json")
if os.path.exists(vita3k_file):
    with open(vita3k_file, "r", encoding="utf-8") as f:
        d = json.load(f)
    d["url"] = "https://github.com/Vita3K/Vita3K"
    s = json.loads(d.get("additionalSettings", "{}"))
    s["filterReleaseTitlesByRegEx"] = "" # Empty to match "Automatic CI builds"
    s["apkFilterRegEx"] = "android-latest\\.apk$"
    s["useLatestAssetDateAsReleaseDate"] = True
    s["includePrereleases"] = False
    s["sortMethodChoice"] = "date"
    d["additionalSettings"] = json.dumps(s)
    with open(vita3k_file, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    print("Fixed org.vita3k.emulator.json")

# 3. Fix RetroArch with Libretro buildbot scraper
retroarch_file = os.path.join(local_dir, "com.retroarch.aarch64.json")
ra_settings = {
    "intermediateLink": [
        {"customLinkFilterRegex": "\\d+\\.\\d+\\.\\d+", "autoLinkFilterByArch": False, "filterByLinkText": False, "matchLinksOutsideATags": False, "skipSort": False, "reverseSort": False, "sortByLastLinkSegment": False},
        {"customLinkFilterRegex": "android", "autoLinkFilterByArch": False, "filterByLinkText": False, "matchLinksOutsideATags": False, "skipSort": False, "reverseSort": False, "sortByLastLinkSegment": False}
    ],
    "customLinkFilterRegex": "aarch64",
    "filterByLinkText": False,
    "matchLinksOutsideATags": False,
    "skipSort": False,
    "reverseSort": False,
    "sortByLastLinkSegment": False,
    "versionExtractWholePage": False,
    "requestHeader": [{"requestHeader": "User-Agent: Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"}],
    "defaultPseudoVersioningMethod": "partialAPKHash",
    "trackOnly": False,
    "versionExtractionRegEx": "(\\d+\\.\\d+\\.\\d+)",
    "matchGroupToUse": "$1_GIT",
    "versionDetection": False,
    "useVersionCodeAsOSVersion": False,
    "apkFilterRegEx": "",
    "invertAPKFilter": False,
    "autoApkFilterByArch": True,
    "appName": "RetroArch (AArch64)",
    "appAuthor": "Libretro",
    "shizukuPretendToBeGooglePlay": False,
    "allowInsecure": False,
    "exemptFromBackgroundUpdates": False,
    "skipUpdateNotifications": False,
    "about": "Multi-system frontend and emulator",
    "refreshBeforeDownload": False
}
ra_data = {
    "id": "com.retroarch.aarch64",
    "url": "https://buildbot.libretro.com/stable",
    "author": "Libretro",
    "name": "RetroArch (AArch64)",
    "installedVersion": "1.22.2_GIT",
    "latestVersion": "1.22.2_GIT",
    "apkUrls": "[]",
    "otherAssetUrls": "[]",
    "preferredApkIndex": 0,
    "additionalSettings": json.dumps(ra_settings),
    "lastUpdateCheck": int(time.time() * 1000000),
    "pinned": False,
    "categories": ["Emulator"],
    "releaseDate": 0,
    "changeLog": "",
    "releaseUrl": None,
    "overrideSource": "HTML",
    "allowIdChange": False,
    "pendingRepoRenameUrl": None
}
with open(retroarch_file, "w", encoding="utf-8") as f:
    json.dump(ra_data, f, indent=2)
print("Updated com.retroarch.aarch64.json with buildbot scraper")

# 4. Push all updated files to device
for fname in os.listdir(local_dir):
    if fname.endswith(".json"):
        lpath = os.path.join(local_dir, fname)
        subprocess.run(adb_cmd("push", lpath, f"{app_data_remote}/{fname}"), check=True)
print("Pushed updated JSONs to device")

# 5. Launch Obtainium
print("Launching Obtainium...")
subprocess.run(adb_cmd("shell", "monkey", "-p", "dev.imranr.obtainium", "-c", "android.intent.category.LAUNCHER", "1"), check=True)
time.sleep(3)

# 6. Trigger refresh
print("Triggering update check swipe...")
subprocess.run(adb_cmd("shell", "input", "swipe", "380", "300", "380", "900", "300"))
time.sleep(5)

# 7. Navigate to Settings and Trigger Export
print("Navigating to Settings -> Import/export...")
subprocess.run(adb_cmd("shell", "input", "tap", "720", "108")) # Settings gear
time.sleep(1)
subprocess.run(adb_cmd("shell", "input", "tap", "960", "240")) # Import/export option
time.sleep(1)
print("Tapping Obtainium export...")
subprocess.run(adb_cmd("shell", "input", "tap", "960", "375")) # Obtainium export
time.sleep(2)

# 8. Pull latest export
res = subprocess.run(adb_cmd("shell", "ls", "-lat", "/storage/<SD_ID>/Downloads/obtainium*"), capture_output=True, text=True)
lines = [l.strip() for l in res.stdout.splitlines() if "obtainium-export" in l]
if lines:
    latest_export_remote = lines[0].split()[-1]
    print(f"Latest export file on device: {latest_export_remote}")
    subprocess.run(adb_cmd("pull", latest_export_remote, "configs/obtainium_export.json"), check=True)
    print("Pulled and updated configs/obtainium_export.json")
