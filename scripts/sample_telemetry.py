#!/usr/bin/env python3
"""
scripts/sample_telemetry.py — Hardware Telemetry & GoldenEye Profiler
====================================================================
Samples CPU, GPU, Thermal status, and Battery temperature at 1Hz into CSV,
and simultaneously records logcat for com.sunjaycy.goldeneye.
"""

import argparse
import csv
import datetime
import os
import re
import subprocess
import sys
import time
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ADB = WORKSPACE_ROOT / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
PERF_DIR = WORKSPACE_ROOT / "scratch" / "perf"

def get_serial(adb: Path) -> str:
    try:
        out = subprocess.check_output([str(adb), "devices"], text=True)
        for line in out.splitlines():
            line = line.strip()
            if line and not line.startswith("List of devices") and "\tdevice" in line:
                return line.split("\t")[0]
    except Exception:
        pass
    return ""

def main():
    parser = argparse.ArgumentParser(description="Sample hardware telemetry and app logcat.")
    parser.add_argument("--run-name", required=True, help="Run identifier (e.g. perf_run1, high_perf_run2)")
    parser.add_argument("--duration", type=int, default=150, help="Run duration in seconds (default: 150s)")
    parser.add_argument("--serial", default="", help="ADB device serial")
    parser.add_argument("--adb", default=str(DEFAULT_ADB), help="Path to adb")
    args = parser.parse_args()

    adb = args.adb
    serial = args.serial or get_serial(Path(adb))
    if not serial:
        print("[ERROR] No ADB device detected.")
        sys.exit(1)

    PERF_DIR.mkdir(parents=True, exist_ok=True)
    csv_file = PERF_DIR / f"{args.run_name}.csv"
    logcat_file = PERF_DIR / f"{args.run_name}_logcat.txt"

    print(f"[*] Starting Telemetry Profiler: {args.run_name}")
    print(f"[*] Target Device: {serial}")
    print(f"[*] Duration: {args.duration}s")
    print(f"[*] Telemetry CSV: {csv_file}")
    print(f"[*] Logcat Dump: {logcat_file}")

    # Clear logcat buffer before run
    subprocess.run([adb, "-s", serial, "logcat", "-c"], check=False)

    # Start background logcat capture filtered to GoldenEye / graphics / shader
    logcat_proc = subprocess.Popen(
        [adb, "-s", serial, "logcat", "-v", "time"],
        stdout=open(logcat_file, "w", encoding="utf-8", errors="replace"),
        stderr=subprocess.DEVNULL
    )

    cmd_shell = (
        "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null; "
        "cat /sys/devices/system/cpu/cpufreq/policy4/scaling_cur_freq 2>/dev/null; "
        "cat /sys/devices/system/cpu/cpufreq/policy7/scaling_cur_freq 2>/dev/null; "
        "cat /sys/class/kgsl/kgsl-3d0/gpuclk 2>/dev/null; "
        "dumpsys battery | grep -i temperature; "
        "dumpsys thermalservice | grep -i 'Thermal Status:'"
    )

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "elapsed_sec",
            "cpu_silver_khz",
            "cpu_gold_khz",
            "cpu_prime_khz",
            "gpu_mhz",
            "thermal_status",
            "battery_temp_c"
        ])

        start_time = time.time()
        sample_idx = 0

        try:
            while sample_idx < args.duration:
                t_loop_start = time.time()
                elapsed = int(t_loop_start - start_time)

                res = subprocess.run([adb, "-s", serial, "shell", cmd_shell], capture_output=True, text=True, check=False)
                lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]

                cpu_silver = int(lines[0]) if len(lines) > 0 and lines[0].isdigit() else 0
                cpu_gold = int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else 0
                cpu_prime = int(lines[2]) if len(lines) > 2 and lines[2].isdigit() else 0

                gpu_hz = int(lines[3]) if len(lines) > 3 and lines[3].isdigit() else 0
                gpu_mhz = gpu_hz // 1000000

                batt_temp = 0.0
                thermal_status = 0

                for line in lines[4:]:
                    if "temperature:" in line.lower():
                        m = re.search(r'temperature:\s*(\d+)', line, re.I)
                        if m:
                            batt_temp = int(m.group(1)) / 10.0
                    elif "thermal status:" in line.lower():
                        m = re.search(r'thermal status:\s*(\d+)', line, re.I)
                        if m:
                            thermal_status = int(m.group(1))

                now_iso = datetime.datetime.now().strftime("%H:%M:%S")
                writer.writerow([
                    now_iso,
                    elapsed,
                    cpu_silver,
                    cpu_gold,
                    cpu_prime,
                    gpu_mhz,
                    thermal_status,
                    batt_temp
                ])
                f.flush()

                if sample_idx % 15 == 0:
                    print(f"[{now_iso}] t={elapsed:3d}s | CPU: {cpu_silver//1000} / {cpu_gold//1000} / {cpu_prime//1000} MHz | GPU: {gpu_mhz} MHz | Batt: {batt_temp:.1f}C | Thermal: {thermal_status}")

                sample_idx += 1
                sleep_time = max(0.0, 1.0 - (time.time() - t_loop_start))
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n[*] Sampling interrupted by user.")
        finally:
            logcat_proc.terminate()
            try:
                logcat_proc.wait(timeout=2)
            except Exception:
                logcat_proc.kill()

    print(f"\n[DONE] Captured {sample_idx} samples to {csv_file}")
    print(f"[*] Logcat written to {logcat_file}")

if __name__ == "__main__":
    main()
