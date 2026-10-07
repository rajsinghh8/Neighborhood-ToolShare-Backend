"""HTTP handlers for /api/v1/notifications."""
from __future__ import annotations

from app.core.errors import ValidationFailedError
from app.core.pagination import SORT_DESC
from app.handlers.base import BaseHandler
from app.handlers.paths import API_PREFIX, ID
from app.schemas.notification import NotificationOut, NotificationUpdate
from app.services.notification_service import NotificationService

_SORT_FIELDS = ["created_at", "id", "is_read"]


class NotificationListHandler(BaseHandler):
    """GET /api/v1/notifications"""

    async def get(self) -> None:
        request = self.page_request(_SORT_FIELDS, "created_at", SORT_DESC)
        is_read = self._query_bool("is_read")
        page = await self.service(NotificationService).list_for_user(self.current_user_id, request, is_read)
        self.send_page(page, NotificationOut)

    def _query_bool(self, name: str) -> bool | None:
        raw = self.get_query_argument(name, None)
        if raw is None or raw == "":
            return None
        lowered = raw.lower()
        if lowered not in ("true", "false"):
            raise ValidationFailedError(f"{name} must be true or false")
        return lowered == "true"


class NotificationDetailHandler(BaseHandler):
    """GET / PATCH / DELETE /api/v1/notifications/{notification_id}"""

    async def get(self, notification_id: str) -> None:
        row = await self.service(NotificationService).get(self.current_user_id, int(notification_id))
        self.send_json(NotificationOut.model_validate(row).to_json())

    async def patch(self, notification_id: str) -> None:
        body = self.parse_body(NotificationUpdate)
        row = await self.service(NotificationService).mark_read(
            self.current_user_id, int(notification_id), body.is_read)
        self.send_json(NotificationOut.model_validate(row).to_json())

    async def delete(self, notification_id: str) -> None:
        await self.service(NotificationService).delete(self.current_user_id, int(notification_id))
        self.send_no_content()


ROUTES = [
    (API_PREFIX + r"/notifications/?", NotificationListHandler),
    (API_PREFIX + r"/notifications/(?P<notification_id>" + ID + ")", NotificationDetailHandler),
]
