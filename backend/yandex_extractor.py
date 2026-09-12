import os
import re
import sys
import json
import time
import hashlib
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

logger = logging.getLogger("YandexExtractor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

AUDIO_CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "audio_cache", "yandex"))
LIBRARY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "yandex_library.json"))
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)


def _format_duration(duration_ms):
    if not duration_ms:
        return "3:00"
    secs = int(duration_ms) // 1000
    return f"{secs // 60}:{secs % 60:02d}"


def get_yandex_client(token: str):
    """Initializes and returns a Yandex Music client or None if invalid"""
    try:
        from yandex_music import Client
        client = Client(token).init()
        return client
    except Exception as e:
        logger.error(f"Error initializing yandex_music.Client: {e}")
        return None


def get_direct_download_url(track_id: str, token: str) -> str:
    """Fallback method: extracts direct MP3 download URL using official Yandex storage protocol"""
    headers = {
        "Authorization": f"OAuth {token}",
        "User-Agent": "Yandex-Music-API",
        "Accept": "application/json",
    }
    url = f"https://api.music.yandex.net/tracks/{track_id}/download-info"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        info_list = json.loads(r.read().decode("utf-8")).get("result", [])

    if not info_list:
        raise ValueError(f"No download info for track {track_id}")

    # Prefer highest bitrate MP3
    selected = None
    for item in info_list:
        if item.get("codec") == "mp3":
            if not selected or item.get("bitrate_in_kbps", 0) > selected.get("bitrate_in_kbps", 0):
                selected = item
    if not selected:
        selected = info_list[0]

    xml_url = selected["download_info_url"]
    xml_req = urllib.request.Request(xml_url, headers=headers)
    with urllib.request.urlopen(xml_req, timeout=10) as xr:
        xml_root = ET.fromstring(xr.read().decode("utf-8"))

    host = xml_root.find("host").text
    path = xml_root.find("path").text
    ts = xml_root.find("ts").text
    s = xml_root.find("s").text

    secret_key = "XGRlBW9FXlekgbPrRHuSiA"
    sign_str = f"{secret_key}{path[1:]}{s}"
    sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    return f"https://{host}/get-mp3/{sign}/{ts}{path}"


def download_single_track(track_dict: dict, token: str, client=None) -> str:
    """Downloads track MP3 file directly to local storage cache. Returns path to file."""
    tid = str(track_dict["ym_id"])
    target_path = os.path.join(AUDIO_CACHE_DIR, f"{tid}.mp3")

    if os.path.exists(target_path) and os.path.getsize(target_path) > 10000:
        return target_path

    temp_path = target_path + ".tmp"
    try:
        if client:
            # Official client download
            track = client.tracks([tid])[0]
            track.download(temp_path, codec="mp3", bitrate_in_kbps=320)
        else:
            # Direct storage protocol download
            stream_url = get_direct_download_url(tid, token)
            urllib.request.urlretrieve(stream_url, temp_path)

        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 10000:
            os.replace(temp_path, target_path)
            return target_path
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Downloaded file too small for track {tid}")
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise e


def parse_track_object(track) -> dict:
    """Normalizes a Yandex Music track object or dict into Wave Music format"""
    if hasattr(track, "id"):
        tid = str(track.id)
        title = track.title or "Без названия"
        artists = ", ".join([a.name for a in track.artists if getattr(a, "name", None)]) or "Артист"
        dur_ms = track.duration_ms or 180000
        cover_uri = getattr(track, "cover_uri", None) or getattr(track, "og_image", None)
    else:
        tid = str(track.get("id"))
        title = track.get("title", "Без названия")
        artists = ", ".join([a.get("name", "") for a in track.get("artists", []) if a.get("name")]) or "Артист"
        dur_ms = track.get("durationMs") or track.get("duration_ms") or 180000
        cover_uri = track.get("coverUri") or track.get("cover_uri")

    if cover_uri:
        if "%%" in cover_uri:
            cover_url = "https://" + cover_uri.replace("%%", "400x400")
        elif not cover_uri.startswith("http"):
            cover_url = f"https://{cover_uri}"
        else:
            cover_url = cover_uri
    else:
        cover_url = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400"

    return {
        "id": f"ym_{tid}",
        "ym_id": tid,
        "title": title,
        "artist": artists,
        "duration": _format_duration(dur_ms),
        "duration_ms": dur_ms,
        "cover": cover_url,
        "source": "yandex",
        "streamUrl": f"/api/stream?id=ym_{tid}",
    }


