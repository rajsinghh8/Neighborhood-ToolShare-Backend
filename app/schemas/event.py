"""Request/response schemas for events."""
from __future__ import annotations

from typing import Annotated, Optional

from pydantic import Field, model_validator

from app.schemas.common import ApiModel, Money, MoneyIn, NameStr, UtcDatetime

_NOT_NULLABLE = ("name", "start_at", "end_at", "guest_capacity", "budget")


class EventCreate(ApiModel):
    """POST /events body."""

    name: NameStr
    description: Optional[Annotated[str, Field(max_length=10000)]] = None
    start_at: UtcDatetime
    end_at: UtcDatetime
    guest_capacity: Annotated[int, Field(ge=0, le=1_000_000)]
    budget: MoneyIn

    @model_validator(mode="after")
    def _check_period(self) -> "EventCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class EventUpdate(ApiModel):
    """PUT /events/{id} body: only the sent fields change; the merged result is validated by the service."""

    name: Optional[NameStr] = None
    description: Optional[Annotated[str, Field(max_length=10000)]] = None
    start_at: Optional[UtcDatetime] = None
    end_at: Optional[UtcDatetime] = None
    guest_capacity: Optional[Annotated[int, Field(ge=0, le=1_000_000)]] = None
    budget: Optional[MoneyIn] = None

    @model_validator(mode="after")
    def _reject_explicit_nulls(self) -> "EventUpdate":
        for field_name in _NOT_NULLABLE:
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} must not be null")
        return self


class EventOut(ApiModel):
    """Event as returned by create/update/list."""

    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    start_at: UtcDatetime
    end_at: UtcDatetime
    guest_capacity: int
    budget: Money


class BudgetBreakdown(ApiModel):
    """Planned vs actual spend of an event."""

    planned: Money
    actual: Money
    remaining: Money


class EventDetail(EventOut):
    """Event with guest and budget aggregates (GET /events/{id})."""

    accepted_guest_count: int
    budget_breakdown: BudgetBreakdown
