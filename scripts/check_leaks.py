#!/usr/bin/env python3
"""
scripts/check_leaks.py - Pre-commit leak checker for Handheld Antigravity Toolkit.
================================================================================
Scans git staged diffs (or the entire tracked tree with --all) for:
  1. Target device serials (e.g. ff152647)
  2. MicroSD filesystem UUIDs (e.g. EEEF-F762)
  3. Hardcoded Windows user directories (e.g. C:\\Users\\<name>)
  4. User account identifiers ('dmill')

Usage:
  python scripts/check_leaks.py                 # Check staged git changes
  python scripts/check_leaks.py --all           # Scan all tracked files in repo
  python scripts/check_leaks.py --install-hook  # Install as .git/hooks/pre-commit
"""

import os
import re
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

LEAK_RULES = [
    ("Leaked hardware serial", re.compile(r"ff152647", re.IGNORECASE)),
    ("Leaked MicroSD UUID", re.compile(r"EEEF-F762", re.IGNORECASE)),
    ("Leaked Windows user path", re.compile(r"[A-Za-z]:[\\/]Users[\\/][a-zA-Z0-9_.-]+", re.IGNORECASE)),
    ("Leaked Windows user identifier", re.compile(r"\bdmill\b", re.IGNORECASE)),
]

# Files exempt from self-reference checks (e.g., this script itself)
EXEMPT_FILES = {
    "scripts/check_leaks.py",
}

def install_hook() -> int:
    hooks_dir = WORKSPACE_ROOT / ".git" / "hooks"
    if not hooks_dir.parent.exists():
        print(f"[!] .git directory not found at {WORKSPACE_ROOT}")
        return 1

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    hook_content = (
        "#!/bin/sh\n"
        "# Handheld Antigravity Toolkit pre-commit leak check hook\n"
        "python scripts/check_leaks.py\n"
        "if [ $? -ne 0 ]; then\n"
        "    echo \"[!] Commit aborted due to detected secret/identifier leaks.\"\n"
        "    exit 1\n"
        "fi\n"
    )

    hook_path.write_text(hook_content, encoding="utf-8")
    try:
        hook_path.chmod(0o755)
    except Exception:
        pass

    print(f"[+] Installed pre-commit hook to {hook_path}")
    return 0


def check_content(filename: str, lines: list[tuple[int, str]]) -> list[str]:
    violations = []
    if filename in EXEMPT_FILES:
        return violations

    for lineno, line in lines:
        for desc, pattern in LEAK_RULES:
            match = pattern.search(line)
            if match:
                matched_str = match.group(0)
                violations.append(
                    f"  {filename}:{lineno}: [{desc}] matched '{matched_str}' in line:\n    {line.strip()}"
                )
    return violations


def check_staged() -> int:
    # Get staged changes with line numbers
    cmd = ["git", "diff", "--cached", "-U0"]
    res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True, errors="replace")
    if res.returncode != 0:
        print(f"[!] git diff --cached failed: {res.stderr}")
        return 1

    diff_output = res.stdout
    if not diff_output.strip():
        return 0

    current_file = ""
    current_lineno = 0
    added_lines: dict[str, list[tuple[int, str]]] = {}

    for line in diff_output.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            if current_file not in added_lines:
                added_lines[current_file] = []
        elif line.startswith("@@ "):
            # Parse @@ -a,b +c,d @@
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                current_lineno = int(m.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            if current_file:
                added_lines[current_file].append((current_lineno, content))
            current_lineno += 1
        elif not line.startswith("-"):
            current_lineno += 1

    all_violations = []
    for fname, lines in added_lines.items():
        all_violations.extend(check_content(fname, lines))

    if all_violations:
        print("[!] ERROR: Sensitive hardware serial, UUID, or user path detected in staged files:")
        for v in all_violations:
            print(v)
        print("\nPlease scrub these values (use <SERIAL>, <SD_ID>, or generic paths) before committing.")
        return 1

    return 0


def check_all() -> int:
    cmd = ["git", "ls-files"]
    res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True, errors="replace")
    if res.returncode != 0:
        print(f"[!] git ls-files failed: {res.stderr}")
        return 1

    files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
    all_violations = []

    for rel_path in files:
        if rel_path in EXEMPT_FILES:
            continue
        full_path = WORKSPACE_ROOT / rel_path
        if not full_path.is_file():
            continue
        # Skip binary files
        try:
            content = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        lines = [(i + 1, l) for i, l in enumerate(content.splitlines())]
        all_violations.extend(check_content(rel_path, lines))

    if all_violations:
        print(f"[!] ERROR: Found {len(all_violations)} leak violation(s) across tracked files:")
        for v in all_violations:
            print(v)
        return 1

    print("[+] All tracked files passed leak check (0 leaks detected).")
    return 0


def main() -> int:
    if "--install-hook" in sys.argv:
        return install_hook()
    elif "--all" in sys.argv:
        return check_all()
    else:
        return check_staged()


if __name__ == "__main__":
    sys.exit(main())
