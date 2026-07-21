"""Константы Cookie Clicker Save Editor."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Cookie Clicker — Save Editor v1.0"
APP_TITLE = "🍪  COOKIE CLICKER — SAVE EDITOR"
WINDOW_SIZE = "720x560"

ACCENT = "#E67E22"
ACCENT_HOVER = "#D35400"
STATUS_OK = "#2ECC71"
STATUS_WARN = "#F39C12"
STATUS_ERROR = "#E74C3C"
STATUS_IDLE = "#95A5A6"

DEFAULT_EXPORT_DIR = os.path.expandvars(r"%USERPROFILE%\Downloads")

MAX_COOKIES = 1e308  # JS Number.MAX_VALUE порядка

MESSAGES = {
    "no_file": "Сначала вставьте или откройте сейв Cookie Clicker.",
    "corrupt": (
        "❌ Не удалось прочитать сейв.\n\n"
        "В игре: Options → Export save / Save to file\n"
        "и откройте этот текст/файл здесь."
    ),
    "save_ok": "✅ Готово! Теперь в игре: Options → Import save (вставьте код).",
    "not_loaded": "● Сейв не загружен",
    "load_ok": "● Сейв загружен",
}


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def log_file_path() -> Path:
    return app_base_dir() / "editor.log"
