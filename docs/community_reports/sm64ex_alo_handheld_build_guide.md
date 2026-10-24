### [Guide] Building SM64EX-ALO with 60 FPS, Puppycam 2 (360° Analog Camera) & Widescreen on Android Handhelds

### Overview
This guide demonstrates how to compile the enhanced Super Mario 64 native Android port (`sm64ex-alo`) directly on an Android handheld (Snapdragon 865, Retroid Pocket 5, Odin) using Termux without needing a separate Linux PC or cross-compiler.

---

### Prerequisites
1. **Termux (Terminal Emulator)**: Installed with storage permissions granted.
2. **Vanilla USA N64 ROM**: Authentic clean `baserom.us.z64` (MD5: `20b854b239203baf6c961b850a4a51a2`) placed in your `/sdcard/Download/` folder.

---

### Step 1: Install Required Toolchain in Termux
Open Termux and run:
```bash
pkg update -y
pkg install -y git wget make python clang binutils aapt apksigner libc++ libssh2
```

### Step 2: Clone Repository & Setup SDL Dependencies
```bash
cd ~
git clone --recursive https://github.com/izzy2fancy/sm64ex-alo-izzys.git
cd sm64ex-alo-izzys
cp /sdcard/Download/baserom.us.z64 baserom.us.z64

# Download Khronos & SDL2 Android headers
cd platform/android
bash ./getkhrplatform.sh
bash ./getSDL.sh
cd ../..
```

### Step 3: Extract Assets & Compile
```bash
# Extract ROM assets
python extract_assets.py us

# Compile with 60 FPS interpolation and Puppycam 2 across all CPU cores
export PREFIX=/data/data/com.termux/files/usr
make -j$(nproc) HIGH_FPS_PC=1 BETTERCAMERA=1 NODRAWINGDISTANCE=1

# Output APK is generated at:
cp build/us_android/sm64.us.f3dex2e.apk /sdcard/sm64_alo_60fps.apk
```

### Step 4: Install & Enjoy
Install `/sdcard/sm64_alo_60fps.apk` using your favorite file manager. Physical gamepad controls and the right analog stick are automatically bound via SDL2!
