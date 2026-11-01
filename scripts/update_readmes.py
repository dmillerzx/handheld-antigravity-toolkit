#!/usr/bin/env python3
"""
update_readmes.py
Synchronizes and updates READMEs across repositories:
1. BanjoRecomp-Android:
   - Clarifies primary test device is Retroid Pocket 5 (RP5) not AYN Thor.
   - Highlights RP5 hardware testing, ZL/L1 crouch multi-bind, Turnip driver loader, and auto-hydration.
   - Updates android/README.md with live hardware verification results.
2. DKR-R:
   - Updates release references to v1.0.14-android and verifies RP5 documentation.
3. handheld-antigravity-toolkit (AntigravityWorkingDir):
   - Registers BanjoRecomp and DKR-R under Native Ports & Decompilations.
   - Updates canonical storage definitions (.z64, .nds, xbox).
   - Documents verified working titles for Banjo and DKR-R on RP5.
"""

from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent

def update_banjo_readme():
    banjo_readme = WORKSPACE / "Banjo-Kazooie-Recomp" / "README.md"
    if not banjo_readme.exists():
        print("Banjo README not found at", banjo_readme)
        return

    content = banjo_readme.read_text(encoding="utf-8").replace("\r\n", "\n")

    old_header = (
        "# Banjo: Recompiled for Android\n\n"
        "**Banjo-Kazooie, recompiled for Android handhelds. With the full Banjo: Recompiled feature set, controller support, and dual screen support.**\n\n"
        "> This repository and its releases do not contain game assets. You must provide your own supported Banjo-Kazooie ROM to build or run the project."
    )

    new_header = (
        "# 📱 Banjo: Recompiled — Community Android & Handheld Port\n\n"
        '<p align="center">\n'
        '  <a href="https://github.com/dmillerzx/BanjoRecomp-Android/releases/latest">\n'
        '    <img src="https://img.shields.io/github/v/release/dmillerzx/BanjoRecomp-Android?label=Latest%20Android%20APK&amp;color=brightgreen&amp;style=for-the-badge" alt="Latest Android APK">\n'
        "  </a>\n"
        '  <a href="https://github.com/dmillerzx/BanjoRecomp-Android/releases">\n'
        '    <img src="https://img.shields.io/badge/Platform-Android%20arm64--v8a-blue?style=for-the-badge&amp;logo=android" alt="Platform: Android arm64-v8a">\n'
        "  </a>\n"
        '  <a href="https://github.com/dmillerzx/BanjoRecomp-Android/issues">\n'
        '    <img src="https://img.shields.io/github/issues/dmillerzx/BanjoRecomp-Android?style=for-the-badge&amp;color=orange" alt="GitHub Issues">\n'
        "  </a>\n"
        "</p>\n\n"
        "> [!NOTE]\n"
        "> **Community Handheld Fork Notice**: This repository is a community-driven fork maintained by [dmillerzx](https://github.com/dmillerzx) focused on physical Android gaming handhelds — actively maintained and verified on the **Retroid Pocket 5** (Qualcomm Snapdragon 865, Adreno 650, Android 13) and generic AArch64 devices.\n"
        ">\n"
        "> * Upstream Android port by [@AurelioB](https://github.com/AurelioB/BanjoRecomp-Android) (originally developed and tested on the AYN Thor dual-screen handheld).\n"
        "> * Desktop releases and core recompilation by [N64: Recompiled](https://github.com/N64Recomp/N64Recomp).\n"
        "> * **No Game Assets**: This repository and its releases do not contain game assets or ROMs. You must provide an authentic **Banjo-Kazooie (USA) v1.0** ROM (`.z64`)."
    )

    old_ctrl = (
        "### Full controller support\n\n"
        "Designed with Android handhelds in mind. Tested on the AYN Thor."
    )

    new_ctrl = (
        "### Full controller & handheld hardware support\n\n"
        "- **Primary Test Device**: Actively maintained and verified on the **Retroid Pocket 5 (RP5)** (Qualcomm Snapdragon 865 / Adreno 650, Android 13) at native 1080p, locked 60 FPS in 16:9 widescreen presentation.\n"
        "- **Physical Controls**: Tuned controller mapping including modern dual-trigger crouch multi-bind (`ZL` + `L1`).\n"
        "- **Adreno 650 / Snapdragon 865 Crash Guard**: Null-pipeline SPIR-V guard preventing driver `SIGSEGV` faults on Qualcomm devices.\n"
        "- **Turnip GPU Driver Loader**: Built-in AdrenoTools driver loader supporting Mesa Turnip drivers (e.g. Turnip v24.3.0 R9v2) for enhanced Vulkan stability.\n"
        "- **Zero-Touch ROM Hydration**: Automatically searches `/storage/*/ROMs/n64/` and app files on launch, extracting `.zip` archives and verifying ROM headers so the game is ready to play immediately.\n"
        "- **Header Inspection Dialog**: Detects unsupported revisions (e.g. Rev A / v1.1) and displays a clear explanation dialog rather than failing silently.\n"
        "- *(Note: Upstream project was originally developed and tested on the dual-screen AYN Thor).*"
    )

    if old_header in content and old_ctrl in content:
        content = content.replace(old_header, new_header).replace(old_ctrl, new_ctrl)
        banjo_readme.write_text(content, encoding="utf-8", newline="\n")
        print("Updated Banjo-Kazooie-Recomp/README.md successfully.")
    else:
        print("Warning: old header or ctrl patterns not matched in Banjo README.")

