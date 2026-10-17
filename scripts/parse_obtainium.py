import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

target_file = sys.argv[1] if len(sys.argv) > 1 else "new_export.json"

with open(target_file, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Reading: {target_file}")
print(f"Total apps in export: {len(data['apps'])}")
print(f"Exported at: {data.get('exportedAt')}")
print("=" * 140)
print(f"{'App Name':<20} | {'Package ID':<26} | {'Installed':<11} | {'Latest':<9} | {'Pre':<5} | {'Filter':<24} | {'URL'}")
print("=" * 140)

for app in data["apps"]:
    settings = json.loads(app.get("additionalSettings", "{}"))
    name = app.get("name", "")
    pkg_id = app.get("id", "")
    inst = str(app.get("installedVersion", ""))
    latest = str(app.get("latestVersion", ""))
    pre = str(settings.get("includePrereleases", False))
    flt = settings.get("apkFilterRegEx", "")
    url = app.get("url", "")
    print(f"{name:<20} | {pkg_id:<26} | {inst:<11} | {latest:<9} | {pre:<5} | {flt:<24} | {url}")

print("=" * 140)
