# Retroid Pocket 5: Master Provisioning & Port Workqueue

This workqueue is maintained to ensure 100% tracking and verification across all emulators, native ports, decompilations, enhancements, and user requests.

---

## 1. Active Task Matrix

| ID | Title / Component | Category | Status | Verification & Assets | Device Storage Location |
|---|---|---|---|---|---|
| **WQ-01** | **OutRun 2006 (Coast 2 Coast)** | DroidDeck (Steam) | **[VERIFIED READY]** | `libraryfolders.vdf` updated with App ID `8960`. OutRun 2006 recognized directly under Games tab in DroidDeck with Launch button & launch settings ready. `outrun2006.ini` configured for 1080p borderless, 2x AA, `WINEDLLOVERRIDES="dinput8=n,b"`. | `/storage/<SD_ID>/Games/Steam/steamapps/common/OutRun 2006 Coast 2 Coast/`<br>`/storage/<SD_ID>/Android/data/com.droiddeck.launcher/files/steam/steamapps/` |
| **WQ-02** | **Mario Kart 64 (SpaghettiKart)** | Native Port | **[VERIFIED]** | `com.izzy.kart` v2.0.0 installed; `mk64.o2r` (12.1 MB) & `spaghetti.o2r` (2.7 MB) staged. Launcher `.app` in ES-DE. | `/sdcard/spaghettikart/`<br>`/sdcard/Android/data/com.izzy.kart/files/` |
| **WQ-03** | **Perfect Dark** | Native Port | **[VERIFIED]** | `com.perfectdark.port` v2.0.0 installed; `pd.ntsc-final.z64` (33.5 MB, MD5 e03b088b) staged. Dual-analog 60fps. Launcher `.app` in ES-DE. | `/sdcard/perfect_dark/data/`<br>`/sdcard/Android/data/com.perfectdark.port/files/data/` |
| **WQ-04** | **GoldenEye 007 (Recomp)** | Native Port | **[VERIFIED RUNNING]** | `com.sunjaycy.goldeneye` v1.4.1 installed. Resolved path issue: moved `default.xex` and game dump out of `files/assets/` directly into `files/` root. Verified running on hardware with full Twycross/Rare intro and iconic James Bond gunbarrel sequence. Launcher `.app` in ES-DE. | `/sdcard/goldeneye/`<br>`/sdcard/Android/data/com.sunjaycy.goldeneye/files/` |
| **WQ-05** | **Diddy Kong Racing (DKR-R)** | Native Port | **[BLOCKED: RT64 ADRENO BUG]** | `io.github.thatguymcd.dkrr.preview` v1.0.6 installed; `dkr.z64` (12.5 MB, Rev A) staged. Launches to title screen, but tapping "Play Offline" crashes inside `/vendor/lib64/hw/vulkan.adreno.so` (`vkCmdBindPipeline`) due to RT64 pipeline limitation on Snapdragon 865. (Mupen64Plus FZ 60fps standalone available as stable alternative). | `/sdcard/dkrr/`<br>`/sdcard/Android/data/io.github.thatguymcd.dkrr.preview/files/` |
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
| **WQ-16** | **PokeMMO** | Native MMO | **[VERIFIED: ALL 5 REGIONS STAGED]** | `eu.pokemmo.client` installed; Black & White 1 (256 MB each), HeartGold, SoulSilver, Platinum, FireRed & Emerald staged to both download & internal roms sandbox. | `/sdcard/Download/pokemmo_roms/`<br>`/sdcard/Android/data/eu.pokemmo.client/files/roms/` |
| **WQ-17** | **DroidDeck: Steam Launcher** | Frontend / Steam | **[VERIFIED]** | `com.droiddeck.launcher` installed; 720p base -> 1080p FSR; Turnip v26.0.0 R8; `WINEDLLOVERRIDES="dinput8=n,b"`; launcher `.app` registered in ES-DE. | `/sdcard/DroidDeck/config.json`<br>`/sdcard/DroidDeck/settings.json` |
| **WQ-18** | **GBA Full Library (486 Games)** | ROM Sync | **[VERIFIED 100%]** | 486 of 486 `.zip` ROMs (2.17 GB) verified in canonical storage layout. | `/storage/<SD_ID>/ROMs/gba/` |
| **WQ-19** | **N64 Best Set (293 Games)** | ROM Sync | **[VERIFIED 100%]** | 293 of 293 `.n64.zip` ROMs (3.60 GB) verified in canonical storage layout. | `/storage/<SD_ID>/ROMs/n64/` |
| **WQ-20** | **AMOLED Homescreen & Wallpaper** | Retroid OS | **[VERIFIED]** | Custom 1080p Cyberpunk Neon Controller AMOLED wallpaper active; Page 1 & Page 2 organized. | Device UI |
| **WQ-21** | **Apotris** | Native Port | **[VERIFIED 100% WORKING]** | `com.apotris.android` (ARM64 v8a) installed and verified running (+236ms launch, SDL2 main, 60fps native). Launcher `.app` staged in ES-DE. Eliminates need for GBA emulation. | Native APK & `/storage/<SD_ID>/ROMs/ports/Apotris.app` |
| **WQ-22** | **Banjo-Kazooie (Banjo Recomp)** | Native Port | **[BLOCKED: RT64 ADRENO BUG]** | `com.aure.banjorecomp` v0.1.2 installed; clean USA v1.0 `banjo.z64` (16 MB) staged to `/sdcard/Android/data/com.aure.banjorecomp/files/`. Crashes on startup inside `recompui::renderer::RT64Context::send_dummy_workload` due to identical Adreno 650 Qualcomm Vulkan driver bug (GitHub issue #19). | `/sdcard/Android/data/com.aure.banjorecomp/files/` |
| **WQ-23** | **Paper Mario 64** | Native Port | **[PENDING ANDROID BUILD]** | Decompilation 100% complete (`pmret/papermario`). HarbourMasters' `PaperBoat` currently officially supports Windows, Linux, and Mac. Community Android port (`YlPorts/PaperBoat-android`) has no precompiled release APKs yet. (Playable via standalone Mupen64Plus FZ). | N64 Standalone |
| **WQ-24** | **Super Mario 64 (sm64ex-alo)** | Native Port | **[QUEUED FOR DEPLOYMENT]** | Standalone Android APK with Render96 HD models/textures, 60 FPS animation interpolation, and 360° right-stick analog camera. | Queued |
| **WQ-25** | **Another Metroid 2 Remake (AM2R)** | Native Port | **[QUEUED FOR DEPLOYMENT]** | v1.5.5+ Android build with HQ uncompressed audio and 16:9 widescreen canvas. | Queued |
| **WQ-26** | **Sonic Mania (RSDKv5)** | Native Port | **[QUEUED FOR DEPLOYMENT]** | Retro Engine v5 native Android APK + `Data.rsdk` assets. | Queued |
| **WQ-27** | **Sonic 1, 2 & CD (RSDKv3/v4)** | Native Port | **[QUEUED FOR DEPLOYMENT]** | Decompilation native ports with widescreen 60fps. | Queued |
| **WQ-28** | **CannonBall: OutRun** | Native Port | **[QUEUED FOR DEPLOYMENT]** | C++ arcade rewrite targeting 60fps widescreen arcade OutRun. | Queued |
| **WQ-29** | **Hollow Knight & Celeste** | Native Port | **[QUEUED FOR DEPLOYMENT]** | Standalone ARM64 native Android ports. | Queued |
| **WQ-30** | **Dreamcast Duplicate Cleanup** | ROM Hygiene | **[VERIFIED CLEAN]** | Duplicate CHD of *Arcade Racing Legends - Road Trip Edition* removed; single verified CDI retained. | `/storage/<SD_ID>/ROMs/dreamcast/` |

---

## 2. Technical Findings & Engine Bottlenecks

### A. The N64 Recomp RT64 Adreno Bug
Both **Diddy Kong Racing (DKR-R)** (`io.github.thatguymcd.dkrr.preview`) and **Banjo-Kazooie (Banjo Recomp)** (`com.aure.banjorecomp`) rely on the `RT64` Vulkan rendering layer.
- **Root Cause Verified via Live Logcat**:
  - DKR-R: `signal 11 (SIGSEGV)` null pointer dereference inside `/vendor/lib64/hw/vulkan.adreno.so` at `qglinternal::vkCmdBindPipeline` when executing `RT64::DisplayList`.
  - Banjo Recomp: Crash inside `recompui::renderer::RT64Context::send_dummy_workload(unsigned int)+132` in `vulkan.adreno.so` (upstream GitHub issue #19: Adreno 650 driver incompatibility).
- **Status**: Standalone APKs do not bundle custom Turnip loaders, so they inherit Qualcomm's proprietary driver bugs. Both games run flawlessly at 60fps with high-resolution texture packs on the RP5 via **Mupen64Plus FZ Standalone**.

### B. DroidDeck & OutRun 2006 Discovery Resolved
- DroidDeck manages multiple Steam mount paths (`/mnt/bannerlator-sd`, `/storage/<SD_ID>/Games/Steam`, and `D:\`).
- By updating `libraryfolders.vdf` in all three locations (`Games/Steam/`, `Games/Steam/steamapps/`, and DroidDeck's rootfs `files/steam/steamapps/`) with App ID `"8960"` ("OutRun 2006: Coast 2 Coast"), DroidDeck immediately recognized the game.
- The game is now fully visible and launchable under the **Games** tab with custom launch profiles, FSR upscaling to 1080p, and `dinput8` tweaks enabled.
