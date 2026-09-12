@echo off
chcp 65001 > nul
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0setup_old_pc.ps1"
echo.
pause
