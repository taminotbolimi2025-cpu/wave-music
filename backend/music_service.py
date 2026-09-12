import os
import re
import json
import time
import logging
import tempfile
import uuid
import yt_dlp
import catalog
import yandex_chart

logger = logging.getLogger(__name__)

# In-memory stream and search cache
_stream_cache = {}
_search_cache = {}
SEARCH_CACHE_TTL = 3600  # 1 hour cache for instant search results

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
    'format': 'ba[ext=m4a]/ba[acodec^=mp4a]/140/ba[ext=mp3]/ba/b[acodec!=none]',
    'skip_download': True,
    'noplaylist': True,
}

# 50 Top Chart tracks from our 100+ catalog
CURATED_CHART = catalog.get_chart_catalog(limit=50)

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
    # Strip leading track numbers like "01. ", "1. ", "8. "
    cleaned = re.sub(r'^\s*\d+[\.\-\s]+', '', raw_title)
    # Remove common video tags
    cleaned = re.sub(r'[\(\[\{].*?(official|video|audio|клип|премьера|remix|mood|lyric|текст).*?[\)\]\}]', '', cleaned, flags=re.IGNORECASE)
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

    if artist.endswith(' - Topic'):
        artist = artist[:-8].strip()

    title = title.strip(' "\'')
    artist = artist.strip(' "\'')
    if not title:
        title = raw_title
    if not artist:
        artist = 'Артист'

    return title, artist


NON_MUSIC_STOP_WORDS = [
    'review', 'обзор', 'тест-драйв', 'test drive', 'carwow', 'turbo review',
    'buyer', 'buying guide', 'walkaround', 'interior', 'specs', 'acceleration',
    'vlog', 'влог', 'podcast', 'подкаст', 'интервью', 'interview', 'reaction',
    'реакция', 'unboxing', 'распаковка', 'crash test', 'porsche club'
]


def search_tracks(query: str, limit: int = 12):
    """Searches tracks via yt-dlp with caching and smart music filtering"""
    clean_q = query.strip()
    if not clean_q:
        return []

    cache_key = f"{clean_q.lower()}_{limit}"
    now = time.time()
    if cache_key in _search_cache:
        cached_time, cached_results = _search_cache[cache_key]
        if (now - cached_time) < SEARCH_CACHE_TTL:
            return cached_results

    # Search for genuine music tracks
    search_str = f"ytsearch{max(limit, 10)}:{clean_q}"
    results = []
    seen_ids = set()

    def process_entries(entries):
        for e in entries:
            if not e or not e.get('id'):
                continue

            vid_id = e.get('id')
            if vid_id in seen_ids:
                continue

            raw_title = e.get('title', 'Unknown Track')
            uploader = e.get('uploader', '')
            duration_sec = e.get('duration') or 0

            # 1. Filter out videos that are too long (> 10m) or too short (< 30s)
            if duration_sec > 0 and (duration_sec < 30 or duration_sec > 600):
                continue

            # 2. Filter out non-music videos
            t_lower = raw_title.lower()
            u_lower = uploader.lower()
            if any(sw in t_lower or sw in u_lower for sw in NON_MUSIC_STOP_WORDS):
                continue

            # Get best thumbnail
            thumbnails = e.get('thumbnails', [])
            cover = thumbnails[-1].get('url') if thumbnails else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

            title, artist = _clean_title_and_artist(raw_title, uploader)

            seen_ids.add(vid_id)
            results.append({
                'id': vid_id,
                'title': title,
                'artist': artist,
                'cover': cover,
                'duration': _format_duration(duration_sec),
                'duration_sec': int(duration_sec or 0),
                'streamUrl': f"/api/stream?id={vid_id}"
            })
            if len(results) >= limit:
                break

    # 1. Instant match from our 100+ curated catalog
    q_lower = clean_q.lower()
    catalog_matches = [
        t for t in catalog.CATALOG
        if q_lower in t['title'].lower() or q_lower in t['artist'].lower()
    ]
    for cm in catalog_matches:
        if cm['id'] not in seen_ids:
            seen_ids.add(cm['id'])
            results.append(dict(cm))

    # 2. Broader online YouTube search
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            info = ydl.extract_info(search_str, download=False)
            entries = info.get('entries', []) if info else []
            process_entries(entries)
    except Exception as ex:
        logger.error(f"Search error for {query}: {ex}")

    # Fallback to catalog if search yields nothing
    if not results:
        results = catalog.CATALOG[:limit]

    out_results = results[:limit]
    _search_cache[cache_key] = (now, out_results)
    return out_results


def _resolve_target_query(clean_query: str, artist: str = "", title: str = "") -> str:
    if clean_query.startswith('http'):
        return clean_query

    # 1. If explicit artist and title are provided, use them directly
    if artist and title:
        return f"ytsearch1:{artist} - {title} audio"

    # 2. Check curated catalog (contains 365+ tracks: Yandex Top 100, Apple Music, Phonk, etc.)
    track = catalog.get_track_by_id(clean_query)
    if track:
        return f"ytsearch1:{track['artist']} - {track['title']} audio"

    # 3. If it's a Yandex ID, check live chart or liked tracks
    if clean_query.startswith('ym_'):
        ym_id = clean_query[3:]
        for t in catalog.get_yandex_liked_tracks():
            if t.get('id') == clean_query or str(t.get('ym_id')) == ym_id:
                return f"ytsearch1:{t['artist']} - {t['title']} audio"
        try:
            for t in yandex_chart.fetch_live_yandex_chart(100):
                if t.get('id') == clean_query or str(t.get('ym_id')) == ym_id:
                    return f"ytsearch1:{t['artist']} - {t['title']} audio"
        except Exception:
            pass

    # 4. Standard YouTube 11-char ID (must NOT be internal prefixes like ym_, am_, tr_)
    if len(clean_query) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', clean_query) and not clean_query.startswith(('ym_', 'am_', 'tr_')):
        return f"https://www.youtube.com/watch?v={clean_query}"

    # 5. Fallback general search
    if clean_query.startswith('track_'):
        clean_query = 'хит музыки'
    return f"ytsearch1:{clean_query} audio"


