@echo off
chcp 65001 > nul
powershell -ExecutionPolicy Bypass -File "%~dp0status.ps1"
echo.
pause
