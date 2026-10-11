@echo off
chcp 65001 >nul
echo 正在查找搜绎进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8321 :8322 :8323" ^| findstr LISTENING') do (
    echo 停止进程 %%a
    taskkill /PID %%a /F
)
echo 完成。
pause
