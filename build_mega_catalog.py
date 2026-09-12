import os
import sys
import re
import json
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
import yandex_chart
import catalog

print(">>> СБОРКА МЕГА-КАТАЛОГА МУЗЫКИ ИЗ ИНТЕРНЕТА ДЛЯ WAVE MUSIC <<<")

all_tracks = []
seen_keys = set()

def make_key(title, artist):
    c_t = re.sub(r"[^a-zA-Zа-яА-Я0-9]", "", title.lower())
    c_a = re.sub(r"[^a-zA-Zа-яА-Я0-9]", "", artist.lower())
    return f"{c_a}_{c_t}"


# 1. Живой ТОП 100 Яндекс Музыки
print("[1/4] Загрузка ТОП-100 чарта Яндекс Музыки...")
try:
    ym_tracks = yandex_chart.fetch_live_yandex_chart(100)
    for t in ym_tracks:
        k = make_key(t["title"], t["artist"])
        if k not in seen_keys:
            seen_keys.add(k)
            t["category"] = "chart"
            t["moods"] = ["all", "drive", "energy"]
            all_tracks.append(t)
    print(f"  -> Добавлено из Яндекс Музыки: {len(all_tracks)} треков")
except Exception as e:
    print("  -> Ошибка Яндекс Музыки:", e)


