@echo off
chcp 65001 > nul
echo ========================================================
echo   Установка Wave Music в Автозагрузку Windows
echo ========================================================

powershell -ExecutionPolicy Bypass -File "%~dp0install_autostart.ps1"

echo.
echo Теперь при включении или перезагрузке компьютера
echo Wave Music будет автоматически запускаться в фоновом режиме!
echo ========================================================
pause
