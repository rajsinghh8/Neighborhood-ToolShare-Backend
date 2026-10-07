"""Ownership guard shared by every event-nested service."""
from __future__ import annotations

from app.core.errors import NotFoundError
from app.core.unit_of_work import UnitOfWork
from app.models import Event
from app.repositories.core_repos import EventRepository


class EventAccess:
    """Resolves an event for its owner; missing and foreign events both raise NotFoundError."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._events = EventRepository(uow.session)

    async def require_owned(self, event_id: int, user_id: int) -> Event:
        event = await self._events.get(event_id)
        if event is None or event.owner_id != user_id:
            raise NotFoundError("Event not found")
        return event
