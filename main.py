"""
Точка входа: Supermarket Simulator — Save Editor.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Корень проекта в PYTHONPATH при запуске из исходников / PyInstaller
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.constants import APP_NAME, log_file_path  # noqa: E402


def setup_logging() -> None:
    log_path = log_file_path()
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]
    try:
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    except OSError:
        # Нет прав на запись рядом с exe — только stdout
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )
    logging.getLogger(__name__).info("Запуск %s", APP_NAME)


def main() -> None:
    setup_logging()
    from app import App

    application = App()
    application.mainloop()


if __name__ == "__main__":
    main()
