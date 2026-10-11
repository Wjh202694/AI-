@echo off
chcp 65001 >nul
cd /d "%~dp0"
call "%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe" main.py
pause
