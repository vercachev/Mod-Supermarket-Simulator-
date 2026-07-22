@echo off
title awake DLC build
cd /d "%~dp0AwakeDLC"

where dotnet >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Install .NET SDK, then open AwakeDLC.csproj in Visual Studio.
    pause
    exit /b 1
)

dotnet restore
dotnet build -c Release
if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo OK: bin\Release\AwakeDLC.ivsdk.dll
echo Copy it to: GTAIV\IVSDKDotNet\scripts\
echo.
pause
