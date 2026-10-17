import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
serial = "ff152647"

targets = [
    ("RetroArch (MicroSD Saves)", "/storage/EEEF-F762/RetroArch/saves"),
    ("RetroArch (MicroSD States)", "/storage/EEEF-F762/RetroArch/states"),
    ("RetroArch (Internal Root Saves)", "/sdcard/RetroArch/saves"),
    ("RetroArch (Internal Root States)", "/sdcard/RetroArch/states"),
    ("RetroArch (App Data Saves)", "/sdcard/Android/data/com.retroarch.aarch64/files/saves"),
    ("RetroArch (App Data States)", "/sdcard/Android/data/com.retroarch.aarch64/files/states"),
    ("Dolphin (GC Memcards)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/GC"),
    ("Dolphin (StateSaves)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/StateSaves"),
    ("Dolphin (Wii Saves)", "/sdcard/Android/data/org.dolphinemu.dolphinemu/files/Wii"),
    ("ARM SX2 (Memcards)", "/sdcard/Android/data/com.armsx2/files/memcards"),
    ("ARM SX2 (Savestates)", "/sdcard/Android/data/com.armsx2/files/sstates"),
    ("NetherSX2 (Memcards)", "/sdcard/Android/data/xyz.aethersx2.android/files/memcards"),
    ("NetherSX2 (Savestates)", "/sdcard/Android/data/xyz.aethersx2.android/files/sstates"),
    ("DuckStation (App Data Memcards)", "/sdcard/Android/data/com.github.stenzek.duckstation/files/memcards"),
    ("DuckStation (App Data Savestates)", "/sdcard/Android/data/com.github.stenzek.duckstation/files/savestates"),
    ("DuckStation (Internal Root)", "/sdcard/duckstation/memcards"),
    ("PPSSPP (Root SAVEDATA)", "/sdcard/PSP/SAVEDATA"),
    ("PPSSPP (Root States)", "/sdcard/PSP/PPSSPP_STATE"),
    ("PPSSPP (App Data SAVEDATA)", "/sdcard/Android/data/org.ppsspp.ppsspp/files/PSP/SAVEDATA"),
    ("Azahar (App Data SDMC)", "/sdcard/Android/data/org.azahar_emu.azahar/files/sdmc"),
    ("Azahar (App Data States)", "/sdcard/Android/data/org.azahar_emu.azahar/files/states"),
    ("Flycast (Root Saves/VMU)", "/sdcard/Flycast"),
    ("Flycast (App Data)", "/sdcard/Android/data/com.flycast.emulator/files"),
    ("Vita3K (Savedata)", "/sdcard/Android/data/org.vita3k.emulator/files/vita/ux0/user/00/savedata")
]

print("=" * 100)
print(f"{'Target Name':<35} | {'Status / File Count':<25} | {'Path'}")
print("=" * 100)

for name, path in targets:
    res = subprocess.run(["platform-tools/adb.exe", "-s", serial, "shell", f"if [ -d '{path}' ]; then find '{path}' -type f | wc -l; else echo 'NOT_FOUND'; fi"], capture_output=True, text=True)
    out = res.stdout.strip()
    if out == "NOT_FOUND":
        status = "Not Found"
    elif out == "0":
        status = "0 files (empty dir)"
    else:
        status = f"{out} file(s)"
    print(f"{name:<35} | {status:<25} | {path}")

print("=" * 100)
