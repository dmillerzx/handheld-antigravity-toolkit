Fix Adreno 650 launch crash, add Turnip GPU driver loader, ZIP ROM extraction & auto-hydration

Hey @AurelioB,

This PR bundles several stability fixes, UX improvements, and GPU compatibility updates for the Android port tested extensively across physical Snapdragon devices (Retroid Pocket 5, Odin, and generic AArch64 Android 13/14 setups).

### 1. Fix Snapdragon 865 / Adreno 650 launch crash (Issue #22)
Stock Qualcomm proprietary Vulkan drivers on Adreno 650 GPUs fail during RT64 SPIR-V pipeline compilation on boot, returning `VK_NULL_HANDLE`. Calling `vkCmdBindPipeline` on that null handle caused a fatal `SIGSEGV` crash in `vulkan.adreno.so` before reaching gameplay.
- Added a null pipeline guard in `plume_vulkan.cpp` preventing the null pointer dereference.
- Integrated AdrenoTools custom Turnip/Mesa GPU driver loader (`active.json` / Turnip ZIPs in `gpu-drivers/` or `Download/drivers/`), allowing Snapdragon 865/870 devices to run on Mesa Turnip for rock-solid Vulkan stability and higher framerates.

### 2. Compressed ROM (.zip) support & user feedback (Issue #23)
Many handheld users store their N64 libraries in standard `.zip` archives or accidentally pick Revision A (v1.1) ROMs.
- Added automatic decompression for zipped `.z64`/`.n64` archives in `BanjoSDLActivity.java` so users don't get kicked back to the launcher menu without explanation.
- Added header inspection (`NBKE`) to check ROM version on selection. If an unsupported revision (Rev A / Rev B) is selected, it presents a helpful dialog explaining that v1.0 (Rev 0) is required rather than failing silently.
- Added zero-touch auto-hydration from common storage locations (`Android/data/.../files/` and MicroSD `ROMs/n64/`), automatically detecting and validating `Banjo-Kazooie (USA).z64` on boot so "Start Game" is ready immediately.

### 3. Handheld quality-of-life defaults
- Added dual-trigger crouch multi-bind (`ZL` + `L1`) in `config.cpp` for modern controller ergonomics.
- Enabled 60 FPS target refresh and 16:9 Expand widescreen presentation by default for 16:9 handheld screens.
- Included an offline Python regression test suite (`tools/test_android_rom_import.py`) verifying ROM extraction and version checking.

Happy to adjust or break this into smaller PRs if you prefer. Zero rush on review!
