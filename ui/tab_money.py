"""Вкладка «Деньги»."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from utils.constants import ACCENT_GREEN, ACCENT_GREEN_HOVER, MAX_FUNDS
from utils.validator import ValidationError, validate_funds


class MoneyTab(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_apply: Callable[[float], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_apply = on_apply
        self._build()

    def _build(self) -> None:
        title = ctk.CTkLabel(
            self,
            text="Текущий баланс:",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(pady=(28, 12))

        self.funds_var = ctk.StringVar(value="0")
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.funds_var,
            width=320,
            height=48,
            justify="center",
            font=ctk.CTkFont(size=24, weight="bold"),
            border_color=ACCENT_GREEN,
        )
        self.entry.pack(pady=8)

        hint = ctk.CTkLabel(
            self,
            text=f"Только числа · максимум {MAX_FUNDS:,}".replace(",", " "),
            text_color="#7F8C8D",
            font=ctk.CTkFont(size=12),
        )
        hint.pack(pady=(0, 16))

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(pady=4)
        for amount in (10_000, 50_000, 100_000, 500_000):
            ctk.CTkButton(
                row1,
                text=f"+{amount:,} $".replace(",", " "),
                width=120,
                command=lambda a=amount: self._add(a),
                fg_color="#1E8449",
                hover_color=ACCENT_GREEN_HOVER,
            ).pack(side="left", padx=4)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(pady=8)
        for amount in (1_000_000, 9_999_999):
            ctk.CTkButton(
                row2,
                text=f"Установить {amount:,} $".replace(",", " "),
                width=200,
                command=lambda a=amount: self.set_funds(a),
                fg_color="#145A32",
                hover_color=ACCENT_GREEN_HOVER,
            ).pack(side="left", padx=6)

        ctk.CTkButton(
            self,
            text="Применить сумму",
            width=220,
            height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
            command=self._apply,
        ).pack(pady=20)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#E74C3C")
        self.error_label.pack()

    def set_funds(self, value: float | int) -> None:
        self.funds_var.set(str(int(value) if float(value).is_integer() else value))
        self.error_label.configure(text="")

    def get_funds(self) -> float:
        return validate_funds(self.funds_var.get())

    def _add(self, amount: int) -> None:
        try:
            current = validate_funds(self.funds_var.get())
        except ValidationError:
            current = 0.0
        new_val = min(MAX_FUNDS, current + amount)
        self.set_funds(new_val)

    def _apply(self) -> None:
        try:
            value = self.get_funds()
            self.error_label.configure(text="")
            self.on_apply(value)
        except ValidationError as exc:
            self.error_label.configure(text=str(exc))
