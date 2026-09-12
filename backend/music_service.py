import os
import re
import json
import time
import logging
import tempfile
import uuid
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
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios']
        }
    }
}

YDL_OPTS_STREAM = {
    'quiet': True,
    'no_warnings': True,
    'format': '18/bestaudio[ext=m4a]/140/bestaudio[acodec^=mp4a]/bestaudio/best',
    'skip_download': True,
    'noplaylist': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios']
        }
    }
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


NON_MUSIC_STOP_WORDS = [
    'review', 'обзор', 'тест-драйв', 'test drive', 'carwow', 'turbo review',
    'buyer', 'buying guide', 'walkaround', 'interior', 'specs', 'acceleration',
    'vlog', 'влог', 'podcast', 'подкаст', 'интервью', 'interview', 'reaction',
    'реакция', 'unboxing', 'распаковка', 'exhaust sound', 'sound system', 'crash test',
    'porsche club', 'exhaust valve', 'oil change', 'car review', 'buyer guide'
]


def search_tracks(query: str, limit: int = 12):
    """Searches tracks via yt-dlp, strictly filtering for genuine music tracks and rejecting car reviews/podcasts"""
    clean_q = query.strip()
    if not clean_q:
        return []

    # Check if query already has explicit music hints
    has_music_hint = any(w in clean_q.lower() for w in ['песн', 'трек', 'music', 'song', 'audio', 'клип', 'альбом', 'feat', 'ft.', 'remix', 'official'])
    
    # Query enhancement to force YouTube (especially on US IPs like Render) to prioritize Music / Audio over cars/vlogs
    search_query = clean_q if has_music_hint else f"{clean_q} music трек"
    fetch_count = max(limit * 2, 24)
    search_str = f"ytsearch{fetch_count}:{search_query}"
    
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

            # 1. Filter out videos that are too long (compilations/podcasts > 7m) or too short (Shorts/clips < 45s)
            if duration_sec > 0 and (duration_sec < 45 or duration_sec > 450):
                continue

            # 2. Filter out non-music videos (car reviews, test drives, unboxings)
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

            # If enhanced query didn't yield enough results, retry with original query + strict filter
            if len(results) < 3 and not has_music_hint:
                fallback_info = ydl.extract_info(f"ytsearch{fetch_count}:{clean_q}", download=False)
                fallback_entries = fallback_info.get('entries', []) if fallback_info else []
                process_entries(fallback_entries)
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

    return results[:limit]


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

AUDIO_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_cache")
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)


def _safe_filename(query: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', query.strip())
    if len(cleaned) > 50:
        cleaned = cleaned[:50]
    return f"{cleaned}.m4a"


def get_cached_audio_path(video_id_or_title: str) -> str:
    """Returns path to cached audio file if it exists and is valid, else empty string"""
    clean_query = video_id_or_title.strip()
    fname = _safe_filename(clean_query)
    fpath = os.path.join(AUDIO_CACHE_DIR, fname)
    if os.path.exists(fpath) and os.path.getsize(fpath) > 50000:
        return fpath
    return ""


def download_and_cache_audio(video_id_or_title: str) -> str:
    """Downloads track directly into persistent cache directory and returns the path."""
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

    out_file = os.path.join(AUDIO_CACHE_DIR, _safe_filename(clean_query))
    ydl_opts = {
        'format': '18/bestaudio[ext=m4a]/140/bestaudio[acodec^=mp4a]/bestaudio/best',
        'outtmpl': out_file,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'max_filesize': 35 * 1024 * 1024,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target])
        if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
            return out_file
    except Exception as ex:
        logger.error(f"Error downloading and caching audio for {video_id_or_title}: {ex}")
        if os.path.exists(out_file):
            try:
                os.remove(out_file)
            except Exception:
                pass
    return ""


def download_track_audio(video_id_or_title: str) -> str:
    """Downloads audio of track or gets it from cache. Returns path to file if successful."""
    return download_and_cache_audio(video_id_or_title)


def pre_cache_top_tracks():
    """Pre-downloads top tracks so mobile playback is instant with zero buffering"""
    logger.info("[PreCache] Начинаю фоновую предзагрузку топ-треков для мгновенного воспроизведения...")
    startup_ids = ['ZZMj3GjGTVU', 'aYw5HDb3z54', '4NRXx6U8ABQ', 'xKzL5zR4H7c', 'XvR07g-R94E', '_Yhyp-_hX2s']
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

