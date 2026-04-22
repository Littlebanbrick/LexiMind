#!/usr/bin/env python3
"""
LexiMind Launcher
"""

import os
import sys
import subprocess
import time
import webbrowser
import urllib.request
import urllib.error
from pathlib import Path
import re

SERVER_URL = "http://127.0.0.1:5000"
WAIT_SECONDS = 30
LOG_FILE = Path("backend") / "server.log"


def parse_version(version_str):
    """Extract major.minor.patch from a version string."""
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", version_str)
    if not m:
        return None
    major, minor, patch = map(int, m.groups())
    return major, minor, patch


def version_satisfies(v_tuple):
    """Check if version meets Python 3.10+ requirement."""
    if not v_tuple:
        return False
    major, minor, _ = v_tuple
    return (major == 3 and minor >= 10) or (major > 3)


def try_cmd_version(cmd_parts):
    """Run a command and return parsed version tuple if version >=3.10."""
    try:
        p = subprocess.run(cmd_parts, capture_output=True, text=True, check=True)
        version_out = (p.stdout or p.stderr).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    v = parse_version(version_out)
    if version_satisfies(v):
        return v
    return None


def find_python_command():
    """
    Locate a Python 3.10+ interpreter.
    On macOS, also check common absolute paths to bypass stale PATH issues.
    Returns a list of command parts (e.g., ['python3'] or ['/usr/local/bin/python3']).
    """
    candidates = []

    # Absolute paths common on macOS (priority when PATH may not be updated yet)
    mac_common_paths = [
        "/usr/local/bin/python3",      # Intel Homebrew / manual install
        "/opt/homebrew/bin/python3",   # Apple Silicon Homebrew
        "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3",
        "/usr/bin/python3",            # macOS built-in (usually older, but check version)
    ]
    # Filter out non-existent paths early
    for abs_path in mac_common_paths:
        if os.path.exists(abs_path):
            candidates.append([abs_path])

    # Then try PATH-based commands (py launcher on Windows, python3, python)
    if os.name == "nt":
        candidates.append(["py", "-3"])
    candidates.append(["python3"])
    candidates.append(["python"])

    # Also try "python3.12", "python3.11", "python3.10" explicitly
    for minor in (12, 11, 10):
        candidates.append([f"python3.{minor}"])

    seen = set()
    for cmd_parts in candidates:
        cmd_key = " ".join(cmd_parts)
        if cmd_key in seen:
            continue
        seen.add(cmd_key)
        v = try_cmd_version(cmd_parts)
        if v:
            return cmd_parts
    return None


def print_python_install_help():
    """Provide detailed instructions for installing Python 3.10+."""
    print("\n[ERROR] Python 3.10 or newer is required but was not found.")
    print("\nInstallation options:")
    print("  1. Official installer: https://www.python.org/downloads/")
    print("  2. Homebrew (macOS):   brew install python@3.12")
    print("\nIMPORTANT: After installing, you MUST:")
    print("  - Close and reopen this terminal window, OR")
    print("  - Run: hash -r   (to refresh command cache)")
    print("Then run this script again.\n")


