# DKR-R Android (Adreno 650) - handoff, 2026-10-25

Fork: https://github.com/dmillerzx/DKR-R  (MIT, upstream ThatGuyMcd/DKR-R)
Local clone: `DKR-R/` (gitignored? no - it is a nested repo; do not `git add` it from the toolkit repo)
Branch: `android/ci-and-adreno-fix` (pushed, 2 commits ahead of `main`)

## Done
- CI baseline green on the fork (Android device compilation, run 40185153827).
  Workflow now also triggers on `android/**` pushes (fork had no registered workflows).
- `patches/android/vulkan-pipeline-failure.patch`: tail stage of the plume patch chain
  (wired in `runtime-recomp/cmake/android/PreRotation.cmake`). Failed
  `vkCreate{Graphics,Compute}Pipelines` previously left a null `VkPipeline` that
  `VulkanCommandList::setPipeline` bound unchecked. Now: records VkResult under
  `Stage::GraphicsPipeline/ComputePipeline`, logs failing shader stages, quarantines via
  existing health path, and guards the bind.
- Contract test `test_failed_pipeline_never_reaches_bind` (applies the real 13-patch chain
  to a private copy). 5/5 pass. CI step added.
- NDK r29 `clang++ --target=aarch64-linux-android28 -fsyntax-only` of the composed+patched
  plume_vulkan.cpp passes; negative control (typo) fails as expected.
- Toolchain installed: JDK17, CMake, Ninja, `C:\Android\Sdk` (NDK 29.0.14206865, platform 35,
  build-tools 35). Gradle NOT installed (winget id `Gradle.Gradle.8` does not exist; fetch from
  gradle.org when needed).

## Corrections to earlier notes
- The SIGSEGV-in-`vkCmdBindPipeline` logcat (CLAUDE.md, WORKQUEUE WQ-05, RT64#282 text) is
  from **Banjo Recomp** (`libgame.so`), not DKR-R (`libDKR-R.so`). No DKR-R trace captured yet.
  Do not edit the already-public RT64#282 without user OK.
- The patch makes the failure diagnosable; it does NOT make Adreno link the shader. Real fix
  needs the driver's link error + offending shader from a DKR-R device run.

## Blockers / open
- Full APK needs the maintainer's frozen "1.0.7 source capsule" + prepared inputs and WSL2
  (not installed; needs admin + reboot). Prepare script checks the US v1.0 ROM SHA-1.
- ROMs: do not download ROMs from the internet. A Rev A zip is on the RP5 SD card
  (`/storage/<SD_ID>/ROMs/n64/`) and a copy in `roms/n64/` (gitignored).
- RP5 is shared with another agent session (it launched/force-stopped NetherSX2 over adb
  at 06:39). Check `adb logcat -d | grep "START u0"` before launching anything.
- v1.0.6 (installed) predates ~25 Android Vulkan patches; first real test needs a build of main.

## Next
1. Confirm CI green on branch, open PR into fork `main`.
2. Open issue on ThatGuyMcd/DKR-R asking for ROM-free dev build path / source capsule.
3. Fix the Banjo-vs-DKR-R wording in CLAUDE.md / WORKQUEUE.md.
4. Decide: WSL2 route (option B) vs waiting on upstream.
5. Put RP5 display to sleep when idle (`adb -s <serial> shell input keyevent 26`).
