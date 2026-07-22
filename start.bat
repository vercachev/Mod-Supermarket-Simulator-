@echo off
title Supermarket Together Save Editor
cd /d "%~dp0"

echo ============================================
echo   SUPERMARKET TOGETHER - SAVE EDITOR v1.1
echo ============================================
echo.
echo 1) Close the game + disable Steam Cloud
echo 2) Open StoreFile0/1.es3  (NOT backups folder)
echo 3) Set Funds - click APPLY TO GAME
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
