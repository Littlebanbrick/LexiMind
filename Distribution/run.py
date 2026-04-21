#!/usr/bin/env python3
"""
LexiMind Launcher
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
import re

SERVER_URL = "http://127.0.0.1:5000"
WAIT_SECONDS = 30
LOG_FILE = Path("backend") / "server.log"


def parse_version(version_str):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", version_str)
    if not m:
        return None
    major, minor, patch = map(int, m.groups())
    return major, minor, patch


def try_version_for_cmd(cmd):
    try:
        p = subprocess.run([cmd, "--version"], capture_output=True, text=True, check=True)
        version_out = (p.stdout or p.stderr).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    v = parse_version(version_out)
    return v


def find_python_command():
    """Return a python command that meets version requirement or None."""
    candidates = []
    # On Windows, prefer the py launcher
    candidates.append("py -3")
    # Platform-typical names
    candidates.extend(["python3", "python"])
    for candidate in candidates:
        parts = candidate.split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        try:
            p = subprocess.run([cmd, *args, "--version"], capture_output=True, text=True, check=True)
            version_out = (p.stdout or p.stderr).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        v = parse_version(version_out)
        if not v:
            continue
        major, minor, _ = v
        # accept Python 3.10+ or any future major > 3
        if (major == 3 and minor >= 10) or (major > 3):
            # Rebuild the original candidate string as a list for invocation
            return candidate.split()
    return None


def run_checked(cmd_list, **kwargs):
    try:
        subprocess.run(cmd_list, check=True, **kwargs)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {' '.join(cmd_list)}")
        print(f"        exit code: {e.returncode}")
        raise


def main():
    print("========================================")
    print("         LexiMind Setup")
    print("========================================")
    print()

    python_cmd = find_python_command()
    if python_cmd is None:
        print("[ERROR] Python 3.10+ not found.")
        print("Please install Python 3.10+ from https://python.org")
        sys.exit(1)
    print(f"[OK] Found Python command: {' '.join(python_cmd)}")

    # 2. Virtual environment
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

    # 3. Install dependencies
    print("[INFO] Installing required packages...")
    try:
        run_checked([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "--disable-pip-version-check"])
        run_checked([str(venv_python), "-m", "pip", "install", "-r", "backend/requirements.txt"])
    except Exception:
        print("[ERROR] Failed to install dependencies. Inspect pip output and retry.")
        sys.exit(1)
    print("[OK] Dependencies installed.")

    # 4. API Key configuration
    env_file = Path("backend") / ".env"
    env_file.parent.mkdir(parents=True, exist_ok=True)
    if not env_file.exists():
        print()
        print("========================================")
        print("        API Key Configuration")
        print("========================================")
        print()
        print("LexiMind uses DeepSeek-V3 via SiliconCloud.")
        print("The API key will be stored in backend/.env (plaintext).")
        print()
        key = input("Please enter your DeepSeek API key (get one at https://siliconcloud.cn): ").strip()
        if key:
            env_file.write_text(f"DEEPSEEK_API_KEY={key}\n")
            print("[OK] API key saved to backend/.env")
        else:
            print("[WARNING] No API key entered. You can add it later to backend/.env as DEEPSEEK_API_KEY=your_key")

    # 5. Start server
    print()
    print("[INFO] Starting LexiMind backend server...")
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

    # 6. Wait for server and open browser
    print(f"[INFO] Waiting for server at {SERVER_URL} (timeout {WAIT_SECONDS}s)...")
    import urllib.request
    start_time = time.time()
    server_ready = False
    while time.time() - start_time < WAIT_SECONDS:
        try:
            with urllib.request.urlopen(SERVER_URL, timeout=2) as _:
                server_ready = True
                break
        except Exception:
            time.sleep(1)

    if server_ready:
        print("[OK] Server is up.")
    else:
        print(f"[WARNING] Server did not respond within {WAIT_SECONDS} seconds. Check {LOG_FILE} for details. You may open the browser manually at {SERVER_URL}")

    print("[INFO] Opening browser at", SERVER_URL)
    try:
        webbrowser.open(SERVER_URL)
    except Exception:
        print("[WARNING] Failed to open browser automatically.")

    print()
    print("========================================")
    print("         LexiMind is running!")
    print("========================================")
    print()
    print("To stop the server, close this window or press Ctrl+C.")
    print("To restart LexiMind, run this script again.")
    print()

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
