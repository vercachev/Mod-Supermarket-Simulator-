"""Валидация ввода для Bitburner Save Editor."""

from __future__ import annotations

from utils.constants import (
    MAX_BITNODE,
    MAX_MONEY,
    MAX_SKILL,
    MESSAGES,
    MIN_BITNODE,
    MIN_SKILL,
)


class ValidationError(ValueError):
    pass


def parse_number(
    value: str | float | int | None,
    *,
    min_v: float = 0,
    max_v: float = MAX_MONEY,
    as_int: bool = False,
    field_name: str | None = None,
) -> float | int:
    prefix = f"{field_name}: " if field_name else ""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(
            prefix + MESSAGES["invalid_number"].format(min_v=min_v, max_v=max_v)
        )
    try:
        if isinstance(value, str):
            cleaned = value.strip().replace(" ", "").replace(",", ".")
            cleaned = cleaned.replace("$", "").replace("€", "")
            # 1e+12 / 1E12 — нормальная научная запись
            num: float | int = float(cleaned)
        else:
            num = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            prefix + MESSAGES["invalid_number"].format(min_v=min_v, max_v=max_v)
        ) from exc

    if as_int:
        if abs(num - round(num)) > 1e-9:
            raise ValidationError(
                prefix
                + MESSAGES["invalid_number"].format(min_v=int(min_v), max_v=int(max_v))
            )
        num = int(round(num))

    if num < min_v or num > max_v:
        raise ValidationError(
            prefix
            + MESSAGES["invalid_number"].format(
                min_v=int(min_v) if as_int else min_v,
                max_v=int(max_v) if as_int else max_v,
            )
        )
    return num


def validate_money(value: str | float | int | None) -> float:
    return float(
        parse_number(value, min_v=0, max_v=MAX_MONEY, as_int=False, field_name="Деньги")
    )


def validate_skill(value: str | float | int | None, skill_name: str = "Навык") -> float:
    return float(
        parse_number(
            value,
            min_v=MIN_SKILL,
            max_v=MAX_SKILL,
            as_int=False,
            field_name=skill_name,
        )
    )


def validate_bitnode(value: str | float | int | None) -> int:
    return int(
        parse_number(
            value,
            min_v=MIN_BITNODE,
            max_v=MAX_BITNODE,
            as_int=True,
            field_name="BitNode",
        )
    )