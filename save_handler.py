"""Чтение/запись экспортированных сейвов Bitburner (.json / .json.gz)."""

from __future__ import annotations

import base64
import gzip
import json
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.constants import (
    DEFAULT_EXPORT_DIR,
    EXPLOIT_EDIT_SAVE,
    GAME_PROCESS_NAMES,
    MESSAGES,
    SKILL_KEYS,
)

logger = logging.getLogger(__name__)

GZIP_MAGIC = b"\x1f\x8b"


@dataclass
class FileMeta:
    path: Path | None = None
    size: int = 0
    modified: datetime | None = None
    game_version: str | None = None
    format_kind: str = "unknown"  # gzip | base64 | json_plain


@dataclass
class SaveSnapshot:
    money: float = 1000.0
    skills: dict[str, float] = field(default_factory=dict)
    bit_node: int = 1
    karma: float = 0.0
    exploits: list[str] = field(default_factory=list)
    factions: list[str] = field(default_factory=list)
    playtime_ms: float = 0.0
    hacking_level: float = 1.0

    def __post_init__(self) -> None:
        if not self.skills:
            self.skills = {key: 1.0 for key in SKILL_KEYS}


class SaveHandler:
    """Работа с экспортом Bitburner (Options → Export save)."""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.root: dict[str, Any] = {}  # {ctor, data} или data-объект
        self.player: dict[str, Any] = {}  # содержимое PlayerObject.data
        self.meta = FileMeta()
        self._original_root: dict[str, Any] = {}
        self._original_player: dict[str, Any] = {}
        self._raw_decoded_json: str = ""

    @staticmethod
    def default_save_dir() -> Path:
        path = Path(DEFAULT_EXPORT_DIR)
        return path if path.exists() else Path.home()

    @classmethod
    def find_default_saves(cls) -> list[Path]:
        roots = [cls.default_save_dir(), Path.home() / "Desktop", Path.home() / "Documents"]
        found: list[Path] = []
        seen: set[Path] = set()
        for root in roots:
            if not root.exists():
                continue
            for pattern in ("bitburnerSave_*.json.gz", "bitburnerSave_*.json", "*.json.gz"):
                for path in root.glob(pattern):
                    if "bitburner" not in path.name.lower() and pattern.startswith("*"):
                        continue
                    resolved = path.resolve()
                    if resolved not in seen and path.is_file():
                        seen.add(resolved)
                        found.append(path)
        found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return found

    @staticmethod
    def unwrap(node: Any) -> Any:
        if isinstance(node, dict) and "ctor" in node and "data" in node:
            return node["data"]
        return node

    @staticmethod
    def wrap_player(data: dict[str, Any], ctor: str = "PlayerObject") -> dict[str, Any]:
        return {"ctor": ctor, "data": data}

    def _decode_bytes(self, raw: bytes) -> tuple[str, str]:
        """Возвращает (json_text, format_kind)."""
        if raw.startswith(GZIP_MAGIC):
            try:
                text = gzip.decompress(raw).decode("utf-8")
                return text, "gzip"
            except OSError as exc:
                raise ValueError(MESSAGES["file_corrupt"]) from exc

        # Может быть текстовый base64 или уже JSON
        try:
            as_text = raw.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError(MESSAGES["file_corrupt"]) from exc

        if as_text.startswith("{") or as_text.startswith("["):
            return as_text, "json_plain"

        # Base64 (иногда с переносами строк)
        compact = "".join(as_text.split())
        try:
            decoded = base64.b64decode(compact, validate=False)
            # Иногда base64 оборачивает gzip
            if decoded.startswith(GZIP_MAGIC):
                text = gzip.decompress(decoded).decode("utf-8")
                return text, "gzip"
            text = decoded.decode("utf-8")
            if text.startswith("{") or text.startswith("["):
                return text, "base64"
        except Exception:  # noqa: BLE001
            pass

        raise ValueError(MESSAGES["file_corrupt"])

    def _encode_bytes(self, json_text: str, format_kind: str) -> bytes:
        if format_kind == "gzip":
            return gzip.compress(json_text.encode("utf-8"))
        if format_kind == "base64":
            return base64.b64encode(json_text.encode("utf-8"))
        return json_text.encode("utf-8")

    def _extract_player(self, root: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Возвращает (player_data, player_envelope).
        player_envelope — объект, который нужно сериализовать обратно в PlayerSave
        (обычно {ctor, data} или сам data-словарь).
        """
        data = self.unwrap(root)
        if not isinstance(data, dict):
            raise ValueError(MESSAGES["file_corrupt"])

        player_save = data.get("PlayerSave")
        if not isinstance(player_save, str):
            # Иногда уже объект
            if isinstance(player_save, dict):
                envelope = player_save
            else:
                raise ValueError(MESSAGES["file_corrupt"])
        else:
            try:
                envelope = json.loads(player_save)
            except json.JSONDecodeError as exc:
                raise ValueError(MESSAGES["file_corrupt"]) from exc

        player_data = self.unwrap(envelope)
        if not isinstance(player_data, dict):
            raise ValueError(MESSAGES["file_corrupt"])
        return player_data, envelope if isinstance(envelope, dict) else self.wrap_player(player_data)

    def load(self, path: Path | str) -> None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(MESSAGES["file_not_found"])

        raw = path.read_bytes()
        text, format_kind = self._decode_bytes(raw)
        try:
            root = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(MESSAGES["file_corrupt"]) from exc

        if not isinstance(root, dict):
            raise ValueError(MESSAGES["file_corrupt"])

        player_data, envelope = self._extract_player(root)
        # Нормализуем envelope к ctor/data, если это был плоский объект
        if "ctor" not in envelope:
            envelope = self.wrap_player(player_data)
        else:
            envelope["data"] = player_data

        self.path = path
        self.root = root
        self.player = player_data
        self._player_envelope = envelope
        self._raw_decoded_json = text
        self._original_root = deepcopy(root)
        self._original_player = deepcopy(player_data)
        self.meta = FileMeta(
            path=path,
            size=path.stat().st_size,
            modified=datetime.fromtimestamp(path.stat().st_mtime),
            game_version=self._read_version(root),
            format_kind=format_kind,
        )
        logger.info("Загружен Bitburner сейв %s (%s)", path.name, format_kind)

    def _read_version(self, root: dict[str, Any]) -> str | None:
        data = self.unwrap(root)
        if not isinstance(data, dict):
            return None
        ver = data.get("VersionSave")
        if isinstance(ver, str):
            try:
                parsed = json.loads(ver)
                return str(parsed)
            except json.JSONDecodeError:
                return ver.strip('"') or None
        return None

    def get_snapshot(self) -> SaveSnapshot:
        skills_raw = self.player.get("skills") or {}
        skills: dict[str, float] = {}
        for key in SKILL_KEYS:
            try:
                skills[key] = float(skills_raw.get(key, 1))
            except (TypeError, ValueError):
                skills[key] = 1.0

        exploits = self.player.get("exploits") or []
        if not isinstance(exploits, list):
            exploits = []
        exploits = [str(x) for x in exploits]

        factions = self.player.get("factions") or []
        if not isinstance(factions, list):
            factions = []
        factions = [str(x) for x in factions]

        try:
            money = float(self.player.get("money", 0) or 0)
        except (TypeError, ValueError):
            money = 0.0
        try:
            bit_node = int(self.player.get("bitNodeN", 1) or 1)
        except (TypeError, ValueError):
            bit_node = 1
        try:
            karma = float(self.player.get("karma", 0) or 0)
        except (TypeError, ValueError):
            karma = 0.0
        try:
            playtime = float(self.player.get("totalPlaytime", 0) or 0)
        except (TypeError, ValueError):
            playtime = 0.0

        return SaveSnapshot(
            money=money,
            skills=skills,
            bit_node=bit_node,
            karma=karma,
            exploits=exploits,
            factions=factions,
            playtime_ms=playtime,
            hacking_level=skills.get("hacking", 1.0),
        )

    def apply_snapshot(self, snap: SaveSnapshot) -> None:
        self.player["money"] = float(snap.money)
        skills = self.player.get("skills")
        if not isinstance(skills, dict):
            skills = {}
            self.player["skills"] = skills
        for key, value in snap.skills.items():
            skills[key] = float(value)
        self.player["bitNodeN"] = int(snap.bit_node)
        self.player["karma"] = float(snap.karma)
        self.player["exploits"] = list(snap.exploits)

    def set_money(self, value: float) -> None:
        self.player["money"] = float(value)

    def set_skill(self, key: str, value: float) -> None:
        skills = self.player.setdefault("skills", {})
        if not isinstance(skills, dict):
            self.player["skills"] = {}
            skills = self.player["skills"]
        skills[key] = float(value)

    def set_all_skills(self, value: float) -> None:
        for key in SKILL_KEYS:
            self.set_skill(key, value)

    def set_bitnode(self, value: int) -> None:
        self.player["bitNodeN"] = int(value)

    def add_edit_exploit(self) -> None:
        exploits = self.player.get("exploits")
        if not isinstance(exploits, list):
            exploits = []
            self.player["exploits"] = exploits
        if EXPLOIT_EDIT_SAVE not in exploits:
            exploits.append(EXPLOIT_EDIT_SAVE)

    def _sync_player_into_root(self) -> None:
        envelope = getattr(self, "_player_envelope", None)
        if not isinstance(envelope, dict):
            envelope = self.wrap_player(self.player)
            self._player_envelope = envelope
        else:
            if "ctor" in envelope and "data" in envelope:
                envelope["data"] = self.player
            else:
                envelope = self.wrap_player(self.player)
                self._player_envelope = envelope

        data = self.unwrap(self.root)
        if not isinstance(data, dict):
            raise ValueError(MESSAGES["file_corrupt"])
        data["PlayerSave"] = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))

        # Если корень был в формате ctor/data — data уже ссылка внутрь root
        if "ctor" in self.root and "data" in self.root:
            self.root["data"] = data
        else:
            self.root = data

    def to_pretty_json(self) -> str:
        self._sync_player_into_root()
        return json.dumps(self.root, indent=2, ensure_ascii=False)

    def apply_raw_json(self, text: str) -> None:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError(MESSAGES["json_invalid"])
        player_data, envelope = self._extract_player(parsed)
        if "ctor" not in envelope:
            envelope = self.wrap_player(player_data)
        else:
            envelope["data"] = player_data
        self.root = parsed
        self.player = player_data
        self._player_envelope = envelope
        self.meta.game_version = self._read_version(parsed)

    def dump_bytes(self) -> bytes:
        self._sync_player_into_root()
        # Компактный JSON как у игры (без лишних пробелов в PlayerSave уже)
        text = json.dumps(self.root, ensure_ascii=False, separators=(",", ":"))
        # Для ctor-формата encodeJsonSaveString требует старт с {"ctor":"BitburnerSaveObject"
        if not text.startswith('{"ctor":"BitburnerSaveObject"'):
            # Оборачиваем, если пользователь открыл «голый» объект data
            if "PlayerSave" in self.root:
                wrapped = {"ctor": "BitburnerSaveObject", "data": self.root}
                text = json.dumps(wrapped, ensure_ascii=False, separators=(",", ":"))
                self.root = wrapped
        return self._encode_bytes(text, self.meta.format_kind or "base64")

    def suggested_edited_path(self) -> Path | None:
        """Путь для сохранения правок без перезаписи исходного экспорта."""
        if not self.path:
            return None
        name = self.path.name
        if name.endswith(".json.gz"):
            base = name[: -len(".json.gz")]
            suffix = ".json.gz"
        else:
            base = self.path.stem
            suffix = self.path.suffix
        if base.endswith("_EDITED"):
            return self.path
        return self.path.with_name(f"{base}_EDITED{suffix}")

    def verify_money_on_disk(self, path: Path | None = None) -> float:
        """Перечитывает файл с диска и возвращает money (для проверки записи)."""
        target = Path(path) if path else self.path
        if target is None:
            raise FileNotFoundError(MESSAGES["no_file"])
        checker = SaveHandler()
        checker.load(target)
        return float(checker.get_snapshot().money)

    def save(self, path: Path | None = None) -> Path:
        dest = Path(path) if path else self.path
        if dest is None:
            raise FileNotFoundError(MESSAGES["no_file"])
        payload = self.dump_bytes()
        dest.write_bytes(payload)
        # Проверка: файл реально читается и money на месте
        expected = float(self.player.get("money", 0) or 0)
        checker = SaveHandler()
        checker.load(dest)
        actual = float(checker.get_snapshot().money)
        if abs(actual - expected) > max(1.0, abs(expected) * 1e-9):
            raise ValueError(
                f"Файл записан, но money не совпало (ждали {expected:g}, в файле {actual:g})."
            )

        self.path = dest
        self.meta.path = dest
        self.meta.size = dest.stat().st_size
        self.meta.modified = datetime.fromtimestamp(dest.stat().st_mtime)
        self.meta.format_kind = checker.meta.format_kind
        self._original_root = deepcopy(self.root)
        self._original_player = deepcopy(self.player)
        logger.info("Bitburner сейв записан: %s (money=%g)", dest, actual)
        return dest

    def reset_to_loaded(self) -> None:
        self.root = deepcopy(self._original_root)
        self.player = deepcopy(self._original_player)
        _, envelope = self._extract_player(self.root)
        if "ctor" not in envelope:
            envelope = self.wrap_player(self.player)
        else:
            envelope["data"] = self.player
        self._player_envelope = envelope

    @staticmethod
    def is_game_running() -> bool:
        try:
            import psutil
        except ImportError:
            return False
        names = {n.lower() for n in GAME_PROCESS_NAMES}
        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name in names or "bitburner" in name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
