@echo off
chcp 65001 > nul
title Выгрузка Яндекс Музыки в Wave Music (Яндекс Плюс)
cd /d "%~dp0"
echo ========================================================
echo   ВЫГРУЗКА ВСЕЙ ЯНДЕКС МУЗЫКИ (Официальный вход)
echo ========================================================
echo.
echo Сейчас автоматически откроется браузер для подтверждения входа.
echo Вам нужно будет ввести 8-значный код, который появится ниже.
echo.

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe backend\yandex_auth.py
) else (
    python backend\yandex_auth.py
)

echo.
pause
