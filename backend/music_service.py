import re
import logging
import yt_dlp

logger = logging.getLogger(__name__)

# In-memory stream cache
_stream_cache = {}

YDL_OPTS_SEARCH = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,
    'skip_download': True,
    'default_search': 'ytsearch',
    'noplaylist': True,
}

YDL_OPTS_STREAM = {
    'quiet': True,
    'no_warnings': True,
    'format': 'bestaudio/best',
    'skip_download': True,
    'noplaylist': True,
}

CURATED_CHART = [
    {
        'id': 'ZZMj3GjGTVU',
        'title': 'Minor',
        'artist': 'MiyaGi & Andy Panda',
        'cover': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400',
        'duration': '2:56'
    },
    {
        'id': 'aYw5HDb3z54',
        'title': 'Останься образом',
        'artist': 'MACAN',
        'cover': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400',
        'duration': '3:12'
    },
    {
        'id': '4NRXx6U8ABQ',
        'title': 'Blinding Lights',
        'artist': 'The Weeknd',
        'cover': 'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400',
        'duration': '3:20'
    },
    {
        'id': 'xKzL5zR4H7c',
        'title': 'Ты и Я',
        'artist': 'Xcho',
        'cover': 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400',
        'duration': '2:45'
    },
    {
        'id': 'XvR07g-R94E',
        'title': 'Комета',
        'artist': 'JONY',
        'cover': 'https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400',
        'duration': '2:38'
    },
    {
        'id': '_Yhyp-_hX2s',
        'title': 'Lose Yourself',
        'artist': 'Eminem',
        'cover': 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400',
        'duration': '5:26'
    }
]

MOOD_QUERIES = {
    'all': ['топ треков 2026', 'популярная музыка хиты', 'новинки музыки'],
    'energy': ['phonk workout', 'бодрая музыка тренировки', 'hip hop hits bass'],
    'chill': ['chill lofi deep house', 'спокойная музыка для расслабления', 'ambient chillout'],
    'drive': ['музыка в машину басы', 'night drive phonk hip hop', 'russian rap bass'],
    'dance': ['club dance hits remix', 'дискотека танцевальная музыка', 'edm house party'],
    'romantic': ['красивая музыка про любовь', 'лирика медляк', 'romantic pop songs']
}


def _format_duration(seconds):
    if not seconds:
        return '3:00'
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


