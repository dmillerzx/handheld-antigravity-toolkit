### [Bug Report] Crash on launch on Qualcomm Snapdragon 865 (Adreno 650) devices (e.g. Retroid Pocket 5 / Odin)

**Device & OS Information:**
- **Device:** Retroid Pocket 5 (Handheld Gaming Console)
- **SoC:** Qualcomm Snapdragon 865 (SM8250)
- **GPU:** Adreno 650
- **OS:** Android 13 (Retroid OS / AOSP)
- **Stock Vulkan Driver:** Qualcomm proprietary `/vendor/lib64/hw/vulkan.adreno.so` (Driver version 0.512.467.0 / 0746.0)

---

### Description
When launching DKR-R / Banjo Recompiled on Qualcomm Snapdragon 865 devices, the application crashes immediately upon booting or selecting a ROM. The crash occurs inside Qualcomm's proprietary Vulkan driver during SPIR-V pipeline creation in the RT64 rendering backend.

---

### Crash Stack Trace (Live Logcat from physical hardware)
```text
AdrenoVK-0: Failed to link shaders. Pipeline create failed
...
DEBUG: signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x30
DEBUG: Cause: null pointer dereference
DEBUG:     #00 pc 000000000021b36c  /vendor/lib64/hw/vulkan.adreno.so (qglinternal::vkCmdBindPipeline+28)
DEBUG:     #01 pc 00000000000c43bc  /data/app/.../lib/arm64-v8a/libgame.so (recompui::renderer::RT64Context::send_dummy_workload(unsigned int)+132)
DEBUG:     #02 pc 00000000000ba710  /data/app/.../lib/arm64-v8a/libgame.so (RT64::DisplayList::draw()+480)
```

---

### Root Cause Analysis
Qualcomm's stock proprietary driver on the Snapdragon 865 contains a known compiler bug with specific SPIR-V shader constructs emitted by RT64. Because the shader fails to compile, `vkCreateGraphicsPipelines` returns `VK_NULL_HANDLE`, and the subsequent call to `vkCmdBindPipeline` attempts to dereference offset `0x30` from a null pipeline pointer, generating a fatal `SIGSEGV` (null pointer dereference).

---

### Suggested Fixes / Workarounds for Developers
1. **Turnip Driver Bundling**: Other modern standalone emulators and ports on Android (NetherSX2, Dolphin, Vita3K, Flycast) resolve Adreno 650 driver bugs by bundling custom Turnip/Mesa drivers via an internal Vulkan driver loader.
2. **Null Check on Pipeline**: Guard calls to `vkCmdBindPipeline` in RT64 against null pipeline handles to avoid hard SIGSEGV crashes and output graceful diagnostics.
3. **Shader Simplification / Fallback**: Provide an option to bypass advanced RT64 effects or fall back to an unextended pipeline.
