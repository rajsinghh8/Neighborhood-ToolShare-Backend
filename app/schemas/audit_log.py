"""Audit log response schema (read-only resource)."""
from __future__ import annotations

from app.models.enums import AuditAction, AuditEntityType
from app.schemas.common import ApiModel, UtcDatetime


class AuditLogOut(ApiModel):
    """An audit row as returned by the API."""

    id: int
    event_id: int
    actor_id: int
    entity_type: AuditEntityType
    entity_id: int
    action: AuditAction
    created_at: UtcDatetime
