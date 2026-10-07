"""Read-only audit log use-case."""
from __future__ import annotations

from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import AuditLog
from app.models.enums import AuditAction, AuditEntityType
from app.repositories.audit_log_repository import AuditLogQueryRepository
from app.services.event_access import EventAccess


class AuditLogService:
    """Lists the audit trail of an event for its owner only (others -> 404)."""

    def __init__(self, uow: UnitOfWork, access: EventAccess) -> None:
        self._repo = AuditLogQueryRepository(uow.session)
        self._access = access

    async def list_for_event(self, event_id: int, user_id: int, request: PageRequest,
                             entity_type: AuditEntityType | None = None,
                             action: AuditAction | None = None) -> Page[AuditLog]:
        """Ownership check first, then the filtered page."""
        await self._access.require_owned(event_id, user_id)
        return await self._repo.list_for_event(event_id, request, entity_type, action)
