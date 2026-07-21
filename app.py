"""Главное окно — простой редактор Cookie Clicker."""

from __future__ import annotations

import logging
import tkinter.messagebox as messagebox
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from save_handler import SaveHandler
from utils.backup import BackupManager
from utils.constants import (
    ACCENT,
    ACCENT_HOVER,
    APP_NAME,
    APP_TITLE,
    DEFAULT_EXPORT_DIR,
    MESSAGES,
    STATUS_ERROR,
    STATUS_IDLE,
    STATUS_OK,
    STATUS_WARN,
    WINDOW_SIZE,
    app_base_dir,
)
from utils.validator import ValidationError, validate_cookies

logger = logging.getLogger(__name__)


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.handler = SaveHandler()
        self.backups = BackupManager()

        icon = app_base_dir() / "assets" / "icon.ico"
        if icon.exists():
            try:
                self.iconbitmap(str(icon))
            except Exception:  # noqa: BLE001
                pass

        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=APP_TITLE,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ACCENT,
        ).pack(pady=14)

        tip = ctk.CTkLabel(
            self,
            text=(
                "1) В Cookie Clicker: Options → Export save (или Save to file)\n"
                "2) Откройте / вставьте код сюда → поставьте печеньки → Сохранить\n"
                "3) В игре: Options → Import save → вставьте новый код\n"
                "На экране игры сверху сразу будет видно новое число."
            ),
            justify="left",
            text_color="#AAAAAA",
            font=ctk.CTkFont(size=13),
        )
        tip.pack(anchor="w", padx=20, pady=(10, 6))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=6)
        ctk.CTkButton(
            btns,
            text="📂 Открыть файл сейва",
            width=180,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self.open_file,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btns,
            text="📋 Вставить из буфера",
            width=180,
            command=self.paste_clipboard,
        ).pack(side="left", padx=4)

        self.status = ctk.CTkLabel(self, text=MESSAGES["not_loaded"], text_color=STATUS_IDLE)
        self.status.pack(anchor="w", padx=20)

        self.info = ctk.CTkLabel(self, text="", text_color="#888888", justify="left")
        self.info.pack(anchor="w", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            self,
            text="Сейчас печенек:",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(8, 4))
        self.current_label = ctk.CTkLabel(
            self,
            text="—",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=ACCENT,
        )
        self.current_label.pack(pady=4)

        ctk.CTkLabel(self, text="Новое значение:").pack(pady=(12, 4))
        self.cookies_var = ctk.StringVar(value="1000000")
        ctk.CTkEntry(
            self,
            textvariable=self.cookies_var,
            width=320,
            height=44,
            justify="center",
            font=ctk.CTkFont(size=20, weight="bold"),
            border_color=ACCENT,
        ).pack(pady=4)

        quick = ctk.CTkFrame(self, fg_color="transparent")
        quick.pack(pady=8)
        for amount, label in (
            (1_000_000, "1 млн"),
            (1_000_000_000, "1 млрд"),
            (1e12, "1 трлн"),
            (1e15, "1 квадрилл."),
        ):
            ctk.CTkButton(
                quick,
                text=label,
                width=100,
                command=lambda a=amount: self.cookies_var.set(
                    str(int(a)) if a < 1e15 else f"{a:.0e}".replace("+0", "+")
                ),
                fg_color="#6E2C00",
                hover_color=ACCENT_HOVER,
            ).pack(side="left", padx=4)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(pady=18)
        ctk.CTkButton(
            bottom,
            text="💾 Сохранить файл + скопировать код",
            width=320,
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self.save_all,
        ).pack()

        self.err = ctk.CTkLabel(self, text="", text_color=STATUS_ERROR)
        self.err.pack(pady=4)

    def set_status(self, text: str, color: str = STATUS_OK) -> None:
        self.status.configure(text=text, text_color=color)

    def _refresh(self) -> None:
        snap = self.handler.get_snapshot()
        self.current_label.configure(text=f"{snap.cookies:,.0f}".replace(",", " "))
        self.cookies_var.set(str(int(snap.cookies)) if snap.cookies < 1e15 else f"{snap.cookies:.6g}")
        self.info.configure(
            text=f"Пекарня: {snap.bakery_name or '—'}   ·   версия сейва: {snap.version or '—'}"
        )

    def open_file(self) -> None:
        initial = Path(DEFAULT_EXPORT_DIR)
        if not initial.exists():
            initial = Path.home()
        path = filedialog.askopenfilename(
            title="Открыть сейв Cookie Clicker",
            initialdir=str(initial),
            filetypes=[
                ("Save / text", "*.txt *.cki *"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            self.handler.load(path)
            self.backups.set_save_path(Path(path))
            self._refresh()
            self.set_status(MESSAGES["load_ok"] + f": {Path(path).name}", STATUS_OK)
            self.err.configure(text="")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, str(exc))
            self.set_status(MESSAGES["not_loaded"], STATUS_ERROR)

    def paste_clipboard(self) -> None:
        try:
            text = self.clipboard_get()
        except Exception:  # noqa: BLE001
            messagebox.showerror(APP_NAME, "Буфер обмена пуст.")
            return
        try:
            self.handler.load_text(text)
            self._refresh()
            self.set_status(MESSAGES["load_ok"] + " (из буфера)", STATUS_OK)
            self.err.configure(text="")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, str(exc))

    def save_all(self) -> None:
        if not self.handler.sections:
            messagebox.showwarning(APP_NAME, MESSAGES["no_file"])
            return
        try:
            cookies = validate_cookies(self.cookies_var.get())
            self.handler.set_cookies(cookies)
            dest = self.handler.suggested_edited_path()
            if self.handler.path and self.handler.path.exists():
                try:
                    self.backups.set_save_path(self.handler.path)
                    self.backups.create_backup(self.handler.path)
                except Exception:  # noqa: BLE001
                    pass
            saved = self.handler.save(dest)
            export_str = self.handler.to_export_string()
            try:
                self.clipboard_clear()
                self.clipboard_append(export_str)
            except Exception:  # noqa: BLE001
                pass
            self._refresh()
            messagebox.showinfo(
                APP_NAME,
                "✅ Печеньки записаны!\n\n"
                f"В файле сейчас: {cookies:g}\n"
                f"Файл: {saved}\n\n"
                "Код уже скопирован в буфер обмена.\n\n"
                "В Cookie Clicker:\n"
                "Options → Import save → Ctrl+V → Load\n\n"
                "Сверху на экране должно стать огромное число печенек.",
            )
            self.set_status(f"● Сохранено: {saved.name} · cookies={cookies:g}", STATUS_OK)
            self.err.configure(text="")
        except ValidationError as exc:
            self.err.configure(text=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("save failed")
            messagebox.showerror(APP_NAME, f"❌ {exc}")
