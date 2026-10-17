#!/usr/bin/env python3
"""
scripts/device_profile.py — Dynamic Hardware Profiling & Storage Resolver
========================================================================
Provides unified device detection, JSON profile loading, and dynamic
MicroSD UUID resolution across the community provisioning toolkit.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = WORKSPACE_ROOT / "profiles"

SD_UUID_REGEX = re.compile(r"^[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$")


def list_available_profiles() -> List[Dict]:
    """Returns all available device profiles loaded from profiles/*.json."""
    profiles = []
    if not PROFILES_DIR.exists():
        return profiles
    for json_file in sorted(PROFILES_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_file"] = str(json_file)
                profiles.append(data)
        except Exception as e:
            print(f"[!] Warning: Failed to load profile {json_file.name}: {e}")
    return profiles


def load_profile_by_id(profile_id: str) -> Optional[Dict]:
    """Loads a specific profile by its device_id or filename."""
    candidate_file = PROFILES_DIR / f"{profile_id}.json"
    if candidate_file.exists():
        with open(candidate_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["_file"] = str(candidate_file)
            return data

    for p in list_available_profiles():
        if p.get("device_id", "").lower() == profile_id.lower():
            return p
    return None


def detect_storage_targets(adb_path: str, serial: Optional[str] = None, dry_run: bool = False) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Dynamically inspects /storage on the device to locate an external MicroSD volume.
    Matches volume names against the canonical FAT32/exFAT UUID format: ^[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}$
    
    Returns:
        (internal_root, external_root, sd_id)
        e.g. ("/sdcard", "/storage/1234-5678", "1234-5678")
        or ("/sdcard", None, None) if no external MicroSD is mounted.
    """
    internal_root = "/sdcard"
    if dry_run:
        return internal_root, "/storage/0000-0000", "0000-0000"

    cmd = [adb_path]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["shell", "ls", "/storage"])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        for entry in lines:
            if SD_UUID_REGEX.match(entry):
                sd_path = f"/storage/{entry}"
                # Verify that directory is readable
                chk_cmd = [adb_path]
                if serial:
                    chk_cmd.extend(["-s", serial])
                chk_cmd.extend(["shell", f"[ -d '{sd_path}' ] && echo 'exists'"])
                chk_res = subprocess.run(chk_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                if "exists" in chk_res.stdout:
                    return internal_root, sd_path, entry
    except Exception as e:
        print(f"[!] Warning during dynamic MicroSD discovery: {e}")

    return internal_root, None, None


def detect_device_profile(adb_path: str, serial: Optional[str] = None, override_id: Optional[str] = None, dry_run: bool = False) -> Tuple[Dict, str]:
    """
    Detects device hardware properties via ADB getprop and resolves the best matching profile.
    If override_id is supplied, forces that profile.
    Falls back cleanly to 'generic.json'.
    
    Returns:
        (profile_dict, detected_model_string)
    """
    if override_id:
        prof = load_profile_by_id(override_id)
        if prof:
            return prof, f"Manual Override ({override_id})"

    if dry_run:
        prof = load_profile_by_id("rp5") or {}
        return prof, "Dry-Run RP5 (Simulated)"

    cmd = [adb_path]
    if serial:
        cmd.extend(["-s", serial])

    def get_prop(prop_name: str) -> str:
        try:
            r = subprocess.run(cmd + ["shell", f"getprop {prop_name}"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
            return r.stdout.strip()
        except Exception:
            return ""

    model = get_prop("ro.product.model")
    device = get_prop("ro.product.device")
    name = get_prop("ro.product.name")
    soc = get_prop("ro.soc.model") or get_prop("ro.board.platform")

    ident_strings = [s.lower() for s in [model, device, name, soc] if s]
    combined_ident = " ".join(ident_strings)

    all_profiles = list_available_profiles()
    for profile in all_profiles:
        patterns = [p.lower() for p in profile.get("model_match", [])]
        for pattern in patterns:
            if pattern in combined_ident or any(pattern in s for s in ident_strings):
                return profile, model or profile.get("name", "Matched Device")

    # Fallback to generic
    generic = load_profile_by_id("generic")
    if generic:
        return generic, model or "Generic Device (Unrecognized)"

    # Fallback minimal dict if generic.json is missing
    return {
        "device_id": "generic",
        "name": "Generic Fallback",
        "emulation": {"force_widescreen": False},
        "soc": {"gpu_family": "generic", "supports_turnip": False},
        "controls": {"trigger_mode": 0, "gamepad_type": 0}
    }, model or "Unknown Device"


def resolve_canonical_path(canonical_subpath: str, sd_id: Optional[str] = None) -> str:
    """
    Resolves canonical path (e.g. 'bios', 'ROMs', 'ES-DE').
    Uses /storage/<SD_ID>/ if available, otherwise falls back to /sdcard/.
    """
    if sd_id:
        return f"/storage/{sd_id}/{canonical_subpath.lstrip('/')}"
    return f"/sdcard/{canonical_subpath.lstrip('/')}"
