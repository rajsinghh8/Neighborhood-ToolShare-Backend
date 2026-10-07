"""Vendor business rules: event ownership, total_amount vs. payments, auditing."""
from __future__ import annotations

import logging
from decimal import Decimal

from app.core.errors import BusinessRuleError, NotFoundError, ValidationFailedError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import Vendor
from app.models.enums import AuditAction, AuditEntityType
from app.repositories.vendor_repository import VendorRepository
from app.schemas.vendor import VendorCreate, VendorOut, VendorUpdate
from app.services.audit_recorder import AuditRecorder
from app.services.event_access import EventAccess

logger = logging.getLogger(__name__)


class VendorService:
    """CRUD for the vendors of an event owned by the current user."""

    def __init__(self, uow: UnitOfWork, access: EventAccess, audit: AuditRecorder) -> None:
        self._uow = uow
        self._access = access
        self._audit = audit
        self._vendors = VendorRepository(uow.session)

    async def list_vendors(self, event_id: int, user_id: int, request: PageRequest) -> Page[VendorOut]:
        """Page of vendors including their paid/outstanding amounts."""
        await self._access.require_owned(event_id, user_id)
        page = await self._vendors.paginate_for_event(event_id, request)
        paid = await self._vendors.total_paid_by_vendor([vendor.id for vendor in page.items])
        items = [VendorOut.build(vendor, paid[vendor.id]) for vendor in page.items]
        return Page(items=items, total=page.total, request=request)

    async def get_vendor(self, event_id: int, vendor_id: int, user_id: int) -> VendorOut:
        """Vendor detail with ``total_paid`` and ``outstanding``."""
        await self._access.require_owned(event_id, user_id)
        vendor = await self._require_vendor(event_id, vendor_id)
        return VendorOut.build(vendor, await self._vendors.total_paid(vendor.id))

    async def create_vendor(self, event_id: int, user_id: int, data: VendorCreate) -> VendorOut:
        """Create a vendor (audited)."""
        await self._access.require_owned(event_id, user_id)
        async with self._uow.transaction():
            vendor = await self._vendors.add(Vendor(
                event_id=event_id, name=data.name, service=data.service, total_amount=data.total_amount))
            await self._audit.record(event_id, user_id, AuditEntityType.VENDOR, vendor.id, AuditAction.CREATE)
        logger.info("Vendor %s created in event %s", vendor.id, event_id)
        return VendorOut.build(vendor, Decimal("0.00"))

    async def update_vendor(self, event_id: int, vendor_id: int, user_id: int, data: VendorUpdate) -> VendorOut:
        """Partial update; ``total_amount`` may not drop below what was already paid."""
        await self._access.require_owned(event_id, user_id)
        vendor = await self._require_vendor(event_id, vendor_id)
        changes = data.changes()
        if changes.get("name", "") is None:
            raise ValidationFailedError("name must not be null")
        if changes.get("total_amount", "") is None:
            raise ValidationFailedError("total_amount must not be null")
        new_total = changes.get("total_amount")
        async with self._uow.transaction():
            vendor = await self._vendors.get_in_event_for_update(event_id, vendor_id) or vendor
            total_paid = await self._vendors.total_paid(vendor.id)
            if new_total is not None and new_total < total_paid:
                raise BusinessRuleError(
                    f"total_amount {new_total:.2f} cannot be less than the amount already paid {total_paid:.2f}")
            for field, value in changes.items():
                setattr(vendor, field, value)
            await self._uow.session.flush()
            await self._audit.record(event_id, user_id, AuditEntityType.VENDOR, vendor.id, AuditAction.UPDATE)
        logger.info("Vendor %s updated in event %s", vendor.id, event_id)
        return VendorOut.build(vendor, total_paid)

    async def delete_vendor(self, event_id: int, vendor_id: int, user_id: int) -> None:
        """Delete a vendor; its payments disappear through the DB foreign-key cascade."""
        await self._access.require_owned(event_id, user_id)
        vendor = await self._require_vendor(event_id, vendor_id)
        async with self._uow.transaction():
            await self._vendors.delete(vendor.id)
            await self._audit.record(event_id, user_id, AuditEntityType.VENDOR, vendor_id, AuditAction.DELETE)
        logger.info("Vendor %s deleted from event %s", vendor_id, event_id)

    async def _require_vendor(self, event_id: int, vendor_id: int) -> Vendor:
        vendor = await self._vendors.get_in_event(event_id, vendor_id)
        if vendor is None:
            raise NotFoundError("Vendor not found")
        return vendor
