"""Vendor payment queries: vendor-scoped lookup, listing and sums."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select

from app.core.pagination import Page, PageRequest
from app.models import VendorPayment
from app.repositories.base import BaseRepository
from app.repositories.vendor_repository import to_money


class VendorPaymentRepository(BaseRepository[VendorPayment]):
    """Data access for vendor payments."""

    model = VendorPayment

    SORT_COLUMNS = {"paid_on": VendorPayment.paid_on, "amount": VendorPayment.amount, "id": VendorPayment.id}

    async def get_for_vendor(self, vendor_id: int, payment_id: int) -> VendorPayment | None:
        """Payment by id only if it belongs to ``vendor_id``."""
        stmt = select(VendorPayment).where(VendorPayment.id == payment_id, VendorPayment.vendor_id == vendor_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def paginate_for_vendor(self, vendor_id: int, request: PageRequest) -> Page[VendorPayment]:
        """Payments of one vendor, sorted per ``request``."""
        stmt = select(VendorPayment).where(VendorPayment.vendor_id == vendor_id)
        return await self.paginate(stmt, request, self.SORT_COLUMNS)

    async def sum_for_vendor(self, vendor_id: int, exclude_id: int | None = None) -> Decimal:
        """Sum of a vendor's payments, optionally leaving out one payment (the one being updated)."""
        stmt = select(func.sum(VendorPayment.amount)).where(VendorPayment.vendor_id == vendor_id)
        if exclude_id is not None:
            stmt = stmt.where(VendorPayment.id != exclude_id)
        return to_money((await self._session.execute(stmt)).scalar_one())
