"""
categorizer/settings.py
------------------------
Persistent user settings stored in a simple JSON file.
Saves Gemini API key, browser preference, etc. locally.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

SETTINGS_DIR = Path.home() / ".config" / "ConradKategorisierer"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

_DEFAULTS: dict = {
    "gemini_api_key": "",
    "gemini_model": "gemini-2.0-flash",
    "browser_mode": "auto",   # "auto", "comet", "chrome"
    "use_gemini": False,
    "use_browser": False,
}


def load() -> dict:
    """Load settings from disk, returning defaults for any missing key."""
    settings = dict(_DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                stored = json.load(f)
            settings.update({k: v for k, v in stored.items() if k in _DEFAULTS})
        except Exception:
            pass
    return settings


def save(settings: dict) -> None:
    """Persist settings to disk."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get(key: str, default=None):
    """Convenience: load and return a single key."""
    return load().get(key, default)
