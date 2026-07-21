"""Вкладка «Деньги»."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from utils.constants import ACCENT_GREEN, ACCENT_GREEN_HOVER, MAX_MONEY
from utils.validator import ValidationError, validate_money


class MoneyTab(ctk.CTkFrame):
    def __init__(self, master, on_apply: Callable[[float], None], **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_apply = on_apply
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Деньги (money):", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(28, 12))

        self.money_var = ctk.StringVar(value="1000")
        ctk.CTkEntry(
            self,
            textvariable=self.money_var,
            width=360,
            height=48,
            justify="center",
            font=ctk.CTkFont(size=22, weight="bold"),
            border_color=ACCENT_GREEN,
        ).pack(pady=8)

        ctk.CTkLabel(
            self,
            text="Можно научную запись: 1e12  ·  максимум очень большой",
            text_color="#7F8C8D",
            font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 12))

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(pady=4)
        for amount in (1e6, 1e9, 1e12, 1e15):
            label = f"+{amount:.0e} $".replace("+1e+", "+1e")
            ctk.CTkButton(
                row1,
                text=f"+{amount:g}",
                width=110,
                command=lambda a=amount: self._add(a),
                fg_color="#1E8449",
                hover_color=ACCENT_GREEN_HOVER,
            ).pack(side="left", padx=4)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(pady=8)
        for amount in (1e18, 1e21):
            ctk.CTkButton(
                row2,
                text=f"Установить {amount:g}",
                width=180,
                command=lambda a=amount: self.set_money(a),
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

    def set_money(self, value: float | int) -> None:
        if abs(value) >= 1e6:
            self.money_var.set(f"{value:.6g}")
        else:
            self.money_var.set(str(int(value) if float(value).is_integer() else value))
        self.error_label.configure(text="")

    def get_money(self) -> float:
        return validate_money(self.money_var.get())

    def _add(self, amount: float) -> None:
        try:
            current = validate_money(self.money_var.get())
        except ValidationError:
            current = 0.0
        self.set_money(min(MAX_MONEY, current + amount))

    def _apply(self) -> None:
        try:
            value = self.get_money()
            self.error_label.configure(text="")
            self.on_apply(value)
        except ValidationError as exc:
            self.error_label.configure(text=str(exc))
