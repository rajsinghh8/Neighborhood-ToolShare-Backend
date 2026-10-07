"""Event endpoints: /api/v1/events and /api/v1/events/{event_id}."""
from __future__ import annotations

from app.core.pagination import SORT_ASC
from app.handlers.base import BaseHandler
from app.handlers.paths import API_PREFIX, EVENT_BASE
from app.schemas.event import BudgetBreakdown, EventCreate, EventDetail, EventOut, EventUpdate
from app.services.event_service import SORT_FIELDS, EventDetailData, EventService


def _detail_json(data: EventDetailData) -> dict:
    """Serialize an event with its aggregates."""
    base = EventOut.model_validate(data.event).model_dump()
    detail = EventDetail(
        **base,
        accepted_guest_count=data.accepted_guest_count,
        budget_breakdown=BudgetBreakdown(planned=data.planned, actual=data.actual, remaining=data.remaining),
    )
    return detail.to_json()


class EventCollectionHandler(BaseHandler):
    """GET (list own events) / POST (create) on /api/v1/events."""

    async def get(self) -> None:
        request = self.page_request(SORT_FIELDS, default_sort="id", default_dir=SORT_ASC)
        page = await self.service(EventService).list_for_owner(self.current_user_id, request)
        self.send_page(page, EventOut)

    async def post(self) -> None:
        body = self.parse_body(EventCreate)
        event = await self.service(EventService).create(self.current_user_id, body)
        self.send_json(EventOut.model_validate(event).to_json(), 201)


class EventItemHandler(BaseHandler):
    """GET / PUT / DELETE on /api/v1/events/{event_id}."""

    async def get(self, event_id: str) -> None:
        data = await self.service(EventService).get_detail(self.current_user_id, int(event_id))
        self.send_json(_detail_json(data))

    async def put(self, event_id: str) -> None:
        body = self.parse_body(EventUpdate)
        event = await self.service(EventService).update(self.current_user_id, int(event_id), body.changes())
        self.send_json(EventOut.model_validate(event).to_json())

    async def delete(self, event_id: str) -> None:
        await self.service(EventService).delete(self.current_user_id, int(event_id))
        self.send_no_content()


ROUTES = [
    (API_PREFIX + r"/events", EventCollectionHandler),
    (EVENT_BASE, EventItemHandler),
]
