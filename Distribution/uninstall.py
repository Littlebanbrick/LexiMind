#!/usr/bin/env python3
"""
LexiMind Uninstaller - Cross-platform user data cleanup (improved).
Removes only user data: venv/, backend/*.db, backend/.env.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

REPO_ROOT = Path.cwd()


def within_repo(p: Path) -> bool:
    try:
        p.resolve().relative_to(REPO_ROOT.resolve())
        return True
    except Exception:
        return False


def on_rm_error(func, path, exc_info):
    # Try to clear read-only and retry
    try:
        os.chmod(path, 0o666)
    except Exception:
        pass
    try:
        if Path(path).is_dir():
            shutil.rmtree(path, onerror=lambda f, pa, ei: None)
        else:
            Path(path).unlink(missing_ok=True)
    except Exception:
        pass


def try_send_to_trash(path: Path) -> bool:
    """Try to send a path to the OS trash. Return True on success."""
    # Preferred cross-platform approach
    try:
        import send2trash  # type: ignore
        send2trash.send2trash(str(path))
        return True
    except Exception:
        pass

    # Minimal macOS attempt (less reliable)
    if sys.platform == "darwin":
        try:
            subprocess.run(
                ["osascript", "-e", f'tell application "Finder" to move (POSIX file "{str(path)}") to the trash'],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass

    # For other platforms, we decline to implement fragile custom trash logic:
    return False


def permanent_delete(path: Path) -> bool:
    """Permanently delete path; return True if successfully removed."""
    if not path.exists():
        return True
    try:
        if path.is_dir():
            shutil.rmtree(path, onerror=on_rm_error)
        else:
            path.unlink(missing_ok=True)
    except Exception:
        pass
    return not path.exists()


def remove_path(path: Path):
    """Delete path safely: try trash, otherwise ask user to confirm permanent deletion."""
    if not path.exists():
        print(f"[INFO] {path} not found, skipping.")
        return

    if not within_repo(path):
        print(f"[ERROR] Refuse to remove {path}: not inside repository root ({REPO_ROOT}).")
        return

    print(f"[INFO] Removing {path} ...")
    try_trash = try_send_to_trash(path)
    if try_trash:
        print(f"[OK] Moved {path} to trash.")
        return

    # Trash not available / failed; ask for confirmation to permanently delete
    while True:
        resp = input(f"Trash not available for {path}. Permanently delete? (y/N): ").strip().lower()
        if resp in ("y", "yes"):
            ok = permanent_delete(path)
            if ok:
                print(f"[OK] Permanently deleted {path}")
            else:
                print(f"[WARNING] Could not permanently delete {path} (locked or permission issue).")
            return
        elif resp in ("n", "no", ""):
            print(f"[INFO] Skipped deleting {path}.")
            return
        else:
            print("Please answer 'y' or 'n'.")


def find_and_stop_server_processes() -> Optional[bool]:
    """
    Try to detect leximind server processes (best-effort).
    If psutil is available, only target processes whose cmdline references backend/app.py.
    Returns True if processes were found and (attempted) stopped, False if none found,
    or None if detection not performed and user should stop manually.
    """
    # Prefer psutil for safe detection
    try:
        import psutil  # type: ignore
    except Exception:
        # No psutil: do conservative detection fallback -> ask user to stop manually
        print("[INFO] psutil not available; cannot reliably detect LexiMind processes.")
        return None

    found = []
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or [])
            # look for backend/app.py in the process cmdline
            if "backend" in cmdline and "app.py" in cmdline:
                found.append(proc)
        except Exception:
            continue

    if not found:
        return False

    print(f"[WARNING] Found {len(found)} LexiMind-related process(es):")
    for p in found:
        print(f"  PID {p.pid}  cmd: {' '.join(p.info.get('cmdline') or [])}")

    ans = input("Attempt to terminate these processes now? (y/N): ").strip().lower()
    if ans not in ("y", "yes"):
        print("Please stop the server processes manually and re-run this script.")
        return None

    for p in found:
        try:
            p.terminate()
        except Exception:
            try:
                p.kill()
            except Exception:
                print(f"[WARNING] Failed to terminate PID {p.pid}")

    # Wait briefly for termination
    import time
    time.sleep(1)
    still_running = [p for p in found if p.is_running()]
    if still_running:
        print("[WARNING] Some processes are still running after termination attempt.")
    else:
        print("[INFO] Processes terminated.")
    return True


def main():
    print("========================================")
    print("       LexiMind Uninstaller")
    print("========================================")
    print()

    # Basic check
    if not Path("backend/app.py").exists():
        print("[ERROR] backend/app.py not found in current folder.")
        print("Please place this script in the LexiMind root folder (next to backend/) and run again.")
        sys.exit(1)

    print("Select uninstall type:")
    print()
    print("[1] Clean user data only (venv/, database files, backend/.env)")
    print("[2] Cancel")
    print()
    choice = input("Enter your choice [1/2]: ").strip()
    if choice == "2":
        print("Uninstall cancelled.")
        sys.exit(0)
    if choice != "1":
        print("[ERROR] Invalid choice.")
        sys.exit(1)

    print()
    print("[INFO] This will remove the following items if present:")
    print("   - venv/           (Python virtual environment)")
    print("   - backend/*.db    (SQLite database files)")
    print("   - backend/.env    (saved API key/config)")
    print()
    confirm = input("Type YES and press Enter to proceed with cleaning user data: ").strip()
    if confirm != "YES":
        print("Operation cancelled by user.")
        sys.exit(0)

    # Try to detect and stop server processes (best-effort)
    prog = find_and_stop_server_processes()
    if prog is None:
        # Could not safely detect processes; ask user to ensure server is stopped
        ans = input("Could not auto-detect safe server processes. Ensure server is stopped and press Enter to continue, or type CANCEL: ").strip()
        if ans.upper() == "CANCEL":
            print("Please stop the server and re-run this script.")
            sys.exit(1)

    # Remove venv
    remove_path(REPO_ROOT / "venv")

    # Remove .db files in backend/ and backend/data/
    for pattern in ("backend/*.db", "backend/data/*.db"):
        for db_file in REPO_ROOT.glob(pattern):
            remove_path(db_file)

    # Remove .env
    remove_path(REPO_ROOT / "backend/.env")

    print()
    print("========================================")
    print("         Cleanup completed")
    print("========================================")
    print("This uninstall removed user data only. To remove static files, delete this entire folder manually.")
    print()


if __name__ == "__main__":
    main()

