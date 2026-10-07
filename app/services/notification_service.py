"""Notification use-cases for the authenticated user."""
from __future__ import annotations

import logging

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import Notification
from app.repositories.notification_repository import NotificationQueryRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Lists, reads, marks and deletes a user's own notifications (others' -> 404)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = NotificationQueryRepository(uow.session)

    async def list_for_user(self, user_id: int, request: PageRequest,
                            is_read: bool | None = None) -> Page[Notification]:
        """Paginated notifications of ``user_id``."""
        return await self._repo.list_for_user(user_id, request, is_read)

    async def get(self, user_id: int, notification_id: int) -> Notification:
        """One notification; NotFoundError if missing or owned by someone else."""
        row = await self._repo.get_for_user(user_id, notification_id)
        if row is None:
            raise NotFoundError("Notification not found")
        return row

    async def mark_read(self, user_id: int, notification_id: int, is_read: bool) -> Notification:
        """Set the read flag on the user's notification."""
        row = await self.get(user_id, notification_id)
        async with self._uow.transaction():
            row.is_read = is_read
            await self._repo.flush()
        logger.info("Notification id=%s user_id=%s is_read=%s", notification_id, user_id, is_read)
        return row

    async def delete(self, user_id: int, notification_id: int) -> None:
        """Delete the user's notification."""
        await self.get(user_id, notification_id)
        async with self._uow.transaction():
            await self._repo.delete(notification_id)
        logger.info("Notification deleted id=%s user_id=%s", notification_id, user_id)
