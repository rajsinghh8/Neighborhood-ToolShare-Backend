"""Event business rules: ownership, period/capacity validation, detail aggregates."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.core.errors import BusinessRuleError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import Event
from app.repositories.event_repository import SORT_COLUMNS, OwnedEventRepository
from app.repositories.stats import StatsRepository
from app.schemas.event import EventCreate
from app.services.event_access import EventAccess

logger = logging.getLogger(__name__)

SORT_FIELDS = list(SORT_COLUMNS)


@dataclass(frozen=True)
class EventDetailData:
    """An event plus its computed aggregates."""

    event: Event
    accepted_guest_count: int
    planned: Decimal
    actual: Decimal
    remaining: Decimal


class EventService:
    """CRUD for events owned by the calling user. Foreign/missing events are always 404."""

    def __init__(self, uow: UnitOfWork, access: EventAccess) -> None:
        self._uow = uow
        self._access = access
        self._events = OwnedEventRepository(uow.session)
        self._stats = StatsRepository(uow.session)

    async def list_for_owner(self, user_id: int, request: PageRequest) -> Page[Event]:
        """Page of the user's own events."""
        return await self._events.list_for_owner(user_id, request)

    async def create(self, user_id: int, data: EventCreate) -> Event:
        """Create an event owned by ``user_id`` (period/budget already validated by the schema)."""
        async with self._uow.transaction():
            event = await self._events.add(Event(owner_id=user_id, **data.model_dump()))
        logger.info("Event created id=%s owner=%s", event.id, user_id)
        return event

    async def get_detail(self, user_id: int, event_id: int) -> EventDetailData:
        """Event with accepted guest count and budget breakdown (planned / actual / remaining)."""
        event = await self._access.require_owned(event_id, user_id)
        accepted = await self._stats.accepted_guest_count(event_id)
        actual = await self._stats.event_actual_spend(event_id)
        return EventDetailData(event, accepted, event.budget, actual, event.budget - actual)

    async def update(self, user_id: int, event_id: int, changes: dict[str, Any]) -> Event:
        """Apply the sent fields; validates the merged period and the capacity against current guests."""
        event = await self._access.require_owned(event_id, user_id)
        start_at = changes.get("start_at", event.start_at)
        end_at = changes.get("end_at", event.end_at)
        if end_at <= start_at:
            raise BusinessRuleError("end_at must be after start_at")
        new_capacity = changes.get("guest_capacity")
        if new_capacity is not None and new_capacity != event.guest_capacity:
            guests = await self._stats.guest_count(event_id)
            if new_capacity < guests:
                raise BusinessRuleError(
                    f"guest_capacity cannot be lower than the current number of guests ({guests})")
        async with self._uow.transaction():
            for field, value in changes.items():
                setattr(event, field, value)
            await self._events.flush()
        logger.info("Event updated id=%s", event_id)
        return event

    async def delete(self, user_id: int, event_id: int) -> None:
        """Delete the event; children are removed by DB cascades."""
        await self._access.require_owned(event_id, user_id)
        async with self._uow.transaction():
            await self._events.delete(event_id)
        logger.info("Event deleted id=%s", event_id)
