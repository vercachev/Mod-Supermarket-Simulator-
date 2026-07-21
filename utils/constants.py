"""Константы приложения: пути, лицензии, лимиты, сообщения."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Supermarket Simulator — Save Editor v1.0"
APP_TITLE = "🛒  SUPERMARKET SIMULATOR — SAVE EDITOR"
WINDOW_SIZE = "900x650"

# Акцентные цвета (тёмная тема + зелёный «деньги»)
ACCENT_GREEN = "#2ECC71"
ACCENT_GREEN_HOVER = "#27AE60"
STATUS_OK = "#2ECC71"
STATUS_WARN = "#F39C12"
STATUS_ERROR = "#E74C3C"
STATUS_IDLE = "#95A5A6"
DANGER_RED = "#E74C3C"

# Стандартный путь к сохранениям (Steam / обычная Windows-версия)
DEFAULT_SAVE_PATH = os.path.expandvars(
    r"%APPDATA%\..\LocalLow\Nokta Games\Supermarket Simulator"
)
# Xbox Game Pass / Microsoft Store (папка игры в C:\XboxGames НЕ содержит сейвы)
XBOX_PACKAGES_ROOT = os.path.expandvars(r"%LOCALAPPDATA%\Packages")
XBOX_PACKAGE_NAME_HINT = "SupermarketSimulator"

DEFAULT_SAVE_FILENAMES = (
    "SaveFile.es3",
    "Save.es3",
    "slot_0.es3",
    "slot_1.es3",
    "slot_2.es3",
    "slot_3.es3",
)

GAME_PROCESS_NAMES = (
    "Supermarket Simulator.exe",
    "SupermarketSimulator.exe",
    "Supermarket Simulator",
)

# Реальные ID лицензий в игре: 21–47 (ID < 21 ломают прогресс)
# Имена составлены по категориям товаров из гайдов сообщества.
LICENSES: dict[int, str] = {
    21: "Базовая лицензия (крупы, хлеб, бакалея)",
    22: "Молочные продукты и напитки",
    23: "Расширенная бакалея",
    24: "Соки и газированные напитки",
    25: "Сладости и снеки",
    26: "Бытовая химия",
    27: "Консервы и сыры",
    28: "Заморозка и полуфабрикаты",
    29: "Молочка и кофе (расширенная)",
    30: "Мясная и рыбная продукция",
    31: "Соусы и мороженое",
    32: "Пиво и алкоголь (базовый)",
    33: "Снеки и приправы",
    34: "Бытовая химия (расширенная)",
    35: "Мясо и готовая еда",
    36: "Напитки и кофе",
    37: "Заморозка (пицца, мороженое)",
    38: "Алкоголь (пиво, водка)",
    39: "Сыры и паста (премиум)",
    40: "Средства для стирки и посуды",
    41: "Книги и канцелярия",
    42: "Зоотовары",
    43: "Кондитерские изделия",
    44: "Гигиена и бумага",
    45: "Книги (расширенная)",
    46: "Шоколад и выпечка",
    47: "Крепкий алкоголь",
}

BASIC_LICENSE_ID = 21
ALL_LICENSE_IDS = list(LICENSES.keys())

# Лимиты значений
MAX_FUNDS = 99_999_999
MAX_DAYS = 9999
MAX_CHECKOUTS = 20
MAX_SHELVES = 200
MAX_EMPLOYEES = 50
MAX_STORE_LEVEL = 50

# Известные ключи в ES3 (реальная структура игры + fallback из ТЗ)
# Деньги лежат в Progression.value.Money (не Funds)
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "money": ("Money", "Funds", "funds"),
    "store_name": ("StoreName", "storeName", "MarketName", "ShopName"),
    "day": ("CurrentDay", "Day", "day"),
    "licenses": ("UnlockedLicenses", "unlockedLicenses"),
    "checkout_count": ("CheckoutCount", "checkoutCount"),
    "shelf_count": ("ShelfCount", "shelfCount"),
    "employee_count": ("EmployeeCount", "employeeCount"),
    "completed_checkouts": ("CompletedCheckoutCount",),
    "store_level": ("CurrentStoreLevel", "StoreLevel"),
    "store_upgrade": ("StoreUpgradeLevel",),
    "game_version": ("Version", "GameVersion", "SaveVersion"),
}

# Сообщения пользователю (русский UI)
MESSAGES = {
    "file_not_found": (
        "❌ Файл сохранения не найден. Убедитесь, что вы хотя бы раз запустили игру."
    ),
    "file_corrupt": (
        "❌ Файл сохранения повреждён или зашифрован. "
        "Попробуйте восстановить из бэкапа."
    ),
    "file_xbox_encrypted": (
        "❌ Это сейв Xbox / Game Pass в зашифрованном контейнере (папка wgs).\n\n"
        "Такие файлы нельзя править как обычный SaveFile.es3 (Steam).\n\n"
        "Что можно сделать:\n"
        "• Править на том ПК, где версия Steam и есть обычный .es3\n"
        "• Или искать файл в LocalLow (если вдруг есть):\n"
        "  %USERPROFILE%\\AppData\\LocalLow\\Nokta Games\\Supermarket Simulator\n\n"
        "Не сохраняйте «сырой текст» поверх Xbox-файла — можно сломать сейв."
    ),
    "game_running": (
        "⚠️ Кажется, игра запущена. Закройте её перед сохранением изменений!"
    ),
    "invalid_number": "❌ Введите корректное число (от {min_v} до {max_v})",
    "save_ok": "✅ Изменения сохранены! Бэкап создан автоматически.",
    "backup_ok": "✅ Резервная копия создана: {name}",
    "restore_ok": "✅ Восстановлено из резервной копии от {date}",
    "no_file": "Сначала откройте файл сохранения.",
    "json_invalid": "❌ Неверный JSON. Изменения не применены.",
    "load_ok": "● Файл загружен: {name}",
    "not_loaded": "● Файл не загружен",
}


def app_base_dir() -> Path:
    """Папка приложения (учитывает PyInstaller --onefile)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def log_file_path() -> Path:
    return app_base_dir() / "editor.log"
