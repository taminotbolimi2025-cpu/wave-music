import os
import html
import json
import logging
import asyncio
import aiohttp
from aiohttp import web
import telebot

from config import BOT_TOKEN, HOST, PORT, FRONTEND_DIR
import music_service
import lyrics_service
import access_control
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)


# Middleware for CORS
@web.middleware
async def cors_middleware(request, handler):
    if request.method == 'OPTIONS':
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            response = web.json_response({'error': str(e)}, status=500)

    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


# Static File Handlers
async def index_handler(request):
    index_file = os.path.join(FRONTEND_DIR, 'index.html')
    return web.FileResponse(index_file, headers={
        'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0'
    })


def _get_audio_content_type(file_or_url: str) -> str:
    """Returns pure audio MIME type to guarantee iOS Safari, Android, and PC playback compatibility"""
    path_lower = file_or_url.lower()
    if path_lower.endswith('.mp3'):
        return 'audio/mpeg'
    elif path_lower.endswith('.webm') or 'webm' in path_lower:
        return 'audio/webm'
    elif path_lower.endswith('.ogg') or path_lower.endswith('.opus'):
        return 'audio/ogg'
    elif path_lower.endswith('.aac'):
        return 'audio/aac'
    return 'audio/mp4'


_caching_ids = set()


async def _bg_cache_track(vid_id: str, artist: str = "", title: str = ""):
    """Caches track in background so future seeks and replays are instantaneous"""
    if not vid_id or vid_id in _caching_ids:
        return
    _caching_ids.add(vid_id)
    try:
        if not music_service.get_cached_audio_path(vid_id):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, music_service.download_and_cache_audio, vid_id, artist, title)
    except Exception as e:
        logger.warning(f"Background cache error for {vid_id}: {e}")
    finally:
        _caching_ids.discard(vid_id)


# API Handlers
async def api_search(request):
    q = request.query.get('q', '').strip()
    if not q:
        return web.json_response({'tracks': []})
    
    loop = asyncio.get_event_loop()
    try:
        tracks = await loop.run_in_executor(None, music_service.search_tracks, q, 12)
        return web.json_response({'tracks': tracks})
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return web.json_response({'tracks': []})


async def api_wave(request):
    mood = request.query.get('mood', 'all')
    loop = asyncio.get_event_loop()
    tracks = await loop.run_in_executor(None, music_service.get_wave_tracks, mood)
    return web.json_response({'tracks': tracks, 'mood': mood})


async def api_chart(request):
    loop = asyncio.get_event_loop()
    tracks = await loop.run_in_executor(None, music_service.get_chart_tracks)
    return web.json_response({'tracks': tracks})


async def api_new_releases(request):
    loop = asyncio.get_event_loop()
    tracks = await loop.run_in_executor(None, music_service.get_new_releases)
    return web.json_response({'tracks': tracks})


async def api_playlist(request):
    name = request.query.get('name', '').strip()
    loop = asyncio.get_event_loop()
    tracks = await loop.run_in_executor(None, music_service.get_playlist_tracks, name)
    return web.json_response({'playlist': name, 'tracks': tracks})


async def api_yandex_chart(request):
    import yandex_chart
    loop = asyncio.get_event_loop()
    tracks = await loop.run_in_executor(None, yandex_chart.fetch_live_yandex_chart, 100)
    return web.json_response({'tracks': tracks})


async def api_yandex_liked(request):
    import catalog
    tracks = catalog.get_yandex_liked_tracks()
    return web.json_response({'tracks': tracks})


async def api_yandex_playlists(request):
    import catalog
    playlists = catalog.get_yandex_playlists()
    return web.json_response({'playlists': playlists})


_yandex_sync_status = {"running": False, "total": 0, "current": 0, "message": "Ожидание"}