def run_checked(cmd_list, **kwargs):
    """Run a command, exit on failure."""
    try:
        subprocess.run(cmd_list, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {' '.join(cmd_list)}")
        print(f"        exit code: {e.returncode}")
        raise


def print_firewall_hint():
    """Print macOS firewall hint if we suspect connection issues."""
    if sys.platform == "darwin":
        print("\n[NOTE] If the browser fails to connect despite 'Server is up':")
        print("       macOS may have blocked incoming connections to Python.")
        print("       Go to System Settings > Network > Firewall > Options...")
        print("       Ensure 'python3' is set to 'Allow incoming connections'.")


def check_process_alive(proc):
    """Return True if process is still running, else print log tail."""
    if proc.poll() is not None:
        print("[ERROR] Backend process exited unexpectedly.")
        if LOG_FILE.exists():
            print(f"Last 10 lines of {LOG_FILE}:")
            try:
                with open(LOG_FILE, "r") as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(f"  {line.rstrip()}")
            except Exception:
                pass
        return False
    return True


def main():
    print("========================================")
    print("         LexiMind Setup")
    print("========================================\n")

    python_cmd = find_python_command()
    if python_cmd is None:
        print_python_install_help()
        sys.exit(1)

    print(f"[OK] Found Python command: {' '.join(python_cmd)}")

    # Virtual environment
    venv_dir = Path("venv")
    if os.name == "nt":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    if not venv_dir.exists() or not venv_python.exists():
        print("[INFO] Creating Python virtual environment...")
        try:
            run_checked([*python_cmd, "-m", "venv", str(venv_dir)])
        except Exception:
            print("[ERROR] Failed to create virtual environment.")
            sys.exit(1)
        if not venv_python.exists():
            print("[ERROR] Virtual environment created but python executable not found in venv.")
            sys.exit(1)
        print("[OK] Virtual environment created.")
    else:
        print("[OK] Virtual environment exists.")

    # Install dependencies
    print("[INFO] Installing required packages...")
    try:
        run_checked([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "--disable-pip-version-check"])
        run_checked([str(venv_python), "-m", "pip", "install", "-r", "backend/requirements.txt"])
    except Exception:
        print("[ERROR] Failed to install dependencies. Inspect pip output and retry.")
        sys.exit(1)
    print("[OK] Dependencies installed.")

    # API Key configuration
    env_file = Path("backend") / ".env"
    env_file.parent.mkdir(parents=True, exist_ok=True)
    if not env_file.exists():
        print("\n========================================")
        print("        API Key Configuration")
        print("========================================\n")
        print("LexiMind uses DeepSeek-V3 via SiliconCloud.")
        print("The API key will be stored in backend/.env (plaintext).\n")
        key = input("Please enter your DeepSeek API key (get one at https://siliconcloud.cn): ").strip()
        if key:
            env_file.write_text(f"DEEPSEEK_API_KEY={key}\n")
            print("[OK] API key saved to backend/.env")
        else:
            print("[WARNING] No API key entered. You can add it later to backend/.env as DEEPSEEK_API_KEY=your_key")

    # Start server
    print("\n[INFO] Starting LexiMind backend server...")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        log_f = open(LOG_FILE, "a", encoding="utf-8")
    except Exception as e:
        print(f"[WARNING] Could not open log file {LOG_FILE}: {e}. Server stdout/stderr will be suppressed.")
        log_f = subprocess.DEVNULL

    try:
        server_process = subprocess.Popen(
            [str(venv_python), "backend/app.py"],
            stdout=log_f,
            stderr=log_f,
            cwd=str(Path.cwd()),
        )
    except Exception as e:
        print("[ERROR] Failed to launch server process:", e)
        if log_f is not subprocess.DEVNULL:
            log_f.close()
        sys.exit(1)

    # Quick check if process died immediately (e.g., syntax error)
    time.sleep(1.5)
    if not check_process_alive(server_process):
        if log_f is not subprocess.DEVNULL:
            log_f.close()
        sys.exit(1)

    # Wait for server to respond on port
    print(f"[INFO] Waiting for server at {SERVER_URL} (timeout {WAIT_SECONDS}s)...")
    start_time = time.time()
    server_ready = False
    while time.time() - start_time < WAIT_SECONDS:
        if not check_process_alive(server_process):
            break
        try:
            with urllib.request.urlopen(SERVER_URL, timeout=2) as resp:
                # Accept any 2xx/3xx status
                server_ready = True
                break
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            time.sleep(1)

    if server_ready:
        print("[OK] Server is up.")
        print_firewall_hint()   # always show on macOS as a precaution
    else:
        print(f"[WARNING] Server did not respond within {WAIT_SECONDS} seconds.")
        print(f"          Check {LOG_FILE} for details.")
        print_firewall_hint()
        print(f"          You may open the browser manually at {SERVER_URL}")

    print("[INFO] Opening browser at", SERVER_URL)
    try:
        webbrowser.open(SERVER_URL)
    except Exception:
        print("[WARNING] Failed to open browser automatically.")

    print("\n========================================")
    print("         LexiMind is running!")
    print("========================================\n")
    print("To stop the server, close this window or press Ctrl+C.")
    print("To restart LexiMind, run this script again.\n")

    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping server...")
        try:
            server_process.terminate()
        except Exception:
            pass
        server_process.wait()
    finally:
        if log_f is not subprocess.DEVNULL:
            log_f.close()


if __name__ == "__main__":
    main()