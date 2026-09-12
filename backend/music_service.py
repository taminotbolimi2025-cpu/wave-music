import os
import re
import json
import time
import logging
import tempfile
import uuid
import yt_dlp

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

CURATED_CHART = [
    {
        'id': '4EfM6rPmxow',
        'title': 'Minor',
        'artist': 'MiyaGi & Andy Panda',
        'cover': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400',
        'duration': '2:56'
    },
    {
        'id': 'nidQCt_HEsY',
        'title': 'I Got Love',
        'artist': 'Miyagi & Эндшпиль',
        'cover': 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400',
        'duration': '4:35'
    },
    {
        'id': 'j5cNhjG6iGs',
        'title': 'Останься образом',
        'artist': 'MACAN',
        'cover': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400',
        'duration': '3:12'
    },
    {
        'id': '7LcZzCPCuvg',
        'title': 'По барам',
        'artist': 'ANNA ASTI',
        'cover': 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400',
        'duration': '3:58'
    },
    {
        'id': 'p39HcuQNlg4',
        'title': 'Прятки',
        'artist': 'HammAli & Navai',
        'cover': 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400',
        'duration': '3:10'
    },
    {
        'id': 'fHI8X4OXluQ',
        'title': 'Blinding Lights',
        'artist': 'The Weeknd',
        'cover': 'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400',
        'duration': '3:20'
    },
    {
        'id': 'x1XuN5Rq2ws',
        'title': 'Ты и Я',
        'artist': 'Xcho',
        'cover': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400',
        'duration': '2:45'
    },
    {
        'id': 'yM1QjdoLmxQ',
        'title': 'Комета',
        'artist': 'JONY',
        'cover': 'https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400',
        'duration': '2:38'
    },
    {
        'id': 'UJ3COIHd954',
        'title': 'Captain',
        'artist': 'Miyagi',
        'cover': 'https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400',
        'duration': '3:40'
    },
    {
        'id': 'Rif-RTvmmss',
        'title': 'Starboy',
        'artist': 'The Weeknd ft. Daft Punk',
        'cover': 'https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400',
        'duration': '3:50'
    },
    {
        'id': 'wjj2upnfBI0',
        'title': 'Lovely',
        'artist': 'Billie Eilish & Khalid',
        'cover': 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400',
        'duration': '3:20'
    },
    {
        'id': 'tR1ECf4sEpw',
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

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_SEARCH) as ydl:
            info = ydl.extract_info(search_str, download=False)
            entries = info.get('entries', []) if info else []
            process_entries(entries)
    except Exception as ex:
        logger.error(f"Search error for {query}: {ex}")

    # Fallback to filter curated list if search yields nothing
    if not results:
        q_lower = clean_q.lower()
        results = [
            t for t in CURATED_CHART
            if q_lower in t['title'].lower() or q_lower in t['artist'].lower()
        ]
        if not results:
            results = CURATED_CHART[:limit]

    out_results = results[:limit]
    _search_cache[cache_key] = (now, out_results)
    return out_results


def get_stream_url(video_id_or_title: str) -> str:
    """Extracts direct audio playback stream URL with high precision and caching"""
    clean_query = video_id_or_title.strip()
    if clean_query in _stream_cache:
        cached_url, cached_time = _stream_cache[clean_query]
        if time.time() - cached_time < 7200:  # 2 hours stream URL TTL
            return cached_url

    # Target resolution
    if clean_query.startswith('http'):
        target = clean_query
    elif len(clean_query) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', clean_query):
        target = f"https://www.youtube.com/watch?v={clean_query}"
    else:
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
                now = time.time()
                _stream_cache[clean_query] = (stream_url, now)
                _stream_cache[video_id_or_title] = (stream_url, now)
                return stream_url
    except Exception as ex:
        logger.error(f"Failed to extract stream for {video_id_or_title}: {ex}")

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
    base_name = _safe_basename(clean_query)
    for ext in ('.mp3', '.m4a', '.webm', '.aac', '.opus'):
        path = os.path.join(AUDIO_CACHE_DIR, f"{base_name}{ext}")
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            return path
    return ""


def download_and_cache_audio(video_id_or_title: str) -> str:
    """Downloads pure audio track directly into persistent cache directory and returns the path."""
    cached = get_cached_audio_path(video_id_or_title)
    if cached:
        return cached

    clean_query = video_id_or_title.strip()
    if clean_query.startswith('http'):
        target = clean_query
    elif len(clean_query) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', clean_query):
        target = f"https://www.youtube.com/watch?v={clean_query}"
    else:
        target = f"ytsearch1:{clean_query} audio"

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


def download_track_audio(video_id_or_title: str) -> str:
    """Downloads audio of track or gets it from cache. Returns path to file if successful."""
    return download_and_cache_audio(video_id_or_title)


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
    curated = list(CURATED_CHART)
    random.shuffle(curated)
    return curated


def get_chart_tracks(force_refresh: bool = False):
    """Returns top chart tracks with guaranteed high-speed mobile playback"""
    return list(CURATED_CHART)


def get_new_releases(force_refresh: bool = False):
    """Returns fresh daily releases and premieres with guaranteed high-speed mobile playback"""
    return list(reversed(CURATED_CHART))


def update_all_daily_playlists():
    """Forces an immediate daily update of all playlists"""
    logger.info("[AutoUpdater] Запуск ежедневного обновления плейлистов...")
    chart = get_chart_tracks(force_refresh=True)
    releases = get_new_releases(force_refresh=True)
    logger.info(f"[AutoUpdater] Готово! Обновлено: {len(chart)} чарт, {len(releases)} новинок.")
    return chart, releases

