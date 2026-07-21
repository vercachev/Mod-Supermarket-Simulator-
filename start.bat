@echo off
REM Bitburner Save Editor launcher (ASCII-only for Windows cmd)
title Bitburner Save Editor
cd /d "%~dp0"

echo ============================================
echo   BITBURNER - SAVE EDITOR
echo ============================================
echo.
echo 1) In Bitburner: Options - Export save
echo 2) Open that file here, edit, Save
echo 3) In Bitburner: Options - Import save
echo.
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Download Python 3.11+ from https://www.python.org/downloads/
    echo Check: Add python.exe to PATH
    pause
    exit /b 1
)

echo [1/3] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo       Creating .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv
        pause
        exit /b 1
    )
)

echo [2/3] Installing libraries...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.txt
    pause
    exit /b 1
)

echo [3/3] Starting editor...
echo.
".venv\Scripts\python.exe" main.py
set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" (
    echo.
    echo [ERROR] Editor exited with code %EXITCODE%
    echo See editor.log
    pause
    exit /b %EXITCODE%
)

exit /b 0
