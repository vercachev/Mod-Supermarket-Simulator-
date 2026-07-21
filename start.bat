@echo off
title Cookie Clicker Save Editor
cd /d "%~dp0"

echo ============================================
echo   COOKIE CLICKER - SAVE EDITOR
echo ============================================
echo.
echo 1) Game: Options - Export save
echo 2) Edit cookies here - Save
echo 3) Game: Options - Import save
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
