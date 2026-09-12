@echo off
chcp 65001 > nul
echo ========================================================
echo   Удаление Wave Music из Автозагрузки Windows
echo ========================================================

powershell -ExecutionPolicy Bypass -Command ^
    "$path = \"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\WaveMusic.lnk\"; " ^
    "if (Test-Path $path) { Remove-Item $path -Force; Write-Host '>> Автозапуск удален!' -ForegroundColor Green } else { Write-Host '>> Автозапуск не был установлен.' -ForegroundColor Yellow }"

echo ========================================================
pause
