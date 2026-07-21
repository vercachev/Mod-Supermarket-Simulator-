"""Главное окно приложения CustomTkinter."""

from __future__ import annotations

import logging
import tkinter.messagebox as messagebox
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from save_handler import SaveHandler, SaveSnapshot
from ui.tab_advanced import AdvancedTab
from ui.tab_licenses import LicensesTab
from ui.tab_money import MoneyTab
from ui.tab_store import StoreTab
from utils.backup import BackupInfo, BackupManager
from utils.constants import (
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    APP_NAME,
    APP_TITLE,
    MESSAGES,
    STATUS_ERROR,
    STATUS_IDLE,
    STATUS_OK,
    STATUS_WARN,
    WINDOW_SIZE,
    app_base_dir,
)
from utils.validator import ValidationError

logger = logging.getLogger(__name__)


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.handler = SaveHandler()
        self.backups = BackupManager()
        self._snapshot = SaveSnapshot()

        self._set_icon()
        self._build_ui()
        self.after(200, self._autodetect_save)

    def _set_icon(self) -> None:
        icon = app_base_dir() / "assets" / "icon.ico"
        if icon.exists():
            try:
                self.iconbitmap(str(icon))
            except Exception:  # noqa: BLE001
                logger.debug("Не удалось установить icon.ico", exc_info=True)

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        # Заголовок
        header = ctk.CTkFrame(self, fg_color=("gray85", "#121212"), corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=APP_TITLE,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT_GREEN,
        ).pack(pady=14)

        # Панель файла
        file_bar = ctk.CTkFrame(self, fg_color="transparent")
        file_bar.pack(fill="x", padx=16, pady=(10, 4))

        ctk.CTkButton(
            file_bar,
            text="📂 Открыть сохранение",
            width=180,
            command=self.open_save_dialog,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
        ).pack(side="left")

        ctk.CTkLabel(file_bar, text="Путь:").pack(side="left", padx=(12, 4))
        self.path_var = ctk.StringVar(value="")
        self.path_entry = ctk.CTkEntry(file_bar, textvariable=self.path_var, width=420)
        self.path_entry.pack(side="left", padx=4)
        ctk.CTkButton(
            file_bar,
            text="...",
            width=40,
            command=self.open_save_dialog,
        ).pack(side="left", padx=4)

        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(0, 6))
        self.status_label = ctk.CTkLabel(
            status_row,
            text=MESSAGES["not_loaded"],
            text_color=STATUS_IDLE,
            anchor="w",
        )
        self.status_label.pack(side="left")
        self.warn_label = ctk.CTkLabel(
            status_row,
            text="⚠️ Убедитесь, что игра закрыта перед сохранением!",
            text_color=STATUS_WARN,
            anchor="e",
        )
        self.warn_label.pack(side="right")

        # Вкладки
        self.tabs = ctk.CTkTabview(self, width=860, height=430)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=8)
        self.tabs.add("💰 Деньги")
        self.tabs.add("🏪 Магазин")
        self.tabs.add("📦 Лицензии")
        self.tabs.add("🔧 Прочее")

        self.money_tab = MoneyTab(self.tabs.tab("💰 Деньги"), on_apply=self._on_money_apply)
        self.money_tab.pack(fill="both", expand=True)

        self.store_tab = StoreTab(self.tabs.tab("🏪 Магазин"), on_apply=self._on_store_apply)
        self.store_tab.pack(fill="both", expand=True)

        self.licenses_tab = LicensesTab(
            self.tabs.tab("📦 Лицензии"), on_change=self._on_licenses_change
        )
        self.licenses_tab.pack(fill="both", expand=True)

        self.advanced_tab = AdvancedTab(
            self.tabs.tab("🔧 Прочее"),
            on_create_backup=self.create_backup_manual,
            on_restore_backup=self.restore_backup,
            on_refresh_json=self.refresh_json_from_fields,
            on_apply_json=self.apply_json_direct,
        )
        self.advanced_tab.pack(fill="both", expand=True)

        # Нижняя панель
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(4, 14))

        ctk.CTkButton(
            bottom,
            text="💾 Сохранить изменения",
            width=200,
            height=36,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.save_changes,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            bottom,
            text="🔄 Сбросить",
            width=140,
            height=36,
            command=self.reset_changes,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            bottom,
            text="📋 Бэкап",
            width=120,
            height=36,
            command=self.create_backup_manual,
        ).pack(side="left", padx=4)

    # ------------------------------------------------------------------ #
    # Статус / уведомления
    # ------------------------------------------------------------------ #
    def set_status(self, text: str, color: str = STATUS_OK) -> None:
        self.status_label.configure(text=text, text_color=color)

    def _require_file(self) -> bool:
        if not self.handler.path:
            messagebox.showwarning(APP_NAME, MESSAGES["no_file"])
            return False
        return True

    # ------------------------------------------------------------------ #
    # Загрузка
    # ------------------------------------------------------------------ #
    def _autodetect_save(self) -> None:
        found = SaveHandler.find_default_saves()
        if not found:
            return
        newest = found[0]
        answer = messagebox.askyesno(
            APP_NAME,
            f"Найдено сохранение:\n{newest}\n\nЗагрузить его автоматически?",
        )
        if answer:
            self.load_file(newest)

    def open_save_dialog(self) -> None:
        initial = SaveHandler.default_save_dir()
        if not initial.exists():
            initial = Path.home()
        path = filedialog.askopenfilename(
            title="Открыть файл сохранения",
            initialdir=str(initial),
            filetypes=[
                ("Save files", "*.es3"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.load_file(Path(path))

    def load_file(self, path: Path) -> None:
        try:
            self.handler.load(path)
        except FileNotFoundError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            self.set_status(MESSAGES["not_loaded"], STATUS_ERROR)
            return
        except ValueError as exc:
            # Предложить открыть как raw
            if messagebox.askyesno(
                APP_NAME,
                f"{exc}\n\nОткрыть файл как сырой текст в редакторе JSON?",
            ):
                try:
                    text = Path(path).read_text(encoding="utf-8", errors="replace")
                    self.handler.path = Path(path)
                    self.handler.data = {}
                    self.handler.raw_text = text
                    self.path_var.set(str(path))
                    self.advanced_tab.set_json(text)
                    self.set_status("● Файл открыт как текст (не распарсен)", STATUS_WARN)
                except OSError as err:
                    messagebox.showerror(APP_NAME, str(err))
            else:
                messagebox.showerror(APP_NAME, str(exc))
            return

        self.path_var.set(str(path))
        self.backups.set_save_path(path)
        self._refresh_ui_from_handler()
        self.set_status(MESSAGES["load_ok"].format(name=path.name), STATUS_OK)
        logger.info("UI обновлён после загрузки %s", path)

    def _refresh_ui_from_handler(self) -> None:
        self._snapshot = self.handler.get_snapshot()
        self.money_tab.set_funds(self._snapshot.money)
        self.store_tab.load_snapshot(self._snapshot)
        self.licenses_tab.set_licenses(self._snapshot.licenses)
        self.advanced_tab.set_json(self.handler.to_pretty_json())
        self.advanced_tab.set_file_info(self.handler.meta)
        self.advanced_tab.set_backups(self.backups.list_backups(5))

    # ------------------------------------------------------------------ #
    # Применение полей вкладок
    # ------------------------------------------------------------------ #
    def _sync_money_from_ui(self) -> None:
        try:
            self._snapshot.money = self.money_tab.get_funds()
        except ValidationError:
            pass

    def _on_money_apply(self, value: float) -> None:
        if not self._require_file():
            return
        self._snapshot.money = value
        self.handler.set_field("money", float(value))
        self.advanced_tab.set_json(self.handler.to_pretty_json())
        self.set_status(f"● Деньги установлены: {value:,.0f} $".replace(",", " "), STATUS_OK)

    def _on_store_apply(self, _unused: SaveSnapshot) -> None:
        if not self._require_file():
            return
        try:
            self._sync_money_from_ui()
            snap = self.store_tab.build_partial_snapshot(self._snapshot)
            snap.licenses = self.licenses_tab.get_licenses()
            self._snapshot = snap
            self.handler.apply_snapshot(snap)
            self.advanced_tab.set_json(self.handler.to_pretty_json())
            self.set_status("● Данные магазина применены (не забудьте сохранить файл)", STATUS_OK)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))

    def _on_licenses_change(self, licenses: list[int]) -> None:
        if not self.handler.path:
            return
        self._snapshot.licenses = licenses
        self.handler.set_field("licenses", licenses)
        self.advanced_tab.set_json(self.handler.to_pretty_json())

    # ------------------------------------------------------------------ #
    # Сохранение / сброс / бэкап
    # ------------------------------------------------------------------ #
    def _collect_ui_into_handler(self) -> None:
        self._sync_money_from_ui()
        try:
            snap = self.store_tab.build_partial_snapshot(self._snapshot)
        except ValidationError:
            snap = self._snapshot
        snap.money = self._snapshot.money
        snap.licenses = self.licenses_tab.get_licenses()
        self._snapshot = snap
        self.handler.apply_snapshot(snap)

    def save_changes(self) -> None:
        if not self._require_file():
            return

        if SaveHandler.is_game_running():
            if not messagebox.askyesno(
                APP_NAME,
                MESSAGES["game_running"] + "\n\nВсё равно сохранить?",
            ):
                return

        try:
            self._collect_ui_into_handler()
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return

        try:
            info = self.backups.create_backup(self.handler.path)
            self.handler.save()
            self._refresh_ui_from_handler()
            messagebox.showinfo(
                APP_NAME,
                MESSAGES["save_ok"] + f"\nБэкап: {info.display_name}",
            )
            self.set_status(MESSAGES["save_ok"], STATUS_OK)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ошибка сохранения")
            messagebox.showerror(APP_NAME, f"❌ Не удалось сохранить:\n{exc}")
            self.set_status(str(exc), STATUS_ERROR)

    def reset_changes(self) -> None:
        if not self._require_file():
            return
        if not messagebox.askyesno(
            APP_NAME,
            "Сбросить все несохранённые изменения к загруженному файлу?",
        ):
            return
        self.handler.reset_to_loaded()
        self._refresh_ui_from_handler()
        self.set_status("● Изменения сброшены", STATUS_WARN)

    def create_backup_manual(self) -> None:
        if not self._require_file():
            return
        try:
            info = self.backups.create_backup(self.handler.path)
            self.advanced_tab.set_backups(self.backups.list_backups(5))
            messagebox.showinfo(
                APP_NAME,
                MESSAGES["backup_ok"].format(name=info.display_name),
            )
            self.set_status(MESSAGES["backup_ok"].format(name=info.display_name), STATUS_OK)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ошибка бэкапа")
            messagebox.showerror(APP_NAME, f"❌ {exc}")

    def restore_backup(self, info: BackupInfo) -> None:
        if not self._require_file():
            return
        if not messagebox.askyesno(
            APP_NAME,
            f"Восстановить сохранение из:\n{info.display_name}?\n"
            "Текущий файл будет сохранён в бэкап.",
        ):
            return
        try:
            if SaveHandler.is_game_running():
                messagebox.showwarning(APP_NAME, MESSAGES["game_running"])
            self.backups.restore(info.path, self.handler.path)
            self.handler.load(self.handler.path)  # type: ignore[arg-type]
            self._refresh_ui_from_handler()
            messagebox.showinfo(
                APP_NAME,
                MESSAGES["restore_ok"].format(date=info.display_date),
            )
            self.set_status(
                MESSAGES["restore_ok"].format(date=info.display_date),
                STATUS_OK,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ошибка восстановления")
            messagebox.showerror(APP_NAME, f"❌ {exc}")

    def refresh_json_from_fields(self) -> None:
        if not self._require_file():
            return
        try:
            self._collect_ui_into_handler()
            self.advanced_tab.set_json(self.handler.to_pretty_json())
            self.set_status("● JSON обновлён из полей", STATUS_OK)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))

    def apply_json_direct(self, text: str) -> None:
        if not self._require_file():
            return
        try:
            self.handler.apply_raw_json(text)
            self._refresh_ui_from_handler()
            self.set_status("● JSON применён в память (сохраните файл)", STATUS_WARN)
            messagebox.showinfo(
                APP_NAME,
                "JSON применён. Нажмите «Сохранить изменения», чтобы записать на диск.",
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, MESSAGES["json_invalid"] + f"\n{exc}")
