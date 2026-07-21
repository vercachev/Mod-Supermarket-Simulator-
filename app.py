"""Главное окно Bitburner Save Editor."""

from __future__ import annotations

import logging
import tkinter.messagebox as messagebox
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from save_handler import SaveHandler, SaveSnapshot
from ui.tab_advanced import AdvancedTab
from ui.tab_money import MoneyTab
from ui.tab_progress import ProgressTab
from ui.tab_skills import SkillsTab
from utils.backup import BackupInfo, BackupManager
from utils.constants import (
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    APP_NAME,
    APP_TITLE,
    EXPLOIT_EDIT_SAVE,
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
                logger.debug("icon.ico skip", exc_info=True)

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color=("gray85", "#121212"), corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=APP_TITLE,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT_GREEN,
        ).pack(pady=14)

        file_bar = ctk.CTkFrame(self, fg_color="transparent")
        file_bar.pack(fill="x", padx=16, pady=(10, 4))

        ctk.CTkButton(
            file_bar,
            text="📂 Открыть экспорт",
            width=180,
            command=self.open_save_dialog,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
        ).pack(side="left")

        ctk.CTkLabel(file_bar, text="Путь:").pack(side="left", padx=(12, 4))
        self.path_var = ctk.StringVar(value="")
        ctk.CTkEntry(file_bar, textvariable=self.path_var, width=420).pack(side="left", padx=4)
        ctk.CTkButton(file_bar, text="...", width=40, command=self.open_save_dialog).pack(
            side="left", padx=4
        )

        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(0, 6))
        self.status_label = ctk.CTkLabel(
            status_row, text=MESSAGES["not_loaded"], text_color=STATUS_IDLE, anchor="w"
        )
        self.status_label.pack(side="left")
        ctk.CTkLabel(
            status_row,
            text="⚠️ Сейв: Export из игры → правка → Import обратно",
            text_color=STATUS_WARN,
            anchor="e",
        ).pack(side="right")

        self.tabs = ctk.CTkTabview(self, width=860, height=430)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=8)
        self.tabs.add("💰 Деньги")
        self.tabs.add("🧠 Навыки")
        self.tabs.add("🛰️ Прогресс")
        self.tabs.add("🔧 Прочее")

        self.money_tab = MoneyTab(self.tabs.tab("💰 Деньги"), on_apply=self._on_money_apply)
        self.money_tab.pack(fill="both", expand=True)

        self.skills_tab = SkillsTab(self.tabs.tab("🧠 Навыки"), on_apply=self._on_skills_apply)
        self.skills_tab.pack(fill="both", expand=True)

        self.progress_tab = ProgressTab(
            self.tabs.tab("🛰️ Прогресс"), on_apply=self._on_progress_apply
        )
        self.progress_tab.pack(fill="both", expand=True)

        self.advanced_tab = AdvancedTab(
            self.tabs.tab("🔧 Прочее"),
            on_create_backup=self.create_backup_manual,
            on_restore_backup=self.restore_backup,
            on_refresh_json=self.refresh_json_from_fields,
            on_apply_json=self.apply_json_direct,
        )
        self.advanced_tab.pack(fill="both", expand=True)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(4, 14))

        ctk.CTkButton(
            bottom,
            text="💾 Сохранить файл",
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
            text="💾 Сохранить как…",
            width=160,
            height=36,
            command=self.save_as,
        ).pack(side="left", padx=4)
        ctk.CTkButton(bottom, text="🔄 Сбросить", width=120, height=36, command=self.reset_changes).pack(
            side="left", padx=4
        )
        ctk.CTkButton(bottom, text="📋 Бэкап", width=100, height=36, command=self.create_backup_manual).pack(
            side="left", padx=4
        )

    def set_status(self, text: str, color: str = STATUS_OK) -> None:
        self.status_label.configure(text=text, text_color=color)

    def _require_file(self) -> bool:
        if not self.handler.path:
            messagebox.showwarning(APP_NAME, MESSAGES["no_file"])
            return False
        return True

    def _autodetect_save(self) -> None:
        found = SaveHandler.find_default_saves()
        if not found:
            return
        newest = found[0]
        if messagebox.askyesno(
            APP_NAME,
            f"Найден экспорт Bitburner:\n{newest}\n\nОткрыть?",
        ):
            self.load_file(newest)

    def open_save_dialog(self) -> None:
        initial = SaveHandler.default_save_dir()
        path = filedialog.askopenfilename(
            title="Открыть экспорт Bitburner",
            initialdir=str(initial),
            filetypes=[
                ("Bitburner save", "*.json *.json.gz"),
                ("JSON", "*.json"),
                ("Gzip JSON", "*.json.gz"),
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
            messagebox.showerror(APP_NAME, str(exc))
            self.set_status(MESSAGES["not_loaded"], STATUS_ERROR)
            return

        self.path_var.set(str(path))
        self.backups.set_save_path(path)
        self._refresh_ui_from_handler()
        self.set_status(MESSAGES["load_ok"].format(name=path.name), STATUS_OK)

    def _refresh_ui_from_handler(self) -> None:
        self._snapshot = self.handler.get_snapshot()
        self.money_tab.set_money(self._snapshot.money)
        self.skills_tab.load_snapshot(self._snapshot)
        self.progress_tab.load_snapshot(self._snapshot)
        self.advanced_tab.set_json(self.handler.to_pretty_json())
        self.advanced_tab.set_file_info(self.handler.meta)
        self.advanced_tab.set_backups(self.backups.list_backups(5))

    def _collect_ui(self) -> SaveSnapshot:
        snap = self.handler.get_snapshot()
        snap.money = self.money_tab.get_money()
        snap.skills = self.skills_tab.get_skills()
        snap.bit_node = self.progress_tab.get_bitnode()
        exploits = list(snap.exploits)
        if self.progress_tab.want_edit_exploit():
            if EXPLOIT_EDIT_SAVE not in exploits:
                exploits.append(EXPLOIT_EDIT_SAVE)
        else:
            exploits = [e for e in exploits if e != EXPLOIT_EDIT_SAVE]
        snap.exploits = exploits
        return snap

    def _on_money_apply(self, value: float) -> None:
        if not self._require_file():
            return
        self.handler.set_money(value)
        self.advanced_tab.set_json(self.handler.to_pretty_json())
        self.set_status(f"● Деньги: {value:g}", STATUS_OK)

    def _on_skills_apply(self) -> None:
        if not self._require_file():
            return
        try:
            skills = self.skills_tab.get_skills()
            for key, value in skills.items():
                self.handler.set_skill(key, value)
            self.advanced_tab.set_json(self.handler.to_pretty_json())
            self.set_status("● Навыки применены (сохраните файл)", STATUS_OK)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))

    def _on_progress_apply(self) -> None:
        if not self._require_file():
            return
        try:
            snap = self._collect_ui()
            self.handler.apply_snapshot(snap)
            self.advanced_tab.set_json(self.handler.to_pretty_json())
            self.set_status("● Прогресс применён (сохраните файл)", STATUS_OK)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))

    def save_changes(self) -> None:
        if not self._require_file():
            return
        # Всегда пишем ОТДЕЛЬНЫЙ файл *_EDITED*, чтобы новый Export из игры
        # не затёр правки и было понятно, что импортировать.
        suggested = self.handler.suggested_edited_path()
        self._save_to_path(suggested)

    def save_as(self) -> None:
        if not self._require_file():
            return
        suggested = self.handler.suggested_edited_path() or Path.home() / "bitburnerSave_EDITED.json.gz"
        path = filedialog.asksaveasfilename(
            title="Сохранить изменённый сейв",
            initialdir=str(suggested.parent),
            initialfile=suggested.name,
            defaultextension=".json.gz",
            filetypes=[
                ("Bitburner gzip", "*.json.gz"),
                ("Bitburner json", "*.json"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._save_to_path(Path(path))

    def _save_to_path(self, dest: Path | None) -> None:
        if dest is None:
            messagebox.showerror(APP_NAME, "Не удалось выбрать путь сохранения.")
            return
        if SaveHandler.is_game_running():
            if not messagebox.askyesno(
                APP_NAME,
                MESSAGES["game_running"] + "\n\nВсё равно сохранить файл?",
            ):
                return
        try:
            snap = self._collect_ui()
            self.handler.apply_snapshot(snap)
            if self.handler.path and self.handler.path.exists():
                self.backups.set_save_path(self.handler.path)
                info = self.backups.create_backup(self.handler.path)
            else:
                info = None

            # Сохраняем в выбранный формат по расширению
            if dest.name.endswith(".json.gz"):
                self.handler.meta.format_kind = "gzip"
            elif dest.suffix == ".json":
                self.handler.meta.format_kind = "base64"

            saved = self.handler.save(dest)
            money_on_disk = self.handler.verify_money_on_disk(saved)
            self.path_var.set(str(saved))
            self.backups.set_save_path(saved)
            self._refresh_ui_from_handler()

            backup_line = f"\nБэкап: {info.display_name}" if info else ""
            messagebox.showinfo(
                APP_NAME,
                "✅ Файл с правками записан!\n\n"
                f"Путь:\n{saved}\n\n"
                f"Проверка money в файле: {money_on_disk:g}"
                f"{backup_line}\n\n"
                "Дальше ОБЯЗАТЕЛЬНО в Bitburner:\n"
                "1) Options → Import save / Import game\n"
                "2) Выберите именно этот файл (*_EDITED*)\n"
                "3) Дождитесь перезагрузки игры\n\n"
                "НЕ делайте Export снова — он затрёт правки старым сейвом!",
            )
            self.set_status(f"● Сохранено: {saved.name} · money={money_on_disk:g}", STATUS_OK)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("save failed")
            messagebox.showerror(APP_NAME, f"❌ Не удалось сохранить:\n{exc}")

    def reset_changes(self) -> None:
        if not self._require_file():
            return
        if not messagebox.askyesno(APP_NAME, "Сбросить несохранённые изменения?"):
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
            messagebox.showinfo(APP_NAME, MESSAGES["backup_ok"].format(name=info.display_name))
            self.set_status(MESSAGES["backup_ok"].format(name=info.display_name), STATUS_OK)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, f"❌ {exc}")

    def restore_backup(self, info: BackupInfo) -> None:
        if not self._require_file():
            return
        if not messagebox.askyesno(APP_NAME, f"Восстановить из:\n{info.display_name}?"):
            return
        try:
            self.backups.restore(info.path, self.handler.path)
            self.handler.load(self.handler.path)  # type: ignore[arg-type]
            self._refresh_ui_from_handler()
            messagebox.showinfo(APP_NAME, MESSAGES["restore_ok"].format(date=info.display_date))
            self.set_status(MESSAGES["restore_ok"].format(date=info.display_date), STATUS_OK)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, f"❌ {exc}")

    def refresh_json_from_fields(self) -> None:
        if not self._require_file():
            return
        try:
            snap = self._collect_ui()
            self.handler.apply_snapshot(snap)
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
            messagebox.showinfo(APP_NAME, "JSON применён. Нажмите «Сохранить файл».")
            self.set_status("● JSON применён", STATUS_WARN)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, MESSAGES["json_invalid"] + f"\n{exc}")
