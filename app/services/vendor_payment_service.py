"""Vendor payment business rules: payments may never exceed the vendor's total amount."""
from __future__ import annotations

import logging
from decimal import Decimal

from app.core.errors import BusinessRuleError, NotFoundError, ValidationFailedError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import Vendor, VendorPayment
from app.models.enums import AuditAction, AuditEntityType
from app.repositories.vendor_payment_repository import VendorPaymentRepository
from app.repositories.vendor_repository import VendorRepository
from app.schemas.vendor_payment import VendorPaymentCreate, VendorPaymentUpdate
from app.services.audit_recorder import AuditRecorder
from app.services.event_access import EventAccess

logger = logging.getLogger(__name__)


def ensure_within_total(vendor_total: Decimal, already_paid: Decimal, amount: Decimal) -> None:
    """Raise BusinessRuleError unless ``already_paid + amount <= vendor_total`` (exact Decimal compare)."""
    if already_paid + amount > vendor_total:
        remaining = max(vendor_total - already_paid, Decimal("0.00"))
        raise BusinessRuleError(
            f"Payment of {amount:.2f} exceeds the remaining vendor balance of {remaining:.2f}")


class VendorPaymentService:
    """CRUD for payments of a vendor that belongs to an event owned by the current user."""

    def __init__(self, uow: UnitOfWork, access: EventAccess, audit: AuditRecorder) -> None:
        self._uow = uow
        self._access = access
        self._audit = audit
        self._vendors = VendorRepository(uow.session)
        self._payments = VendorPaymentRepository(uow.session)

    async def list_payments(self, event_id: int, vendor_id: int, user_id: int,
                            request: PageRequest) -> Page[VendorPayment]:
        """Page of the vendor's payments."""
        await self._access.require_owned(event_id, user_id)
        vendor = await self._require_vendor(event_id, vendor_id)
        return await self._payments.paginate_for_vendor(vendor.id, request)

    async def get_payment(self, event_id: int, vendor_id: int, payment_id: int, user_id: int) -> VendorPayment:
        """Single payment of the vendor."""
        await self._access.require_owned(event_id, user_id)
        vendor = await self._require_vendor(event_id, vendor_id)
        return await self._require_payment(vendor.id, payment_id)

    async def create_payment(self, event_id: int, vendor_id: int, user_id: int,
                             data: VendorPaymentCreate) -> VendorPayment:
        """Record a payment (audited); rejected with 422 if it would overpay the vendor."""
        await self._access.require_owned(event_id, user_id)
        await self._require_vendor(event_id, vendor_id)
        async with self._uow.transaction():
            vendor = await self._lock_vendor(event_id, vendor_id)
            paid = await self._payments.sum_for_vendor(vendor.id)
            ensure_within_total(vendor.total_amount, paid, data.amount)
            payment = await self._payments.add(VendorPayment(
                vendor_id=vendor.id, amount=data.amount, paid_on=data.paid_on))
            await self._audit.record(event_id, user_id, AuditEntityType.VENDOR_PAYMENT, payment.id,
                                     AuditAction.CREATE)
        logger.info("Payment %s of %s recorded for vendor %s", payment.id, payment.amount, vendor_id)
        return payment

    async def update_payment(self, event_id: int, vendor_id: int, payment_id: int, user_id: int,
                             data: VendorPaymentUpdate) -> VendorPayment:
        """Partial update; the payment itself is excluded from the already-paid sum."""
        await self._access.require_owned(event_id, user_id)
        await self._require_vendor(event_id, vendor_id)
        changes = data.changes()
        if any(value is None for value in changes.values()):
            raise ValidationFailedError("amount and paid_on must not be null")
        async with self._uow.transaction():
            vendor = await self._lock_vendor(event_id, vendor_id)
            payment = await self._require_payment(vendor.id, payment_id)
            if "amount" in changes:
                paid_by_others = await self._payments.sum_for_vendor(vendor.id, exclude_id=payment.id)
                ensure_within_total(vendor.total_amount, paid_by_others, changes["amount"])
            for field, value in changes.items():
                setattr(payment, field, value)
            await self._uow.session.flush()
            await self._audit.record(event_id, user_id, AuditEntityType.VENDOR_PAYMENT, payment.id,
                                     AuditAction.UPDATE)
        logger.info("Payment %s of vendor %s updated", payment_id, vendor_id)
        return payment

    async def delete_payment(self, event_id: int, vendor_id: int, payment_id: int, user_id: int) -> None:
        """Delete a payment (audited)."""
        await self._access.require_owned(event_id, user_id)
        vendor = await self._require_vendor(event_id, vendor_id)
        payment = await self._require_payment(vendor.id, payment_id)
        async with self._uow.transaction():
            await self._payments.delete(payment.id)
            await self._audit.record(event_id, user_id, AuditEntityType.VENDOR_PAYMENT, payment_id,
                                     AuditAction.DELETE)
        logger.info("Payment %s of vendor %s deleted", payment_id, vendor_id)

    async def _require_vendor(self, event_id: int, vendor_id: int) -> Vendor:
        vendor = await self._vendors.get_in_event(event_id, vendor_id)
        if vendor is None:
            raise NotFoundError("Vendor not found")
        return vendor

    async def _lock_vendor(self, event_id: int, vendor_id: int) -> Vendor:
        """Re-read the vendor with a row lock so concurrent payments cannot jointly overpay."""
        vendor = await self._vendors.get_in_event_for_update(event_id, vendor_id)
        if vendor is None:
            raise NotFoundError("Vendor not found")
        return vendor

    async def _require_payment(self, vendor_id: int, payment_id: int) -> VendorPayment:
        payment = await self._payments.get_for_vendor(vendor_id, payment_id)
        if payment is None:
            raise NotFoundError("Payment not found")
        return payment
