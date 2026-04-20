#!/bin/bash
set -euo pipefail

# ------------------------------------------------------------
# LexiMind Setup Script (macOS / Linux)
# ------------------------------------------------------------

SERVER_URL="http://127.0.0.1:5000"
WAIT_SECONDS=30

echo "========================================"
echo "         LexiMind Setup"
echo "========================================"
echo

# --- Detect Python 3 command ---
PY_CMD=""
if command -v python3 &> /dev/null; then
    PY_CMD="python3"
elif command -v python &> /dev/null; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 is not installed or not in PATH."
    echo "Please install Python 3.10+ from https://python.org"
    exit 1
fi

# --- Version check ---
pyver=$($PY_CMD --version 2>&1 | awk '{print $2}')
major=$(echo "$pyver" | cut -d. -f1)
minor=$(echo "$pyver" | cut -d. -f2)

if [[ -z "$major" || -z "$minor" ]]; then
    echo "[ERROR] Could not determine Python version."
    exit 1
fi

if [[ $major -lt 3 ]] || ( [[ $major -eq 3 && $minor -lt 10 ]] ); then
    echo "[ERROR] Python $pyver found, but version 3.10+ is required."
    echo "Please upgrade Python from https://python.org"
    exit 1
fi

echo "[OK] Using Python command: $PY_CMD (version $pyver)"

# --- Virtual environment ---
if [[ ! -d "venv" ]]; then
    echo
    echo "[INFO] Creating Python virtual environment..."
    $PY_CMD -m venv venv
    if [[ $? -ne 0 ]]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
    echo "[OK] Virtual environment created."
fi

echo "[INFO] Activating virtual environment..."
# shellcheck source=/dev/null
source venv/bin/activate

echo "[INFO] Upgrading pip and installing required packages..."
pip install --upgrade pip --disable-pip-version-check -q
pip install -r backend/requirements.txt -q
if [[ $? -ne 0 ]]; then
    echo "[ERROR] Package installation failed. Check the output above."
    exit 1
fi
echo "[OK] Dependencies installed."

# --- API Key configuration ---
mkdir -p backend
if [[ ! -f "backend/.env" ]]; then
    echo
    echo "========================================"
    echo "        API Key Configuration"
    echo "========================================"
    echo
    echo "LexiMind uses DeepSeek-V3 via SiliconCloud."
    echo "The API key will be stored in backend/.env (plaintext)."
    echo
    read -p "Please enter your DeepSeek API key (get one at https://siliconcloud.cn): " apikey
    if [[ -z "$apikey" ]]; then
        echo "[WARNING] No API key entered. You can add it later to backend/.env as DEEPSEEK_API_KEY=your_key"
    else
        echo "DEEPSEEK_API_KEY=$apikey" > backend/.env
        echo "[OK] API key saved to backend/.env"
    fi
fi

# --- Start server ---
echo
echo "[INFO] Starting LexiMind backend server..."
# Launch server in background, keeping venv active
(
    source venv/bin/activate
    python backend/app.py
) &
SERVER_PID=$!

# Wait for server to respond
echo "[INFO] Waiting for server at $SERVER_URL (timeout ${WAIT_SECONDS}s)..."
count=0
while [[ $count -lt $WAIT_SECONDS ]]; do
    if curl --output /dev/null --silent --head --fail "$SERVER_URL"; then
        echo "[OK] Server is up."
        break
    fi
    sleep 1
    ((count++))
done

if [[ $count -ge $WAIT_SECONDS ]]; then
    echo "[WARNING] Server did not respond within $WAIT_SECONDS seconds. You may open the browser manually at $SERVER_URL"
fi

# --- Open browser ---
echo "[INFO] Opening browser at $SERVER_URL"
if command -v open &> /dev/null; then
    open "$SERVER_URL"          # macOS
elif command -v xdg-open &> /dev/null; then
    xdg-open "$SERVER_URL"      # Linux
else
    echo "[WARNING] Could not detect browser opener. Please visit $SERVER_URL manually."
fi

echo
echo "========================================"
echo "         LexiMind is running!"
echo "========================================"
echo
echo "To stop the server, press Ctrl+C or close the terminal."
echo "To restart LexiMind, run this script again."
echo

# Wait for server process (so script doesn't exit immediately)
wait $SERVER_PID