@echo off
chcp 65001 >nul
title Install Souyi to Edge

cd /d "%~dp0"

echo.
echo ========================================
echo   搜绎 - 一键安装到 Edge
echo ========================================
echo.

REM 找到 Edge 安装路径
set "EDGE_PATH="
for %%P in (
    "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
    "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
    "%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"
) do (
    if exist %%P set "EDGE_PATH=%%P"
)

if "%EDGE_PATH%"=="" (
    echo [ERROR] Microsoft Edge not found
    echo Please install Edge first.
    pause
    exit /b 1
)

echo [INFO] Edge path: %EDGE_PATH%
echo.

set "EXT_PATH=%~dp0extension"

if not exist "%EXT_PATH%\manifest.json" (
    echo [ERROR] Extension not found at: %EXT_PATH%
    pause
    exit /b 1
)

echo [INFO] Extension path: %EXT_PATH%
echo.
echo ========================================
echo   IMPORTANT: A new Edge window will open
echo   All existing Edge windows will be closed first.
echo   Please save your work before continuing.
echo ========================================
echo.
pause

REM 关闭所有 Edge 进程（先确认）
echo [STEP] Closing existing Edge windows...
taskkill /F /IM msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM 用 --load-extension 启动 Edge（会一次性把扩展"加载到本地配置"）
echo [STEP] Launching Edge with --load-extension...
start "" "%EDGE_PATH%" --load-extension="%EXT_PATH%" --enable-extensions --no-first-run --no-default-browser-check

echo.
echo ========================================
echo   Done! Edge should open with Souyi loaded.
echo.
echo   Next steps:
echo   1. Edge should open a new window.
echo   2. Go to edge://extensions/ (copy-paste in address bar)
echo   3. Find "搜绎" and enable it (toggle ON).
echo   4. Click the puzzle icon in toolbar to pin it.
echo   5. Done! Right-click any text on any page to use it.
echo ========================================
echo.
timeout /t 5 /nobreak >nul
