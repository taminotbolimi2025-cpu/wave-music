import os
import sys
import time
import threading
import logging
from aiohttp import web

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import config
from server import create_app
from bot import bot
import setup_tunnel

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("AppMaster")

_tunnel_proc = None


def start_server():
    app = create_app()
    runner = web.AppRunner(app)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, config.HOST, config.PORT)
    loop.run_until_complete(site.start())
    logger.info(f"Web Server successfully running at http://localhost:{config.PORT}")
    loop.run_forever()


def tunnel_watchdog():
    """Keeps the tunnel alive permanently. If it ever closes, restarts automatically."""
    global _tunnel_proc
    while True:
        try:
            print("[Watchdog] Инициализация HTTPS-туннеля...", flush=True)
            tunnel_url, proc = setup_tunnel.start_single_tunnel(config.PORT)
            if proc and tunnel_url:
                _tunnel_proc = proc
                config.WEBAPP_URL = tunnel_url
                print(f"[Watchdog] Активный URL туннеля: {tunnel_url}", flush=True)
                # Wait for tunnel process to finish (if it dies)
                proc.wait()
                print("[Watchdog] Туннель был разорван. Перезапуск через 3 сек...", flush=True)
            else:
                print("[Watchdog] Не удалось получить URL. Повторная попытка через 5 сек...", flush=True)
        except Exception as e:
            print(f"[Watchdog] Ошибка в туннеле: {e}. Перезапуск через 5 сек...", flush=True)

        time.sleep(3)


def daily_updater_thread():
    """Background job that automatically refreshes charts and new releases every 12 hours."""
    time.sleep(10)  # Let server and tunnel initialize first
    import music_service
    while True:
        try:
            music_service.update_all_daily_playlists()
        except Exception as e:
            logger.warning(f"Error in daily playlist updater: {e}")
        # Refresh every 12 hours
        time.sleep(12 * 3600)


def bot_polling_loop():
    """Keeps bot polling alive forever, auto-recovering from any network drops."""
    while True:
        try:
            logger.info("Bot polling started...")
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.warning(f"Bot polling exception: {e}. Reconnecting in 3s...")
            time.sleep(3)


def main():
    print("=============================================================", flush=True)
    print(">> ЗАПУСК WAVE MUSIC — TELEGRAM MINI APP (Яндекс Музыка Free)", flush=True)
    print("=============================================================", flush=True)

    # 1. Start Web Server
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    # 2. Start Tunnel Watchdog in background thread (only if running locally)
    if not config.RENDER_URL and not os.environ.get("NO_TUNNEL"):
        tunnel_thread = threading.Thread(target=tunnel_watchdog, daemon=True)
        tunnel_thread.start()
        time.sleep(4)
    else:
        print(f"[Cloud] Облачный режим активен! URL: {config.WEBAPP_URL}", flush=True)

    # 3. Start Daily Playlist Auto-Updater thread
    updater_thread = threading.Thread(target=daily_updater_thread, daemon=True)
    updater_thread.start()

    # 4. Start Telegram Bot polling (self-healing loop)
    print(f"\n[Bot] Telegram-бот @{config.BOT_USERNAME} готов к работе!", flush=True)
    print(f"[Bot] Отправьте /start боту в Telegram для открытия плеера.\n", flush=True)

    bot_polling_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОстановка приложения...")
        if _tunnel_proc:
            _tunnel_proc.terminate()
