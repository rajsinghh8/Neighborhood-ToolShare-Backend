"""Request/response schemas for expenses."""
from __future__ import annotations

from datetime import date

from pydantic import Field, StrictInt, model_validator

from app.schemas.common import ApiModel, Money, PositiveMoneyIn

DescriptionStr = Field(min_length=1, max_length=500)


class ExpenseCreate(ApiModel):
    """POST body."""

    category_id: StrictInt
    description: str = DescriptionStr
    amount: PositiveMoneyIn
    incurred_on: date


class ExpenseUpdate(ApiModel):
    """PUT body: only the sent fields change; sent fields may not be null."""

    category_id: StrictInt | None = None
    description: str | None = Field(default=None, min_length=1, max_length=500)
    amount: PositiveMoneyIn | None = None
    incurred_on: date | None = None

    @model_validator(mode="after")
    def _no_explicit_nulls(self) -> "ExpenseUpdate":
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} must not be null")
        return self


class ExpenseOut(ApiModel):
    """Expense response."""

    id: int
    event_id: int
    category_id: int
    description: str
    amount: Money
    incurred_on: date
