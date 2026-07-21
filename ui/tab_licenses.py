"""Вкладка «Лицензии»."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from utils.constants import (
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    ALL_LICENSE_IDS,
    BASIC_LICENSE_ID,
    LICENSES,
)


class LicensesTab(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_change: Callable[[list[int]], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_change = on_change
        self._vars: dict[int, ctk.BooleanVar] = {}
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        self.status_label = ctk.CTkLabel(
            header,
            text="Разблокировано: 0 из 0",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.status_label.pack(side="left")

        btns = ctk.CTkFrame(header, fg_color="transparent")
        btns.pack(side="right")
        ctk.CTkButton(
            btns,
            text="Разблокировать все лицензии",
            width=220,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
            command=self.unlock_all,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btns,
            text="Сбросить лицензии",
            width=160,
            fg_color="#922B21",
            hover_color="#C0392B",
            command=self.reset_basic,
        ).pack(side="left", padx=4)

        warn = ctk.CTkLabel(
            self,
            text=(
                "⚠️ В игре лицензии имеют ID 21–47. Значения ниже 21 могут сломать "
                "прогресс разблокировки на компьютере."
            ),
            text_color="#F39C12",
            font=ctk.CTkFont(size=11),
            wraplength=820,
            justify="left",
        )
        warn.pack(anchor="w", padx=16, pady=(0, 6))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=("gray90", "#1A1A1A"))
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=8)

        for lid, title in LICENSES.items():
            var = ctk.BooleanVar(value=False)
            self._vars[lid] = var
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            cb = ctk.CTkCheckBox(
                row,
                text=f"ID {lid}  —  {title}",
                variable=var,
                command=self._emit,
                font=ctk.CTkFont(size=13),
            )
            cb.pack(anchor="w", padx=8)

        self._update_status()

    def set_licenses(self, licenses: list[int]) -> None:
        selected = set(int(x) for x in licenses)
        for lid, var in self._vars.items():
            var.set(lid in selected)
        self._update_status()

    def get_licenses(self) -> list[int]:
        result = [lid for lid, var in self._vars.items() if var.get()]
        if BASIC_LICENSE_ID not in result:
            result.insert(0, BASIC_LICENSE_ID)
            self._vars[BASIC_LICENSE_ID].set(True)
        return sorted(set(result))

    def unlock_all(self) -> None:
        for lid in ALL_LICENSE_IDS:
            self._vars[lid].set(True)
        self._emit()

    def reset_basic(self) -> None:
        for lid, var in self._vars.items():
            var.set(lid == BASIC_LICENSE_ID)
        self._emit()

    def _emit(self) -> None:
        self._update_status()
        self.on_change(self.get_licenses())

    def _update_status(self) -> None:
        unlocked = sum(1 for var in self._vars.values() if var.get())
        total = len(self._vars)
        self.status_label.configure(text=f"Разблокировано: {unlocked} из {total}")
