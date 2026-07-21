"""Вкладка «Прогресс»."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from save_handler import SaveSnapshot
from utils.constants import (
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    EXPLOIT_EDIT_SAVE,
    MAX_BITNODE,
    MIN_BITNODE,
)
from utils.validator import ValidationError, validate_bitnode


class ProgressTab(ctk.CTkFrame):
    def __init__(self, master, on_apply: Callable[[], None], **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_apply = on_apply
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="Прогресс и BitNode",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 12))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(row, text=f"BitNode (1–{MAX_BITNODE})", width=200, anchor="w").pack(
            side="left"
        )
        self.bitnode_var = ctk.StringVar(value="1")
        ctk.CTkEntry(row, textvariable=self.bitnode_var, width=120).pack(side="left")

        self.info_label = ctk.CTkLabel(
            self,
            text="",
            justify="left",
            anchor="w",
            text_color="#B0B0B0",
        )
        self.info_label.pack(anchor="w", padx=20, pady=12)

        self.exploit_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self,
            text=f"Добавить эксплойт «{EXPLOIT_EDIT_SAVE}» (достижение Edit Save)",
            variable=self.exploit_var,
        ).pack(anchor="w", padx=20, pady=8)

        ctk.CTkButton(
            self,
            text="Применить прогресс",
            width=220,
            height=40,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
            command=self._apply,
        ).pack(pady=16)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#E74C3C")
        self.error_label.pack()

        tip = ctk.CTkLabel(
            self,
            text=(
                "Подсказка: после правок сохраните файл и в Bitburner сделайте\n"
                "Options → Import game / Import save."
            ),
            text_color="#7F8C8D",
            justify="left",
        )
        tip.pack(anchor="w", padx=20, pady=10)

    def load_snapshot(self, snap: SaveSnapshot) -> None:
        self.bitnode_var.set(str(snap.bit_node))
        self.exploit_var.set(EXPLOIT_EDIT_SAVE in snap.exploits)
        hours = snap.playtime_ms / 1000 / 3600 if snap.playtime_ms else 0
        self.info_label.configure(
            text=(
                f"Карма: {snap.karma:g}\n"
                f"Фракций: {len(snap.factions)}\n"
                f"Эксплойтов: {len(snap.exploits)}\n"
                f"Наиграно (прибл.): {hours:.1f} ч\n"
                f"Hacking: {snap.hacking_level:g}"
            )
        )
        self.error_label.configure(text="")

    def get_bitnode(self) -> int:
        return validate_bitnode(self.bitnode_var.get())

    def want_edit_exploit(self) -> bool:
        return bool(self.exploit_var.get())

    def _apply(self) -> None:
        try:
            bn = self.get_bitnode()
            if bn < MIN_BITNODE or bn > MAX_BITNODE:
                raise ValidationError("Неверный BitNode")
            self.error_label.configure(text="")
            self.on_apply()
        except ValidationError as exc:
            self.error_label.configure(text=str(exc))
