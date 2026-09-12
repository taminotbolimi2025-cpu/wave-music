@echo off
chcp 65001 > nul
title Wave Music - Яндекс Музыка Telegram Mini App
echo ========================================================
echo   Запуск Wave Music (Telegram Mini App)
echo ========================================================
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe run_app.py
) else (
    python run_app.py
)
pause
