#!/usr/bin/env python3
"""
Android UI Automation & Deterministic Element Interaction Utility.

Eliminates visual coordinate guesswork and trial-and-error tapping by:
1. Parsing live Android UI hierarchy via Accessibility/UIAutomator XML.
2. Locating exact UI elements by text, resource ID, or content description.
3. Calculating true geometric centroids for 100% deterministic tapping.
4. Providing automated handlers for Android Storage Access Framework (DocumentsUI)
   file pickers (search, match, select, verify).
"""

import argparse
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple


class UIElement:
    def __init__(self, node: ET.Element):
        self.node = node
        self.text = node.attrib.get("text", "")
        self.resource_id = node.attrib.get("resource-id", "")
        self.class_name = node.attrib.get("class", "")
        self.content_desc = node.attrib.get("content-desc", "")
        self.package = node.attrib.get("package", "")
        self.bounds_str = node.attrib.get("bounds", "[0,0][0,0]")
        self.x1, self.y1, self.x2, self.y2 = self._parse_bounds(self.bounds_str)
        self.cx = (self.x1 + self.x2) // 2
        self.cy = (self.y1 + self.y2) // 2
        self.width = self.x2 - self.x1
        self.height = self.y2 - self.y1

    @staticmethod
    def _parse_bounds(bounds: str) -> Tuple[int, int, int, int]:
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return 0, 0, 0, 0

    def __repr__(self):
        desc = f"text='{self.text}'" if self.text else f"id='{self.resource_id}'"
        return f"<UIElement {desc} bounds=[{self.x1},{self.y1}][{self.x2},{self.y2}] center=({self.cx},{self.cy})>"


