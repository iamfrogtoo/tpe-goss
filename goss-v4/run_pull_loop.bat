@echo off
chcp 65001 >nul
echo ============================================================
echo TPE GOSS 數據同步腳本
echo ============================================================
echo.

cd /d "%~dp0"

:loop
echo [%time%] 開始執行...
python pull_from_server.py
echo [%time%] 執行完成，等待 30 秒...
timeout /t 30 /nobreak >nul
goto loop
