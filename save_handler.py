"""Чтение/запись экспортированных сейвов Bitburner (.json / .json.gz)."""

from __future__ import annotations

import base64
import gzip
import json
import logging
import re
import time
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


def _json_number(value: float | int) -> str:
    """Число в JSON как у JS (без лишнего .0 если целое)."""
    f = float(value)
    if abs(f) >= 1e15 or (abs(f) > 0 and abs(f) < 1e-4):
        return format(f, ".15g")
    if float(f).is_integer():
        return str(int(f))
    return format(f, ".15g")


class SaveHandler:
    """Работа с экспортом Bitburner (Options → Export save)."""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.root: dict[str, Any] = {}
        self.player: dict[str, Any] = {}
        self.meta = FileMeta()
        self._original_root: dict[str, Any] = {}
        self._original_player: dict[str, Any] = {}
        self._raw_decoded_json: str = ""
        self._player_envelope: dict[str, Any] = {}

    @staticmethod
    def default_save_dir() -> Path:
        path = Path(DEFAULT_EXPORT_DIR)
        return path if path.exists() else Path.home()

    @classmethod
    def find_default_saves(cls) -> list[Path]:
        roots = [
            cls.default_save_dir(),
            Path.home() / "Desktop",
            Path.home() / "OneDrive" / "Desktop",
            Path.home() / "Documents",
        ]
        found: list[Path] = []
        seen: set[Path] = set()
        for root in roots:
            if not root.exists():
                continue
            for pattern in ("bitburnerSave_*.json.gz", "bitburnerSave_*.json"):
                for path in root.glob(pattern):
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
        if raw.startswith(GZIP_MAGIC):
            try:
                return gzip.decompress(raw).decode("utf-8"), "gzip"
            except OSError as exc:
                raise ValueError(MESSAGES["file_corrupt"]) from exc

        try:
            as_text = raw.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError(MESSAGES["file_corrupt"]) from exc

        if as_text.startswith("{") or as_text.startswith("["):
            return as_text, "json_plain"

        compact = "".join(as_text.split())
        try:
            decoded = base64.b64decode(compact, validate=False)
            if decoded.startswith(GZIP_MAGIC):
                return gzip.decompress(decoded).decode("utf-8"), "gzip"
            text = decoded.decode("utf-8")
            if text.startswith("{") or text.startswith("["):
                return text, "base64"
        except Exception:  # noqa: BLE001
            pass
        raise ValueError(MESSAGES["file_corrupt"])

    def _encode_bytes(self, json_text: str, format_kind: str) -> bytes:
        if format_kind == "gzip":
            # mtime=0 — стабильный gzip, как у многих веб-экспортов
            return gzip.compress(json_text.encode("utf-8"), mtime=0)
        if format_kind == "base64":
            return base64.b64encode(json_text.encode("utf-8"))
        return json_text.encode("utf-8")

    def _extract_player(self, root: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        data = self.unwrap(root)
        if not isinstance(data, dict):
            raise ValueError(MESSAGES["file_corrupt"])

        player_save = data.get("PlayerSave")
        if isinstance(player_save, dict):
            envelope = player_save
        elif isinstance(player_save, str):
            try:
                envelope = json.loads(player_save)
            except json.JSONDecodeError as exc:
                raise ValueError(MESSAGES["file_corrupt"]) from exc
        else:
            raise ValueError(MESSAGES["file_corrupt"])

        player_data = self.unwrap(envelope)
        if not isinstance(player_data, dict):
            raise ValueError(MESSAGES["file_corrupt"])
        if not isinstance(envelope, dict):
            envelope = self.wrap_player(player_data)
        return player_data, envelope

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
        if "ctor" not in envelope:
            envelope = self.wrap_player(player_data)
        else:
            # держим одну ссылку на data
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
                return str(json.loads(ver))
            except json.JSONDecodeError:
                return ver.strip('"') or None
        return None

    def get_snapshot(self) -> SaveSnapshot:
        skills_raw = self.player.get("skills") or {}
        skills: dict[str, float] = {}
        for key in SKILL_KEYS:
            try:
                skills[key] = float(skills_raw.get(key, 1) or 1)
            except (TypeError, ValueError):
                skills[key] = 1.0

        exploits = self.player.get("exploits") or []
        if not isinstance(exploits, list):
            exploits = []
        factions = self.player.get("factions") or []
        if not isinstance(factions, list):
            factions = []

        def fnum(key: str, default: float = 0.0) -> float:
            try:
                return float(self.player.get(key, default) or default)
            except (TypeError, ValueError):
                return default

        def inum(key: str, default: int = 1) -> int:
            try:
                return int(self.player.get(key, default) or default)
            except (TypeError, ValueError):
                return default

        return SaveSnapshot(
            money=fnum("money", 0.0),
            skills=skills,
            bit_node=inum("bitNodeN", 1),
            karma=fnum("karma", 0.0),
            exploits=[str(x) for x in exploits],
            factions=[str(x) for x in factions],
            playtime_ms=fnum("totalPlaytime", 0.0),
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
        # Чтобы Import Comparison видел более новый сейв
        self.player["lastSave"] = int(time.time() * 1000)

    def set_money(self, value: float) -> None:
        self.player["money"] = float(value)
        self.player["lastSave"] = int(time.time() * 1000)

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

    def _build_player_save_string(self) -> str:
        envelope = self._player_envelope
        if not isinstance(envelope, dict) or "ctor" not in envelope:
            envelope = self.wrap_player(self.player)
        else:
            envelope["data"] = self.player
        self._player_envelope = envelope
        return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))

    def _patch_raw_json(self) -> str:
        """
        Точечно подменяет PlayerSave в исходном decoded JSON.
        Так мы не пересобираем весь гигантский сейв и меньше ломаем Import.
        """
        player_save = self._build_player_save_string()
        # PlayerSave как JSON-строка внутри объекта → нужен dumps ещё раз для экранирования
        encoded_field = json.dumps(player_save, ensure_ascii=False)

        raw = self._raw_decoded_json
        pattern = re.compile(r'("PlayerSave"\s*:\s*)"(?:\\.|[^"\\])*"')
        new_raw, count = pattern.subn(rf"\1{encoded_field}", raw, count=1)
        if count != 1:
            # fallback: полная пересборка корня
            logger.warning("PlayerSave regex patch failed (%s) — full rebuild", count)
            data = self.unwrap(self.root)
            if not isinstance(data, dict):
                raise ValueError(MESSAGES["file_corrupt"])
            data["PlayerSave"] = player_save
            if "ctor" in self.root and "data" in self.root:
                self.root["data"] = data
                new_raw = json.dumps(self.root, ensure_ascii=False, separators=(",", ":"))
            else:
                wrapped = {"ctor": "BitburnerSaveObject", "data": data}
                self.root = wrapped
                new_raw = json.dumps(wrapped, ensure_ascii=False, separators=(",", ":"))
        else:
            # синхронизируем self.root из патченного текста
            self.root = json.loads(new_raw)

        if not new_raw.startswith('{"ctor":"BitburnerSaveObject"'):
            # на всякий случай
            parsed = json.loads(new_raw)
            if "PlayerSave" in parsed and "ctor" not in parsed:
                wrapped = {"ctor": "BitburnerSaveObject", "data": parsed}
                new_raw = json.dumps(wrapped, ensure_ascii=False, separators=(",", ":"))
                self.root = wrapped

        self._raw_decoded_json = new_raw
        return new_raw

    def to_pretty_json(self) -> str:
        self._patch_raw_json()
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
        self._raw_decoded_json = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        self.meta.game_version = self._read_version(parsed)

    def dump_bytes(self) -> bytes:
        text = self._patch_raw_json()
        return self._encode_bytes(text, self.meta.format_kind or "gzip")

    def suggested_edited_path(self) -> Path | None:
        # Пишем в Downloads — меньше проблем с OneDrive Desktop
        folder = self.default_save_dir()
        stamp = int(time.time())
        snap = self.get_snapshot()
        name = f"bitburnerSave_{stamp}_BN{snap.bit_node}_EDITED.json.gz"
        return folder / name

    def verify_money_on_disk(self, path: Path | None = None) -> float:
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

        if dest.name.endswith(".json.gz"):
            self.meta.format_kind = "gzip"
        elif dest.suffix == ".json" and self.meta.format_kind not in ("base64", "json_plain"):
            self.meta.format_kind = "base64"

        expected = float(self.player.get("money", 0) or 0)
        payload = self.dump_bytes()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)

        actual = self.verify_money_on_disk(dest)
        if abs(actual - expected) > max(1.0, abs(expected) * 1e-9):
            raise ValueError(
                f"Файл записан, но money не совпало (ждали {expected:g}, в файле {actual:g})."
            )

        self.path = dest
        self.meta.path = dest
        self.meta.size = dest.stat().st_size
        self.meta.modified = datetime.fromtimestamp(dest.stat().st_mtime)
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
        self._raw_decoded_json = json.dumps(self.root, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def is_game_running() -> bool:
        try:
            import psutil
        except ImportError:
            return False
        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if "bitburner" in name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
