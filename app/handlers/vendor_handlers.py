"""Vendor endpoints: /api/v1/events/{event_id}/vendors[/{vendor_id}]."""
from __future__ import annotations

from app.handlers.base import BaseHandler
from app.handlers.paths import EVENT_BASE, VENDOR_BASE
from app.repositories.vendor_repository import VendorRepository
from app.schemas.vendor import VendorCreate, VendorOut, VendorUpdate
from app.services.vendor_service import VendorService


class VendorCollectionHandler(BaseHandler):
    """List and create vendors of an event."""

    async def get(self, event_id: str) -> None:
        request = self.page_request(VendorRepository.SORT_COLUMNS, default_sort="id")
        page = await self.service(VendorService).list_vendors(int(event_id), self.current_user_id, request)
        self.send_page(page, VendorOut)

    async def post(self, event_id: str) -> None:
        data = self.parse_body(VendorCreate)
        vendor = await self.service(VendorService).create_vendor(int(event_id), self.current_user_id, data)
        self.send_json(vendor.to_json(), 201)


class VendorItemHandler(BaseHandler):
    """Read, update and delete one vendor."""

    async def get(self, event_id: str, vendor_id: str) -> None:
        vendor = await self.service(VendorService).get_vendor(int(event_id), int(vendor_id), self.current_user_id)
        self.send_json(vendor.to_json())

    async def put(self, event_id: str, vendor_id: str) -> None:
        data = self.parse_body(VendorUpdate)
        vendor = await self.service(VendorService).update_vendor(
            int(event_id), int(vendor_id), self.current_user_id, data)
        self.send_json(vendor.to_json())

    async def delete(self, event_id: str, vendor_id: str) -> None:
        await self.service(VendorService).delete_vendor(int(event_id), int(vendor_id), self.current_user_id)
        self.send_no_content()


ROUTES = [
    (EVENT_BASE + r"/vendors", VendorCollectionHandler),
    (VENDOR_BASE, VendorItemHandler),
]
