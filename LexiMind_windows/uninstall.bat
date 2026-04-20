@echo off
setlocal enabledelayedexpansion

title LexiMind Uninstaller (Safe)

echo ========================================
echo       LexiMind Uninstaller (Safe)
echo ========================================
echo.

:: Ensure script is run from LexiMind folder
if not exist "backend\app.py" (
    echo [ERROR] backend\app.py not found in current folder.
    echo Please place this script in the LexiMind root folder (next to backend\) and run again.
    pause
    exit /b 1
)

:: Menu: only clean user data or cancel
echo Select uninstall type:
echo.
echo [1] Clean user data only (venv, database files, backend\.env)
echo [2] Cancel
echo.
choice /c 12 /m "Enter your choice"
if errorlevel 2 goto :cancel
if errorlevel 1 goto :clean_data

:cancel
echo.
echo Uninstall cancelled.
pause
exit /b 0

:clean_data
echo.
echo [INFO] This will remove the following items if present:
echo    - venv/           (Python virtual environment)
echo    - backend\*.db    (common backend SQLite database files)
echo    - backend\.env    (saved API key/config)
echo.
echo The script will attempt to send items to the Recycle Bin first; if that fails it will try permanent deletion.
echo.

:: Confirm user really wants to proceed
set /p CONFIRM="Type YES and press Enter to proceed with cleaning user data: "
if /i not "%CONFIRM%"=="YES" (
    echo Operation cancelled by user.
    pause
    exit /b 0
)

:: Ensure no running python processes that may lock files
call :ensure_no_running_server

:: Perform removals
call :remove_venv
call :remove_db
call :remove_env

echo.
echo ========================================
echo         Cleanup completed
echo ========================================
echo This uninstall removed user data only. To remove static files please manually delete the entire folder.
echo.
pause
exit /b 0

:: -------------------------------------------------
:: Helper: ensure no running python processes
:: -------------------------------------------------
:ensure_no_running_server
setlocal
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /I "python.exe" >nul
if %ERRORLEVEL%==0 (
    echo [WARNING] Detected running python.exe processes which may lock files.
    choice /c YN /m "Attempt to terminate all python.exe processes now? (Y=terminate, N=cancel and close programs manually)"
    if errorlevel 2 (
        echo Please close any LexiMind/Python processes and re-run this script.
        endlocal
        pause
        exit /b 1
    ) else (
        echo Attempting to terminate python processes...
        taskkill /F /IM python.exe >nul 2>&1
        timeout /t 1 >nul
    )
) else (
    echo [INFO] No python.exe processes detected.
)
endlocal
exit /b

:: -------------------------------------------------
:: Helper: remove virtual environment (try Recycle Bin first)
:: -------------------------------------------------
:remove_venv
if exist "venv\" (
    echo [INFO] Removing venv/ (attempting Recycle Bin)...
    powershell -NoProfile -Command ^
      "try { $p=(Get-Item -LiteralPath 'venv').FullName; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($p, [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs, [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin); exit 0 } catch { exit 1 }"
    if %ERRORLEVEL% NEQ 0 (
        echo [INFO] Recycle Bin removal failed, attempting direct removal...
        rmdir /s /q "venv" >nul 2>&1
    )
    if exist "venv\" (
        echo [WARNING] Could not remove venv\ (files may be in use or permission denied). Close programs and retry or remove manually.
    ) else (
        echo [OK] venv removed.
    )
) else (
    echo [INFO] No venv/ found.
)
exit /b

:: -------------------------------------------------
:: Helper: remove database files (*.db in backend\ and backend\data\)
:: -------------------------------------------------
:remove_db
set "DB_FOUND=0"
for %%P in ("backend\data\*.db" "backend\*.db") do (
    for %%F in (%%~P) do (
        if exist "%%~F" (
            set "DB_FOUND=1"
            echo [INFO] Found database file: %%~F
            echo [INFO] Attempting to move to Recycle Bin...
            powershell -NoProfile -Command ^
              "try{ [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile((Get-Item -LiteralPath '%%~F').FullName, [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs, [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin); exit 0 } catch { exit 1 }"
            if %ERRORLEVEL% NEQ 0 (
                echo [INFO] Recycle Bin removal failed, attempting direct delete...
                del /q "%%~F" >nul 2>&1
            )
            if exist "%%~F" (
                echo [WARNING] Could not delete %%~F (file may be locked or permission denied).
            ) else (
                echo [OK] Deleted %%~F
            )
        )
    )
)
if "%DB_FOUND%"=="0" (
    echo [INFO] No database files (*.db) found in backend\ or backend\data\.
)
exit /b

:: -------------------------------------------------
:: Helper: remove backend\.env
:: -------------------------------------------------
:remove_env
if exist "backend\.env" (
    echo [INFO] Removing backend\.env (attempting Recycle Bin)...
    powershell -NoProfile -Command ^
      "try{ [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile((Get-Item -LiteralPath 'backend\.env').FullName, [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs, [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin); exit 0 } catch { exit 1 }"
    if %ERRORLEVEL% NEQ 0 (
        del /q "backend\.env" >nul 2>&1
    )
    if exist "backend\.env" (
        echo [WARNING] Could not delete backend\.env (locked or permission issue).
    ) else (
        echo [OK] backend\.env removed.
    )
) else (
    echo [INFO] No backend\.env found.
)
exit /b