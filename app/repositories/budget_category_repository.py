"""Queries for budget categories."""
from __future__ import annotations

from sqlalchemy import select

from app.core.pagination import Page, PageRequest
from app.models import BudgetCategory
from app.repositories.base import BaseRepository

SORT_COLUMNS = {
    "id": BudgetCategory.id,
    "name": BudgetCategory.name,
    "planned_amount": BudgetCategory.planned_amount,
}


class BudgetCategoryRepository(BaseRepository[BudgetCategory]):
    """Data access for :class:`BudgetCategory`."""

    model = BudgetCategory

    async def get_in_event(self, category_id: int, event_id: int) -> BudgetCategory | None:
        """Return the category only if it belongs to ``event_id``."""
        category = await self.get(category_id)
        if category is None or category.event_id != event_id:
            return None
        return category

    async def list_for_event(self, event_id: int, request: PageRequest) -> Page[BudgetCategory]:
        """Paginated categories of one event."""
        stmt = select(BudgetCategory).where(BudgetCategory.event_id == event_id)
        return await self.paginate(stmt, request, SORT_COLUMNS)
