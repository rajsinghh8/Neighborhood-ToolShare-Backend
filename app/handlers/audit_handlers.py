"""HTTP handler for /api/v1/events/{event_id}/audit-logs."""
from __future__ import annotations

from app.core.pagination import SORT_DESC
from app.handlers.base import BaseHandler
from app.handlers.paths import EVENT_BASE
from app.models.enums import AuditAction, AuditEntityType
from app.schemas.audit_log import AuditLogOut
from app.services.audit_log_service import AuditLogService


class AuditLogListHandler(BaseHandler):
    """GET /api/v1/events/{event_id}/audit-logs"""

    async def get(self, event_id: str) -> None:
        request = self.page_request(["created_at", "id"], "id", SORT_DESC)
        entity_type = self.query_enum("entity_type", AuditEntityType)
        action = self.query_enum("action", AuditAction)
        page = await self.service(AuditLogService).list_for_event(
            int(event_id), self.current_user_id, request, entity_type, action)
        self.send_page(page, AuditLogOut)


ROUTES = [(EVENT_BASE + r"/audit-logs/?", AuditLogListHandler)]
