# Retroid Pocket 5: Master Provisioning & Port Workqueue

This workqueue is maintained to ensure 100% tracking and verification across all emulators, native ports, decompilations, enhancements, and user requests.

---

## 1. Active Task Matrix

| ID | Title / Component | Category | Status | Verification & Assets | Device Storage Location |
|---|---|---|---|---|---|
| **WQ-01** | **OutRun 2006 (Coast 2 Coast)** | DroidDeck (Steam) | **[VERIFIED 1080p 60FPS]** | Heavy `spr_*` folders (2.8 GB) removed; `Xbox` button prompts (160 MB) retained. `outrun2006.ini` configured for 1080p borderless with 2x AA and fog. `WINEDLLOVERRIDES="dinput8=n,b"` active. | `/storage/EEEF-F762/Games/Steam/steamapps/common/OutRun 2006 Coast 2 Coast/` |
| **WQ-02** | **Mario Kart 64 (SpaghettiKart)** | Native Port | **[VERIFIED]** | `com.izzy.kart` v2.0.0 installed; `mk64.o2r` (12.1 MB) & `spaghetti.o2r` (2.7 MB) staged. Launcher `.app` in ES-DE. | `/sdcard/spaghettikart/`<br>`/sdcard/Android/data/com.izzy.kart/files/` |
| **WQ-03** | **Perfect Dark** | Native Port | **[VERIFIED]** | `com.perfectdark.port` v2.0.0 installed; `pd.ntsc-final.z64` (33.5 MB, MD5 e03b088b) staged. Dual-analog 60fps. Launcher `.app` in ES-DE. | `/sdcard/perfect_dark/data/`<br>`/sdcard/Android/data/com.perfectdark.port/files/data/` |
| **WQ-04** | **GoldenEye 007 (Recomp)** | Native Port | **[VERIFIED]** | `com.sunjaycy.goldeneye` v1.4.1 installed; Full XBLA asset package (705 MB) extracted and staged. Native Adreno 650 Vulkan. Launcher `.app` in ES-DE. | `/sdcard/goldeneye/assets/`<br>`/sdcard/Android/data/com.sunjaycy.goldeneye/files/assets/` |
| **WQ-05** | **Diddy Kong Racing (DKR-R)** | Native Port | **[VERIFIED]** | `io.github.thatguymcd.dkrr.preview` v1.0.6 installed; `dkr.z64` (12.5 MB, Rev A) staged. Native 60fps widescreen. Launcher `.app` in ES-DE. | `/sdcard/dkrr/`<br>`/sdcard/Android/data/io.github.thatguymcd.dkrr.preview/files/` |
| **WQ-06** | **Ship of Harkinian (OOT)** | Native Port | **[VERIFIED + MODS]** | `com.dishii.soh` v9.0.2P2 installed; `oot.otr` (29.9 MB) & `soh.otr` (1.45 MB) staged; 3DS Link & Young Link HD models (`3ds_link.otr`, `3ds_young_link.otr`) staged to `mods/`. Launcher `.app` in ES-DE. | `/sdcard/ShipOfHarkinian/`<br>`/sdcard/Android/data/com.dishii.soh/files/` |
| **WQ-07** | **2 Ship 2 Harkinian (MM)** | Native Port | **[VERIFIED]** | `com.dishii.mm` v1.1.2P1 installed; `mm.o2r` (40.4 MB) & `2ship.o2r` (395 KB) staged. Launcher `.app` in ES-DE. | `/sdcard/2Ship2Harkinian/`<br>`/sdcard/Android/data/com.dishii.mm/files/` |
| **WQ-08** | **Star Fox 64 (Starship)** | Native Port | **[VERIFIED]** | `com.starship.android` v2.0.0 installed; `sf64.o2r` (14.5 MB) & `starship.o2r` (10.6 KB) staged. Launcher `.app` in ES-DE. | `/sdcard/starship/`<br>`/sdcard/Android/data/com.starship.android/files/` |
| **WQ-09** | **Zelda 3 (A Link to the Past)** | Native Port | **[VERIFIED]** | `com.dishii.zelda3` v1.0.2 installed; `zelda3_assets.dat` staged. Widescreen 16:9. Launcher `.app` in ES-DE. | `/sdcard/zelda3/`<br>`/sdcard/Android/data/com.dishii.zelda3/files/` |
| **WQ-10** | **Mega Man X8 16-bit Demake** | Native Port | **[VERIFIED]** | `org.godotengine.rockmanx816bitdemakemod` installed; Touch v1.6 mod active; 100% master save restored as `save_slot_1`. Controls tested working by user. | `/data/data/org.godotengine.rockmanx816bitdemakemod/files/saves/` |
| **WQ-11** | **Mega Man X: Regenesis** | Native Port | **[VERIFIED]** | `com.example.megamanxregenesis` v1.00.92 installed; self-contained. Controls tested working by user. | Self-contained APK |
| **WQ-12** | **Sonic 3 A.I.R.** | Native Port | **[VERIFIED]** | `org.eukaryot.sonic3air` installed; `Sonic_Knuckles_wSonic3.bin` staged. Tested working by user. | `/sdcard/Android/data/org.eukaryot.sonic3air/files/` |
| **WQ-13** | **Sonic Robo Blast 2 (SRB2)** | Native Port | **[VERIFIED]** | `org.stjr.srb2` v2.2.13 installed; core assets pre-bundled. Optional `.pk3`/`.wad` addons folder created. | `/sdcard/SRB2/addons/` |
| **WQ-14** | **Balatro** | Native Port | **[VERIFIED]** | `com.unofficial.balatro` installed; native 1080p 60fps AMOLED; full unlocked save state restored. | `/sdcard/Android/data/com.unofficial.balatro/files/save/game/Balatro/1/` |
| **WQ-15** | **Space Cadet 3D Pinball** | Native Port | **[VERIFIED]** | `com.fexed.spacecadetpinball` installed; full native decompilation. | Self-contained APK |
| **WQ-16** | **PokeMMO** | Native MMO | **[STAGED: 4 REGIONS]** | `eu.pokemmo.client` installed; Black & White 1 clean USA/Europe `.nds` (256 MB each) staged; FireRed (Kanto) & Emerald (Hoenn) `.gba` staged. *(Pending: Platinum & HeartGold/SoulSilver)* | `/sdcard/Download/pokemmo_roms/`<br>`/storage/EEEF-F762/ROMs/nds/` |
| **WQ-17** | **DroidDeck: Steam Launcher** | Frontend / Steam | **[VERIFIED]** | `com.droiddeck.launcher` installed; 720p base -> 1080p FSR; Turnip v26.0.0 R8; `WINEDLLOVERRIDES="dinput8=n,b"`; launcher `.app` registered in ES-DE. | `/sdcard/DroidDeck/config.json`<br>`/sdcard/DroidDeck/settings.json` |
| **WQ-18** | **GBA Full Library (486 Games)** | ROM Sync | **[VERIFIED 100%]** | 486 of 486 `.zip` ROMs (2.17 GB) verified in canonical storage layout. | `/storage/EEEF-F762/ROMs/gba/` |
| **WQ-19** | **N64 Best Set (293 Games)** | ROM Sync | **[VERIFIED 100%]** | 293 of 293 `.n64.zip` ROMs (3.60 GB) verified in canonical storage layout. | `/storage/EEEF-F762/ROMs/n64/` |
| **WQ-20** | **AMOLED Homescreen & Wallpaper** | Retroid OS | **[VERIFIED]** | Custom 1080p Cyberpunk Neon Controller AMOLED wallpaper active; Page 1 & Page 2 organized. | Device UI |

---

## 2. Pending User Items & External Drop Actions

| Item | System | Status | Action Required |
|---|---|---|---|
| **Pokemon Platinum** | PokeMMO (Sinnoh Region) | **[Awaiting User Download]** | Not found on PC drives. When downloaded, place `.nds` into `Downloads/` or directly into `/sdcard/Download/pokemmo_roms/`. |
| **Pokemon HeartGold / SoulSilver** | PokeMMO (Johto Region & Follower Sprites) | **[Awaiting User Download]** | Not found on PC drives. When downloaded, place `.nds` into `Downloads/` or directly into `/sdcard/Download/pokemmo_roms/`. |
