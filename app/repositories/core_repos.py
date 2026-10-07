"""Repositories for the shared/core entities (users, events, audit logs, notifications)."""
from __future__ import annotations

from sqlalchemy import select

from app.models import AuditLog, Event, Notification, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        return (await self._session.execute(select(User).where(User.email == email))).scalar_one_or_none()


class EventRepository(BaseRepository[Event]):
    model = Event


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    async def get_by_dedup_key(self, user_id: int, dedup_key: str) -> Notification | None:
        stmt = select(Notification).where(Notification.user_id == user_id, Notification.dedup_key == dedup_key)
        return (await self._session.execute(stmt)).scalar_one_or_none()
