import os
import sys
import time
import webbrowser
import logging
from yandex_music import Client
from yandex_music.exceptions import DeviceAuthError

logger = logging.getLogger("YandexAuth")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TOKEN_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "yandex_token.txt"))


def perform_device_login(auto_open_browser: bool = True):
    """Performs official Yandex OAuth Device Flow:
    1. Requests device code
    2. Displays verification URL and user code
    3. Opens browser automatically
    4. Waits for confirmation and returns access_token
    """
    client = Client()
    logger.info("Запрос одноразового кода авторизации Яндекс...")
    code = client.request_device_code()

    print("\n" + "=" * 60, flush=True)
    print("  АВТОРИЗАЦИЯ ЯНДЕКС МУЗЫКИ (Официальный безопасный вход)", flush=True)
    print("=" * 60, flush=True)
    print(f"\n1. Откройте страницу: {code.verification_url}", flush=True)
    print(f"2. Введите этот 8-значный код: >>  {code.user_code}  <<", flush=True)
    print(f"3. Нажмите «Разрешить» или «Войти» в браузере.\n", flush=True)
    print("=" * 60, flush=True)

    if auto_open_browser:
        try:
            webbrowser.open(code.verification_url)
            print("[Браузер] Страница авторизации открыта в вашем браузере!", flush=True)
        except Exception:
            pass

    print(f"\nОжидание подтверждения (код действует {code.expires_in // 60} минут)...", flush=True)

    def on_code_cb(c):
        pass

    try:
        token_obj = client.device_auth(on_code=on_code_cb, timeout=code.expires_in)
        token = token_obj.access_token
        print("\n" + "=" * 60, flush=True)
        print("  [УСПЕХ] Вход выполнен! Токен Яндекс Музыки успешно получен.", flush=True)
        print("=" * 60 + "\n", flush=True)

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token.strip())

        return token
    except DeviceAuthError as e:
        logger.error(f"Ошибка авторизации: {e}")
        return None
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        return None


def run_full_export_flow():
    token = perform_device_login(auto_open_browser=True)
    if not token:
        print("[ОШИБКА] Не удалось получить авторизацию. Попробуйте еще раз.")
        return

    print("[Запуск] Начинаем выгрузку треков и MP3-файлов...")
    import yandex_extractor
    yandex_extractor.extract_full_library(token, download_audio=True)
    print("\n" + "=" * 60)
    print("  [ГОТОВО] Вся ваша музыка из Яндекс Музыки спасена и сохранена!")
    print("=" * 60)


if __name__ == "__main__":
    run_full_export_flow()