def extract_full_library(token: str, download_audio: bool = True, progress_cb=None) -> dict:
    """Extracts all liked tracks, playlists, and audio files from user's Yandex account"""
    client = get_yandex_client(token)
    logger.info("Connecting to Yandex Music...")

    liked_tracks = []
    user_playlists = []

    if client:
        user_id = client.me.account.uid
        login = client.me.account.login
        logger.info(f"Connected to user: {login} (UID: {user_id})")

        # 1. Liked tracks
        logger.info("Fetching liked tracks...")
        likes = client.users_likes_tracks()
        if likes:
            track_ids = [t.id for t in likes]
            logger.info(f"Total liked tracks found: {len(track_ids)}")
            # Batch fetch track details (up to 100 per batch)
            chunk_size = 100
            for i in range(0, len(track_ids), chunk_size):
                chunk = track_ids[i:i + chunk_size]
                full_tracks = client.tracks(chunk)
                for t in full_tracks:
                    parsed = parse_track_object(t)
                    liked_tracks.append(parsed)

        # 2. Playlists
        logger.info("Fetching user playlists...")
        try:
            playlists = client.users_playlists_list()
            for pl in playlists:
                pl_obj = client.users_playlists(pl.kind, user_id)
                pl_tracks = [parse_track_object(tr.track) for tr in pl_obj.tracks if getattr(tr, "track", None)]
                user_playlists.append({
                    "kind": pl.kind,
                    "title": pl.title,
                    "track_count": len(pl_tracks),
                    "tracks": pl_tracks
                })
        except Exception as e:
            logger.warning(f"Could not fetch playlists: {e}")
    else:
        # Fallback via direct HTTP API
        headers = {
            "Authorization": f"OAuth {token}",
            "User-Agent": "Yandex-Music-API",
            "Accept": "application/json",
        }
        # Get status/account
        req = urllib.request.Request("https://api.music.yandex.net/account/status", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            acc_data = json.loads(r.read().decode("utf-8")).get("result", {})
            user_id = acc_data.get("account", {}).get("uid")
            logger.info(f"Connected to UID: {user_id}")

        # Get likes
        req = urllib.request.Request(f"https://api.music.yandex.net/users/{user_id}/likes/tracks", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            likes_res = json.loads(r.read().decode("utf-8")).get("result", {})
            track_ids = [str(t.get("id")) for t in likes_res.get("library", {}).get("tracks", [])]

        logger.info(f"Total liked tracks found: {len(track_ids)}")
        chunk_size = 100
        for i in range(0, len(track_ids), chunk_size):
            chunk = track_ids[i:i + chunk_size]
            post_data = urllib.parse.urlencode({"track-ids": ",".join(chunk)}).encode("utf-8")
            treq = urllib.request.Request("https://api.music.yandex.net/tracks", data=post_data, headers=headers)
            with urllib.request.urlopen(treq, timeout=15) as tr:
                tr_list = json.loads(tr.read().decode("utf-8")).get("result", [])
                for t in tr_list:
                    liked_tracks.append(parse_track_object(t))

    library_data = {
        "updated_at": time.time(),
        "liked_tracks": liked_tracks,
        "playlists": user_playlists,
    }

    with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
        json.dump(library_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(liked_tracks)} liked tracks and {len(user_playlists)} playlists to {LIBRARY_FILE}")

    # 3. Download MP3 audio files if requested
    if download_audio:
        total = len(liked_tracks)
        logger.info(f"Starting audio download for {total} tracks (320 kbps MP3)...")
        for idx, track in enumerate(liked_tracks, 1):
            try:
                local_path = download_single_track(track, token, client)
                size_mb = os.path.getsize(local_path) / (1024 * 1024)
                msg = f"[{idx}/{total}] Скачан: {track['artist']} - {track['title']} ({size_mb:.1f} MB)"
                logger.info(msg)
                if progress_cb:
                    progress_cb(idx, total, track, msg)
            except Exception as e:
                logger.error(f"[{idx}/{total}] Ошибка при скачивании {track['artist']} - {track['title']}: {e}")

    return library_data


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tok = sys.argv[1]
        extract_full_library(tok, download_audio=True)
    else:
        print("Использование: python yandex_extractor.py <ВАШ_ТОКЕН>")