# 2. Apple Music Russia Top 100
print("[2/4] Загрузка ТОП-100 Apple Music Россия...")
try:
    req = urllib.request.Request("https://itunes.apple.com/ru/rss/topsongs/limit=100/json", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
        entries = data.get("feed", {}).get("entry", [])
        added_am_ru = 0
        for e in entries:
            title = e.get("im:name", {}).get("label", "").strip()
            artist = e.get("im:artist", {}).get("label", "").strip()
            if not title or not artist:
                continue
            k = make_key(title, artist)
            if k in seen_keys:
                continue
            seen_keys.add(k)

            images = e.get("im:image", [])
            raw_cover = images[-1].get("label") if images else ""
            cover = raw_cover.replace("170x170bb.png", "600x600bb.jpg") if raw_cover else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400"
            safe_id = "am_ru_" + re.sub(r"[^a-zA-Z0-9_]", "_", f"{artist}_{title}")[:30]

            all_tracks.append({
                "id": safe_id,
                "title": title,
                "artist": artist,
                "cover": cover,
                "duration": "3:20",
                "category": "chart",
                "moods": ["all", "dance", "energy"],
                "source": "apple_ru",
                "streamUrl": f"/api/stream?id={safe_id}"
            })
            added_am_ru += 1
        print(f"  -> Добавлено из Apple Music RU: {added_am_ru} треков")
except Exception as e:
    print("  -> Ошибка Apple Music RU:", e)


# 3. Apple Music Global / US Top 100
print("[3/4] Загрузка ТОП-100 Apple Music Мировые хиты...")
try:
    req = urllib.request.Request("https://itunes.apple.com/us/rss/topsongs/limit=100/json", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
        entries = data.get("feed", {}).get("entry", [])
        added_am_us = 0
        for e in entries:
            title = e.get("im:name", {}).get("label", "").strip()
            artist = e.get("im:artist", {}).get("label", "").strip()
            if not title or not artist:
                continue
            k = make_key(title, artist)
            if k in seen_keys:
                continue
            seen_keys.add(k)

            images = e.get("im:image", [])
            raw_cover = images[-1].get("label") if images else ""
            cover = raw_cover.replace("170x170bb.png", "600x600bb.jpg") if raw_cover else "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400"
            safe_id = "am_us_" + re.sub(r"[^a-zA-Z0-9_]", "_", f"{artist}_{title}")[:30]

            all_tracks.append({
                "id": safe_id,
                "title": title,
                "artist": artist,
                "cover": cover,
                "duration": "3:15",
                "category": "world",
                "moods": ["all", "energy", "drive"],
                "source": "apple_us",
                "streamUrl": f"/api/stream?id={safe_id}"
            })
            added_am_us += 1
        print(f"  -> Добавлено из Apple Music Global: {added_am_us} треков")
except Exception as e:
    print("  -> Ошибка Apple Music Global:", e)


# 4. Базовый отобранный каталог (Кальянный рэп, Phonk, Chill, Восточный вайб)
print("[4/4] Слияние с базовым каталогом...")
base_catalog = catalog.CATALOG
added_base = 0
for t in base_catalog:
    k = make_key(t["title"], t["artist"])
    if k not in seen_keys:
        seen_keys.add(k)
        item = dict(t)
        if "streamUrl" not in item:
            item["streamUrl"] = f"/api/stream?id={item['id']}"
        all_tracks.append(item)
        added_base += 1

print(f"  -> Добавлено из базового каталога: {added_base} треков")
print(f"\n==================================================")
print(f"  ИТОГО В КАТАЛОГЕ: {len(all_tracks)} ТРЕКОВ ИЗ ИНТЕРНЕТА!")
print(f"==================================================")

# Сохраняем в frontend/tracks.json
json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend", "tracks.json"))
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_tracks, f, ensure_ascii=False, indent=2)
print(f"[OK] Сохранено в {json_path}")

# Обновляем backend/catalog.py
cat_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "catalog.py"))
cat_content = f'''"""
Wave Music - Comprehensive Mega-Catalog ({len(all_tracks)}+ tracks from Internet)
Includes live Yandex Music Top 100, Apple Music Top Charts, Phonk, Rap, Pop, World Hits.
"""
import os
import json

CATALOG = {json.dumps(all_tracks, ensure_ascii=False, indent=2)}

# Quick lookup indexes
TRACKS_BY_ID = {{t["id"]: t for t in CATALOG}}

def get_catalog_tracks():
    return list(CATALOG)

def get_chart_catalog(limit=50):
    return [t for t in CATALOG if t.get("category") in ("chart", "world")][:limit]

def get_mood_catalog(mood="all", limit=60):
    if mood == "all":
        return list(CATALOG)[:limit]
    matched = [t for t in CATALOG if mood in t.get("moods", [])]
    return matched[:limit] if matched else list(CATALOG)[:limit]

def get_playlist_tracks(name):
    lower_name = name.lower()
    if "кальян" in lower_name or "рэп" in lower_name:
        return [t for t in CATALOG if any(k in t.get("artist", "").lower() for k in ["miyagi", "macan", "xcho", "jony", "navai", "asti", "hammali", "jah"])]
    elif "deep" in lower_name or "chill" in lower_name:
        return [t for t in CATALOG if "chill" in t.get("moods", [])]
    elif "восточн" in lower_name:
        return [t for t in CATALOG if any(k in t.get("artist", "").lower() for k in ["shohruhxon", "munisa", "gafur", "ulukmanapo", "blok3", "miyagi", "xcho", "jony"])]
    elif "энерги" in lower_name or "phonk" in lower_name or "драйв" in lower_name:
        return [t for t in CATALOG if "drive" in t.get("moods", []) or "energy" in t.get("moods", [])]
    elif "зарубеж" in lower_name or "world" in lower_name:
        return [t for t in CATALOG if t.get("category") == "world" or t.get("source") == "apple_us"]
    elif "яндекс" in lower_name:
        return [t for t in CATALOG if t.get("source") == "yandex"]
    return list(CATALOG)

def get_yandex_library():
    lib_file = os.path.join(os.path.dirname(__file__), "yandex_library.json")
    if os.path.exists(lib_file):
        try:
            with open(lib_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {{"liked_tracks": [], "playlists": []}}

def get_yandex_liked_tracks():
    return get_yandex_library().get("liked_tracks", [])

def get_yandex_playlists():
    return get_yandex_library().get("playlists", [])
'''

with open(cat_py_path, "w", encoding="utf-8") as f:
    f.write(cat_content)
print(f"[OK] Обновлен backend/catalog.py с {len(all_tracks)} треками!")
