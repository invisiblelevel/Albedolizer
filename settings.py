"""
settings.py — загрузка и сохранение пользовательских настроек.
Хранит config.json в %APPDATA%/Albedolizer/ (Windows) или в домашней папке.
"""

import os
import sys
import json


def get_settings_dir():
    """Возвращает путь к папке для настроек. Создаёт её, если нет."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    path = os.path.join(base, "Albedolizer")
    os.makedirs(path, exist_ok=True)
    return path


SETTINGS_FILE = os.path.join(get_settings_dir(), "config.json")


DEFAULT_SETTINGS = {
    "lang": "ru",
    "theme": "dark",
    "ui_mode": "simple",
    "profile": "metal",
    "profile_category": "metal",
    "correction_mode": "ai",
    "soap_fix_strength": 1.0,
    "saturation_boost": 1.15,
    "pbr_bit_depth": 8,
    "window": {
        "width": 1280,
        "height": 820
    }
}


def load_settings():
    """Загружает настройки. Если файла нет или он битый — возвращает дефолт."""
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_SETTINGS)

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Мержим с дефолтом — если новых ключей нет, добавим
        result = dict(DEFAULT_SETTINGS)
        result.update(data)
        # Для вложенных словарей — тоже мерж
        if "window" in data:
            result["window"] = {**DEFAULT_SETTINGS["window"], **data["window"]}
        return result
    except Exception as e:
        print(f"⚠ Не удалось загрузить настройки: {e}")
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    """Сохраняет настройки в config.json."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠ Не удалось сохранить настройки: {e}")
        return False