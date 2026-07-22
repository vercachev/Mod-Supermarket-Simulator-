"""Парсинг/запись сейвов Supermarket Together (.es3)."""

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

logger = logging.getLogger(__name__)


@dataclass
class FileMeta:
    path: Path | None = None
    size: int = 0
    modified: datetime | None = None
    store_name: str = ""
    encrypted: bool = True
    key_size: int = 16


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


def _parse_json_bytes(raw: bytes) -> dict[str, Any]:
    candidates = [raw]
    decompressed = try_decompress(raw)
    if decompressed is not None:
        candidates.insert(0, decompressed)
    last_err: Exception | None = None
    for blob in candidates:
        text = _to_text(blob).strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            last_err = exc
            continue
        if isinstance(data, dict):
            return data
    raise ValueError(MESSAGES["corrupt"]) from last_err


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


class SaveHandler:
    """Supermarket Together StoreFile*.es3 (Easy Save 3)."""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.data: dict[str, Any] = {}
        self._original: dict[str, Any] = {}
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
        encrypted = True
        key_size = 16
        if looks_like_json(raw):
            data = _parse_json_bytes(raw)
            encrypted = False
        else:
            pt, ks = decrypt_raw(raw, ES3_PASSWORD)
            if pt is None:
                raise ValueError(MESSAGES["corrupt"])
            key_size = ks or 16
            # если после decrypt сразу JSON — ок; иначе попробуем decompress
            try:
                data = _parse_json_bytes(pt)
                if try_decompress(pt) is not None and not looks_like_json(pt):
                    self._plaintext_was_compressed = True
            except ValueError:
                raise
        if "Funds" not in data and "StoreName" not in data and "Day" not in data:
            # похоже не тот сейв, но всё же позволим если есть хоть ключи
            if len(data) < 2:
                raise ValueError(MESSAGES["corrupt"])

        self.data = data
        self._original = deepcopy(data)
        self.path = path
        self._was_encrypted = encrypted
        self._key_size = key_size
        snap = self.get_snapshot()
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
        )
        logger.info(
            "Together сейв загружен: funds=%s day=%s name=%s encrypted=%s",
            snap.funds,
            snap.day,
            self.meta.store_name,
            encrypted,
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

    def set_day(self, day: int) -> None:
        set_es3_value(self.data, "Day", int(day), type_name="int")

    def set_franchise_experience(self, value: int) -> None:
        set_es3_value(self.data, "FranchiseExperience", int(value), type_name="int")

    def set_franchise_points(self, value: int) -> None:
        set_es3_value(self.data, "FranchisePoints", int(value), type_name="int")

    def set_last_awarded_level(self, value: int) -> None:
        set_es3_value(self.data, "LastAwardedLevel", int(value), type_name="int")

    def set_store_name(self, name: str) -> None:
        set_es3_value(self.data, "StoreName", str(name), type_name="string")
        # часто дублируется
        if "SupermarketName" in self.data:
            set_es3_value(self.data, "SupermarketName", str(name), type_name="string")

    def to_json_bytes(self) -> bytes:
        text = json.dumps(self.data, indent=4, ensure_ascii=False)
        # ES3 обычно без финального переноса критичен, но \n ок
        return (text + "\n").encode("utf-8")

    def to_file_bytes(self) -> bytes:
        plain = self.to_json_bytes()
        if not self._was_encrypted:
            return plain
        return encrypt(plain, ES3_PASSWORD, key_size=self._key_size)

    def save(self, path: Path | None = None) -> Path:
        dest = Path(path) if path else self.path
        if dest is None:
            dest = Path(DEFAULT_EXPORT_DIR) / "StoreFile0_EDITED.es3"
            dest.parent.mkdir(parents=True, exist_ok=True)
        blob = self.to_file_bytes()
        dest.write_bytes(blob)
        # verify round-trip
        check = SaveHandler()
        check.load(dest)
        expected = self.get_snapshot().funds
        actual = check.get_snapshot().funds
        if abs(actual - expected) > max(0.01, abs(expected) * 1e-6):
            raise ValueError(
                f"Проверка не прошла: ждали Funds={expected}, в файле {actual}"
            )
        self.path = dest
        self.meta.path = dest
        self.meta.size = dest.stat().st_size
        self.meta.modified = datetime.fromtimestamp(dest.stat().st_mtime)
        logger.info("Together сейв записан: %s (Funds=%s)", dest, actual)
        return dest

    def reset_to_loaded(self) -> None:
        self.data = deepcopy(self._original)

    def suggested_edited_path(self) -> Path:
        folder = Path(DEFAULT_EXPORT_DIR)
        if not folder.exists():
            folder = Path.home()
        base = "StoreFile0"
        if self.path is not None:
            base = self.path.stem
        safe = re.sub(r"[^\w\-]+", "_", base)[:48] or "StoreFile"
        return folder / f"{safe}_EDITED.es3"