def _clean_title_and_artist(raw_title, uploader):
    # Common formats: "Artist - Title (Official Video)", "Artist — Title"
    cleaned = re.sub(r'[\(\[\{].*?(official|video|audio|клип|премьера|remix|mood).*?[\)\]\}]', '', raw_title, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    if ' - ' in cleaned:
        parts = cleaned.split(' - ', 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    elif ' — ' in cleaned:
        parts = cleaned.split(' — ', 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        artist = uploader or 'Артист'
        title = cleaned

    return title, artist


def search_tracks(query: str, limit: int = 12):
    """Searches tracks via yt-dlp and returns structured list"""
    search_str = f"ytsearch{limit}:{query}"
    results = []

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            info = ydl.extract_info(search_str, download=False)
            entries = info.get('entries', []) if info else []

            for e in entries:
                if not e or not e.get('id'):
                    continue
                
                vid_id = e.get('id')
                raw_title = e.get('title', 'Unknown Track')
                uploader = e.get('uploader', '')
                duration_sec = e.get('duration')
                
                # Get best thumbnail
                thumbnails = e.get('thumbnails', [])
                cover = thumbnails[-1].get('url') if thumbnails else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                title, artist = _clean_title_and_artist(raw_title, uploader)

                results.append({
                    'id': vid_id,
                    'title': title,
                    'artist': artist,
                    'cover': cover,
                    'duration': _format_duration(duration_sec),
                    'duration_sec': int(duration_sec or 0),
                    'streamUrl': f"/api/stream?id={vid_id}"
                })
    except Exception as ex:
        logger.error(f"Search error for {query}: {ex}")

    # Fallback to filter curated list if search yields nothing
    if not results:
        q_lower = query.lower()
        results = [
            t for t in CURATED_CHART
            if q_lower in t['title'].lower() or q_lower in t['artist'].lower()
        ]
        if not results:
            results = CURATED_CHART[:limit]

    return results


def get_stream_url(video_id_or_title: str) -> str:
    """Extracts direct audio playback stream URL with high precision"""
    clean_query = video_id_or_title.strip()
    if clean_query in _stream_cache:
        return _stream_cache[clean_query]

    # Target resolution
    if clean_query.startswith('http'):
        target = clean_query
    elif len(clean_query) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', clean_query):
        target = f"https://www.youtube.com/watch?v={clean_query}"
    else:
        # Ignore dummy placeholder ids like track_1, track_2
        if clean_query.startswith('track_'):
            clean_query = 'хит музыки'
        target = f"ytsearch1:{clean_query} audio"

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_STREAM) as ydl:
            info = ydl.extract_info(target, download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            stream_url = info.get('url')
            if stream_url:
                _stream_cache[clean_query] = stream_url
                _stream_cache[video_id_or_title] = stream_url
                return stream_url
    except Exception as ex:
        logger.error(f"Failed to extract stream for {video_id_or_title}: {ex}")

    # Fallback to search without 'audio' keyword if needed
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_STREAM) as ydl:
            info = ydl.extract_info(f"ytsearch1:{clean_query}", download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            stream_url = info.get('url')
            if stream_url:
                _stream_cache[clean_query] = stream_url
                return stream_url
    except Exception:
        pass

    return ""


import tempfile
import uuid


def download_track_audio(video_id_or_title: str) -> str:
    """Downloads audio of track to a local m4a file in temp directory.
    Returns path to file if successful, or empty string on failure.
    Caller is responsible for removing the file after sending."""
    clean_query = video_id_or_title.strip()
    if clean_query.startswith('http'):
        target = clean_query
    elif len(clean_query) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', clean_query):
        target = f"https://www.youtube.com/watch?v={clean_query}"
    else:
        target = f"ytsearch1:{clean_query} audio"

    out_file = os.path.join(tempfile.gettempdir(), f"wave_{uuid.uuid4().hex[:8]}.m4a")
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': out_file,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 30 * 1024 * 1024,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target])
        if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
            return out_file
    except Exception as ex:
        logger.error(f"Error downloading audio for {video_id_or_title}: {ex}")
        if os.path.exists(out_file):
            try:
                os.remove(out_file)
            except Exception:
                pass
    return ""



import os
import json
import time

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))
CHART_CACHE_FILE = os.path.join(CACHE_DIR, "daily_chart.json")
RELEASES_CACHE_FILE = os.path.join(CACHE_DIR, "daily_releases.json")
CACHE_TTL_HOURS = 12


def _load_cache(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                updated_at = data.get('updated_at', 0)
                if (time.time() - updated_at) < (CACHE_TTL_HOURS * 3600):
                    return data.get('tracks', [])
        except Exception as e:
            logger.warning(f"Error reading cache {filepath}: {e}")
    return None


def _save_cache(filepath, tracks):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({'updated_at': time.time(), 'tracks': tracks}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Error saving cache {filepath}: {e}")


def get_wave_tracks(mood: str = 'all'):
    """Returns dynamic recommendation stream for 'Моя Волна'"""
    queries = MOOD_QUERIES.get(mood, MOOD_QUERIES['all'])
    import random
    selected_query = random.choice(queries)
    tracks = search_tracks(selected_query, limit=15)
    return tracks


def get_chart_tracks(force_refresh: bool = False):
    """Returns top chart tracks, automatically refreshed daily"""
    if not force_refresh:
        cached = _load_cache(CHART_CACHE_FILE)
        if cached:
            return cached

    logger.info("Auto-updating daily chart from trending hits...")
    tracks = search_tracks("топ чарт хиты 2026 новинки", limit=15)
    if tracks:
        _save_cache(CHART_CACHE_FILE, tracks)
        return tracks
    return CURATED_CHART


def get_new_releases(force_refresh: bool = False):
    """Returns fresh daily releases and premieres"""
    if not force_refresh:
        cached = _load_cache(RELEASES_CACHE_FILE)
        if cached:
            return cached

    logger.info("Auto-updating daily new releases...")
    tracks = search_tracks("новинки музыки премьеры 2026", limit=15)
    if tracks:
        _save_cache(RELEASES_CACHE_FILE, tracks)
        return tracks
    return CURATED_CHART


def update_all_daily_playlists():
    """Forces an immediate daily update of all playlists"""
    logger.info("[AutoUpdater] Запуск ежедневного обновления плейлистов...")
    chart = get_chart_tracks(force_refresh=True)
    releases = get_new_releases(force_refresh=True)
    logger.info(f"[AutoUpdater] Готово! Обновлено: {len(chart)} чарт, {len(releases)} новинок.")
    return chart, releases

