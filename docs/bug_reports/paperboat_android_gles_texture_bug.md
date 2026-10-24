- [x] I have checked the known issues and searched Github to ensure this issue has not already been reported.
- [x] This is not a feature request, I know those belong on Discord/Github Discussions.

### Description of the bug:
On Android 13 using the OpenGL ES rendering backend on Qualcomm Adreno GPUs (tested on Snapdragon 865 / Adreno 650), all 2D text (File Select UI, options, fonts), the title banner, and 2D billboard sprites (such as Mario at the piano in the intro and the theater curtains) render with severe graphical corruption consisting of vertical barcode-like stripes and scrambled palette dither artifacts.

In contrast, all 3D polygon geometry (the theater stage, Mario's house, terrain, and roofs) renders cleanly and runs smoothly at locked 60 FPS.

### Can you reproduce? If so please list the steps:
- [x] Yes, here are the steps to reproduce the bug:
1. Install PaperBoat APK (v1.0.3, CI build 39825683378) on an Android device with Qualcomm Adreno graphics (Snapdragon 865 / Adreno 650, Android 13).
2. Generate `pm64.o2r` using authentic `baserom.us.z64` (Paper Mario USA).
3. Launch `dev.net64.paperboat/.LauncherActivity` with OpenGL ES backend (`"Backend": {"Id": 1}`).
4. Advance through the intro cutscene to the File Select menu.
5. Notice that while 3D stage geometry and UI card borders render properly, all font glyphs, slot labels, and 2D character billboard textures are scrambled into vertical barcode patterns.

### Expected behavior:
2D paletted textures (CI4 / CI8 / IA fonts and character sprites) should sample colors correctly from their palettes and render cleanly without vertical striping or palette aliasing artifacts, matching desktop OpenGL / Vulkan backends.

### Screenshots or videos:
**1. File Select Menu (Font Glyphs & UI Labels Corrupted into Vertical Barcodes):**
![File Select Menu Corruption](https://raw.githubusercontent.com/dmillerzx/handheld-antigravity-toolkit/main/docs/assets/screenshots/paperboat_gles_file_select_artifact.png)

**2. Title Banner & Intro Theater Curtains (Billboard Texture Corruption):**
![Title Banner Corruption](https://raw.githubusercontent.com/dmillerzx/handheld-antigravity-toolkit/main/docs/assets/screenshots/paperboat_gles_title_banner_artifact.png)

### System Information:
- OS: Android 13 (Retroid OS / AOSP)
- Device: Retroid Pocket 5 (Qualcomm Snapdragon 865 / SM8250)
- GPU: Qualcomm Adreno 650 (Qualcomm proprietary driver 0.512.467.0 / 0746.0)
- GFX Backend: OpenGL ES 3.0 / 3.2 (`"Backend": {"Id": 1}`)
- Game Version: PaperBoat v1.0.3 (build 39825683378)
- ROM Version: Paper Mario (USA) (CRC32: `E5A5BC1E`, MD5: `04A7B2065842CAE1B5ED9FDEBDEBCE61`)

### Additional Information & Technical Analysis:
1. **OpenGL ES Restriction**:
   Inspection of `lib/arm64-v8a/libmain.so` indicates that the Vulkan backend is not currently compiled in Android CI builds (`Vulkan symbols: []`), making GLES the sole available rendering path on Android.
2. **Fast3D Texture Sampling**:
   In `libultraship` (`lus-converge` branch), color-indexed (CI4/CI8) and IA textures are uploaded with palettes sampled via `paletteSample()` in `shaders/opengl/include/palette.glsli` and `interpreter.cpp`. Under Adreno's OpenGL ES implementation, the coordinate sampling or index dereferencing against `uTexPal` produces vertical stripe aliasing across 4-bit and 8-bit texture rasters, leaving 3D polygon geometry unaffected while scrambling all 2D text and billboard assets.
