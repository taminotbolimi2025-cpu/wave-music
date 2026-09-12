import re
import time
import logging
import urllib.parse
import urllib.request
import json

logger = logging.getLogger(__name__)

# Cache: key = "artist::title", value = (timestamp, data)
_lyrics_cache = {}
CACHE_TTL = 86400 * 7  # 7 days cache


def _clean_string(text: str) -> str:
    if not text:
        return ""
    # Remove featuring, feat, remakes, ft., extra tags
    cleaned = re.sub(r'[\(\[\{].*?(feat|ft|remix|prod|official|video|клип).*?[\)\]\}]', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def parse_lrc(lrc_text: str) -> list:
    """Parses LRC format [mm:ss.xx] line into a list of dicts: [{'time': float, 'text': str}]"""
    lines = []
    if not lrc_text:
        return lines

    pattern = re.compile(r'\[(\d{2}):(\d{2}(?:\.\d+)?)\](.*)')
    for raw_line in lrc_text.splitlines():
        match = pattern.match(raw_line.strip())
        if match:
            mins = int(match.group(1))
            secs = float(match.group(2))
            total_sec = mins * 60 + secs
            text = match.group(3).strip()
            lines.append({"time": round(total_sec, 2), "text": text})

    return lines


def get_lyrics(artist: str, title: str) -> dict:
    """Fetches lyrics from lrclib.net with fallback and caching."""
    clean_art = _clean_string(artist)
    clean_tit = _clean_string(title)

    cache_key = f"{clean_art.lower()}::{clean_tit.lower()}"
    now = time.time()
    if cache_key in _lyrics_cache:
        cached_time, cached_data = _lyrics_cache[cache_key]
        if (now - cached_time) < CACHE_TTL:
            return cached_data

    headers = {"User-Agent": "WaveMusic/3.5.0"}

    # 1. Try exact match
    try:
        url = "https://lrclib.net/api/get?" + urllib.parse.urlencode({
            "artist_name": clean_art,
            "track_name": clean_tit
        })
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            plain = data.get("plainLyrics")
            synced_raw = data.get("syncedLyrics")
            if plain or synced_raw:
                result = {
                    "found": True,
                    "artist": data.get("artistName", artist),
                    "title": data.get("trackName", title),
                    "plain": plain or "",
                    "synced": parse_lrc(synced_raw) if synced_raw else []
                }
                _lyrics_cache[cache_key] = (now, result)
                return result
    except Exception as e:
        logger.debug(f"Direct lyrics lookup failed for {artist} - {title}: {e}")

    # 2. Try search query fallback
    try:
        search_query = f"{clean_art} {clean_tit}".strip()
        url = "https://lrclib.net/api/search?" + urllib.parse.urlencode({"q": search_query})
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and isinstance(data, list):
                item = data[0]
                plain = item.get("plainLyrics")
                synced_raw = item.get("syncedLyrics")
                if plain or synced_raw:
                    result = {
                        "found": True,
                        "artist": item.get("artistName", artist),
                        "title": item.get("trackName", title),
                        "plain": plain or "",
                        "synced": parse_lrc(synced_raw) if synced_raw else []
                    }
                    _lyrics_cache[cache_key] = (now, result)
                    return result
    except Exception as e:
        logger.debug(f"Search lyrics lookup failed for {artist} - {title}: {e}")

    # 3. Not found
    not_found_res = {
        "found": False,
        "artist": artist,
        "title": title,
        "plain": "Текст этой песни пока не добавлен в базу.\n\nНаслаждайтесь чистым звучанием в Wave Music! 🎵",
        "synced": []
    }
    _lyrics_cache[cache_key] = (now, not_found_res)
    return not_found_res
