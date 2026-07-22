@echo off
title Supermarket Together Save Editor
cd /d "%~dp0"

echo ============================================
echo   SUPERMARKET TOGETHER - SAVE EDITOR
echo ============================================
echo.
echo 1) Close the game
echo 2) Open StoreFile0.es3 - set Funds - Save
echo 3) Replace save / use "overwrite" button
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from python.org with PATH.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo [ERROR] See editor.log
    pause
)
