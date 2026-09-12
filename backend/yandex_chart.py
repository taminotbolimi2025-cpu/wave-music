import re
import json
import time
import logging
import urllib.request

logger = logging.getLogger("YandexChart")

_chart_cache = None
_chart_cached_at = 0
CHART_CACHE_TTL = 1800  # 30 minutes cache


def fetch_live_yandex_chart(limit: int = 100) -> list:
    """Fetches real-time Top Chart tracks from Yandex Music with full metadata and covers"""
    global _chart_cache, _chart_cached_at

    now = time.time()
    if _chart_cache and (now - _chart_cached_at < CHART_CACHE_TTL):
        return _chart_cache[:limit]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    url = "https://music.yandex.ru/chart"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")

        patches = re.findall(r"window\.__PAGE_STATE_PATCHES__\[.*?\]\.push\((\[.*?\])\);", html, re.DOTALL)
        chart_dict = {}
        for p in patches:
            try:
                data = json.loads(p)
                for item in data:
                    path = item.get("path", "")
                    val = item.get("value")
                    m = re.match(r"^/tracksSubPage/items/(\d+)$", path)
                    if m and isinstance(val, dict):
                        idx = int(m.group(1))
                        chart_dict[idx] = val
            except Exception:
                pass

        if not chart_dict:
            logger.warning("No tracks parsed from Yandex Music chart page patches")
            return _chart_cache[:limit] if _chart_cache else []

        extracted = []
        for idx in sorted(chart_dict.keys()):
            val = chart_dict[idx]
            tid = str(val.get("id"))
            title = val.get("title", "Без названия")
            artists = ", ".join([a.get("name", "") for a in val.get("artists", []) if a.get("name")]) or "Артист"
            dur_ms = val.get("durationMs") or 180000
            mins = int(dur_ms) // 60000
            secs = (int(dur_ms) % 60000) // 1000
            cover_uri = val.get("coverUri", "")
            if cover_uri:
                cover = "https://" + cover_uri.replace("%%", "400x400")
            else:
                cover = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400"

            extracted.append({
                "id": f"ym_{tid}",
                "ym_id": tid,
                "title": title,
                "artist": artists,
                "duration": f"{mins}:{secs:02d}",
                "duration_ms": dur_ms,
                "cover": cover,
                "category": "chart",
                "source": "yandex",
                "streamUrl": f"/api/stream?id=ym_{tid}",
            })

        _chart_cache = extracted
        _chart_cached_at = now
        logger.info(f"Successfully fetched {len(extracted)} tracks from live Yandex Music Chart!")
        return extracted[:limit]
    except Exception as e:
        logger.error(f"Error fetching Yandex Music chart: {e}")
        return _chart_cache[:limit] if _chart_cache else []


if __name__ == "__main__":
    tracks = fetch_live_yandex_chart(15)
    print(f"Total tracks: {len(tracks)}")
    for i, t in enumerate(tracks):
        print(f"#{i+1}: {t['artist']} - {t['title']} ({t['duration']}) | {t['cover']}")
