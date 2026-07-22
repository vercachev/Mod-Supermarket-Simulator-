"""Парсинг/запись сейвов Supermarket Together (.es3).

Важно: значения правятся хирургически в исходном plaintext ES3,
чтобы не ломать остальной JSON полной пересборкой.
"""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.constants import DEFAULT_EXPORT_DIR, ES3_PASSWORD, MESSAGES
from utils.es3_crypto import (
    decrypt_raw,
    encrypt,
    looks_like_json,
    try_decompress,
)
from utils.paths import canonical_store_path, describe_path_risk, is_under_backups

logger = logging.getLogger(__name__)


@dataclass
class FileMeta:
    path: Path | None = None
    size: int = 0
    modified: datetime | None = None
    store_name: str = ""
    encrypted: bool = True
    key_size: int = 16
    risk: str = ""


@dataclass
class SaveSnapshot:
    funds: float = 0.0
    day: int = 0
    store_name: str = ""
    supermarket_name: str = ""
    franchise_experience: int = 0
    franchise_points: int = 0
    last_awarded_level: int = 0


def _to_text(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _extract_plaintext(raw: bytes, password: str) -> tuple[str, bool, int, bool]:
    """Return (text, encrypted, key_size, was_compressed)."""
    if looks_like_json(raw):
        return _to_text(raw), False, 16, False

    pt, ks = decrypt_raw(raw, password)
    if pt is None:
        raise ValueError(MESSAGES["corrupt"])
    key_size = ks or 16

    if looks_like_json(pt):
        return _to_text(pt), True, key_size, False

    decompressed = try_decompress(pt)
    if decompressed is not None and looks_like_json(decompressed):
        return _to_text(decompressed), True, key_size, True

    # иногда JSON с BOM/мусором
    text = _to_text(pt).strip()
    if text.startswith("{") or text.startswith("["):
        return text, True, key_size, False
    raise ValueError(MESSAGES["corrupt"])


def _parse_json_text(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(MESSAGES["corrupt"]) from exc
    if not isinstance(data, dict):
        raise ValueError(MESSAGES["corrupt"])
    return data


def get_es3_value(data: dict[str, Any], key: str, default: Any = None) -> Any:
    if key not in data:
        return default
    node = data[key]
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def set_es3_value(
    data: dict[str, Any],
    key: str,
    value: Any,
    *,
    type_name: str | None = None,
) -> None:
    node = data.get(key)
    if isinstance(node, dict) and "value" in node:
        node["value"] = value
        if type_name and "__type" not in node:
            node["__type"] = type_name
        return
    if type_name is None:
        if isinstance(value, bool):
            type_name = "bool"
        elif isinstance(value, int) and not isinstance(value, bool):
            type_name = "int"
        elif isinstance(value, float):
            type_name = "float"
        else:
            type_name = "string"
    data[key] = {"__type": type_name, "value": value}


def _format_json_number(value: float | int) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    f = float(value)
    if f != f:  # NaN
        raise ValueError("NaN")
    if f == int(f) and abs(f) < 1e15:
        return str(int(f))
    return format(f, ".15g")


def patch_es3_numeric_field(text: str, key: str, value: float | int) -> str:
    """Заменить только value у ключа ES3, сохранив остальной текст."""
    repl = _format_json_number(value)
    pattern = re.compile(
        rf'("{re.escape(key)}"\s*:\s*\{{[^{{}}]*?"value"\s*:\s*)'
        rf'(-?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?)',
        re.DOTALL,
    )
    new_text, count = pattern.subn(rf"\g<1>{repl}", text, count=1)
    if count != 1:
        raise ValueError(f"Не найден ключ {key} в сейве для правки")
    return new_text


def patch_es3_string_field(text: str, key: str, value: str) -> str:
    escaped = json.dumps(value, ensure_ascii=False)[1:-1]
    pattern = re.compile(
        rf'("{re.escape(key)}"\s*:\s*\{{[^{{}}]*?"value"\s*:\s*)"([^"\\]|\\.)*"',
        re.DOTALL,
    )
    new_text, count = pattern.subn(rf'\g<1>"{escaped}"', text, count=1)
    if count != 1:
        raise ValueError(f"Не найден ключ {key} в сейве для правки")
    return new_text


class SaveHandler:
    """Supermarket Together StoreFile*.es3 (Easy Save 3)."""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.data: dict[str, Any] = {}
        self._original: dict[str, Any] = {}
        self._plain_text: str = ""
        self._pending: dict[str, Any] = {}
        self.meta = FileMeta()
        self._was_encrypted = True
        self._key_size = 16
        self._plaintext_was_compressed = False

    def load(self, path: Path | str) -> None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(MESSAGES["corrupt"])
        raw = path.read_bytes()
        self._load_bytes(raw, path)

    def load_bytes(self, raw: bytes, path: Path | None = None) -> None:
        self._load_bytes(raw, path)

    def _load_bytes(self, raw: bytes, path: Path | None) -> None:
        text, encrypted, key_size, compressed = _extract_plaintext(raw, ES3_PASSWORD)
        data = _parse_json_text(text)

        if "Funds" not in data and "StoreName" not in data and "Day" not in data:
            if len(data) < 2:
                raise ValueError(MESSAGES["corrupt"])

        self.data = data
        self._original = deepcopy(data)
        self._plain_text = text
        self._pending = {}
        self.path = path
        self._was_encrypted = encrypted
        self._key_size = key_size
        self._plaintext_was_compressed = compressed
        snap = self.get_snapshot()
        risk = describe_path_risk(path) if path else ""
        self.meta = FileMeta(
            path=path,
            size=path.stat().st_size if path and path.exists() else len(raw),
            modified=(
                datetime.fromtimestamp(path.stat().st_mtime)
                if path and path.exists()
                else datetime.now()
            ),
            store_name=snap.store_name or snap.supermarket_name,
            encrypted=encrypted,
            key_size=key_size,
            risk=risk or "",
        )
        if path and path.stat().st_size < 400:
            logger.warning("Подозрительно маленький сейв: %s (%s байт)", path, path.stat().st_size)
        logger.info(
            "Together сейв загружен: funds=%s day=%s name=%s path=%s",
            snap.funds,
            snap.day,
            self.meta.store_name,
            path,
        )

    def get_snapshot(self) -> SaveSnapshot:
        def as_float(v: Any) -> float:
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        def as_int(v: Any) -> int:
            try:
                return int(float(v))
            except (TypeError, ValueError):
                return 0

        def as_str(v: Any) -> str:
            return "" if v is None else str(v)

        return SaveSnapshot(
            funds=as_float(get_es3_value(self.data, "Funds", 0)),
            day=as_int(get_es3_value(self.data, "Day", 0)),
            store_name=as_str(get_es3_value(self.data, "StoreName", "")),
            supermarket_name=as_str(get_es3_value(self.data, "SupermarketName", "")),
            franchise_experience=as_int(
                get_es3_value(self.data, "FranchiseExperience", 0)
            ),
            franchise_points=as_int(get_es3_value(self.data, "FranchisePoints", 0)),
            last_awarded_level=as_int(get_es3_value(self.data, "LastAwardedLevel", 0)),
        )

    def set_funds(self, funds: float) -> None:
        set_es3_value(self.data, "Funds", float(funds), type_name="float")
        self._pending["Funds"] = float(funds)

    def set_franchise_experience(self, value: int) -> None:
        set_es3_value(self.data, "FranchiseExperience", int(value), type_name="int")
        self._pending["FranchiseExperience"] = int(value)

    def set_franchise_points(self, value: int) -> None:
        set_es3_value(self.data, "FranchisePoints", int(value), type_name="int")
        self._pending["FranchisePoints"] = int(value)

    def set_last_awarded_level(self, value: int) -> None:
        set_es3_value(self.data, "LastAwardedLevel", int(value), type_name="int")
        self._pending["LastAwardedLevel"] = int(value)

    def set_store_name(self, name: str) -> None:
        set_es3_value(self.data, "StoreName", str(name), type_name="string")
        self._pending["StoreName"] = str(name)
        if "SupermarketName" in self.data:
            set_es3_value(self.data, "SupermarketName", str(name), type_name="string")
            self._pending["SupermarketName"] = str(name)

    def build_plaintext(self) -> str:
        if not self._plain_text:
            return json.dumps(self.data, indent=4, ensure_ascii=False) + "\n"

        text = self._plain_text
        for key, value in self._pending.items():
            if isinstance(value, str):
                text = patch_es3_string_field(text, key, value)
            else:
                text = patch_es3_numeric_field(text, key, value)

        # sanity: JSON still parses and Funds matches
        parsed = _parse_json_text(text)
        if "Funds" in self._pending:
            got = get_es3_value(parsed, "Funds")
            if abs(float(got) - float(self._pending["Funds"])) > 0.01:
                raise ValueError("Проверка Funds после патча не прошла")
        return text

    def to_file_bytes(self) -> bytes:
        plain = self.build_plaintext().encode("utf-8")
        if not self._was_encrypted:
            return plain
        # сжатие обратно не включаем: игра принимает обычный JSON в AES
        return encrypt(plain, ES3_PASSWORD, key_size=self._key_size)

    def target_game_path(self) -> Path | None:
        if self.path is None:
            return None
        return canonical_store_path(self.path)

    def save(self, path: Path | None = None) -> Path:
        dest = Path(path) if path else self.path
        if dest is None:
            dest = Path(DEFAULT_EXPORT_DIR) / "StoreFile0_EDITED.es3"
            dest.parent.mkdir(parents=True, exist_ok=True)
        if is_under_backups(dest):
            raise ValueError(
                "Нельзя сохранять в папку backups — игра этот файл не читает.\n"
                f"Сохраните в: {canonical_store_path(dest)}"
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        blob = self.to_file_bytes()
        dest.write_bytes(blob)

        check = SaveHandler()
        check.load(dest)
        expected = self.get_snapshot().funds
        actual = check.get_snapshot().funds
        if abs(actual - expected) > max(0.01, abs(expected) * 1e-6):
            raise ValueError(
                f"Проверка не прошла: ждали Funds={expected}, в файле {actual}"
            )

        # обновить локальный plaintext после успешной записи
        self._plain_text = check._plain_text
        self._pending = {}
        self.data = check.data
        self.path = dest
        self.meta.path = dest
        self.meta.size = dest.stat().st_size
        self.meta.modified = datetime.fromtimestamp(dest.stat().st_mtime)
        self.meta.risk = describe_path_risk(dest) or ""
        logger.info("Together сейв записан: %s (Funds=%s, %s байт)", dest, actual, self.meta.size)
        return dest

    def reset_to_loaded(self) -> None:
        self.data = deepcopy(self._original)
        self._pending = {}

    def suggested_edited_path(self) -> Path:
        folder = Path(DEFAULT_EXPORT_DIR)
        if not folder.exists():
            folder = Path.home()
        base = "StoreFile0"
        if self.path is not None:
            stem = extract_store_stem_safe(self.path.stem) or self.path.stem
            base = stem
        safe = re.sub(r"[^\w\-]+", "_", base)[:48] or "StoreFile"
        return folder / f"{safe}_EDITED.es3"


def extract_store_stem_safe(name: str) -> str | None:
    from utils.paths import extract_store_stem

    return extract_store_stem(name)
