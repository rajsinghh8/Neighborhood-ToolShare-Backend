"""Vendor payment endpoints: /api/v1/events/{event_id}/vendors/{vendor_id}/payments[/{payment_id}]."""
from __future__ import annotations

from app.handlers.base import BaseHandler
from app.handlers.paths import ID, VENDOR_BASE
from app.repositories.vendor_payment_repository import VendorPaymentRepository
from app.schemas.vendor_payment import VendorPaymentCreate, VendorPaymentOut, VendorPaymentUpdate
from app.services.vendor_payment_service import VendorPaymentService


class PaymentCollectionHandler(BaseHandler):
    """List and create payments of a vendor."""

    async def get(self, event_id: str, vendor_id: str) -> None:
        request = self.page_request(VendorPaymentRepository.SORT_COLUMNS, default_sort="paid_on")
        page = await self.service(VendorPaymentService).list_payments(
            int(event_id), int(vendor_id), self.current_user_id, request)
        self.send_page(page, VendorPaymentOut)

    async def post(self, event_id: str, vendor_id: str) -> None:
        data = self.parse_body(VendorPaymentCreate)
        payment = await self.service(VendorPaymentService).create_payment(
            int(event_id), int(vendor_id), self.current_user_id, data)
        self.send_json(VendorPaymentOut.model_validate(payment).to_json(), 201)


class PaymentItemHandler(BaseHandler):
    """Read, update and delete one payment."""

    async def get(self, event_id: str, vendor_id: str, payment_id: str) -> None:
        payment = await self.service(VendorPaymentService).get_payment(
            int(event_id), int(vendor_id), int(payment_id), self.current_user_id)
        self.send_json(VendorPaymentOut.model_validate(payment).to_json())

    async def put(self, event_id: str, vendor_id: str, payment_id: str) -> None:
        data = self.parse_body(VendorPaymentUpdate)
        payment = await self.service(VendorPaymentService).update_payment(
            int(event_id), int(vendor_id), int(payment_id), self.current_user_id, data)
        self.send_json(VendorPaymentOut.model_validate(payment).to_json())

    async def delete(self, event_id: str, vendor_id: str, payment_id: str) -> None:
        await self.service(VendorPaymentService).delete_payment(
            int(event_id), int(vendor_id), int(payment_id), self.current_user_id)
        self.send_no_content()


ROUTES = [
    (VENDOR_BASE + r"/payments", PaymentCollectionHandler),
    (VENDOR_BASE + r"/payments/(?P<payment_id>" + ID + ")", PaymentItemHandler),
]
