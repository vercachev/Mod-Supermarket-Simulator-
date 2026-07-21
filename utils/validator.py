"""Валидация чисел Cookie Clicker."""

from __future__ import annotations

from utils.constants import MAX_COOKIES


class ValidationError(ValueError):
    pass


def validate_cookies(value: str | float | int | None) -> float:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError("❌ Введите число печенек (например 1000000 или 1e12)")
    try:
        if isinstance(value, str):
            cleaned = value.strip().replace(" ", "").replace(",", ".")
            num = float(cleaned)
        else:
            num = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("❌ Некорректное число") from exc
    if num < 0 or num > MAX_COOKIES or num != num:  # NaN check
        raise ValidationError("❌ Число вне допустимого диапазона")
    return num
