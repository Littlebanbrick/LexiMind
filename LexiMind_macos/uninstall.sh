#!/bin/bash
set -euo pipefail

# ------------------------------------------------------------
# LexiMind Uninstaller (macOS / Linux)
# ------------------------------------------------------------

echo "========================================"
echo "       LexiMind Uninstaller"
echo "========================================"
echo

# Ensure script is run from LexiMind folder
if [[ ! -f "backend/app.py" ]]; then
    echo "[ERROR] backend/app.py not found in current folder."
    echo "Please place this script in the LexiMind root folder (next to backend/) and run again."
    exit 1
fi

# --- Menu ---
echo "Select uninstall type:"
echo
echo "[1] Clean user data only (venv/, database files, backend/.env)"
echo "[2] Cancel"
echo
read -p "Enter your choice [1/2]: " choice

if [[ "$choice" == "2" ]]; then
    echo
    echo "Uninstall cancelled."
    exit 0
elif [[ "$choice" != "1" ]]; then
    echo "[ERROR] Invalid choice. Exiting."
    exit 1
fi

echo
echo "[INFO] This will remove the following items if present:"
echo "   - venv/           (Python virtual environment)"
echo "   - backend/*.db    (SQLite database files)"
echo "   - backend/.env    (saved API key/config)"
echo

read -p "Type YES and press Enter to proceed with cleaning user data: " confirm
if [[ "$confirm" != "YES" ]]; then
    echo "Operation cancelled by user."
    exit 0
fi

# --- Ensure server not running to avoid file locks ---
if pgrep -f "python backend/app.py" > /dev/null; then
    echo "[WARNING] LexiMind server appears to be running (files may be locked)."
    read -p "Attempt to stop the server now? (y/N): " stop_choice
    if [[ "$stop_choice" =~ ^[Yy]$ ]]; then
        pkill -f "python backend/app.py" 2>/dev/null || true
        sleep 1
        echo "[INFO] Server stopped."
    else
        echo "Please stop the server manually and re-run this script."
        exit 1
    fi
fi

# --- Helper: remove with trash (if available) else rm ---
remove_item() {
    local path="$1"
    if [[ ! -e "$path" ]]; then
        echo "[INFO] $path not found, skipping."
        return
    fi

    echo "[INFO] Removing $path ..."
    if command -v trash &> /dev/null; then
        # Use trash-cli if installed (macOS: brew install trash; Linux: apt install trash-cli)
        trash "$path"
    elif [[ "$(uname)" == "Darwin" ]] && command -v osascript &> /dev/null; then
        # macOS native trash via AppleScript
        osascript -e "tell application \"Finder\" to delete POSIX file \"$(realpath "$path")\"" 2>/dev/null || rm -rf "$path"
    else
        # Fallback to rm (with confirmation for directories)
        if [[ -d "$path" ]]; then
            rm -rf "$path"
        else
            rm -f "$path"
        fi
    fi

    if [[ -e "$path" ]]; then
        echo "[WARNING] Could not remove $path (permission denied or file in use)."
    else
        echo "[OK] Removed $path"
    fi
}

# --- Remove venv ---
remove_item "venv"

# --- Remove database files ---
db_found=0
for pattern in "backend/data/*.db" "backend/*.db"; do
    for db in $pattern; do
        if [[ -f "$db" ]]; then
            remove_item "$db"
            db_found=1
        fi
    done
done
if [[ $db_found -eq 0 ]]; then
    echo "[INFO] No database files (*.db) found in backend/ or backend/data/."
fi

# --- Remove .env ---
remove_item "backend/.env"

echo
echo "========================================"
echo "         Cleanup completed"
echo "========================================"
echo "This uninstall removed user data only. To remove static files, delete this entire folder manually."
echo