async def api_yandex_sync(request):
    global _yandex_sync_status
    try:
        data = await request.json()
        token = data.get("token", "").strip()
        if not token:
            return web.json_response({"error": "Токен не предоставлен"}, status=400)

        if _yandex_sync_status["running"]:
            return web.json_response({"status": "already_running", "progress": _yandex_sync_status})

        import threading
        import yandex_extractor

        def run_sync():
            global _yandex_sync_status
            _yandex_sync_status["running"] = True
            _yandex_sync_status["message"] = "Подключение к Яндекс Музыке..."
            def on_progress(curr, total, track, msg):
                _yandex_sync_status["current"] = curr
                _yandex_sync_status["total"] = total
                _yandex_sync_status["message"] = msg
            try:
                yandex_extractor.extract_full_library(token, download_audio=True, progress_cb=on_progress)
                _yandex_sync_status["message"] = "Выгрузка успешно завершена! Все треки сохранены локально."
            except Exception as e:
                _yandex_sync_status["message"] = f"Ошибка: {e}"
            finally:
                _yandex_sync_status["running"] = False

        threading.Thread(target=run_sync, daemon=True).start()
        return web.json_response({"status": "started", "message": "Выгрузка запущена в фоновом режиме"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def api_yandex_status(request):
    return web.json_response(_yandex_sync_status)


async def api_stream(request):
    vid_id = request.query.get('id', '').strip()
    if not vid_id:
        return web.Response(status=400, text='Missing id parameter')

    artist = request.query.get('artist', '').strip()
    title = request.query.get('title', '').strip()
    
    # Check access permission if user_id is passed
    user_id_str = request.query.get('user_id') or request.headers.get('X-User-Id')
    if user_id_str:
        try:
            uid = int(user_id_str)
            if not access_control.is_allowed(uid):
                return web.Response(status=403, text='Access restricted. Approval required.')
        except (ValueError, TypeError):
            return web.Response(status=403, text='Invalid user credentials.')

    # 1. Fast path: check if track is already cached locally on disk
    cached_path = music_service.get_cached_audio_path(vid_id)
    if cached_path and os.path.exists(cached_path) and os.path.getsize(cached_path) > 10000:
        ctype = _get_audio_content_type(cached_path)
        return web.FileResponse(cached_path, headers={
            'Content-Type': ctype,
            'Accept-Ranges': 'bytes',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=86400'
        })

    loop = asyncio.get_event_loop()

    # Trigger non-blocking background caching
    asyncio.create_task(_bg_cache_track(vid_id, artist=artist, title=title))

    # 2. Try fast direct stream URL without blocking event loop
    stream_url = await loop.run_in_executor(None, music_service.get_stream_url, vid_id, artist, title)
    if stream_url and not stream_url.endswith('.m3u8'):
        try:
            headers = {}
            range_header = request.headers.get('Range')
            if range_header:
                headers['Range'] = range_header

            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None, sock_read=60, sock_connect=10))
            upstream = await session.get(stream_url, headers=headers)
            if upstream.status in (200, 206):
                # Always send pure audio MIME type so iOS Safari / WebKit and Android play without error
                content_type = _get_audio_content_type(stream_url)
                res_headers = {
                    'Content-Type': content_type,
                    'Accept-Ranges': 'bytes',
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'public, max-age=3600'
                }
                if 'Content-Range' in upstream.headers:
                    res_headers['Content-Range'] = upstream.headers['Content-Range']
                if 'Content-Length' in upstream.headers:
                    res_headers['Content-Length'] = upstream.headers['Content-Length']

                response = web.StreamResponse(status=upstream.status, headers=res_headers)
                await response.prepare(request)
                try:
                    async for chunk in upstream.content.iter_chunked(64 * 1024):
                        await response.write(chunk)
                except (asyncio.CancelledError, ConnectionResetError):
                    pass
                finally:
                    try:
                        await response.write_eof()
                    except Exception:
                        pass
                    upstream.close()
                    await session.close()
                return response
            else:
                await session.close()
        except Exception as proxy_err:
            logger.warning(f"Direct stream proxy error for {vid_id}: {proxy_err}")

    # 3. Robust Mobile Fallback: Download track in worker thread and stream via FileResponse
    try:
        downloaded = await loop.run_in_executor(None, music_service.download_and_cache_audio, vid_id, artist, title)
        if downloaded and os.path.exists(downloaded) and os.path.getsize(downloaded) > 10000:
            ctype = _get_audio_content_type(downloaded)
            return web.FileResponse(downloaded, headers={
                'Content-Type': ctype,
                'Accept-Ranges': 'bytes',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=86400'
            })
    except Exception as dl_err:
        logger.error(f"Fallback download error for {vid_id}: {dl_err}")

    return web.Response(status=404, text='Track could not be loaded')


