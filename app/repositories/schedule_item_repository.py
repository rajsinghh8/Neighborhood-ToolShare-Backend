"""Queries for schedule items."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.core.pagination import Page, PageRequest
from app.models import ScheduleItem
from app.repositories.base import BaseRepository


class ScheduleItemRepository(BaseRepository[ScheduleItem]):
    """Data access for :class:`ScheduleItem`."""

    model = ScheduleItem

    async def get_for_event(self, event_id: int, item_id: int) -> ScheduleItem | None:
        """Return the item only when it belongs to ``event_id``."""
        item = await self.get(item_id)
        if item is None or item.event_id != event_id:
            return None
        return item

    async def find_overlapping(self, event_id: int, start_at: datetime, end_at: datetime,
                               exclude_id: int | None = None) -> ScheduleItem | None:
        """First item of the event overlapping ``[start_at, end_at)`` (touching bounds do not overlap)."""
        stmt = (select(ScheduleItem)
                .where(ScheduleItem.event_id == event_id,
                       ScheduleItem.start_at < end_at,
                       start_at < ScheduleItem.end_at)
                .order_by(ScheduleItem.start_at.asc(), ScheduleItem.id.asc())
                .limit(1))
        if exclude_id is not None:
            stmt = stmt.where(ScheduleItem.id != exclude_id)
        return (await self._session.execute(stmt)).scalars().first()

    async def list_for_event(self, event_id: int, request: PageRequest,
                             start_date: date | None = None,
                             end_date: date | None = None) -> Page[ScheduleItem]:
        """Paginated items of an event, optionally restricted to a start_at date range (inclusive)."""
        stmt = select(ScheduleItem).where(ScheduleItem.event_id == event_id)
        if start_date is not None:
            stmt = stmt.where(ScheduleItem.start_at >= datetime.combine(start_date, time.min))
        if end_date is not None:
            stmt = stmt.where(ScheduleItem.start_at < datetime.combine(end_date + timedelta(days=1), time.min))
        return await self.paginate(stmt, request, {
            "start_at": ScheduleItem.start_at,
            "id": ScheduleItem.id,
        })
