"""Парсинг/запись экспорта Cookie Clicker."""

from __future__ import annotations

import base64
import logging
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, quote

from utils.constants import MESSAGES

logger = logging.getLogger(__name__)


@dataclass
class FileMeta:
    path: Path | None = None
    size: int = 0
    modified: datetime | None = None
    version: str = ""
    bakery_name: str = ""


@dataclass
class SaveSnapshot:
    cookies: float = 0.0
    cookies_earned: float = 0.0
    cookie_clicks: int = 0
    bakery_name: str = ""
    version: str = ""


def _js_escape(s: str) -> str:
    """Приближение JS escape() для ASCII/UTF-8 сейвов."""
    out: list[str] = []
    for ch in s:
        o = ord(ch)
        if ch.isalnum() or ch in "@*_+-./":
            out.append(ch)
        elif o < 256:
            out.append(f"%{o:02X}")
        else:
            out.append(f"%u{o:04X}")
    return "".join(out)


def _js_unescape(s: str) -> str:
    # Сначала %uXXXX, потом %XX (как JS unescape)
    def repl_u(m: re.Match[str]) -> str:
        return chr(int(m.group(1), 16))

    s = re.sub(r"%u([0-9A-Fa-f]{4})", repl_u, s)

    def repl(m: re.Match[str]) -> str:
        return chr(int(m.group(1), 16))

    return re.sub(r"%([0-9A-Fa-f]{2})", repl, s)


def utf8_to_b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def b64_to_utf8(text: str) -> str:
    # убрать пробелы/переносы
    compact = "".join(text.split())
    # иногда URL-safe
    compact = compact.replace("-", "+").replace("_", "/")
    pad = (-len(compact)) % 4
    if pad:
        compact += "=" * pad
    return base64.b64decode(compact).decode("utf-8")


class SaveHandler:
    """Cookie Clicker export string / .txt file."""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.sections: list[str] = []
        self.meta = FileMeta()
        self._export_escaped = True  # как Export save в игре
        self._original_sections: list[str] = []
        self.raw_export: str = ""

    def load_text(self, text: str, path: Path | None = None) -> None:
        text = text.strip()
        if not text:
            raise ValueError(MESSAGES["corrupt"])

        # Снять escape, если есть
        working = text
        if "%21END%21" in working.upper() or "%3D" in working.upper() or "%21" in working:
            working = _js_unescape(working)
            self._export_escaped = True
        elif "!END!" in working:
            self._export_escaped = False
        else:
            # попробуем как сырой base64 без маркера
            self._export_escaped = True

        if "!END!" in working:
            working = working.split("!END!")[0]

        try:
            plain = b64_to_utf8(working)
        except Exception as exc:  # noqa: BLE001
            # может уже plain с пайпами
            if "|" in text and text.split("|")[0].replace(".", "", 1).isdigit():
                plain = text
            else:
                raise ValueError(MESSAGES["corrupt"]) from exc

        parts = plain.split("|")
        if len(parts) < 5:
            raise ValueError(MESSAGES["corrupt"])

        self.sections = parts
        self._original_sections = list(parts)
        self.raw_export = text
        self.path = path
        snap = self.get_snapshot()
        self.meta = FileMeta(
            path=path,
            size=path.stat().st_size if path and path.exists() else len(text.encode("utf-8")),
            modified=datetime.fromtimestamp(path.stat().st_mtime) if path and path.exists() else datetime.now(),
            version=snap.version,
            bakery_name=snap.bakery_name,
        )
        logger.info("Cookie Clicker сейв загружен (v%s, cookies=%g)", snap.version, snap.cookies)

    def load(self, path: Path | str) -> None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(MESSAGES["corrupt"])
        raw = path.read_bytes()
        # .cki иногда бинарный/тот же текст
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        self.load_text(text, path)

    def get_snapshot(self) -> SaveSnapshot:
        version = self.sections[0] if self.sections else ""
        bakery = ""
        if len(self.sections) > 2:
            run = self.sections[2].split(";")
            if len(run) > 3:
                bakery = run[3]
        cookies = 0.0
        earned = 0.0
        clicks = 0
        if len(self.sections) > 4:
            misc = self.sections[4].split(";")
            if misc:
                try:
                    cookies = float(misc[0] or 0)
                except ValueError:
                    cookies = 0.0
            if len(misc) > 1:
                try:
                    earned = float(misc[1] or 0)
                except ValueError:
                    earned = 0.0
            if len(misc) > 2:
                try:
                    clicks = int(float(misc[2] or 0))
                except ValueError:
                    clicks = 0
        return SaveSnapshot(
            cookies=cookies,
            cookies_earned=earned,
            cookie_clicks=clicks,
            bakery_name=bakery,
            version=version,
        )

    def set_cookies(self, cookies: float, *, bump_earned: bool = True) -> None:
        if len(self.sections) <= 4:
            raise ValueError(MESSAGES["corrupt"])
        misc = self.sections[4].split(";")
        while len(misc) < 2:
            misc.append("0")
        misc[0] = self._fmt(cookies)
        if bump_earned:
            try:
                earned = float(misc[1] or 0)
            except ValueError:
                earned = 0.0
            if cookies > earned:
                misc[1] = self._fmt(cookies)
        self.sections[4] = ";".join(misc)

    @staticmethod
    def _fmt(num: float) -> str:
        # как JS parseFloat(...).toString()
        if float(num).is_integer() and abs(num) < 1e21:
            return str(int(num))
        return format(float(num), ".15g")

    def to_plain(self) -> str:
        return "|".join(self.sections)

    def to_export_string(self) -> str:
        b64 = utf8_to_b64(self.to_plain()) + "!END!"
        if self._export_escaped:
            return _js_escape(b64)
        return b64

    def save(self, path: Path | None = None) -> Path:
        dest = Path(path) if path else self.path
        if dest is None:
            dest = Path.home() / "Downloads" / "cookie_clicker_EDITED.txt"
            dest.parent.mkdir(parents=True, exist_ok=True)
        text = self.to_export_string()
        dest.write_text(text, encoding="utf-8")
        self.path = dest
        self.meta.path = dest
        self.meta.size = dest.stat().st_size
        self.meta.modified = datetime.fromtimestamp(dest.stat().st_mtime)
        # verify
        check = SaveHandler()
        check.load(dest)
        expected = self.get_snapshot().cookies
        actual = check.get_snapshot().cookies
        if abs(actual - expected) > max(1.0, abs(expected) * 1e-9):
            raise ValueError(f"Проверка не прошла: ждали {expected:g}, в файле {actual:g}")
        logger.info("Cookie Clicker сейв записан: %s (cookies=%g)", dest, actual)
        return dest

    def reset_to_loaded(self) -> None:
        self.sections = list(self._original_sections)

    def suggested_edited_path(self) -> Path:
        from utils.constants import DEFAULT_EXPORT_DIR

        folder = Path(DEFAULT_EXPORT_DIR)
        if not folder.exists():
            folder = Path.home()
        name = "cookie_clicker_EDITED.txt"
        if self.meta.bakery_name:
            safe = re.sub(r"[^\w\-]+", "", self.meta.bakery_name.replace(" ", ""))[:40]
            if safe:
                name = f"{safe}_EDITED.txt"
        return folder / name
