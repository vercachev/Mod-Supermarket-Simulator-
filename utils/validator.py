"""Валидация пользовательского ввода."""

from __future__ import annotations

from utils.constants import (
    MAX_CHECKOUTS,
    MAX_DAYS,
    MAX_EMPLOYEES,
    MAX_FUNDS,
    MAX_SHELVES,
    MAX_STORE_LEVEL,
    MESSAGES,
)


class ValidationError(ValueError):
    """Ошибка валидации с сообщением для UI."""


def parse_number(
    value: str | float | int | None,
    *,
    min_v: float = 0,
    max_v: float = MAX_FUNDS,
    as_int: bool = False,
) -> float | int:
    """Парсит число из строки/значения и проверяет диапазон."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(MESSAGES["invalid_number"].format(min_v=min_v, max_v=max_v))

    try:
        if isinstance(value, str):
            cleaned = value.strip().replace(" ", "").replace(",", ".")
            # Убираем символ валюты, если пользователь вставил
            cleaned = cleaned.replace("$", "").replace("€", "")
            num: float | int = float(cleaned)
        else:
            num = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            MESSAGES["invalid_number"].format(min_v=min_v, max_v=max_v)
        ) from exc

    if as_int:
        if abs(num - round(num)) > 1e-9:
            raise ValidationError(
                MESSAGES["invalid_number"].format(min_v=int(min_v), max_v=int(max_v))
            )
        num = int(round(num))

    if num < min_v or num > max_v:
        raise ValidationError(
            MESSAGES["invalid_number"].format(
                min_v=int(min_v) if as_int else min_v,
                max_v=int(max_v) if as_int else max_v,
            )
        )
    return num


def validate_funds(value: str | float | int | None) -> float:
    return float(parse_number(value, min_v=0, max_v=MAX_FUNDS, as_int=False))


def validate_day(value: str | float | int | None) -> int:
    return int(parse_number(value, min_v=1, max_v=MAX_DAYS, as_int=True))


def validate_checkouts(value: str | float | int | None) -> int:
    return int(parse_number(value, min_v=0, max_v=MAX_CHECKOUTS, as_int=True))


def validate_shelves(value: str | float | int | None) -> int:
    return int(parse_number(value, min_v=0, max_v=MAX_SHELVES, as_int=True))


def validate_employees(value: str | float | int | None) -> int:
    return int(parse_number(value, min_v=0, max_v=MAX_EMPLOYEES, as_int=True))


def validate_store_level(value: str | float | int | None) -> int:
    return int(parse_number(value, min_v=1, max_v=MAX_STORE_LEVEL, as_int=True))


def validate_store_name(value: str | None) -> str:
    name = (value or "").strip()
    if not name:
        raise ValidationError("❌ Название магазина не может быть пустым.")
    if len(name) > 64:
        raise ValidationError("❌ Название магазина слишком длинное (макс. 64 символа).")
    return name
