"""Request/response schemas for budget categories."""
from __future__ import annotations

from typing import Any

from pydantic import model_validator

from app.schemas.common import ApiModel, Money, MoneyIn, NameStr


class BudgetCategoryCreate(ApiModel):
    """POST body."""

    name: NameStr
    planned_amount: MoneyIn


class BudgetCategoryUpdate(ApiModel):
    """PUT body: only the sent fields change; sent fields may not be null."""

    name: NameStr | None = None
    planned_amount: MoneyIn | None = None

    @model_validator(mode="after")
    def _no_explicit_nulls(self) -> "BudgetCategoryUpdate":
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} must not be null")
        return self


class BudgetCategoryOut(ApiModel):
    """Category with spend figures (actual = sum of its expenses)."""

    id: int
    event_id: int
    name: str
    planned_amount: Money
    actual_amount: Money
    remaining_amount: Money

    @classmethod
    def build(cls, category: Any, actual: Any) -> "BudgetCategoryOut":
        """Combine a category entity with its actual spend."""
        return cls(
            id=category.id, event_id=category.event_id, name=category.name,
            planned_amount=category.planned_amount, actual_amount=actual,
            remaining_amount=category.planned_amount - actual,
        )