def update_banjo_android_readme():
    banjo_android_readme = WORKSPACE / "Banjo-Kazooie-Recomp" / "android" / "README.md"
    if not banjo_android_readme.exists():
        print("Banjo android README not found at", banjo_android_readme)
        return

    content = banjo_android_readme.read_text(encoding="utf-8").replace("\r\n", "\n")

    old_text = "Source tests and an offline arm64 APK build verify the integration, but a successful launch, swapchain presentation, and gameplay session with Turnip on a real arm64 Adreno device are still required."
    new_text = "Verified on hardware: Tested on the Retroid Pocket 5 (Qualcomm Snapdragon 865 / Adreno 650, Android 13). Both Mesa Turnip drivers (Turnip v24.3.0 R9v2, TurnipZ 0.3.0) and stock Qualcomm drivers launch cleanly, establish swapchain presentation, and run at a locked 60 FPS in 16:9 widescreen."

    if old_text in content:
        content = content.replace(old_text, new_text)
        banjo_android_readme.write_text(content, encoding="utf-8", newline="\n")
        print("Updated Banjo-Kazooie-Recomp/android/README.md successfully.")
    else:
        print("Warning: old text pattern not found in Banjo android README.")

def update_dkrr_readme():
    dkrr_readme = WORKSPACE / "DKR-R" / "README.md"
    if not dkrr_readme.exists():
        print("DKR-R README not found at", dkrr_readme)
        return

    content = dkrr_readme.read_text(encoding="utf-8").replace("\r\n", "\n")

    # Update v1.0.12 mentions to current release v1.0.14-android
    content = content.replace("## DKR-R v1.0.12 Release Build", "## DKR-R v1.0.14 Release Build")
    content = content.replace("v1.0.12 is available for", "v1.0.14 is available for")
    content = content.replace("complete v1.0.12 packages", "complete v1.0.14 packages")
    content = content.replace("v1.0.12 release notes", "v1.0.14 release notes")

    dkrr_readme.write_text(content, encoding="utf-8", newline="\n")
    print("Updated DKR-R/README.md successfully.")