async def api_send_to_chat(request):
    """Sends track audio directly to user's Telegram chat for background playback"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        track = data.get('track', {})

        if not user_id:
            return web.json_response({'error': 'Missing user_id'}, status=400)

        try:
            if not access_control.is_allowed(int(user_id)):
                return web.json_response({'error': 'Access denied. Please request access from administrator.'}, status=403)
        except (ValueError, TypeError):
            return web.json_response({'error': 'Invalid user_id'}, status=400)

        title = track.get('title', 'Трек')
        artist = track.get('artist', 'Wave Music')
        track_id = track.get('id', '')

        # Download audio track in worker thread
        loop = asyncio.get_event_loop()
        audio_file = await loop.run_in_executor(
            None,
            music_service.download_track_audio,
            track_id or f"{artist} {title}"
        )

        caption = (
            f"🎵 <b>{html.escape(artist)} — {html.escape(title)}</b>\n\n"
            f"✨ <i>Воспроизводится в фоновом режиме даже с выключенным экраном</i>"
        )

        if audio_file and os.path.exists(audio_file):
            try:
                with open(audio_file, 'rb') as f:
                    bot.send_audio(
                        chat_id=user_id,
                        audio=f,
                        title=title,
                        performer=artist,
                        caption=caption,
                        parse_mode='HTML'
                    )
            finally:
                if audio_file and not audio_file.startswith(music_service.AUDIO_CACHE_DIR):
                    try:
                        os.remove(audio_file)
                    except Exception:
                        pass
        else:
            bot.send_message(
                chat_id=user_id,
                text=caption,
                parse_mode='HTML'
            )

        return web.json_response({'success': True})
    except Exception as ex:
        logger.error(f"Error in send_to_chat: {ex}")
        return web.json_response({'error': str(ex)}, status=500)


async def api_check_access(request):
    user_id_str = request.query.get('user_id', '').strip()
    try:
        user_id = int(user_id_str) if user_id_str else 0
    except (ValueError, TypeError):
        user_id = 0

    allowed = access_control.is_allowed(user_id) if user_id else False
    is_admin = access_control.is_admin(user_id) if user_id else False

    return web.json_response({
        'user_id': user_id,
        'allowed': allowed,
        'is_admin': is_admin
    })


async def api_request_access(request):
    try:
        data = await request.json()
        user_id = int(data.get('user_id', 0))
        first_name = html.escape(str(data.get('first_name') or 'Пользователь'))
        username = data.get('username', '')
        username_str = f"@{html.escape(username)}" if username else "нет юзернейма"

        if not user_id:
            return web.json_response({'error': 'Missing user_id'}, status=400)

        if access_control.is_allowed(user_id):
            return web.json_response({
                'success': True,
                'already_allowed': True,
                'message': 'Доступ уже открыт!'
            })

        # Send notification to Telegram bot admins
        admins = access_control.get_admins()
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(text="✅ Разрешить доступ", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")
        )
        admin_text = (
            f"🔔 <b>Новый запрос на доступ из Mini App:</b>\n\n"
            f"👤 <b>Имя:</b> {first_name}\n"
            f"🔗 <b>Юзернейм:</b> {username_str}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
            f"Разрешить этому человеку использовать плеер?"
        )
        for admin_id in admins:
            try:
                bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=markup, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Could not notify admin {admin_id}: {e}")

        return web.json_response({
            'success': True,
            'message': 'Запрос отправлен администратору. Ожидайте одобрения.'
        })
    except Exception as ex:
        logger.error(f"Error handling access request: {ex}")
        return web.json_response({'error': str(ex)}, status=500)


async def api_version(request):
    import config
    return web.json_response({
        'status': 'ok',
        'version': '3.4.0',
        'admin_id': config.ADMIN_ID
    })


async def api_debug_stream(request):
    import traceback
    vid_id = request.query.get('id', 'ZZMj3GjGTVU')
    client_param = request.query.get('client', 'android,ios')
    clients = [c.strip() for c in client_param.split(',') if c.strip()]
    target = f"https://www.youtube.com/watch?v={vid_id}"
    diag = {'id': vid_id, 'tested_clients': clients}
    
    test_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'format': '18/bestaudio[ext=m4a]/140/bestaudio/best',
        'extractor_args': {
            'youtube': {
                'player_client': clients,
                'player_skip': ['webpage', 'configs']
            }
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(test_opts) as ydl:
            info = ydl.extract_info(target, download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            stream_url = info.get('url', '')
            diag['success'] = bool(stream_url)
            diag['url'] = (stream_url[:100] + '...') if stream_url else ''
            diag['format'] = info.get('format_id')
            diag['ext'] = info.get('ext')
            diag['acodec'] = info.get('acodec')
            diag['title'] = info.get('title')
    except Exception as e:
        diag['success'] = False
        diag['error'] = f"{type(e).__name__}: {str(e)}"

    return web.json_response(diag)


async def api_lyrics(request):
    artist = request.query.get('artist', '')
    title = request.query.get('title', '')
    if not artist and not title:
        return web.json_response({'found': False, 'message': 'Параметры artist или title обязательны'}, status=400)
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lyrics_service.get_lyrics, artist, title)
    return web.json_response(data)


def create_app():
    app = web.Application(middlewares=[cors_middleware])
    
    # API Routes
    app.router.add_get('/api/version', api_version)
    app.router.add_get('/api/check_access', api_check_access)
    app.router.add_post('/api/request_access', api_request_access)
    app.router.add_get('/api/debug_stream', api_debug_stream)
    app.router.add_get('/api/search', api_search)
    app.router.add_get('/api/wave', api_wave)
    app.router.add_get('/api/chart', api_chart)
    app.router.add_get('/api/new_releases', api_new_releases)
    app.router.add_get('/api/playlist', api_playlist)
    app.router.add_get('/api/yandex/chart', api_yandex_chart)
    app.router.add_get('/api/yandex/liked', api_yandex_liked)
    app.router.add_get('/api/yandex/playlists', api_yandex_playlists)
    app.router.add_post('/api/yandex/sync', api_yandex_sync)
    app.router.add_get('/api/yandex/status', api_yandex_status)
    app.router.add_get('/api/stream', api_stream)
    app.router.add_get('/api/lyrics', api_lyrics)
    app.router.add_post('/api/send_to_chat', api_send_to_chat)

    # Static Routes
    app.router.add_get('/', index_handler)
    app.router.add_static('/', path=FRONTEND_DIR, name='frontend')

    return app


if __name__ == '__main__':
    app = create_app()
    logger.info(f"Starting Wave Music Server on http://{HOST}:{PORT}")
    web.run_app(app, host=HOST, port=PORT)
