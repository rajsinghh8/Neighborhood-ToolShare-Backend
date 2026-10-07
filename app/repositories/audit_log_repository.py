"""Queries for the audit-log API."""
from __future__ import annotations

from sqlalchemy import select

from app.core.pagination import Page, PageRequest
from app.models import AuditLog
from app.models.enums import AuditAction, AuditEntityType
from app.repositories.core_repos import AuditLogRepository


class AuditLogQueryRepository(AuditLogRepository):
    """Event-scoped, filterable audit-log listing."""

    SORT_COLUMNS = {"created_at": AuditLog.created_at, "id": AuditLog.id}

    async def list_for_event(self, event_id: int, request: PageRequest,
                             entity_type: AuditEntityType | None,
                             action: AuditAction | None) -> Page[AuditLog]:
        """Page of audit rows for one event with optional entity_type/action filters."""
        stmt = select(AuditLog).where(AuditLog.event_id == event_id)
        if entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        return await self.paginate(stmt, request, self.SORT_COLUMNS)
