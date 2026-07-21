"""Менеджер резервных копий сохранений."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

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
    """Создаёт и восстанавливает бэкапы рядом с файлом сохранения."""

    def __init__(self, save_path: Path | None = None) -> None:
        self.save_path = Path(save_path) if save_path else None

    def set_save_path(self, save_path: Path) -> None:
        self.save_path = Path(save_path)

    @property
    def backup_dir(self) -> Path | None:
        if not self.save_path:
            return None
        return self.save_path.parent / "backups"

    def create_backup(self, source: Path | None = None) -> BackupInfo:
        src = Path(source) if source else self.save_path
        if src is None or not src.exists():
            raise FileNotFoundError("Файл сохранения для бэкапа не найден.")

        backup_root = src.parent / "backups"
        backup_root.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest = backup_root / f"{src.stem}_backup_{stamp}{src.suffix}"
        counter = 1
        while dest.exists():
            dest = backup_root / f"{src.stem}_backup_{stamp}_{counter}{src.suffix}"
            counter += 1

        shutil.copy2(src, dest)
        info = BackupInfo(
            path=dest,
            created_at=datetime.fromtimestamp(dest.stat().st_mtime),
            size=dest.stat().st_size,
        )
        logger.info("Создан бэкап: %s", dest)
        return info

    def list_backups(self, limit: int = 5) -> list[BackupInfo]:
        if not self.save_path:
            return []
        backup_root = self.backup_dir
        if backup_root is None or not backup_root.exists():
            return []

        files = sorted(
            backup_root.glob(f"{self.save_path.stem}_backup_*.es3"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        result: list[BackupInfo] = []
        for path in files[:limit]:
            stat = path.stat()
            result.append(
                BackupInfo(
                    path=path,
                    created_at=datetime.fromtimestamp(stat.st_mtime),
                    size=stat.st_size,
                )
            )
        return result

    def restore(self, backup_path: Path, target: Path | None = None) -> Path:
        dest = Path(target) if target else self.save_path
        if dest is None:
            raise FileNotFoundError("Целевой файл сохранения не задан.")
        src = Path(backup_path)
        if not src.exists():
            raise FileNotFoundError(f"Резервная копия не найдена: {src}")

        if dest.exists():
            self.create_backup(dest)

        shutil.copy2(src, dest)
        logger.info("Восстановлено из %s → %s", src, dest)
        return dest