def update_toolkit_readme():
    toolkit_readme = WORKSPACE / "README.md"
    if not toolkit_readme.exists():
        print("Toolkit README not found at", toolkit_readme)
        return

    content = toolkit_readme.read_text(encoding="utf-8").replace("\r\n", "\n")

    # 1. Update Ecosystem count and list
    old_eco_intro = "### 4. Native Android Ports & Decompilations Ecosystem\n- Manages 19 native Android C/C++ source ports, static recompilations, and standalone fan projects"
    new_eco_intro = "### 4. Native Android Ports & Decompilations Ecosystem\n- Manages 21 native Android C/C++ source ports, static recompilations, and standalone fan projects"

    if old_eco_intro in content:
        content = content.replace(old_eco_intro, new_eco_intro)

    old_n64_entry = "  - **N64 Classics**: Mario Kart 64 (SpaghettiKart), Star Fox 64 (Starship), GoldenEye 007 (Recomp), Perfect Dark, Paper Mario 64 (PaperBoat)"
    new_n64_entry = (
        "  - **N64 Static Recompilations**: Banjo-Kazooie Recompiled (`com.dishii.banjorecomp` - RP5 verified, Turnip loader, auto-hydration, ZL/L1 crouch), Diddy Kong Racing Recompiled (`io.github.thatguymcd.dkrr.preview` - v1.0.14-android, Adreno 650 compute guards, 60 FPS interpolated)\n"
        "  - **N64 Classics**: Mario Kart 64 (SpaghettiKart), Star Fox 64 (Starship), GoldenEye 007 (Recomp), Perfect Dark, Paper Mario 64 (PaperBoat)"
    )

    if old_n64_entry in content:
        content = content.replace(old_n64_entry, new_n64_entry)

    # 2. Update storage layout n64 / nds / xbox
    old_storage = (
        "│   ├── gba/                       # Full verified GBA library (.zip)\n"
        "│   ├── gc/                        # GameCube games (.rvz)\n"
        "│   ├── n64/                       # Full N64 Best Set (.n64.zip)\n"
        "│   ├── nds/                       # Nintendo DS (.zip)\n"
        "│   ├── ports/                     # Native Android port launchers (*.app)\n"
        "│   ├── ps2/                       # PlayStation 2 (.chd)\n"
        "│   ├── psx/                       # PlayStation 1 (.chd)\n"
        "│   ├── snes/                      # Super Nintendo (.zip)\n"
        "│   └── wii/                       # Nintendo Wii (.rvz)"
    )

    new_storage = (
        "│   ├── gba/                       # Full verified GBA library (.zip)\n"
        "│   ├── gc/                        # GameCube games (.rvz)\n"
        "│   ├── n64/                       # Full N64 library (uncompressed .z64 big-endian)\n"
        "│   ├── nds/                       # Nintendo DS (.nds)\n"
        "│   ├── ports/                     # Native Android port launchers (*.app)\n"
        "│   ├── ps2/                       # PlayStation 2 (.chd)\n"
        "│   ├── psx/                       # PlayStation 1 (.chd)\n"
        "│   ├── snes/                      # Super Nintendo (.zip)\n"
        "│   ├── wii/                       # Nintendo Wii (.rvz)\n"
        "│   └── xbox/                      # Original Xbox trimmed XISO images (*.iso)"
    )

    if old_storage in content:
        content = content.replace(old_storage, new_storage)

    # 3. Add Banjo-Kazooie and DKR-R to Verified Working Titles
    old_titles = "- **GoldenEye 007 (Native Android Recomp)**:"
    new_titles = (
        "- **Banjo-Kazooie (Native Android Recomp)**:\n"
        "  - Native 60 FPS 1080p widescreen presentation (`16:9 Expand`) verified on the Retroid Pocket 5.\n"
        "  - Integrated AdrenoTools GPU driver loader with Mesa Turnip support, dual-trigger crouch multi-bind (`ZL` + `L1`), and automatic US v1.0 ROM hydration from `/storage/*/ROMs/n64/`.\n"
        "- **Diddy Kong Racing (DKR-R Native Port)**:\n"
        "  - Locked 60 FPS interpolated rendering at native 1080p on Snapdragon 865 / Adreno 650 with dedicated Vulkan compute pipeline guards eliminating driver crashes.\n"
        "- **GoldenEye 007 (Native Android Recomp)**:"
    )

    if old_titles in content and "- **Banjo-Kazooie (Native Android Recomp)**:" not in content:
        content = content.replace(old_titles, new_titles)

    toolkit_readme.write_text(content, encoding="utf-8", newline="\n")
    print("Updated handheld-antigravity-toolkit/README.md successfully.")

if __name__ == "__main__":
    update_banjo_readme()
    update_banjo_android_readme()
    update_dkrr_readme()
    update_toolkit_readme()
