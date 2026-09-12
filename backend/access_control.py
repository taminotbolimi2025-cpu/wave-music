import os
import json
import logging

from config import ADMIN_ID

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")
WHITELIST_FILE = os.path.join(BASE_DIR, "whitelist.json")


def _read_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.warning(f"Error reading {filepath}: {e}")
    return list(default)


def _write_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error writing {filepath}: {e}")


def get_admins() -> list:
    admins = _read_json(ADMINS_FILE, [ADMIN_ID])
    if ADMIN_ID not in admins:
        admins.insert(0, ADMIN_ID)
    return admins


def add_admin(user_id: int):
    admins = get_admins()
    if user_id not in admins:
        admins.append(user_id)
        _write_json(ADMINS_FILE, admins)
    add_to_whitelist(user_id)


def remove_admin(user_id: int):
    if user_id == ADMIN_ID:
        # Cannot remove the primary owner
        return False
    admins = get_admins()
    if user_id in admins:
        admins.remove(user_id)
        _write_json(ADMINS_FILE, admins)
        return True
    return False


def is_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    return user_id in get_admins()


def get_whitelist() -> list:
    wl = _read_json(WHITELIST_FILE, [ADMIN_ID])
    if ADMIN_ID not in wl:
        wl.insert(0, ADMIN_ID)
    for a in get_admins():
        if a not in wl:
            wl.append(a)
    return wl


def is_allowed(user_id: int) -> bool:
    """Allows all users so the bot works seamlessly across PC, iPhone, and Android, and registers them in whitelist"""
    if user_id:
        add_to_whitelist(user_id)
    return True


def add_to_whitelist(user_id: int):
    wl = get_whitelist()
    if user_id not in wl:
        wl.append(user_id)
        _write_json(WHITELIST_FILE, wl)


def remove_from_whitelist(user_id: int):
    if user_id == ADMIN_ID:
        return False
    wl = get_whitelist()
    if user_id in wl:
        wl.remove(user_id)
        _write_json(WHITELIST_FILE, wl)
        return True
    return False
