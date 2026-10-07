"""Read-only aggregate queries shared by several services (event detail, categories, scheduler)."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Expense, Guest
from app.models.enums import InvitationStatus
from app.models.types import ZERO


class StatsRepository:
    """Aggregates over guests and expenses. Money sums are always Decimal."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def accepted_guest_count(self, event_id: int) -> int:
        stmt = select(func.count()).select_from(Guest).where(
            Guest.event_id == event_id, Guest.invitation_status == InvitationStatus.ACCEPTED)
        return (await self._session.execute(stmt)).scalar_one()

    async def guest_count(self, event_id: int) -> int:
        stmt = select(func.count()).select_from(Guest).where(Guest.event_id == event_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def event_actual_spend(self, event_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.event_id == event_id)
        return Decimal((await self._session.execute(stmt)).scalar_one() or 0) or ZERO

    async def category_actual_spend(self, category_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.category_id == category_id)
        return Decimal((await self._session.execute(stmt)).scalar_one() or 0) or ZERO

    async def category_actuals(self, category_ids: list[int]) -> dict[int, Decimal]:
        """Actual spend per category id (missing ids -> 0.00) in one query."""
        if not category_ids:
            return {}
        stmt = (select(Expense.category_id, func.sum(Expense.amount))
                .where(Expense.category_id.in_(category_ids)).group_by(Expense.category_id))
        rows = (await self._session.execute(stmt)).all()
        result = {cid: ZERO for cid in category_ids}
        result.update({cid: Decimal(total) for cid, total in rows})
        return result
