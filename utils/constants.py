"""Константы Bitburner Save Editor."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Bitburner — Save Editor v1.0"
APP_TITLE = "⚡  BITBURNER — SAVE EDITOR"
WINDOW_SIZE = "900x650"

ACCENT_GREEN = "#2ECC71"
ACCENT_GREEN_HOVER = "#27AE60"
STATUS_OK = "#2ECC71"
STATUS_WARN = "#F39C12"
STATUS_ERROR = "#E74C3C"
STATUS_IDLE = "#95A5A6"
DANGER_RED = "#E74C3C"

# Папка загрузок — типичное место после Export save
DEFAULT_EXPORT_DIR = os.path.expandvars(r"%USERPROFILE%\Downloads")

GAME_PROCESS_NAMES = (
    "Bitburner.exe",
    "bitburner.exe",
    "Bitburner",
)

SKILL_KEYS: dict[str, str] = {
    "hacking": "Hacking",
    "strength": "Strength",
    "defense": "Defense",
    "dexterity": "Dexterity",
    "agility": "Agility",
    "charisma": "Charisma",
    "intelligence": "Intelligence",
}

MAX_MONEY = 1e33  # достаточно для mid/late game
MAX_SKILL = 1_000_000
MAX_BITNODE = 14
MIN_BITNODE = 1

EXPLOIT_EDIT_SAVE = "EditSaveFile"

MESSAGES = {
    "file_not_found": "❌ Файл сохранения не найден.",
    "file_corrupt": (
        "❌ Не удалось прочитать сейв Bitburner.\n\n"
        "Нужен файл из игры: Options → Export game / Export save\n"
        "(обычно bitburnerSave_....json или .json.gz)."
    ),
    "game_running": (
        "⚠️ Кажется, Bitburner запущен. Лучше закрыть игру перед импортом сейва."
    ),
    "invalid_number": "❌ Введите корректное число (от {min_v} до {max_v})",
    "save_ok": "✅ Файл обновлён! Бэкап создан. Импортируйте сейв обратно в игру.",
    "backup_ok": "✅ Резервная копия создана: {name}",
    "restore_ok": "✅ Восстановлено из резервной копии от {date}",
    "no_file": "Сначала откройте экспортированный сейв Bitburner.",
    "json_invalid": "❌ Неверный JSON. Изменения не применены.",
    "load_ok": "● Файл загружен: {name}",
    "not_loaded": "● Файл не загружен",
}


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def log_file_path() -> Path:
    return app_base_dir() / "editor.log"
