"""Менеджер бэкапов (в папке backups рядом с сейвом игры)."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from utils.paths import game_save_root, is_under_backups

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    created_at: datetime
    size: int

    @property
    def display_name(self) -> str:
        return self.path.name

    @property
    def display_date(self) -> str:
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")


class BackupManager:
    def __init__(self, save_path: Path | None = None) -> None:
        self.save_path = Path(save_path) if save_path else None

    def set_save_path(self, save_path: Path) -> None:
        self.save_path = Path(save_path)

    def create_backup(self, source: Path | None = None) -> BackupInfo:
        src = Path(source) if source else self.save_path
        if src is None or not src.exists():
            raise FileNotFoundError("Нет файла для бэкапа")
        if is_under_backups(src):
            raise ValueError("Нельзя делать бэкап из папки backups — откройте StoreFileN.es3")

        root = game_save_root(src)
        backup_root = root / "backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest = backup_root / f"{src.stem}_backup_{stamp}{src.suffix}"
        shutil.copy2(src, dest)
        logger.info("Бэкап: %s → %s", src, dest)
        return BackupInfo(
            path=dest,
            created_at=datetime.fromtimestamp(dest.stat().st_mtime),
            size=dest.stat().st_size,
        )

    def list_backups(self, limit: int = 5) -> list[BackupInfo]:
        return []
