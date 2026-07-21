"""Вкладка «Прочее» — бэкапы, JSON, инфо."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from save_handler import FileMeta
from utils.backup import BackupInfo
from utils.constants import ACCENT_GREEN, ACCENT_GREEN_HOVER, DANGER_RED


class AdvancedTab(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        on_create_backup: Callable[[], None],
        on_restore_backup: Callable[[BackupInfo], None],
        on_refresh_json: Callable[[], None],
        on_apply_json: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_create_backup = on_create_backup
        self.on_restore_backup = on_restore_backup
        self.on_refresh_json = on_refresh_json
        self.on_apply_json = on_apply_json
        self._build()

    def _section_title(self, text: str) -> None:
        ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=16, pady=(16, 6)
        )

    def _build(self) -> None:
        self._section_title("Резервные копии")
        ctk.CTkButton(
            self,
            text="Создать резервную копию",
            width=240,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
            command=self.on_create_backup,
        ).pack(anchor="w", padx=16, pady=4)

        self.backups_frame = ctk.CTkFrame(self, fg_color=("gray90", "#1A1A1A"))
        self.backups_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(
            self.backups_frame, text="Резервных копий пока нет.", text_color="#7F8C8D"
        ).pack(pady=8)

        self._section_title("Редактор JSON")
        ctk.CTkLabel(
            self,
            text="⚠️ Осторожно: неверный JSON повредит сохранение!",
            text_color=DANGER_RED,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16)

        self.json_box = ctk.CTkTextbox(
            self, height=220, font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.json_box.pack(fill="x", padx=16, pady=8)

        json_btns = ctk.CTkFrame(self, fg_color="transparent")
        json_btns.pack(anchor="w", padx=16, pady=4)
        ctk.CTkButton(
            json_btns, text="Обновить JSON из полей", width=200, command=self.on_refresh_json
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            json_btns,
            text="Применить JSON напрямую",
            width=220,
            fg_color="#922B21",
            hover_color="#C0392B",
            command=lambda: self.on_apply_json(self.get_json()),
        ).pack(side="left", padx=4)

        self._section_title("Инфо о файле")
        self.info_label = ctk.CTkLabel(
            self, text="Файл не загружен", justify="left", anchor="w"
        )
        self.info_label.pack(anchor="w", padx=16, pady=(0, 20))

    def set_json(self, text: str) -> None:
        self.json_box.delete("1.0", "end")
        self.json_box.insert("1.0", text)

    def get_json(self) -> str:
        return self.json_box.get("1.0", "end").rstrip("\n")

    def set_backups(self, backups: list[BackupInfo]) -> None:
        for child in self.backups_frame.winfo_children():
            child.destroy()
        if not backups:
            ctk.CTkLabel(
                self.backups_frame, text="Резервных копий пока нет.", text_color="#7F8C8D"
            ).pack(pady=8)
            return
        for info in backups:
            row = ctk.CTkFrame(self.backups_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=3)
            ctk.CTkLabel(
                row, text=f"{info.display_name}  ·  {info.display_date}", anchor="w"
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row,
                text="Восстановить",
                width=120,
                command=lambda b=info: self.on_restore_backup(b),
            ).pack(side="right")

    def set_file_info(self, meta: FileMeta | None) -> None:
        if meta is None or meta.path is None:
            self.info_label.configure(text="Файл не загружен")
            return
        modified = meta.modified.strftime("%Y-%m-%d %H:%M:%S") if meta.modified else "—"
        version = meta.game_version or "не указана"
        text = (
            f"Путь: {meta.path}\n"
            f"Размер: {meta.size / 1024:.1f} КБ\n"
            f"Изменён: {modified}\n"
            f"Формат файла: {meta.format_kind}\n"
            f"Версия игры: {version}"
        )
        self.info_label.configure(text=text)
