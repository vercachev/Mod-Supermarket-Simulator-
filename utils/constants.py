"""Константы Supermarket Together Save Editor."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Supermarket Together — Save Editor v1.0"
APP_TITLE = "SUPERMARKET TOGETHER — SAVE EDITOR"
WINDOW_SIZE = "740x620"

ACCENT = "#2E8B57"
ACCENT_HOVER = "#246B44"
STATUS_OK = "#2ECC71"
STATUS_WARN = "#F39C12"
STATUS_ERROR = "#E74C3C"
STATUS_IDLE = "#95A5A6"

# Публичный пароль ES3 для Supermarket Together (Steam guides)
ES3_PASSWORD = "g#asojrtg@omos)^yq"

GAME_PROCESS_NAMES = (
    "Supermarket Together.exe",
    "SupermarketTogether.exe",
    "Supermarket Together",
)

MAX_FUNDS = 1e15
MAX_INT_FIELD = 2_000_000_000

DEFAULT_EXPORT_DIR = os.path.expandvars(r"%USERPROFILE%\Downloads")

MESSAGES = {
    "no_file": "Сначала откройте StoreFile*.es3",
    "corrupt": (
        "❌ Не удалось расшифровать сейв.\n\n"
        "Нужен файл StoreFile0.es3 (и т.п.) из папки:\n"
        "AppData\\LocalLow\\DDTNL\\Supermarket Together\n\n"
        "Игра должна быть закрыта. Steam Cloud может мешать."
    ),
    "save_ok": "✅ Готово! Закройте игру и подмените файл сейва.",
    "not_loaded": "● Сейв не загружен",
    "load_ok": "● Сейв загружен",
    "game_running": (
        "⚠ Игра запущена. Закройте Supermarket Together,\n"
        "иначе Steam Cloud / игра перезапишет правки."
    ),
}


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def log_file_path() -> Path:
    return app_base_dir() / "editor.log"


def default_save_dirs() -> list[Path]:
    """Возможные пути сейвов (Windows LocalLow)."""
    home = Path.home()
    roots = [
        home / "AppData" / "LocalLow" / "DDTNL" / "Supermarket Together",
        home / "AppData" / "LocalLow" / "DDTNL" / "SupermarketTogether",
        # на случай опечатки из гайдов
        home / "AppData" / "LocalLow" / "DDNTL" / "Supermarket Together",
    ]
    # Linux/Wine
    wine = home / ".wine" / "drive_c" / "users"
    if wine.exists():
        for user_dir in wine.iterdir():
            roots.append(
                user_dir
                / "AppData"
                / "LocalLow"
                / "DDTNL"
                / "Supermarket Together"
            )
    return roots


def find_save_dir() -> Path | None:
    for d in default_save_dirs():
        if d.is_dir():
            return d
    return None


def list_store_files(folder: Path | None = None) -> list[Path]:
    folder = folder or find_save_dir()
    if folder is None or not folder.is_dir():
        return []
    files = sorted(folder.glob("StoreFile*.es3"))
    # без DayN-бэкапов на первом месте — основные слоты
    mains = [p for p in files if "Day" not in p.stem]
    days = [p for p in files if "Day" in p.stem]
    return mains + days
