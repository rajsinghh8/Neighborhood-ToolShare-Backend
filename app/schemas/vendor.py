"""Vendor request/response schemas."""
from __future__ import annotations

from decimal import Decimal

from typing import Annotated

from pydantic import StringConstraints

from app.schemas.common import ApiModel, Money, MoneyIn, NameStr

ServiceStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class VendorCreate(ApiModel):
    """Body of POST /events/{event_id}/vendors."""

    name: NameStr
    service: ServiceStr | None = None
    total_amount: MoneyIn


class VendorUpdate(ApiModel):
    """Body of PUT /events/{event_id}/vendors/{vendor_id}; only sent fields change."""

    name: NameStr | None = None
    service: ServiceStr | None = None
    total_amount: MoneyIn | None = None


class VendorOut(ApiModel):
    """Vendor with payment totals (used for detail, create/update responses and list items)."""

    id: int
    event_id: int
    name: str
    service: str | None = None
    total_amount: Money
    total_paid: Money
    totalPaid: Money
    outstanding: Money

    @classmethod
    def build(cls, vendor, total_paid: Decimal) -> "VendorOut":
        """Combine a Vendor row with its computed paid total."""
        return cls(
            id=vendor.id, event_id=vendor.event_id, name=vendor.name, service=vendor.service,
            total_amount=vendor.total_amount, total_paid=total_paid, totalPaid=total_paid,
            outstanding=vendor.total_amount - total_paid,
        )