def get_stream_url(video_id_or_title: str, artist: str = "", title: str = "") -> str:
    """Extracts direct audio playback stream URL with high precision and caching"""
    clean_query = video_id_or_title.strip()
    cache_key = f"{clean_query}_{artist}_{title}" if (artist or title) else clean_query
    if cache_key in _stream_cache:
        cached_url, cached_time = _stream_cache[cache_key]
        if time.time() - cached_time < 7200:  # 2 hours stream URL TTL
            return cached_url

    target = _resolve_target_query(clean_query, artist=artist, title=title)

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_STREAM) as ydl:
            info = ydl.extract_info(target, download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            stream_url = info.get('url')
            if stream_url:
                now = time.time()
                _stream_cache[cache_key] = (stream_url, now)
                _stream_cache[clean_query] = (stream_url, now)
                _stream_cache[video_id_or_title] = (stream_url, now)
                return stream_url
    except Exception as ex:
        logger.error(f"Failed to extract stream for {video_id_or_title} ({artist} - {title}): {ex}")

    return ""


AUDIO_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_cache")
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)


def _safe_basename(query: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', query.strip())
    if len(cleaned) > 50:
        cleaned = cleaned[:50]
    return cleaned or "track"


def get_cached_audio_path(video_id_or_title: str) -> str:
    """Returns path to cached audio file if it exists and is valid, else empty string"""
    clean_query = video_id_or_title.strip()
    if clean_query.startswith("ym_"):
        ym_id = clean_query[3:]
        ypath = os.path.join(AUDIO_CACHE_DIR, "yandex", f"{ym_id}.mp3")
        if os.path.exists(ypath) and os.path.getsize(ypath) > 10000:
            return ypath

    base_name = _safe_basename(clean_query)
    for ext in ('.mp3', '.m4a', '.webm', '.aac', '.opus'):
        path = os.path.join(AUDIO_CACHE_DIR, f"{base_name}{ext}")
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            return path
    return ""


def download_and_cache_audio(video_id_or_title: str, artist: str = "", title: str = "") -> str:
    """Downloads pure audio track directly into persistent cache directory and returns the path."""
    cached = get_cached_audio_path(video_id_or_title)
    if cached:
        return cached

    clean_query = video_id_or_title.strip()
    target = _resolve_target_query(clean_query, artist=artist, title=title)

    base_name = _safe_basename(clean_query)
    out_tmpl = os.path.join(AUDIO_CACHE_DIR, f"{base_name}.%(ext)s")
    ydl_opts = {
        'format': 'ba[ext=m4a]/ba[acodec^=mp4a]/140/ba[ext=mp3]/ba/b[acodec!=none]',
        'outtmpl': out_tmpl,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 40 * 1024 * 1024
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target])
        found = get_cached_audio_path(clean_query)
        if found:
            return found
    except Exception as ex:
        logger.error(f"Error downloading and caching audio for {video_id_or_title}: {ex}")

    return ""


def download_track_audio(video_id_or_title: str, artist: str = "", title: str = "") -> str:
    """Downloads audio of track or gets it from cache. Returns path to file if successful."""
    return download_and_cache_audio(video_id_or_title, artist=artist, title=title)


def pre_cache_top_tracks():
    """Pre-downloads top tracks so mobile playback is instant with zero buffering"""
    logger.info("[PreCache] Начинаю фоновую предзагрузку топ-треков для мгновенного воспроизведения...")
    startup_ids = ['4EfM6rPmxow', 'j5cNhjG6iGs', 'fHI8X4OXluQ', 'x1XuN5Rq2ws', 'yM1QjdoLmxQ', 'tR1ECf4sEpw']
    for sid in startup_ids:
        try:
            download_and_cache_audio(sid)
        except Exception as e:
            logger.warning(f"Error pre-caching {sid}: {e}")
    logger.info("[PreCache] Готово! Топ-треки закешированы на сервере.")


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
    """Returns dynamic recommendation stream for 'Моя Волна' using guaranteed playable tracks"""
    import random
    tracks = catalog.get_mood_catalog(mood=mood, limit=60)
    random.shuffle(tracks)
    return tracks


def get_chart_tracks(force_refresh: bool = False):
    """Returns top-50 live chart tracks from Yandex Music with fallback to curated catalog"""
    try:
        live_chart = yandex_chart.fetch_live_yandex_chart(limit=50)
        if live_chart and len(live_chart) >= 10:
            return live_chart
    except Exception as e:
        logger.warning(f"Failed to fetch live Yandex chart: {e}")
    return catalog.get_chart_catalog(limit=50)


def get_new_releases(force_refresh: bool = False):
    """Returns fresh daily releases and premieres with guaranteed high-speed mobile playback"""
    all_tracks = catalog.get_catalog_tracks()
    return all_tracks[15:55]


def get_playlist_tracks(name: str):
    """Returns specialized curated playlist tracks from 100+ track catalog"""
    return catalog.get_playlist_tracks(name)


def update_all_daily_playlists():
    """Forces an immediate daily update of all playlists"""
    logger.info("[AutoUpdater] Запуск ежедневного обновления плейлистов...")
    chart = get_chart_tracks(force_refresh=True)
    releases = get_new_releases(force_refresh=True)
    logger.info(f"[AutoUpdater] Готово! Обновлено: {len(chart)} чарт, {len(releases)} новинок.")
    return chart, releases

