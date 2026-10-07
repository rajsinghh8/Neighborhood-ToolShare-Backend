"""HTTP handlers for /api/v1/events/{event_id}/schedule-items."""
from __future__ import annotations

from app.handlers.base import BaseHandler
from app.handlers.paths import EVENT_BASE, ID
from app.schemas.schedule_item import ScheduleItemCreate, ScheduleItemOut, ScheduleItemUpdate
from app.services.schedule_item_service import ScheduleItemService

SORT_FIELDS = ("start_at", "id")


class ScheduleItemCollectionHandler(BaseHandler):
    """List and create schedule items."""

    async def get(self, event_id: str) -> None:
        request = self.page_request(SORT_FIELDS, "start_at")
        start_date, end_date = self.query_date_range()
        page = await self.service(ScheduleItemService).list_items(
            int(event_id), self.current_user_id, request, start_date, end_date)
        self.send_page(page, ScheduleItemOut)

    async def post(self, event_id: str) -> None:
        data = self.parse_body(ScheduleItemCreate)
        item = await self.service(ScheduleItemService).create(int(event_id), self.current_user_id, data)
        self.send_json(ScheduleItemOut.model_validate(item).to_json(), 201)


class ScheduleItemHandler(BaseHandler):
    """Read, update and delete one schedule item."""

    async def get(self, event_id: str, item_id: str) -> None:
        item = await self.service(ScheduleItemService).get(int(event_id), self.current_user_id, int(item_id))
        self.send_json(ScheduleItemOut.model_validate(item).to_json())

    async def put(self, event_id: str, item_id: str) -> None:
        data = self.parse_body(ScheduleItemUpdate)
        item = await self.service(ScheduleItemService).update(
            int(event_id), self.current_user_id, int(item_id), data)
        self.send_json(ScheduleItemOut.model_validate(item).to_json())

    patch = put

    async def delete(self, event_id: str, item_id: str) -> None:
        await self.service(ScheduleItemService).delete(int(event_id), self.current_user_id, int(item_id))
        self.send_no_content()


ROUTES = [
    (EVENT_BASE + r"/schedule-items", ScheduleItemCollectionHandler),
    (EVENT_BASE + r"/schedule-items/(?P<item_id>" + ID + ")", ScheduleItemHandler),
]
