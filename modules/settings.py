"""Ajustes que BMO recuerda entre reinicios (volumen, ciudad del clima...). Se guardan en JSON."""
import json
import os
import threading

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bmo_settings.json")
_lock = threading.Lock()


def _load():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def get(key, default=None):
    with _lock:
        return _load().get(key, default)


def set(key, value):
    with _lock:
        data = _load()
        data[key] = value
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[!] No se pudieron guardar los ajustes: {e}")
