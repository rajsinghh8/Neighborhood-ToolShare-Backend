"""Notification request/response schemas."""
from __future__ import annotations

from pydantic import StrictBool

from app.models.enums import NotificationType
from app.schemas.common import ApiModel, UtcDatetime


class NotificationOut(ApiModel):
    """A notification as returned by the API."""

    id: int
    user_id: int
    event_id: int | None = None
    type: NotificationType
    message: str
    is_read: bool
    dedup_key: str
    created_at: UtcDatetime


class NotificationUpdate(ApiModel):
    """PATCH body: ``is_read`` is required and must be a real boolean."""

    is_read: StrictBool
