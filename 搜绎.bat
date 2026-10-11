@echo off
chcp 65001 >nul
title Souyi Launcher

cd /d "%~dp0"

echo.
echo ========================================
echo   Souyi - Local search assistant
echo ========================================
echo.

set PYTHON="%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found at: %PYTHON%
    echo Please edit this file to set correct Python path.
    pause
    exit /b 1
)

%PYTHON% -c "import fastapi, httpx, bs4, lxml" >nul 2>&1
if errorlevel 1 (
    echo [INFO] First run detected. Installing dependencies...
    echo.
    call install.bat
    if errorlevel 1 (
        echo [ERROR] Dependency install failed
        pause
        exit /b 1
    )
)

echo [START] Launching Souyi in background...
start "" wscript.exe "%~dp0start-bg.vbs"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Souyi is running!
echo.
echo   Browser should be open automatically.
echo   Manual URL: http://127.0.0.1:8321/
echo.
echo   To stop: double-click stop.bat
echo ========================================
echo.
pause
