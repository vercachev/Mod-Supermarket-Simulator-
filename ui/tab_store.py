"""Вкладка «Магазин»."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from save_handler import SaveSnapshot
from utils.constants import (
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    MAX_CHECKOUTS,
    MAX_EMPLOYEES,
    MAX_SHELVES,
)
from utils.validator import (
    ValidationError,
    validate_checkouts,
    validate_day,
    validate_employees,
    validate_shelves,
    validate_store_level,
    validate_store_name,
)


class StoreTab(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_apply: Callable[[SaveSnapshot], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_apply = on_apply
        self._build()

    def _row(self, parent: ctk.CTkFrame, label: str) -> tuple[ctk.CTkFrame, ctk.StringVar]:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=6, padx=20)
        ctk.CTkLabel(frame, text=label, width=220, anchor="w").pack(side="left")
        var = ctk.StringVar(value="")
        entry = ctk.CTkEntry(frame, textvariable=var, width=200)
        entry.pack(side="left", padx=8)
        return frame, var

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="Информация о магазине",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(16, 10), anchor="w", padx=20)

        # Название
        name_row, self.store_name_var = self._row(self, "Название магазина")
        ctk.CTkButton(
            name_row,
            text="Применить",
            width=100,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
            command=self._apply_name_only,
        ).pack(side="left", padx=4)

        # День
        day_row, self.day_var = self._row(self, "Текущий день")
        for delta, label in ((1, "+1"), (7, "+7"), (30, "+30")):
            ctk.CTkButton(
                day_row,
                text=label,
                width=48,
                command=lambda d=delta: self._add_day(d),
            ).pack(side="left", padx=2)

        # Кассы / полки / сотрудники
        _, self.checkout_var = self._row(self, f"Количество касс (0–{MAX_CHECKOUTS})")
        _, self.shelf_var = self._row(self, f"Количество полок (0–{MAX_SHELVES})")
        _, self.employee_var = self._row(self, f"Количество сотрудников (0–{MAX_EMPLOYEES})")

        # Доп. поля из реальной структуры сохранения
        _, self.store_level_var = self._row(self, "Уровень магазина")
        _, self.completed_var = self._row(self, "Завершённые кассы (стат.)")

        note = ctk.CTkLabel(
            self,
            text=(
                "Примечание: кассы/полки/сотрудники пишутся в файл, если ключи есть "
                "в сохранении. Уровень и день — стандартные поля Progression."
            ),
            text_color="#7F8C8D",
            wraplength=760,
            justify="left",
            font=ctk.CTkFont(size=11),
        )
        note.pack(padx=20, pady=(4, 10), anchor="w")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=12)
        ctk.CTkButton(
            btn_row,
            text="Максимум всего",
            width=160,
            command=self._set_max,
            fg_color="#1E8449",
            hover_color=ACCENT_GREEN_HOVER,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            btn_row,
            text="Применить изменения",
            width=200,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            text_color="#0B1A12",
            command=self._apply_all,
        ).pack(side="left", padx=6)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#E74C3C")
        self.error_label.pack(pady=4)

    def load_snapshot(self, snap: SaveSnapshot) -> None:
        self.store_name_var.set(snap.store_name or "")
        self.day_var.set(str(snap.day))
        self.checkout_var.set("" if snap.checkout_count is None else str(snap.checkout_count))
        self.shelf_var.set("" if snap.shelf_count is None else str(snap.shelf_count))
        self.employee_var.set("" if snap.employee_count is None else str(snap.employee_count))
        self.store_level_var.set("" if snap.store_level is None else str(snap.store_level))
        self.completed_var.set(
            "" if snap.completed_checkouts is None else str(snap.completed_checkouts)
        )
        self.error_label.configure(text="")

    def _add_day(self, delta: int) -> None:
        try:
            current = validate_day(self.day_var.get())
        except ValidationError:
            current = 1
        self.day_var.set(str(min(9999, current + delta)))

    def _set_max(self) -> None:
        self.checkout_var.set(str(MAX_CHECKOUTS))
        self.shelf_var.set(str(MAX_SHELVES))
        self.employee_var.set(str(MAX_EMPLOYEES))

    def _optional_int(self, raw: str, validator) -> int | None:
        if not raw.strip():
            return None
        return int(validator(raw))

    def build_partial_snapshot(self, base: SaveSnapshot) -> SaveSnapshot:
        name = self.store_name_var.get().strip()
        if name:
            name = validate_store_name(name)
        else:
            name = base.store_name

        day = validate_day(self.day_var.get())
        checkout = self._optional_int(self.checkout_var.get(), validate_checkouts)
        shelf = self._optional_int(self.shelf_var.get(), validate_shelves)
        employees = self._optional_int(self.employee_var.get(), validate_employees)
        level = self._optional_int(self.store_level_var.get(), validate_store_level)
        completed = self._optional_int(self.completed_var.get(), validate_day)

        return SaveSnapshot(
            money=base.money,
            store_name=name,
            day=day,
            licenses=list(base.licenses),
            checkout_count=checkout if checkout is not None else base.checkout_count,
            shelf_count=shelf if shelf is not None else base.shelf_count,
            employee_count=employees if employees is not None else base.employee_count,
            completed_checkouts=completed if completed is not None else base.completed_checkouts,
            store_level=level if level is not None else base.store_level,
            store_upgrade=base.store_upgrade,
        )

    def _apply_name_only(self) -> None:
        try:
            validate_store_name(self.store_name_var.get())
            self.error_label.configure(text="")
            # Родитель применит через общий snapshot
            self._apply_all()
        except ValidationError as exc:
            self.error_label.configure(text=str(exc))

    def _apply_all(self) -> None:
        # Реальная валидация — в app через build_partial_snapshot
        try:
            # Быстрая проверка полей
            if self.store_name_var.get().strip():
                validate_store_name(self.store_name_var.get())
            validate_day(self.day_var.get())
            if self.checkout_var.get().strip():
                validate_checkouts(self.checkout_var.get())
            if self.shelf_var.get().strip():
                validate_shelves(self.shelf_var.get())
            if self.employee_var.get().strip():
                validate_employees(self.employee_var.get())
            if self.store_level_var.get().strip():
                validate_store_level(self.store_level_var.get())
            self.error_label.configure(text="")
            # Передаём пустой snapshot-маркер; app соберёт актуальный
            self.on_apply(SaveSnapshot())
        except ValidationError as exc:
            self.error_label.configure(text=str(exc))
