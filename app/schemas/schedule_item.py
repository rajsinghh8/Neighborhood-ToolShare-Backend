"""Request/response schemas for schedule items."""
from __future__ import annotations

from pydantic import model_validator

from app.schemas.common import ApiModel, NameStr, UtcDatetime


class ScheduleItemCreate(ApiModel):
    """POST body: all fields required."""

    title: NameStr
    start_at: UtcDatetime
    end_at: UtcDatetime

    @model_validator(mode="after")
    def _check_range(self) -> "ScheduleItemCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class ScheduleItemUpdate(ApiModel):
    """PUT body: partial; only provided fields change. Explicit nulls are rejected."""

    title: NameStr | None = None
    start_at: UtcDatetime | None = None
    end_at: UtcDatetime | None = None

    @model_validator(mode="after")
    def _no_nulls(self) -> "ScheduleItemUpdate":
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} must not be null")
        return self


class ScheduleItemOut(ApiModel):
    """Response representation."""

    id: int
    event_id: int
    title: str
    start_at: UtcDatetime
    end_at: UtcDatetime
