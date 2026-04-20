@echo off
setlocal enabledelayedexpansion

title LexiMind Setup (Improved)

:: --- Configurable ---
set SERVER_URL=http://127.0.0.1:5000
set WAIT_SECONDS=30
:: ----------------------

echo ========================================
echo          LexiMind Setup (Improved)
echo ========================================
echo.

:: -------------------------
:: 1. Find Python command
:: -------------------------
set PY_CMD=
:: Prefer py -3 if available
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "tokens=2 delims= " %%v in ('py -3 --version 2^>^&1') do set pyver=%%v
    if defined pyver set PY_CMD=py -3
)
if not defined PY_CMD (
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
        for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set pyver=%%v
        if defined pyver set PY_CMD=python
    )
)

if not defined PY_CMD (
    echo [WARNING] Python (3.10+) not found on PATH.
    echo.
    where winget >nul 2>&1
    if %ERRORLEVEL%==0 (
        echo [INFO] Attempting to install Python via winget...
        :: try to install latest Python 3 package (may require admin)
        winget install --id Python.Python.3 -e --silent --accept-package-agreements --accept-source-agreements
        if %ERRORLEVEL% NEQ 0 (
            echo [ERROR] winget install failed. Please install Python 3.10+ manually from https://python.org
            start https://python.org
            pause
            exit /b 1
        ) else (
            echo [INFO] Python installation initiated. After install, re-run this script.
            pause
            exit /b 0
        )
    ) else (
        echo [ERROR] winget not available. Please install Python 3.10+ from https://python.org
        start https://python.org
        pause
        exit /b 1
    )
)

echo [OK] Using Python command: %PY_CMD% (reported version: %pyver%)

:: -------------------------
:: 2. Version check (>=3.10)
:: -------------------------
for /f "tokens=1,2 delims=." %%a in ("!pyver!") do (
    set major=%%a
    set minor=%%b
)
if "!major!"=="" (
    echo [ERROR] Could not parse Python version: !pyver!
    goto :python_fail
)
if !major! lss 3 (
    goto :python_fail
) else (
    if !major! equ 3 (
        if !minor! lss 10 (
            goto :python_fail
        )
    )
)
echo [OK] Python !pyver! meets requirement.

:: -------------------------------------------------
:: 3. Virtual Environment & Dependencies
:: -------------------------------------------------
if not exist "venv\" (
    echo.
    echo [INFO] Creating Python virtual environment...
    %PY_CMD% -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    echo [INFO] Falling back to using venv\Scripts\python explicitly for installs.
)

echo [INFO] Upgrading pip and installing required packages...
:: Use venv python to ensure correct pip if activation failed
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -m pip install --upgrade pip --disable-pip-version-check
    venv\Scripts\python.exe -m pip install -r backend\requirements.txt
) else (
    %PY_CMD% -m pip install --upgrade pip --disable-pip-version-check
    %PY_CMD% -m pip install -r backend\requirements.txt
)
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Package installation failed. Check the output above.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

:: -------------------------------------------------
:: 4. API Key Configuration (.env)
:: -------------------------------------------------
if not exist "backend\" (
    mkdir backend
)
if not exist "backend\.env" (
    echo.
    echo ========================================
    echo        API Key Configuration
    echo ========================================
    echo.
    echo LexiMind uses DeepSeek-V3 via SiliconCloud.
    echo For development, we will store the API key in backend\.env (plaintext).
    echo If you prefer to set it as a system environment variable or use credential manager, do so instead.
    echo.
    set /p apikey="Please enter your DeepSeek API key (get one at https://siliconcloud.cn): "
    if "!apikey!"=="" (
        echo [WARNING] No API key entered. You can add it later to backend\.env as DEEPSEEK_API_KEY=your_key
    ) else (
        echo DEEPSEEK_API_KEY=!apikey! > backend\.env
        echo [OK] API key saved to backend\.env
    )
)

:: -------------------------------------------------
:: 5. Start Server & Open Browser (ensure venv used)
:: -------------------------------------------------
echo.
echo [INFO] Starting LexiMind backend server...
:: Start a new cmd that activates venv and runs the app (so the server uses venv python)
start "" /B cmd /c "call venv\Scripts\activate.bat && python backend\app.py"

:: Wait for server to come up (poll)
echo [INFO] Waiting for server %SERVER_URL% to respond (timeout %WAIT_SECONDS%s)...
set /a END_TIME=%WAIT_SECONDS%
set /a COUNT=0
:wait_loop
powershell -Command "try{ $r=Invoke-WebRequest -UseBasicParsing -Uri '%SERVER_URL%' -TimeoutSec 2; exit 0 } catch { exit 1 }"
if %ERRORLEVEL%==0 (
    echo [OK] Server is up.
) else (
    set /a COUNT+=1
    if %COUNT% GEQ %END_TIME% (
        echo [WARNING] Server did not respond within %WAIT_SECONDS% seconds. You can try opening the browser manually at %SERVER_URL%
        goto :open_browser
    )
    timeout /t 1 >nul
    goto :wait_loop
)

:open_browser
echo [INFO] Opening browser at %SERVER_URL%
start %SERVER_URL%

echo.
echo ========================================
echo         LexiMind is running (or starting)!
echo ========================================
echo.
echo To stop the server, close the server window or find the Python process.
echo Press any key to exit this setup window (server will continue in background).
pause >nul
exit /b 0

:python_fail
echo.
echo [ERROR] Python !pyver! found, but version 3.10+ is required.
echo Please install/upgrade Python from https://python.org
start https://python.org
pause
exit /b 1