import json

with open("configs/obtainium_export.json", "r", encoding="utf-8") as f:
    export_data = json.load(f)

# Keep the export format or clean apps list
master_data = {
    "apps": export_data.get("apps", [])
}

with open("configs/rp5_master_obtainium.json", "w", encoding="utf-8") as f:
    json.dump(master_data, f, indent=2)

print(f"Successfully synced configs/rp5_master_obtainium.json with {len(master_data['apps'])} apps from configs/obtainium_export.json")
