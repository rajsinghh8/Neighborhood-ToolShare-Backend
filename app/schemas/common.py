"""Shared schema building blocks: money, UTC datetimes, name strings, base model."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer, StringConstraints

_TWO_PLACES = Decimal("0.01")


def format_money(value: Decimal) -> str:
    """Fixed 2-decimal string; never goes through float."""
    return f"{Decimal(value).quantize(_TWO_PLACES):.2f}"


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def format_datetime(value: datetime) -> str:
    return _to_naive_utc(value).isoformat() + "Z"


# Output money: Decimal in Python, "123.40" in JSON.
Money = Annotated[Decimal, PlainSerializer(format_money, return_type=str, when_used="json")]

# Input money (Decimal only, max 2 decimal places).
MoneyIn = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
PositiveMoneyIn = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]

# Datetimes are stored naive-UTC; input with an offset is converted, output ends in "Z".
UtcDatetime = Annotated[
    datetime,
    AfterValidator(_to_naive_utc),
    PlainSerializer(format_datetime, return_type=str, when_used="json"),
]

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class ApiModel(BaseModel):
    """Base for request and response schemas. Unknown request fields are ignored."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    def to_json(self) -> dict[str, Any]:
        """JSON-safe dict (Decimal -> 2dp string, datetime -> ISO-8601 Z)."""
        return self.model_dump(mode="json")

    def changes(self) -> dict[str, Any]:
        """Only the fields the client actually sent (for partial PUT updates)."""
        return {name: getattr(self, name) for name in self.model_fields_set}
