@echo off
REM ASCII-only messages: UTF-8 Russian breaks in Windows cmd.exe
title Supermarket Simulator Save Editor
cd /d "%~dp0"

echo ============================================
echo   SUPERMARKET SIMULATOR - SAVE EDITOR
echo ============================================
echo.
echo IMPORTANT: close the game BEFORE saving!
echo (Zakroyte igru pered sohraneniem)
echo.
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo.
    echo 1. Download Python 3.11+ from https://www.python.org/downloads/
    echo 2. Check the box: Add python.exe to PATH
    echo 3. Run this file again.
    echo.
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

echo [2/3] Installing libraries (first run may take a minute)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.txt
    echo Check your internet connection and try again.
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
    echo See editor.log in this folder.
    pause
    exit /b %EXITCODE%
)

exit /b 0
