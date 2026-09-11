@echo off
chcp 65001 > nul
title Wave Music - Яндекс Музыка Telegram Mini App
echo ========================================================
echo   Запуск Wave Music (Telegram Mini App)
echo ========================================================
cd /d "%~dp0"
python run_app.py
pause
