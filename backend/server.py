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
    vid_id = request.query.get('id', '')
    if not vid_id:
        return web.Response(status=400, text='Missing id parameter')
    
    stream_url = music_service.get_stream_url(vid_id)
    if not stream_url:
        return web.Response(status=404, text='Track not found')
    
    # Proxy audio stream directly through the server so YouTube IP restrictions don't block the mobile client
    headers = {}
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header
    
    client_timeout = aiohttp.ClientTimeout(total=None, sock_read=60, sock_connect=10)
    try:
        session = aiohttp.ClientSession(timeout=client_timeout)
        upstream = await session.get(stream_url, headers=headers)
        
        res_headers = {
            'Content-Type': upstream.headers.get('Content-Type', 'audio/webm'),
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'public, max-age=3600',
            'Access-Control-Allow-Origin': '*'
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
    except Exception as ex:
        logger.error(f"Stream proxy error for {vid_id}: {ex}")
        return web.Response(status=500, text=f"Streaming error: {ex}")


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
        'version': '2.1.0',
        'admin_id': config.ADMIN_ID
    })


def create_app():
    app = web.Application(middlewares=[cors_middleware])
    
    # API Routes
    app.router.add_get('/api/version', api_version)
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
