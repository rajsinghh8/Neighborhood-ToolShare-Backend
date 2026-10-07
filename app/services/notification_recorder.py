"""Creates de-duplicated notifications inside the caller's transaction."""
from __future__ import annotations

import logging

from app.core.unit_of_work import UnitOfWork
from app.events.domain import DomainEvent
from app.models import Notification
from app.models.enums import NotificationType
from app.repositories.core_repos import NotificationRepository

logger = logging.getLogger(__name__)

NOTIFICATION_EVENT_TYPE = "notification.created"


class NotificationRecorder:
    """Single place that inserts Notification rows; used by GuestService and the scheduler."""

    def __init__(self, uow: UnitOfWork, topic: str = "eventforge.notifications") -> None:
        self._uow = uow
        self._repo = NotificationRepository(uow.session)
        self._topic = topic

    async def notify(self, user_id: int, event_id: int | None, type_: NotificationType,
                     message: str, dedup_key: str) -> Notification | None:
        """Insert unless (user_id, dedup_key) already exists; returns None when de-duplicated."""
        if await self._repo.get_by_dedup_key(user_id, dedup_key) is not None:
            logger.debug("Notification de-duplicated user_id=%s key=%s", user_id, dedup_key)
            return None
        row = await self._repo.add(Notification(
            user_id=user_id, event_id=event_id, type=type_, message=message,
            is_read=False, dedup_key=dedup_key,
        ))
        self._uow.add_event(DomainEvent(
            topic=self._topic,
            key=str(user_id),
            event_type=NOTIFICATION_EVENT_TYPE,
            payload={"notification_id": row.id, "user_id": user_id, "event_id": event_id,
                     "type": type_.value, "message": message},
        ))
        logger.info("Notification created user_id=%s type=%s key=%s", user_id, type_.value, dedup_key)
        return row
