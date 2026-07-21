"""Вкладка «Навыки»."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from save_handler import SaveSnapshot
from utils.constants import ACCENT_GREEN, ACCENT_GREEN_HOVER, SKILL_KEYS
from utils.validator import ValidationError, validate_skill


class SkillsTab(ctk.CTkScrollableFrame):
    def __init__(self, master, on_apply: Callable[[], None], **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_apply = on_apply
        self._vars: dict[str, ctk.StringVar] = {}
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="Навыки персонажа",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 10))

        for key, title in SKILL_KEYS.items():
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=title, width=160, anchor="w").pack(side="left")
            var = ctk.StringVar(value="1")
            self._vars[key] = var
            ctk.CTkEntry(row, textvariable=var, width=160).pack(side="left", padx=8)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)
        for level in (100, 1000, 2500):
            ctk.CTkButton(
                btn_row,
                text=f"Все → {level}",
                width=120,
                command=lambda lv=level: self._set_all(lv),
                fg_color="#1E8449",
                hover_color=ACCENT_GREEN_HOVER,
            ).pack(side="left", padx=4)

        ctk.CTkButton(
            self,
            text="Применить навыки",
            width=220,
            height=40,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
            command=self._apply,
        ).pack(pady=8)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#E74C3C")
        self.error_label.pack()

    def load_snapshot(self, snap: SaveSnapshot) -> None:
        for key, var in self._vars.items():
            value = snap.skills.get(key, 1)
            var.set(str(int(value) if float(value).is_integer() else value))
        self.error_label.configure(text="")

    def get_skills(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for key, var in self._vars.items():
            result[key] = float(validate_skill(var.get()))
        return result

    def _set_all(self, level: int) -> None:
        for var in self._vars.values():
            var.set(str(level))

    def _apply(self) -> None:
        try:
            self.get_skills()
            self.error_label.configure(text="")
            self.on_apply()
        except ValidationError as exc:
            self.error_label.configure(text=str(exc))
