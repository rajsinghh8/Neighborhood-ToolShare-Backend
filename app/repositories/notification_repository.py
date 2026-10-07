"""Queries for the notification API (user-scoped listing and lookup)."""
from __future__ import annotations

from sqlalchemy import select

from app.core.pagination import Page, PageRequest
from app.models import Notification
from app.repositories.core_repos import NotificationRepository


class NotificationQueryRepository(NotificationRepository):
    """Adds user-scoped queries on top of the shared notification repository."""

    SORT_COLUMNS = {
        "created_at": Notification.created_at,
        "id": Notification.id,
        "is_read": Notification.is_read,
    }

    async def list_for_user(self, user_id: int, request: PageRequest, is_read: bool | None) -> Page[Notification]:
        """Page of the user's notifications, optionally filtered by read state."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            stmt = stmt.where(Notification.is_read.is_(is_read))
        return await self.paginate(stmt, request, self.SORT_COLUMNS)

    async def get_for_user(self, user_id: int, notification_id: int) -> Notification | None:
        """The notification only if it belongs to ``user_id``."""
        stmt = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()
