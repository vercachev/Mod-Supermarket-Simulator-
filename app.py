"""Главное окно — редактор сейвов Supermarket Together."""

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
    MESSAGES,
    STATUS_ERROR,
    STATUS_IDLE,
    STATUS_OK,
    STATUS_WARN,
    WINDOW_SIZE,
    app_base_dir,
    find_save_dir,
    list_store_files,
)
from utils.paths import (
    canonical_store_path,
    describe_path_risk,
    is_under_backups,
)
from utils.validator import (
    ValidationError,
    validate_funds,
    validate_int_field,
)

logger = logging.getLogger(__name__)


def _game_running() -> bool:
    try:
        import psutil

        from utils.constants import GAME_PROCESS_NAMES

        names = {n.lower() for n in GAME_PROCESS_NAMES}
        for proc in psutil.process_iter(["name"]):
            name = (proc.info.get("name") or "").lower()
            if name in names or "supermarket together" in name:
                return True
    except Exception:  # noqa: BLE001
        return False
    return False


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
        self.save_dir = find_save_dir()

        icon = app_base_dir() / "assets" / "icon.ico"
        if icon.exists():
            try:
                self.iconbitmap(str(icon))
            except Exception:  # noqa: BLE001
                pass

        self._build()
        self.after(200, self._startup_hints)

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="#14261C", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=APP_TITLE,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT,
        ).pack(pady=14)

        tip = ctk.CTkLabel(
            self,
            text=(
                "ВАЖНО: открывайте StoreFile0.es3 / StoreFile1.es3  —  НЕ файлы из папки backups\n"
                "1) Закройте игру  ·  2) Быстрый слот  ·  3) Деньги  ·  4) «Применить к игре»\n"
                "Steam Cloud должен быть выключен."
            ),
            justify="left",
            text_color="#CCCCCC",
            font=ctk.CTkFont(size=12),
        )
        tip.pack(anchor="w", padx=20, pady=(10, 4))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=6)
        ctk.CTkButton(
            btns,
            text="Открыть сейв",
            width=130,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self.open_file,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btns,
            text="Папка сейвов",
            width=120,
            command=self.open_save_folder,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btns,
            text="Слот 0",
            width=80,
            command=lambda: self._open_slot(0),
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btns,
            text="Слот 1",
            width=80,
            command=lambda: self._open_slot(1),
        ).pack(side="left", padx=3)

        self.status = ctk.CTkLabel(self, text=MESSAGES["not_loaded"], text_color=STATUS_IDLE)
        self.status.pack(anchor="w", padx=20)

        self.info = ctk.CTkLabel(self, text="", text_color="#888888", justify="left")
        self.info.pack(anchor="w", padx=20, pady=(0, 2))

        self.path_label = ctk.CTkLabel(
            self,
            text="",
            text_color="#AAAAAA",
            justify="left",
            font=ctk.CTkFont(size=11),
            wraplength=720,
        )
        self.path_label.pack(anchor="w", padx=20, pady=(0, 6))

        ctk.CTkLabel(
            self,
            text="Сейчас денег (Funds):",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(6, 2))
        self.current_label = ctk.CTkLabel(
            self,
            text="—",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=ACCENT,
        )
        self.current_label.pack(pady=2)

        ctk.CTkLabel(self, text="Новое значение Funds:").pack(pady=(10, 2))
        self.funds_var = ctk.StringVar(value="100000")
        ctk.CTkEntry(
            self,
            textvariable=self.funds_var,
            width=320,
            height=42,
            justify="center",
            font=ctk.CTkFont(size=20, weight="bold"),
            border_color=ACCENT,
        ).pack(pady=4)

        quick = ctk.CTkFrame(self, fg_color="transparent")
        quick.pack(pady=6)
        for amount, label in (
            (10_000, "10 тыс"),
            (100_000, "100 тыс"),
            (1_000_000, "1 млн"),
            (10_000_000, "10 млн"),
        ):
            ctk.CTkButton(
                quick,
                text=label,
                width=90,
                command=lambda a=amount: self.funds_var.set(str(a)),
                fg_color="#1E3D2F",
                hover_color=ACCENT_HOVER,
            ).pack(side="left", padx=3)

        extra = ctk.CTkFrame(self, fg_color="transparent")
        extra.pack(fill="x", padx=40, pady=(10, 4))
        self.fp_var = ctk.StringVar(value="0")
        self.fx_var = ctk.StringVar(value="0")
        self.lvl_var = ctk.StringVar(value="0")
        self._labeled_entry(extra, "Franchise Points", self.fp_var, 0)
        self._labeled_entry(extra, "Franchise Exp", self.fx_var, 1)
        self._labeled_entry(extra, "Last Awarded Level", self.lvl_var, 2)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(pady=14)
        ctk.CTkButton(
            bottom,
            text="Применить к игре (StoreFile)",
            width=340,
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self.apply_to_game,
        ).pack()
        ctk.CTkButton(
            bottom,
            text="Сохранить копию в Загрузки",
            width=300,
            height=32,
            fg_color="#333333",
            hover_color="#444444",
            command=self.save_copy,
        ).pack(pady=(8, 0))

        self.err = ctk.CTkLabel(self, text="", text_color=STATUS_ERROR)
        self.err.pack(pady=4)

    def _labeled_entry(
        self,
        parent: ctk.CTkFrame,
        label: str,
        var: ctk.StringVar,
        col: int,
    ) -> None:
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=0, column=col, padx=8)
        ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=11)).pack()
        ctk.CTkEntry(box, textvariable=var, width=140, justify="center").pack()

    def _startup_hints(self) -> None:
        if _game_running():
            self.set_status(MESSAGES["game_running"], STATUS_WARN)
            messagebox.showwarning(APP_NAME, MESSAGES["game_running"])
        elif self.save_dir:
            files = list_store_files(self.save_dir)
            names = ", ".join(p.name for p in files[:5]) or "нет StoreFile*.es3"
            self.info.configure(
                text=f"Папка сейвов: {self.save_dir}\nНайдено: {names}"
            )
        else:
            self.info.configure(
                text="Папка сейвов не найдена автоматически — откройте StoreFile вручную."
            )

    def set_status(self, text: str, color: str = STATUS_OK) -> None:
        self.status.configure(text=text, text_color=color)

    def _refresh(self) -> None:
        snap = self.handler.get_snapshot()
        self.current_label.configure(text=f"{snap.funds:,.2f}".replace(",", " "))
        if snap.funds == int(snap.funds):
            self.funds_var.set(str(int(snap.funds)))
        else:
            self.funds_var.set(f"{snap.funds:.2f}")
        self.fp_var.set(str(snap.franchise_points))
        self.fx_var.set(str(snap.franchise_experience))
        self.lvl_var.set(str(snap.last_awarded_level))
        name = snap.store_name or snap.supermarket_name or "—"
        path = self.handler.path
        self.info.configure(text=f"Магазин: {name}   ·   день: {snap.day}")
        if path:
            risk = describe_path_risk(path)
            color = STATUS_WARN if risk else "#AAAAAA"
            self.path_label.configure(text=f"Файл: {path}", text_color=color)
            if risk:
                self.err.configure(text=risk.split("\n")[0])
            else:
                self.err.configure(text="")
        else:
            self.path_label.configure(text="")

    def open_save_folder(self) -> None:
        folder = self.save_dir or find_save_dir()
        if folder is None or not folder.exists():
            messagebox.showinfo(
                APP_NAME,
                "Папка не найдена.\nОбычно:\n"
                "%USERPROFILE%\\AppData\\LocalLow\\DDTNL\\Supermarket Together",
            )
            return
        try:
            import os

            os.startfile(str(folder))  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            messagebox.showinfo(APP_NAME, str(folder))

    def _open_slot(self, index: int) -> None:
        folder = self.save_dir or find_save_dir()
        if folder is None:
            messagebox.showwarning(APP_NAME, "Папка сейвов не найдена.")
            return
        path = folder / f"StoreFile{index}.es3"
        if not path.exists():
            messagebox.showwarning(APP_NAME, f"Нет файла:\n{path}")
            return
        self._load_path(path)

    def open_file(self) -> None:
        initial = self.save_dir or find_save_dir() or Path.home()
        path = filedialog.askopenfilename(
            title="Открыть StoreFileN.es3 (НЕ из backups)",
            initialdir=str(initial),
            filetypes=[
                ("Easy Save 3", "*.es3"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self._load_path(Path(path))

    def _load_path(self, path: Path) -> None:
        try:
            if _game_running():
                messagebox.showwarning(APP_NAME, MESSAGES["game_running"])

            if is_under_backups(path):
                target = canonical_store_path(path)
                messagebox.showwarning(
                    APP_NAME,
                    "Вы открыли файл из папки backups.\n"
                    "Игра его НЕ использует.\n\n"
                    f"Открываю вместо него:\n{target}",
                )
                if not target.exists():
                    messagebox.showerror(
                        APP_NAME,
                        f"Основной сейв не найден:\n{target}\n\n"
                        "Скопируйте нужный файл в папку игры как StoreFile1.es3",
                    )
                    return
                path = target

            self.handler.load(path)
            if path.stat().st_size < 400:
                messagebox.showwarning(
                    APP_NAME,
                    f"Файл очень маленький ({path.stat().st_size} байт).\n"
                    "Похоже на пустой/битый сейв. Возьмите другой StoreFile.",
                )
            self.backups.set_save_path(path)
            self.save_dir = path.parent
            self._refresh()
            self.set_status(MESSAGES["load_ok"] + f": {path.name}", STATUS_OK)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(APP_NAME, str(exc))
            self.set_status(MESSAGES["not_loaded"], STATUS_ERROR)

    def _apply_fields(self) -> float:
        funds = validate_funds(self.funds_var.get())
        self.handler.set_funds(funds)
        self.handler.set_franchise_points(
            validate_int_field(self.fp_var.get(), "Franchise Points")
        )
        self.handler.set_franchise_experience(
            validate_int_field(self.fx_var.get(), "Franchise Exp")
        )
        self.handler.set_last_awarded_level(
            validate_int_field(self.lvl_var.get(), "Last Awarded Level")
        )
        return funds

    def apply_to_game(self) -> None:
        """Главная кнопка: всегда пишет в канонический StoreFileN.es3."""
        if not self.handler.data:
            messagebox.showwarning(APP_NAME, MESSAGES["no_file"])
            return
        if _game_running():
            messagebox.showerror(
                APP_NAME,
                "Игра запущена — нельзя писать сейв.\nЗакройте игру полностью и повторите.",
            )
            return

        target = self.handler.target_game_path()
        if target is None:
            folder = self.save_dir or find_save_dir()
            if folder is None:
                messagebox.showerror(APP_NAME, "Не найдена папка сейвов игры.")
                return
            target = folder / "StoreFile1.es3"

        if not messagebox.askyesno(
            APP_NAME,
            "Записать деньги ПРЯМО в сейв игры?\n\n"
            f"{target}\n\n"
            "Сначала будет бэкап. Steam Cloud должен быть выключен.",
        ):
            return

        try:
            funds = self._apply_fields()
            # если открыт другой файл — грузим/пишем в target, но патчим текущие данные
            if self.handler.path != target and target.exists():
                # переносим правки на актуальный игровой файл
                pending_funds = funds
                pending_fp = int(self.fp_var.get() or 0)
                pending_fx = int(self.fx_var.get() or 0)
                pending_lvl = int(self.lvl_var.get() or 0)
                self.handler.load(target)
                self.handler.set_funds(pending_funds)
                self.handler.set_franchise_points(pending_fp)
                self.handler.set_franchise_experience(pending_fx)
                self.handler.set_last_awarded_level(pending_lvl)
                funds = pending_funds

            if target.exists():
                self.backups.set_save_path(target)
                backup = self.backups.create_backup(target)
            else:
                backup = None
                target.parent.mkdir(parents=True, exist_ok=True)

            saved = self.handler.save(target)
            # verify on disk
            verify = SaveHandler()
            verify.load(saved)
            got = verify.get_snapshot().funds
            self._refresh()
            msg = (
                "✅ ГОТОВО — деньги в файле игры!\n\n"
                f"Funds в файле: {got:g}\n"
                f"Записано в:\n{saved}\n"
                f"Размер: {saved.stat().st_size} байт\n"
            )
            if backup:
                msg += f"\nБэкап: {backup.path.name}\n"
            msg += (
                "\nТеперь:\n"
                "1) Запустите игру\n"
                "2) Откройте ЭТОТ магазин (тот же слот)\n"
                "3) Сразу смотрите деньги — не ждите автосейв"
            )
            messagebox.showinfo(APP_NAME, msg)
            self.set_status(f"● Применено к игре: {saved.name} · Funds={got:g}", STATUS_OK)
            self.err.configure(text="")
        except ValidationError as exc:
            self.err.configure(text=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("apply_to_game failed")
            messagebox.showerror(APP_NAME, f"❌ {exc}")

    def save_copy(self) -> None:
        if not self.handler.data:
            messagebox.showwarning(APP_NAME, MESSAGES["no_file"])
            return
        try:
            funds = self._apply_fields()
            dest = self.handler.suggested_edited_path()
            saved = self.handler.save(dest)
            self._refresh()
            messagebox.showinfo(
                APP_NAME,
                "Копия сохранена в Загрузки.\n\n"
                f"{saved}\n\n"
                "Чтобы сработало в игре, лучше нажать\n"
                "«Применить к игре» — это надёжнее.",
            )
            self.set_status(f"● Копия: {saved.name} · Funds={funds:g}", STATUS_OK)
        except ValidationError as exc:
            self.err.configure(text=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("save_copy failed")
            messagebox.showerror(APP_NAME, f"❌ {exc}")
