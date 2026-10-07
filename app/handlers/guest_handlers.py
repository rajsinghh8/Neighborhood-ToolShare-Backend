"""HTTP handlers for /api/v1/events/{event_id}/guests."""
from __future__ import annotations

from app.handlers.base import BaseHandler
from app.handlers.paths import EVENT_BASE, ID
from app.models.enums import InvitationStatus
from app.repositories.guest_repository import GUEST_SORT_FIELDS
from app.schemas.guest import Guest, GuestCreate, GuestUpdate
from app.services.guest_service import GuestService


class GuestCollectionHandler(BaseHandler):
    """List and create guests."""

    async def get(self, event_id: str) -> None:
        request = self.page_request(GUEST_SORT_FIELDS, "id")
        status = self.query_enum("invitation_status", InvitationStatus)
        page = await self.service(GuestService).list_guests(
            self.current_user_id, int(event_id), request, status)
        self.send_page(page, Guest)

    async def post(self, event_id: str) -> None:
        data = self.parse_body(GuestCreate)
        guest = await self.service(GuestService).create_guest(self.current_user_id, int(event_id), data)
        self.send_json(Guest.model_validate(guest).to_json(), 201)


class GuestItemHandler(BaseHandler):
    """Read, update and delete one guest."""

    async def get(self, event_id: str, guest_id: str) -> None:
        guest = await self.service(GuestService).get_guest(
            self.current_user_id, int(event_id), int(guest_id))
        self.send_json(Guest.model_validate(guest).to_json())

    async def put(self, event_id: str, guest_id: str) -> None:
        data = self.parse_body(GuestUpdate)
        guest = await self.service(GuestService).update_guest(
            self.current_user_id, int(event_id), int(guest_id), data)
        self.send_json(Guest.model_validate(guest).to_json())

    patch = put

    async def delete(self, event_id: str, guest_id: str) -> None:
        await self.service(GuestService).delete_guest(self.current_user_id, int(event_id), int(guest_id))
        self.send_no_content()


ROUTES = [
    (EVENT_BASE + r"/guests", GuestCollectionHandler),
    (EVENT_BASE + r"/guests/(?P<guest_id>" + ID + ")", GuestItemHandler),
]
