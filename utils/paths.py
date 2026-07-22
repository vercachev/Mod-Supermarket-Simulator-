"""Пути сейвов Supermarket Together — канонический StoreFile, не backups."""

from __future__ import annotations

import re
from pathlib import Path


_STORE_STEM = re.compile(r"^(StoreFile\d+)", re.IGNORECASE)


def is_under_backups(path: Path) -> bool:
    return any(part.lower() == "backups" for part in path.parts)


def is_day_backup(path: Path) -> bool:
    return bool(re.search(r"Day\d+", path.stem, re.IGNORECASE))


def is_edited_name(path: Path) -> bool:
    return "_EDITED" in path.stem.upper()


def extract_store_stem(name: str) -> str | None:
    m = _STORE_STEM.match(name)
    return m.group(1) if m else None


def game_save_root(path: Path) -> Path:
    """Папка игры (родитель backups, если открыт бэкап)."""
    cur = path if path.is_dir() else path.parent
    while cur.name.lower() == "backups" and cur.parent != cur:
        cur = cur.parent
    return cur


def canonical_store_path(path: Path) -> Path:
    """
    Куда игра реально читает сейв.
    backups/StoreFile1_backup_....es3  →  ../StoreFile1.es3
    StoreFile1_EDITED.es3              →  StoreFile1.es3 (рядом)
    """
    path = Path(path)
    stem = extract_store_stem(path.stem)
    if stem is None:
        return path

    if is_under_backups(path):
        return game_save_root(path) / f"{stem}.es3"

    if is_edited_name(path) or "_backup_" in path.stem.lower():
        return path.with_name(f"{stem}.es3")

    if is_day_backup(path):
        # StoreFile1Day3.es3 → лучше править основной StoreFile1.es3
        return path.with_name(f"{stem}.es3")

    return path


def describe_path_risk(path: Path) -> str | None:
    if is_under_backups(path):
        return (
            "⚠ Это файл из папки backups — игра его НЕ читает.\n"
            f"Нужен: {canonical_store_path(path)}"
        )
    if is_edited_name(path):
        return (
            "⚠ Файл с именем _EDITED — подставьте его как StoreFileN.es3\n"
            "или нажмите «Применить к игре»."
        )
    if is_day_backup(path):
        return "⚠ Это Day-бэкап. Лучше править основной StoreFileN.es3."
    if path.suffix.lower() != ".es3":
        return "⚠ Ожидается файл .es3"
    return None
