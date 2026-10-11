@echo off
chcp 65001 >nul
title Souyi - Install Dependencies

cd /d "%~dp0"

echo.
echo ========================================
echo   Souyi - First Run: Installing deps
echo ========================================
echo.

set PYTHON="%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

%PYTHON% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not available
    pause
    exit /b 1
)

echo [1/3] Upgrading pip...
%PYTHON% -m pip install --upgrade pip -q

echo [2/3] Installing requirements (1-2 minutes)...
%PYTHON% -m pip install -r requirements.txt -q

if errorlevel 1 (
    echo [ERROR] Install failed. Try manually:
    echo    %PYTHON% -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo [3/3] Verifying...
%PYTHON% -c "import fastapi, uvicorn, httpx, bs4, lxml, pydantic; print('All deps OK')"

echo.
echo ========================================
echo   Done! Double-click 搜绎.bat to start
echo ========================================
echo.
timeout /t 3 /nobreak >nul
