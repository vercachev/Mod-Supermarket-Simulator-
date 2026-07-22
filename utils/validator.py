"""Валидация полей Supermarket Together."""

from __future__ import annotations

from utils.constants import MAX_FUNDS, MAX_INT_FIELD


class ValidationError(ValueError):
    pass


def _parse_number(value: str | float | int | None, label: str) -> float:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f"❌ Введите {label}")
    try:
        if isinstance(value, str):
            cleaned = value.strip().replace(" ", "").replace(",", ".")
            return float(cleaned)
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"❌ Некорректное число ({label})") from exc


def validate_funds(value: str | float | int | None) -> float:
    num = _parse_number(value, "деньги (Funds)")
    if num < 0 or num > MAX_FUNDS or num != num:
        raise ValidationError("❌ Funds вне допустимого диапазона")
    return num


def validate_int_field(value: str | float | int | None, label: str) -> int:
    num = _parse_number(value, label)
    if num < 0 or num > MAX_INT_FIELD or num != int(num):
        raise ValidationError(f"❌ {label}: нужно целое число ≥ 0")
    return int(num)
