"""Queries for expenses."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.core.pagination import Page, PageRequest
from app.models import Expense
from app.repositories.base import BaseRepository

SORT_COLUMNS = {
    "id": Expense.id,
    "incurred_on": Expense.incurred_on,
    "amount": Expense.amount,
}


class ExpenseRepository(BaseRepository[Expense]):
    """Data access for :class:`Expense`."""

    model = Expense

    async def get_in_event(self, expense_id: int, event_id: int) -> Expense | None:
        """Return the expense only if it belongs to ``event_id``."""
        expense = await self.get(expense_id)
        if expense is None or expense.event_id != event_id:
            return None
        return expense

    async def list_for_event(self, event_id: int, request: PageRequest,
                             start: date | None = None, end: date | None = None) -> Page[Expense]:
        """Paginated expenses of one event; ``start``/``end`` filter ``incurred_on`` inclusively."""
        stmt = select(Expense).where(Expense.event_id == event_id)
        if start is not None:
            stmt = stmt.where(Expense.incurred_on >= start)
        if end is not None:
            stmt = stmt.where(Expense.incurred_on <= end)
        return await self.paginate(stmt, request, SORT_COLUMNS)
