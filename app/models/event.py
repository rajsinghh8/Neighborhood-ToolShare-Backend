from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.types import money_column


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    guest_capacity: Mapped[int] = mapped_column(Integer)
    budget: Mapped[Decimal] = mapped_column(money_column())

    owner: Mapped["User"] = relationship(back_populates="events", lazy="raise")
    tasks: Mapped[list["Task"]] = relationship(back_populates="event", lazy="raise", passive_deletes=True)
    guests: Mapped[list["Guest"]] = relationship(back_populates="event", lazy="raise", passive_deletes=True)
    budget_categories: Mapped[list["BudgetCategory"]] = relationship(back_populates="event", lazy="raise", passive_deletes=True)
    expenses: Mapped[list["Expense"]] = relationship(back_populates="event", lazy="raise", passive_deletes=True)
    schedule_items: Mapped[list["ScheduleItem"]] = relationship(back_populates="event", lazy="raise", passive_deletes=True)
    vendors: Mapped[list["Vendor"]] = relationship(back_populates="event", lazy="raise", passive_deletes=True)
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="event", lazy="raise", passive_deletes=True)

    def __repr__(self) -> str:
        return f"Event(id={self.id!r}, owner_id={self.owner_id!r}, name={self.name!r})"
