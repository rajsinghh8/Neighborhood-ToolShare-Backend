"""Vendor payment request/response schemas."""
from __future__ import annotations

from datetime import date

from app.schemas.common import ApiModel, Money, PositiveMoneyIn


class VendorPaymentCreate(ApiModel):
    """Body of POST .../vendors/{vendor_id}/payments."""

    amount: PositiveMoneyIn
    paid_on: date


class VendorPaymentUpdate(ApiModel):
    """Body of PUT .../payments/{payment_id}; only sent fields change."""

    amount: PositiveMoneyIn | None = None
    paid_on: date | None = None


class VendorPaymentOut(ApiModel):
    """Payment representation."""

    id: int
    vendor_id: int
    amount: Money
    paid_on: date
