@echo off
chcp 65001 >nul
title Supermarket Simulator — Save Editor
cd /d "%~dp0"

echo ============================================
echo   SUPERMARKET SIMULATOR — SAVE EDITOR
echo ============================================
echo.
echo ВАЖНО: перед сохранением изменений
echo закройте игру Supermarket Simulator!
echo.
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден.
    echo.
    echo 1. Скачайте Python 3.11+ с https://www.python.org/downloads/
    echo 2. При установке поставьте галочку "Add python.exe to PATH"
    echo 3. Запустите этот файл снова.
    echo.
    pause
    exit /b 1
)

echo [1/3] Проверка виртуального окружения...
if not exist ".venv\Scripts\python.exe" (
    echo       Создаю .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение.
        pause
        exit /b 1
    )
)

echo [2/3] Установка / обновление библиотек...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости.
    echo Проверьте интернет и повторите.
    pause
    exit /b 1
)

echo [3/3] Запуск редактора...
echo.
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Редактор завершился с ошибкой.
    echo Смотрите файл editor.log рядом с этим bat-ником.
    pause
    exit /b 1
)

exit /b 0
