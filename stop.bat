@echo off
chcp 65001 >nul
title Souyi - Stop Service

echo.
echo [STOP] Stopping Souyi...

REM 通过端口找到 PID 并结束
set FOUND=0
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8321" ^| findstr "LISTENING"') do (
    echo [STOP] Killing PID %%P
    taskkill /F /PID %%P >nul 2>&1
    set FOUND=1
)

if "%FOUND%"=="0" (
    echo [INFO] Port 8321 not in use, Souyi not running.
) else (
    echo [OK] Souyi stopped.
)

REM 兜底：杀掉所有 python.exe 残留（搜绎相关）
taskkill /F /IM python.exe /FI "MEMUSAGE gt 50000" >nul 2>&1

echo.
timeout /t 2 /nobreak >nul
