import os
import json
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")
WHITELIST_FILE = os.path.join(BASE_DIR, "whitelist.json")


def _read_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading {filepath}: {e}")
    return default


def _write_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error writing {filepath}: {e}")


def get_admins() -> list:
    return _read_json(ADMINS_FILE, [])


def add_admin(user_id: int):
    admins = get_admins()
    if user_id not in admins:
        admins.append(user_id)
        _write_json(ADMINS_FILE, admins)
    # Admin is automatically whitelisted
    add_to_whitelist(user_id)


def is_admin(user_id: int) -> bool:
    admins = get_admins()
    return user_id in admins


def get_whitelist() -> list:
    return _read_json(WHITELIST_FILE, [])


def is_allowed(user_id: int) -> bool:
    admins = get_admins()
    if not admins:
        # If no admins configured yet, first user who interacts will become admin
        return True
    if user_id in admins:
        return True
    whitelist = get_whitelist()
    return user_id in whitelist


def add_to_whitelist(user_id: int):
    wl = get_whitelist()
    if user_id not in wl:
        wl.append(user_id)
        _write_json(WHITELIST_FILE, wl)


def remove_from_whitelist(user_id: int):
    wl = get_whitelist()
    if user_id in wl:
        wl.remove(user_id)
        _write_json(WHITELIST_FILE, wl)
