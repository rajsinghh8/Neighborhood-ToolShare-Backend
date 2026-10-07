"""Shared column type helpers."""
from __future__ import annotations

import enum
from decimal import Decimal

from sqlalchemy import Enum, Numeric


def str_enum(enum_cls: type[enum.Enum], length: int = 20) -> Enum:
    """Enum column persisted as VARCHAR holding the enum *value*."""
    return Enum(
        enum_cls,
        values_callable=lambda members: [m.value for m in members],
        native_enum=False,
        length=length,
        validate_strings=True,
    )


def money_column() -> Numeric:
    return Numeric(precision=14, scale=2, asdecimal=True)


ZERO = Decimal("0.00")
