"""Vendor queries: event-scoped lookup, paginated listing and payment aggregates."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select

from app.core.pagination import Page, PageRequest
from app.models import Vendor, VendorPayment
from app.models.types import ZERO
from app.repositories.base import BaseRepository

_CENT = Decimal("0.01")


def to_money(value: object) -> Decimal:
    """Normalise a DB aggregate (Decimal, float on SQLite, or None) to an exact 2-dp Decimal."""
    if value is None:
        return ZERO
    return Decimal(str(value)).quantize(_CENT)


class VendorRepository(BaseRepository[Vendor]):
    """Data access for vendors."""

    model = Vendor

    SORT_COLUMNS = {"name": Vendor.name, "id": Vendor.id}

    async def get_in_event(self, event_id: int, vendor_id: int) -> Vendor | None:
        """Vendor by id only if it belongs to ``event_id``."""
        stmt = select(Vendor).where(Vendor.id == vendor_id, Vendor.event_id == event_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_in_event_for_update(self, event_id: int, vendor_id: int) -> Vendor | None:
        """Same as :meth:`get_in_event` but row-locks the vendor (serialises concurrent payment writes)."""
        stmt = (select(Vendor).where(Vendor.id == vendor_id, Vendor.event_id == event_id)
                .with_for_update().execution_options(populate_existing=True))
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def paginate_for_event(self, event_id: int, request: PageRequest) -> Page[Vendor]:
        """Vendors of one event, sorted per ``request``."""
        stmt = select(Vendor).where(Vendor.event_id == event_id)
        return await self.paginate(stmt, request, self.SORT_COLUMNS)

    async def total_paid(self, vendor_id: int) -> Decimal:
        """Sum of all payments of a vendor (0.00 when none)."""
        stmt = select(func.sum(VendorPayment.amount)).where(VendorPayment.vendor_id == vendor_id)
        return to_money((await self._session.execute(stmt)).scalar_one())

    async def total_paid_by_vendor(self, vendor_ids: list[int]) -> dict[int, Decimal]:
        """Total paid per vendor id in one query (vendors without payments -> 0.00)."""
        result = {vendor_id: ZERO for vendor_id in vendor_ids}
        if not vendor_ids:
            return result
        stmt = (select(VendorPayment.vendor_id, func.sum(VendorPayment.amount))
                .where(VendorPayment.vendor_id.in_(vendor_ids)).group_by(VendorPayment.vendor_id))
        for vendor_id, total in (await self._session.execute(stmt)).all():
            result[vendor_id] = to_money(total)
        return result
