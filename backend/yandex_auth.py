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
    for attempt in range(1, 15):
        client = Client()
        logger.info(f"Запрос одноразового кода авторизации Яндекс (попытка {attempt})...")
        code = client.request_device_code()

        code_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "current_code.txt"))
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(f"URL: {code.verification_url}\nCODE: {code.user_code}\nEXPIRES_IN: {code.expires_in}\n")

        print("\n" + "=" * 60, flush=True)
        print("  АВТОРИЗАЦИЯ ЯНДЕКС МУЗЫКИ (Официальный вход)", flush=True)
        print("=" * 60, flush=True)
        print(f"\n1. Откройте в браузере: {code.verification_url}", flush=True)
        print(f"2. Введите этот 8-значный код: >>  {code.user_code}  <<", flush=True)
        print(f"3. Нажмите «Разрешить» или «Войти» в браузере.\n", flush=True)
        print("=" * 60, flush=True)

        if auto_open_browser and attempt == 1:
            try:
                webbrowser.open(code.verification_url)
                print("[Браузер] Страница авторизации открыта в вашем браузере!", flush=True)
            except Exception:
                pass

        print(f"\nОжидание подтверждения (код действует {code.expires_in // 60} минут)...", flush=True)

        try:
            token_obj = client.device_auth(on_code=lambda c: None, timeout=code.expires_in)
            token = token_obj.access_token
            print("\n" + "=" * 60, flush=True)
            print("  [УСПЕХ] Вход выполнен! Токен Яндекс Музыки успешно получен.", flush=True)
            print("=" * 60 + "\n", flush=True)

            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(token.strip())

            if os.path.exists(code_file):
                try:
                    os.remove(code_file)
                except Exception:
                    pass

            return token
        except DeviceAuthError as e:
            if "invalid_grant" in str(e) or "timeout" in str(e).lower() or "expired" in str(e).lower():
                print("\n[Внимание] Время действия предыдущего кода истекло. Запрашиваю свежий код...\n", flush=True)
                continue
            else:
                logger.error(f"Ошибка авторизации: {e}")
                time.sleep(3)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {e}")
            time.sleep(3)

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
