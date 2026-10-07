from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.types import money_column


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    service: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(money_column())

    event: Mapped["Event"] = relationship(back_populates="vendors", lazy="raise")
    payments: Mapped[list["VendorPayment"]] = relationship(back_populates="vendor", lazy="raise", passive_deletes=True)

    def __repr__(self) -> str:
        return f"Vendor(id={self.id!r}, event_id={self.event_id!r}, name={self.name!r})"


class VendorPayment(Base):
    __tablename__ = "vendor_payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(money_column())
    paid_on: Mapped[date] = mapped_column(Date)

    vendor: Mapped["Vendor"] = relationship(back_populates="payments", lazy="raise")

    def __repr__(self) -> str:
        return f"VendorPayment(id={self.id!r}, vendor_id={self.vendor_id!r}, amount={self.amount!r})"
