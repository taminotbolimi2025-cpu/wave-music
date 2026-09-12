@echo off
chcp 65001 > nul
title Выгрузка Яндекс Музыки в Wave Music
echo ========================================================
echo   ЭКСПОРТ ЯНДЕКС МУЗЫКИ В WAVE MUSIC (Яндекс Плюс)
echo ========================================================
echo.
echo Чтобы выгрузить ваши любимые треки и плейлисты прямо сейчас,
echo перейдите по ссылке (если токен еще не получен):
echo https://oauth.yandex.ru/authorize?response_type=token^&client_id=23cabbbdc6cd418abb4b9c13230e92b8
echo.
set /p YM_TOKEN="Вставьте ваш токен Яндекс Музыки: "
if "%YM_TOKEN%"=="" (
    echo [ОШИБКА] Токен не введен.
    pause
    exit /b
)
echo.
echo [Запуск] Извлечение треков, плейлистов и MP3-файлов...
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe backend\yandex_extractor.py %YM_TOKEN%
) else (
    python backend\yandex_extractor.py %YM_TOKEN%
)
echo.
echo ========================================================
echo   Готово! Ваша библиотека Яндекс Музыки сохранена.
echo ========================================================
pause
