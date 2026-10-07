"""Business rules for schedule items: valid range, no overlaps within an event, auditing."""
from __future__ import annotations

import logging
from datetime import date, datetime

from app.core.errors import BusinessRuleError, NotFoundError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import ScheduleItem
from app.models.enums import AuditAction, AuditEntityType
from app.repositories.schedule_item_repository import ScheduleItemRepository
from app.schemas.schedule_item import ScheduleItemCreate, ScheduleItemUpdate
from app.services.audit_recorder import AuditRecorder
from app.services.event_access import EventAccess

logger = logging.getLogger(__name__)


def intervals_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Half-open interval overlap: touching boundaries do NOT overlap."""
    return a_start < b_end and b_start < a_end


class ScheduleItemService:
    """CRUD for the schedule of an event owned by the caller."""

    def __init__(self, uow: UnitOfWork, access: EventAccess, audit: AuditRecorder) -> None:
        self._uow = uow
        self._access = access
        self._audit = audit
        self._items = ScheduleItemRepository(uow.session)

    async def list_items(self, event_id: int, user_id: int, request: PageRequest,
                   start_date: date | None, end_date: date | None) -> Page[ScheduleItem]:
        """Paginated items of the event, optionally filtered by start_at date."""
        await self._access.require_owned(event_id, user_id)
        return await self._items.list_for_event(event_id, request, start_date, end_date)

    async def get(self, event_id: int, user_id: int, item_id: int) -> ScheduleItem:
        """Fetch one item (404 for foreign events or items of other events)."""
        await self._access.require_owned(event_id, user_id)
        return await self._require_item(event_id, item_id)

    async def create(self, event_id: int, user_id: int, data: ScheduleItemCreate) -> ScheduleItem:
        """Create an item; rejects overlaps with existing items of the event."""
        await self._access.require_owned(event_id, user_id)
        async with self._uow.transaction():
            await self._ensure_no_overlap(event_id, data.start_at, data.end_at)
            item = await self._items.add(ScheduleItem(
                event_id=event_id, title=data.title, start_at=data.start_at, end_at=data.end_at))
            await self._audit.record(event_id, user_id, AuditEntityType.SCHEDULE_ITEM,
                                     item.id, AuditAction.CREATE)
        logger.info("Schedule item %s created in event %s", item.id, event_id)
        return item

    async def update(self, event_id: int, user_id: int, item_id: int,
                     data: ScheduleItemUpdate) -> ScheduleItem:
        """Partial update; the merged range must be valid and overlap-free (excluding itself)."""
        await self._access.require_owned(event_id, user_id)
        item = await self._require_item(event_id, item_id)
        changes = data.changes()
        title = changes.get("title", item.title)
        start_at = changes.get("start_at", item.start_at)
        end_at = changes.get("end_at", item.end_at)
        if end_at <= start_at:
            raise BusinessRuleError("end_at must be after start_at")
        async with self._uow.transaction():
            await self._ensure_no_overlap(event_id, start_at, end_at, exclude_id=item.id)
            item.title, item.start_at, item.end_at = title, start_at, end_at
            await self._items.flush()
            await self._audit.record(event_id, user_id, AuditEntityType.SCHEDULE_ITEM,
                                     item.id, AuditAction.UPDATE)
        logger.info("Schedule item %s updated in event %s", item.id, event_id)
        return item

    async def delete(self, event_id: int, user_id: int, item_id: int) -> None:
        """Delete an item and audit it."""
        await self._access.require_owned(event_id, user_id)
        item = await self._require_item(event_id, item_id)
        async with self._uow.transaction():
            await self._items.delete(item.id)
            await self._audit.record(event_id, user_id, AuditEntityType.SCHEDULE_ITEM,
                                     item_id, AuditAction.DELETE)
        logger.info("Schedule item %s deleted from event %s", item_id, event_id)

    async def _require_item(self, event_id: int, item_id: int) -> ScheduleItem:
        item = await self._items.get_for_event(event_id, item_id)
        if item is None:
            raise NotFoundError("Schedule item not found")
        return item

    async def _ensure_no_overlap(self, event_id: int, start_at: datetime, end_at: datetime,
                                 exclude_id: int | None = None) -> None:
        clash = await self._items.find_overlapping(event_id, start_at, end_at, exclude_id)
        if clash is not None:
            raise BusinessRuleError(
                f"Schedule item overlaps with existing item {clash.id} ('{clash.title}')")