class AndroidUIAutomator:
    def __init__(self, adb_path: str = "platform-tools/adb.exe", serial: Optional[str] = None):
        self.adb_path = adb_path if os.path.isabs(adb_path) else os.path.abspath(adb_path)
        self.serial = serial
        if not self.serial:
            self.serial = self._detect_device()

    def _adb_cmd(self, args: List[str]) -> List[str]:
        cmd = [self.adb_path]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        return cmd

    def run_cmd(self, args: List[str], check: bool = True, timeout: float = 15.0) -> subprocess.CompletedProcess:
        cmd = self._adb_cmd(args)
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, returncode=124, stdout="", stderr="Timeout")

    def _detect_device(self) -> Optional[str]:
        res = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True)
        lines = [line.strip() for line in res.stdout.strip().splitlines()[1:] if line.strip()]
        for line in lines:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                return parts[0]
        return None

    def dump_hierarchy(self) -> Optional[ET.Element]:
        """Dumps current window hierarchy via uiautomator and returns XML root."""
        # Dump to temporary file on device and pull stdout
        res = self.run_cmd(["shell", "uiautomator dump /sdcard/uidump.xml"], check=False)
        if res.returncode != 0:
            time.sleep(1)
            res = self.run_cmd(["shell", "uiautomator dump /sdcard/uidump.xml"], check=False)

        cat_res = self.run_cmd(["shell", "cat /sdcard/uidump.xml"], check=False)
        xml_str = cat_res.stdout.strip()
        if not xml_str or not xml_str.startswith("<?xml"):
            # Fallback: pull file
            temp_local = "scratch_uidump.xml"
            self.run_cmd(["pull", "/sdcard/uidump.xml", temp_local], check=False)
            if os.path.exists(temp_local):
                with open(temp_local, "r", encoding="utf-8", errors="ignore") as f:
                    xml_str = f.read()
                try:
                    os.remove(temp_local)
                except OSError:
                    pass

        if xml_str:
            try:
                # Clean any stray shell output before the xml tag
                idx = xml_str.find("<?xml")
                if idx != -1:
                    xml_str = xml_str[idx:]
                return ET.fromstring(xml_str)
            except ET.ParseError:
                return None
        return None

    def find_all(
        self,
        text: Optional[str] = None,
        text_contains: Optional[str] = None,
        resource_id: Optional[str] = None,
        content_desc: Optional[str] = None,
        class_name: Optional[str] = None,
        package: Optional[str] = None,
    ) -> List[UIElement]:
        root = self.dump_hierarchy()
        if root is None:
            return []

        matches = []
        for node in root.iter("node"):
            elem = UIElement(node)
            # Filter checks
            if text is not None and elem.text != text:
                continue
            if text_contains is not None and text_contains.lower() not in elem.text.lower():
                continue
            if resource_id is not None and not (
                elem.resource_id == resource_id or elem.resource_id.endswith(f"/{resource_id}")
            ):
                continue
            if content_desc is not None and content_desc.lower() not in elem.content_desc.lower():
                continue
            if class_name is not None and elem.class_name != class_name:
                continue
            if package is not None and elem.package != package:
                continue
            matches.append(elem)
        return matches

    def find_first(self, **kwargs) -> Optional[UIElement]:
        elems = self.find_all(**kwargs)
        return elems[0] if elems else None

    def tap(self, x: int, y: int):
        self.run_cmd(["shell", f"input tap {x} {y}"])

    def tap_element(self, elem: UIElement):
        self.tap(elem.cx, elem.cy)

    def type_text(self, text: str):
        # Escape spaces for input text
        safe_text = text.replace(" ", "%s")
        self.run_cmd(["shell", f"input text {safe_text}"])

    def screencap(self, local_dest: str):
        self.run_cmd(["shell", "screencap", "-p", "/sdcard/screen.png"], check=False)
        self.run_cmd(["pull", "/sdcard/screen.png", local_dest], check=False)

    def press_key(self, keycode: int):
        self.run_cmd(["shell", f"input keyevent {keycode}"])

    def wait_and_click(
        self,
        text: Optional[str] = None,
        text_contains: Optional[str] = None,
        resource_id: Optional[str] = None,
        content_desc: Optional[str] = None,
        timeout: float = 10.0,
        poll_interval: float = 0.8,
    ) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            elem = self.find_first(
                text=text,
                text_contains=text_contains,
                resource_id=resource_id,
                content_desc=content_desc,
            )
            if elem:
                self.tap_element(elem)
                return True
            time.sleep(poll_interval)
        return False

    def select_in_documentsui(self, target_filename: str, timeout: float = 15.0) -> bool:
        """
        Deterministically selects a file in Android's DocumentsUI (Storage Access Framework).
        Uses search box filtering to avoid directory traversal and grid scrolling pitfalls.
        """
        print(f"[*] Navigating DocumentsUI to select '{target_filename}'...")
        start = time.time()

        # Step 1: Check if already visible in current view
        while time.time() - start < timeout:
            target = self.find_first(text_contains=target_filename)
            if target and target.height > 20:
                print(f"[+] Found direct target item: {target}. Tapping...")
                self.tap_element(target)
                time.sleep(1.0)
                return True

            # Look for search button
            search_btn = (
                self.find_first(resource_id="option_menu_search")
                or self.find_first(resource_id="sub_menu_search")
                or self.find_first(resource_id="action_search")
                or self.find_first(content_desc="Search")
            )
            if search_btn:
                print(f"[+] Found search button: {search_btn}. Opening search...")
                self.tap_element(search_btn)
                time.sleep(0.8)

                # Find search edit text
                search_box = self.find_first(resource_id="search_src_text")
                if search_box:
                    print(f"[+] Found search box. Typing '{target_filename}'...")
                    self.tap_element(search_box)
                    time.sleep(0.3)
                    self.type_text(target_filename)
                    self.press_key(66)  # KEYCODE_ENTER
                    time.sleep(1.2)

                    # Look for result
                    res_elem = self.find_first(text_contains=target_filename)
                    if res_elem:
                        print(f"[+] Selected search match: {res_elem}. Tapping...")
                        self.tap_element(res_elem)
                        time.sleep(1.0)
                        return True
            time.sleep(0.8)

        print(f"[-] Could not find or select '{target_filename}' in DocumentsUI within {timeout}s.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Deterministic Android UI Automator")
    parser.add_argument("--serial", "-s", help="Target device serial")
    parser.add_argument("--adb", default="platform-tools/adb.exe", help="ADB binary path")
    parser.add_argument("--dump", action="store_true", help="Print all visible UI elements")
    parser.add_argument("--click-text", help="Click element with exact text")
    parser.add_argument("--click-contains", help="Click element containing text")
    parser.add_argument("--click-id", help="Click element matching resource ID")
    parser.add_argument("--select-file", help="Search and select filename in DocumentsUI/SAF")
    parser.add_argument("--screencap", help="Capture screen to local path")
    parser.add_argument("--timeout", type=float, default=10.0, help="Wait timeout in seconds")

    args = parser.parse_args()
    ui = AndroidUIAutomator(adb_path=args.adb, serial=args.serial)

    if args.screencap:
        ui.screencap(args.screencap)
        print(f"Screenshot saved to {args.screencap}")
        return

    if args.dump:
        elems = ui.find_all()
        print(f"Total UI Elements: {len(elems)}")
        for e in elems:
            if e.text or e.resource_id or e.content_desc:
                print(f"  {e}")
        return

    if args.click_text:
        ok = ui.wait_and_click(text=args.click_text, timeout=args.timeout)
        print(f"Click text '{args.click_text}': {'SUCCESS' if ok else 'FAILED'}")
        sys.exit(0 if ok else 1)

    if args.click_contains:
        ok = ui.wait_and_click(text_contains=args.click_contains, timeout=args.timeout)
        print(f"Click contains '{args.click_contains}': {'SUCCESS' if ok else 'FAILED'}")
        sys.exit(0 if ok else 1)

    if args.click_id:
        ok = ui.wait_and_click(resource_id=args.click_id, timeout=args.timeout)
        print(f"Click resource-id '{args.click_id}': {'SUCCESS' if ok else 'FAILED'}")
        sys.exit(0 if ok else 1)

    if args.select_file:
        ok = ui.select_in_documentsui(args.select_file, timeout=args.timeout)
        print(f"Select file '{args.select_file}': {'SUCCESS' if ok else 'FAILED'}")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
