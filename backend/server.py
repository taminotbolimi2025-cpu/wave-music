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
import yt_dlp

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
    return web.FileResponse(index_file)


# API Handlers
async def api_search(request):
    q = request.query.get('q', '').strip()
    if not q:
        return web.json_response({'tracks': []})
    
    tracks = music_service.search_tracks(q, limit=12)
    return web.json_response({'tracks': tracks})


async def api_wave(request):
    mood = request.query.get('mood', 'all')
    tracks = music_service.get_wave_tracks(mood)
    return web.json_response({'tracks': tracks, 'mood': mood})


async def api_chart(request):
    tracks = music_service.get_chart_tracks()
    return web.json_response({'tracks': tracks})


async def api_new_releases(request):
    tracks = music_service.get_new_releases()
    return web.json_response({'tracks': tracks})


async def api_stream(request):
    vid_id = request.query.get('id', '').strip()
    if not vid_id:
        return web.Response(status=400, text='Missing id parameter')
    
    # 1. Fast path: check if track is already cached locally on disk
    cached_path = music_service.get_cached_audio_path(vid_id)
    if cached_path and os.path.exists(cached_path) and os.path.getsize(cached_path) > 10000:
        return web.FileResponse(cached_path, headers={
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=86400'
        })

    # 2. Try fast direct stream URL
    stream_url = music_service.get_stream_url(vid_id)
    if stream_url and not stream_url.endswith('.m3u8'):
        try:
            headers = {}
            range_header = request.headers.get('Range')
            if range_header:
                headers['Range'] = range_header

            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None, sock_read=60, sock_connect=10))
            upstream = await session.get(stream_url, headers=headers)
            if upstream.status in (200, 206):
                content_type = upstream.headers.get('Content-Type', 'audio/mp4')
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
                    await response.write_eof()
                    upstream.close()
                    await session.close()
                return response
            else:
                await session.close()
        except Exception as proxy_err:
            logger.warning(f"Direct stream proxy error for {vid_id}: {proxy_err}")

    # 3. Robust Mobile Fallback: Download track in worker thread and stream via FileResponse!
    loop = asyncio.get_event_loop()
    try:
        downloaded = await loop.run_in_executor(None, music_service.download_and_cache_audio, vid_id)
        if downloaded and os.path.exists(downloaded) and os.path.getsize(downloaded) > 10000:
            return web.FileResponse(downloaded, headers={
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


async def api_version(request):
    import config
    return web.json_response({
        'status': 'ok',
        'version': '2.4.0',
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
                'player_client': clients
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


def create_app():
    app = web.Application(middlewares=[cors_middleware])
    
    # API Routes
    app.router.add_get('/api/version', api_version)
    app.router.add_get('/api/debug_stream', api_debug_stream)
    app.router.add_get('/api/search', api_search)
    app.router.add_get('/api/wave', api_wave)
    app.router.add_get('/api/chart', api_chart)
    app.router.add_get('/api/new_releases', api_new_releases)
    app.router.add_get('/api/stream', api_stream)
    app.router.add_post('/api/send_to_chat', api_send_to_chat)

    # Static Routes
    app.router.add_get('/', index_handler)
    app.router.add_static('/', path=FRONTEND_DIR, name='frontend')

    return app


if __name__ == '__main__':
    app = create_app()
    logger.info(f"Starting Wave Music Server on http://{HOST}:{PORT}")
    web.run_app(app, host=HOST, port=PORT)
