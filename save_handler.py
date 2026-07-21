"""Чтение, парсинг и запись файлов Easy Save 3 (.es3)."""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.constants import (
    ALL_LICENSE_IDS,
    BASIC_LICENSE_ID,
    DEFAULT_SAVE_FILENAMES,
    DEFAULT_SAVE_PATH,
    FIELD_ALIASES,
    GAME_PROCESS_NAMES,
    MESSAGES,
)

logger = logging.getLogger(__name__)


@dataclass
class FileMeta:
    path: Path | None = None
    size: int = 0
    modified: datetime | None = None
    game_version: str | None = None
    format_kind: str = "unknown"  # json | es3_typed | raw


@dataclass
class SaveSnapshot:
    """Снимок редактируемых полей для UI."""

    money: float = 0.0
    store_name: str = ""
    day: int = 1
    licenses: list[int] = field(default_factory=lambda: [BASIC_LICENSE_ID])
    checkout_count: int | None = None
    shelf_count: int | None = None
    employee_count: int | None = None
    completed_checkouts: int | None = None
    store_level: int | None = None
    store_upgrade: int | None = None


class SaveHandler:
    """Работа с .es3 сохранениями Supermarket Simulator."""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.data: dict[str, Any] = {}
        self.raw_text: str = ""
        self.meta = FileMeta()
        self._original_data: dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # Обнаружение файлов
    # ------------------------------------------------------------------ #
    @staticmethod
    def default_save_dir() -> Path:
        return Path(DEFAULT_SAVE_PATH).resolve()

    @classmethod
    def candidate_save_dirs(cls) -> list[Path]:
        """Папки, где могут лежать сохранения (Steam + Xbox Game Pass)."""
        from utils.constants import XBOX_PACKAGE_NAME_HINT, XBOX_PACKAGES_ROOT

        dirs: list[Path] = []
        steam_dir = cls.default_save_dir()
        if steam_dir.exists():
            dirs.append(steam_dir)

        packages = Path(XBOX_PACKAGES_ROOT)
        if packages.exists():
            for pkg in packages.glob(f"*{XBOX_PACKAGE_NAME_HINT}*"):
                wgs = pkg / "SystemAppData" / "wgs"
                if wgs.exists():
                    dirs.append(wgs)
                    # Вложенные контейнеры Xbox
                    for child in wgs.iterdir():
                        if child.is_dir():
                            dirs.append(child)

        # Уникальные пути с сохранением порядка
        unique: list[Path] = []
        seen: set[Path] = set()
        for d in dirs:
            resolved = d.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique.append(resolved)
        return unique

    @staticmethod
    def _looks_like_save_text(path: Path) -> bool:
        """Проверяет, похож ли файл без .es3 на JSON-сейв игры."""
        try:
            if path.stat().st_size < 20 or path.stat().st_size > 50_000_000:
                return False
            sample = path.read_bytes()[:4096]
            if b"\x00" in sample[:64]:
                return False
            text = sample.decode("utf-8", errors="ignore")
            return ("Money" in text or "Progression" in text or "UnlockedLicenses" in text) and "{" in text
        except OSError:
            return False

    @classmethod
    def find_default_saves(cls) -> list[Path]:
        """Ищет сохранения в Steam LocalLow и Xbox Packages/wgs."""
        found: list[Path] = []
        seen: set[Path] = set()

        def add(path: Path) -> None:
            resolved = path.resolve()
            if resolved in seen or not path.is_file():
                return
            if "backup" in path.name.lower():
                return
            seen.add(resolved)
            found.append(path)

        roots = cls.candidate_save_dirs()
        if not roots:
            logger.info("Папки сохранений не найдены (ни Steam, ни Xbox)")
            return found

        for root in roots:
            for name in DEFAULT_SAVE_FILENAMES:
                add(root / name)

            for path in root.glob("*.es3"):
                add(path)

            # Xbox WGS: файлы часто без расширения, с hex-именами
            for path in root.iterdir():
                if path.is_file() and path.suffix.lower() != ".es3":
                    if cls._looks_like_save_text(path):
                        add(path)

        found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return found

    # ------------------------------------------------------------------ #
    # Парсинг ES3
    # ------------------------------------------------------------------ #
    @staticmethod
    def unwrap_es3(node: Any) -> Any:
        """Разворачивает обёртки {__type, value}."""
        if isinstance(node, dict) and "__type" in node and "value" in node:
            return SaveHandler.unwrap_es3(node["value"])
        if isinstance(node, dict):
            return {k: SaveHandler.unwrap_es3(v) for k, v in node.items()}
        if isinstance(node, list):
            return [SaveHandler.unwrap_es3(v) for v in node]
        return node

    @staticmethod
    def parse_es3_value(data: dict[str, Any], key: str) -> Any:
        """Извлекает значение из ES3 структуры, обрабатывая __type обёртки."""
        if key not in data:
            return None
        val = data[key]
        if isinstance(val, dict) and "__type" in val:
            return val.get("value")
        return val

    @staticmethod
    def set_es3_value(data: dict[str, Any], key: str, new_value: Any) -> None:
        """Устанавливает значение, сохраняя ES3 структуру."""
        if key in data and isinstance(data[key], dict) and "__type" in data[key]:
            data[key]["value"] = new_value
        else:
            data[key] = new_value

    def _detect_format(self, text: str, data: dict[str, Any] | None) -> str:
        if data is None:
            return "raw"
        for value in data.values():
            if isinstance(value, dict) and "__type" in value:
                return "es3_typed"
        return "json"

    def _try_load_json(self, text: str) -> dict[str, Any] | None:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return None

    def _extract_json_via_regex(self, text: str) -> dict[str, Any] | None:
        """Пытается вытащить JSON-объект из текста с мусором вокруг."""
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        return self._try_load_json(match.group(0))

    def load(self, path: Path | str) -> None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(MESSAGES["file_not_found"])

        # Бинарные/зашифрованные файлы — не текст
        raw_bytes = path.read_bytes()
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw_bytes.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise ValueError(MESSAGES["file_corrupt"]) from exc

        if "\x00" in text[:200] or not text.strip().startswith(("{", "[", '"')):
            # Может быть валидный JSON с BOM/пробелами
            stripped = text.lstrip("\ufeff \t\r\n")
            if not stripped.startswith(("{", "[")):
                raise ValueError(MESSAGES["file_corrupt"])

        data = self._try_load_json(text)
        if data is None:
            data = self._extract_json_via_regex(text)
        if data is None:
            raise ValueError(MESSAGES["file_corrupt"])

        self.path = path
        self.raw_text = text
        self.data = data
        self._original_data = deepcopy(data)
        self.meta = FileMeta(
            path=path,
            size=path.stat().st_size,
            modified=datetime.fromtimestamp(path.stat().st_mtime),
            game_version=self._find_game_version(data),
            format_kind=self._detect_format(text, data),
        )
        logger.info("Загружен файл %s (формат: %s)", path, self.meta.format_kind)

    def reload(self) -> None:
        if not self.path:
            raise FileNotFoundError(MESSAGES["no_file"])
        self.load(self.path)

    # ------------------------------------------------------------------ #
    # Поиск / установка значений по дереву
    # ------------------------------------------------------------------ #
    def _walk(self, node: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
        results: list[tuple[tuple[str, ...], Any]] = []
        if isinstance(node, dict):
            # Не спускаемся только в value обёртки — обходим и их
            for key, value in node.items():
                if key == "__type":
                    continue
                cur = path + (key,)
                results.append((cur, value))
                results.extend(self._walk(value, cur))
        elif isinstance(node, list):
            for idx, value in enumerate(node):
                cur = path + (str(idx),)
                results.extend(self._walk(value, cur))
        return results

    def find_first(self, *keys: str) -> tuple[tuple[str, ...] | None, Any]:
        """Ищет первое вхождение любого из ключей в дереве данных."""
        wanted = set(keys)
        for path, value in self._walk(self.data):
            if path and path[-1] in wanted:
                # Если это ES3 обёртка — вернём value
                if isinstance(value, dict) and "__type" in value and "value" in value:
                    return path, value["value"]
                return path, value
        return None, None

    def _resolve_parent(self, path: tuple[str, ...]) -> dict[str, Any] | None:
        """Возвращает родительский dict для последнего ключа пути."""
        if not path:
            return None
        parent: Any = self.data
        for part in path[:-1]:
            if not isinstance(parent, dict) or part not in parent:
                return None
            parent = parent[part]
        return parent if isinstance(parent, dict) else None

    def _set_at_path(self, path: tuple[str, ...], new_value: Any) -> bool:
        """Записывает значение по пути, сохраняя ES3-обёртки {__type, value}."""
        parent = self._resolve_parent(path)
        if parent is None:
            return False

        key = path[-1]
        current = parent.get(key)
        if isinstance(current, dict) and "__type" in current and "value" in current:
            current["value"] = new_value
        else:
            parent[key] = new_value
        return True
    def get_field(self, logical_name: str, default: Any = None) -> Any:
        aliases = FIELD_ALIASES.get(logical_name, (logical_name,))
        _, value = self.find_first(*aliases)
        return default if value is None else value

    def set_field(self, logical_name: str, new_value: Any) -> bool:
        aliases = FIELD_ALIASES.get(logical_name, (logical_name,))
        path, _ = self.find_first(*aliases)
        if path is None:
            # Создаём на верхнем уровне под каноническим именем
            canonical = aliases[0]
            # Предпочитаем писать внутрь Progression.value, если контейнер есть
            prog = self.data.get("Progression")
            if isinstance(prog, dict):
                target = prog.get("value", prog) if "__type" in prog else prog
                if isinstance(target, dict):
                    if (
                        canonical in target
                        and isinstance(target[canonical], dict)
                        and "__type" in target[canonical]
                    ):
                        target[canonical]["value"] = new_value
                    else:
                        target[canonical] = new_value
                    return True
            self.data[canonical] = new_value
            return True
        return self._set_at_path(path, new_value)

    def _find_game_version(self, data: dict[str, Any]) -> str | None:
        for path, value in self._walk(data):
            if path and path[-1] in ("Version", "GameVersion", "SaveVersion"):
                if isinstance(value, dict) and "value" in value:
                    value = value["value"]
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def get_snapshot(self) -> SaveSnapshot:
        licenses_raw = self.get_field("licenses", [BASIC_LICENSE_ID])
        licenses: list[int] = []
        if isinstance(licenses_raw, list):
            for item in licenses_raw:
                try:
                    licenses.append(int(item))
                except (TypeError, ValueError):
                    continue
        if not licenses:
            licenses = [BASIC_LICENSE_ID]

        def as_int(val: Any) -> int | None:
            if val is None:
                return None
            try:
                return int(val)
            except (TypeError, ValueError):
                return None

        def as_float(val: Any) -> float:
            try:
                return float(val)
            except (TypeError, ValueError):
                return 0.0

        store_name = self.get_field("store_name", "")
        if not isinstance(store_name, str):
            store_name = str(store_name) if store_name is not None else ""

        return SaveSnapshot(
            money=as_float(self.get_field("money", 0)),
            store_name=store_name,
            day=as_int(self.get_field("day", 1)) or 1,
            licenses=licenses,
            checkout_count=as_int(self.get_field("checkout_count")),
            shelf_count=as_int(self.get_field("shelf_count")),
            employee_count=as_int(self.get_field("employee_count")),
            completed_checkouts=as_int(self.get_field("completed_checkouts")),
            store_level=as_int(self.get_field("store_level")),
            store_upgrade=as_int(self.get_field("store_upgrade")),
        )

    def apply_snapshot(self, snap: SaveSnapshot) -> None:
        self.set_field("money", float(snap.money))
        if snap.store_name:
            self.set_field("store_name", snap.store_name)
        self.set_field("day", int(snap.day))
        self.set_field("licenses", [int(x) for x in snap.licenses])
        if snap.checkout_count is not None:
            self.set_field("checkout_count", int(snap.checkout_count))
        if snap.shelf_count is not None:
            self.set_field("shelf_count", int(snap.shelf_count))
        if snap.employee_count is not None:
            self.set_field("employee_count", int(snap.employee_count))
        if snap.completed_checkouts is not None:
            self.set_field("completed_checkouts", int(snap.completed_checkouts))
        if snap.store_level is not None:
            self.set_field("store_level", int(snap.store_level))
        if snap.store_upgrade is not None:
            self.set_field("store_upgrade", int(snap.store_upgrade))

    def set_all_licenses(self) -> None:
        self.set_field("licenses", list(ALL_LICENSE_IDS))

    def reset_licenses(self) -> None:
        self.set_field("licenses", [BASIC_LICENSE_ID])

    def to_pretty_json(self) -> str:
        return json.dumps(self.data, indent=2, ensure_ascii=False)

    def apply_raw_json(self, text: str) -> None:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError(MESSAGES["json_invalid"])
        self.data = parsed
        self.meta.format_kind = self._detect_format(text, parsed)
        self.meta.game_version = self._find_game_version(parsed)

    def dump_bytes(self) -> bytes:
        if self.meta.format_kind == "es3_typed":
            # Сохраняем компактно, как типичные ES3, но с отступами для читаемости
            text = json.dumps(self.data, indent=2, ensure_ascii=False)
        else:
            text = json.dumps(self.data, indent=2, ensure_ascii=False)
        return text.encode("utf-8")

    def save(self, path: Path | None = None) -> Path:
        dest = Path(path) if path else self.path
        if dest is None:
            raise FileNotFoundError(MESSAGES["no_file"])
        dest.write_bytes(self.dump_bytes())
        self.path = dest
        self.meta.path = dest
        self.meta.size = dest.stat().st_size
        self.meta.modified = datetime.fromtimestamp(dest.stat().st_mtime)
        self._original_data = deepcopy(self.data)
        logger.info("Сохранение записано: %s", dest)
        return dest

    def reset_to_loaded(self) -> None:
        self.data = deepcopy(self._original_data)

    @staticmethod
    def is_game_running() -> bool:
        try:
            import psutil
        except ImportError:
            logger.warning("psutil не установлен — проверка процесса игры пропущена")
            return False

        names_lower = {n.lower() for n in GAME_PROCESS_NAMES}
        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name in names_lower:
                    return True
                # Частичное совпадение для Wine/Steam
                if "supermarket" in name and "simulator" in name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
