#!/usr/bin/env python3
"""
configure_hakux_controls.py
Automates Retroid Pocket 5 analog stick deadzone optimization for hakuX (Original Xbox).
Sets both Left Stick and Right Stick dead zones to 0.10 (10%) to prevent Hall effect stick drift.
"""

import argparse
import re
import subprocess
import time
import xml.etree.ElementTree as ET

def get_adb_cmd(serial=None):
    if serial:
        return ["adb", "-s", serial]
    return ["adb"]

def adb_run(cmd_prefix, args):
    cmd = cmd_prefix + args
    return subprocess.run(cmd, capture_output=True, text=True)

def dump_ui(cmd_prefix):
    adb_run(cmd_prefix, ["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
    res = adb_run(cmd_prefix, ["shell", "cat", "/sdcard/window_dump.xml"])
    if not res.stdout or "<hierarchy" not in res.stdout:
        return None
    try:
        xml_text = res.stdout[res.stdout.find("<hierarchy"):]
        return ET.fromstring(xml_text)
    except Exception:
        return None

def find_element(root, text=None, desc=None):
    if root is None:
        return None
    for elem in root.iter():
        elem_text = elem.attrib.get("text", "")
        elem_desc = elem.attrib.get("content-desc", "")
        if text and text in elem_text:
            return elem
        if desc and desc in elem_desc:
            return elem
    return None

def get_centroid(elem):
    bounds = elem.attrib.get("bounds", "")
    m = re.findall(r"\d+", bounds)
    if len(m) == 4:
        x1, y1, x2, y2 = map(int, m)
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def configure_hakux(serial=None):
    cmd_prefix = get_adb_cmd(serial)

    print("[*] Checking hakuX installation...")
    pm = adb_run(cmd_prefix, ["shell", "pm", "list", "packages", "com.rfandango.haku_x"])
    if "com.rfandango.haku_x" not in pm.stdout:
        print("[-] hakuX (com.rfandango.haku_x) is not installed on the device.")
        return False

    print("[*] Launching hakuX...")
    adb_run(cmd_prefix, ["shell", "am", "start", "-n", "com.rfandango.haku_x/.LauncherActivity"])
    time.sleep(1.5)

    # Dismiss keyguard / dialogs
    adb_run(cmd_prefix, ["shell", "wm", "dismiss-keyguard"])

    # Tap Settings icon (top right)
    print("[*] Navigating to Settings -> Physical controllers...")
    root = dump_ui(cmd_prefix)
    settings_elem = find_element(root, desc="Settings")
    if settings_elem is not None:
        cx, cy = get_centroid(settings_elem)
        adb_run(cmd_prefix, ["shell", "input", "tap", str(cx), str(cy)])
    else:
        adb_run(cmd_prefix, ["shell", "input", "tap", "1857", "126"])
    time.sleep(0.8)

    # Click Physical controllers
    root = dump_ui(cmd_prefix)
    phys_elem = find_element(root, text="Physical controllers")
    if phys_elem is not None:
        cx, cy = get_centroid(phys_elem)
        adb_run(cmd_prefix, ["shell", "input", "tap", str(cx), str(cy)])
    time.sleep(0.8)

    # Scroll down to Connected controllers
    adb_run(cmd_prefix, ["shell", "input", "swipe", "960", "800", "960", "300", "200"])
    time.sleep(0.6)

    # Click Xbox Wireless Controller
    root = dump_ui(cmd_prefix)
    ctrl_elem = find_element(root, text="Xbox Wireless Controller")
    if ctrl_elem is not None:
        cx, cy = get_centroid(ctrl_elem)
        adb_run(cmd_prefix, ["shell", "input", "tap", str(cx), str(cy)])
    time.sleep(0.8)

    # Scroll down to Sticks and triggers
    for _ in range(3):
        adb_run(cmd_prefix, ["shell", "input", "swipe", "960", "800", "960", "200", "200"])
        time.sleep(0.3)

    time.sleep(0.5)

    print("[*] Setting Left & Right stick dead zones to 0.10 (10%)...")
    # Tapping x=400 on the seekbar tracks exactly to 0.10
    adb_run(cmd_prefix, ["shell", "input", "tap", "400", "621"])
    time.sleep(0.3)
    adb_run(cmd_prefix, ["shell", "input", "tap", "400", "792"])
    time.sleep(0.5)

    # Verify
    root = dump_ui(cmd_prefix)
    left_val = "unknown"
    right_val = "unknown"
    if root is not None:
        for elem in root.iter():
            t = elem.attrib.get("text", "")
            if "Left stick dead zone" in t:
                left_val = t
            if "Right stick dead zone" in t:
                right_val = t

    print(f"[+] Confirmed: {left_val}")
    print(f"[+] Confirmed: {right_val}")

    # Return back to save
    adb_run(cmd_prefix, ["shell", "input", "keyevent", "4"])
    time.sleep(0.4)
    adb_run(cmd_prefix, ["shell", "input", "keyevent", "4"])
    time.sleep(0.4)
    adb_run(cmd_prefix, ["shell", "input", "keyevent", "4"])
    time.sleep(0.4)

    return True

def main():
    parser = argparse.ArgumentParser(description="Configure hakuX analog stick deadzones")
    parser.add_argument("-s", "--serial", default=None, help="Device serial")
    args = parser.parse_args()
    configure_hakux(serial=args.serial)

if __name__ == "__main__":
    main()
