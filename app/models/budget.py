from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.types import money_column


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    planned_amount: Mapped[Decimal] = mapped_column(money_column())

    event: Mapped["Event"] = relationship(back_populates="budget_categories", lazy="raise")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="category", lazy="raise", passive_deletes=True)

    def __repr__(self) -> str:
        return f"BudgetCategory(id={self.id!r}, event_id={self.event_id!r}, name={self.name!r})"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("budget_categories.id", ondelete="CASCADE"), index=True)
    description: Mapped[str] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(money_column())
    incurred_on: Mapped[date] = mapped_column(Date, index=True)

    event: Mapped["Event"] = relationship(back_populates="expenses", lazy="raise")
    category: Mapped["BudgetCategory"] = relationship(back_populates="expenses", lazy="raise")

    def __repr__(self) -> str:
        return f"Expense(id={self.id!r}, category_id={self.category_id!r}, amount={self.amount!r})"
