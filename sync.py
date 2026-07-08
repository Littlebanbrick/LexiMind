#!/usr/bin/env python3
"""
sync.py - Copy core backend/ and frontend/ from development to distribution folder.
Excludes Docker-related files, cache, app.py, and sensitive data.
Run this script from the project root directory (Windows compatible).
"""

import os
import shutil
import sys
from pathlib import Path

# Configuration
# NOTE: the folder on disk is `LexiMind_development` (capital L and M). The
# previous value was all-lowercase, which happened to work on case-insensitive
# filesystems (Windows / macOS) but failed on Linux. Match the real name.
DEV_DIR = Path("LexiMind_development")
DIST_DIRS = [
    Path("Distribution"),
]

# Subdirectories to copy (relative to DEV_DIR)
DIRS_TO_COPY = ["backend", "frontend"]

# Specific files/folders to exclude (exact names or patterns)
EXCLUDE_NAMES = {
    # Sensitive / generated files
    ".env",
    "*.db",
    "*.sqlite",
    "__pycache__",
    "*.pyc",
    ".DS_Store",
    "data/*.db",
    # Development-only files
    "app.py",
    "Dockerfile",
}

def should_exclude(path: Path) -> bool:
    """Return True if the path or its name matches any exclude rule."""
    name = path.name
    for pattern in EXCLUDE_NAMES:
        if pattern == name:
            return True
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
        if "/" in pattern or "\\" in pattern:
            # For patterns like "data/*.db", check full relative path later
            pass
    return False

def copy_tree_safe(src: Path, dst: Path) -> None:
    """Copy src to dst, overwriting existing, skipping excluded items."""
    if not src.exists():
        print(f"  [WARNING] Source does not exist: {src}")
        return

    if dst.exists():
        print(f"  [INFO] Removing existing: {dst}")
        shutil.rmtree(dst, ignore_errors=True)

    def ignore_func(directory, files):
        ignored = []
        for f in files:
            full_path = Path(directory) / f
            # Check relative path for patterns like "data/*.db"
            try:
                rel_path = full_path.relative_to(src)
            except ValueError:
                rel_path = full_path
            if should_exclude(full_path):
                ignored.append(f)
            elif "data" in rel_path.parts and f.endswith(".db"):
                ignored.append(f)
        return ignored

    shutil.copytree(src, dst, ignore=ignore_func)
    print(f"  [OK] Copied {src} -> {dst}")

def main():
    print("========================================")
    print("    LexiMind Core Sync Script")
    print("========================================")
    print()

    if not DEV_DIR.exists():
        print(f"[ERROR] Development directory '{DEV_DIR}' not found.")
        print("Please run this script from the project root.")
        sys.exit(1)

    print(f"[INFO] Source: {DEV_DIR}")
    print()

    for dist_dir in DIST_DIRS:
        print(f"--- Syncing to {dist_dir} ---")
        if not dist_dir.exists():
            print(f"  [INFO] Creating directory: {dist_dir}")
            dist_dir.mkdir(parents=True, exist_ok=True)

        for sub in DIRS_TO_COPY:
            src_path = DEV_DIR / sub
            dst_path = dist_dir / sub
            copy_tree_safe(src_path, dst_path)

        print(f"[OK] {dist_dir} sync complete.\n")

    print("========================================")
    print("         Sync finished successfully!")
    print("========================================")

if __name__ == "__main__":
    main()