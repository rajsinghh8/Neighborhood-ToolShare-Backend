"""Read queries used by the notification scheduler (cross-event, not user-scoped)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BudgetCategory, Event, Expense, Task
from app.models.enums import TaskStatus

_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class TaskDueCandidate:
    """An unfinished task with a due date at or before the look-ahead horizon."""

    task_id: int
    event_id: int
    owner_id: int
    title: str
    due_at: datetime


@dataclass(frozen=True)
class CategorySpend:
    """A budget category with its planned amount and total spend."""

    category_id: int
    event_id: int
    owner_id: int
    name: str
    planned_amount: Decimal
    actual_amount: Decimal


class SchedulerRepository:
    """Queries for due/overdue tasks and budget category spend."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def tasks_due_until(self, horizon: datetime) -> list[TaskDueCandidate]:
        """Non-completed tasks with ``due_at <= horizon`` (overdue ones included), with the event owner."""
        stmt = (
            select(Task.id, Task.event_id, Event.owner_id, Task.title, Task.due_at)
            .join(Event, Event.id == Task.event_id)
            .where(Task.status != TaskStatus.COMPLETED, Task.due_at.is_not(None), Task.due_at <= horizon)
            .order_by(Task.id)
        )
        rows = (await self._session.execute(stmt)).all()
        return [TaskDueCandidate(r[0], r[1], r[2], r[3], r[4]) for r in rows]

    async def category_spend(self) -> list[CategorySpend]:
        """Every category with planned_amount > 0 and the sum of its expenses (0 when none)."""
        spent = func.coalesce(func.sum(Expense.amount), 0)
        stmt = (
            select(BudgetCategory.id, BudgetCategory.event_id, Event.owner_id, BudgetCategory.name,
                   BudgetCategory.planned_amount, spent)
            .join(Event, Event.id == BudgetCategory.event_id)
            .outerjoin(Expense, Expense.category_id == BudgetCategory.id)
            .where(BudgetCategory.planned_amount > 0)
            .group_by(BudgetCategory.id, BudgetCategory.event_id, Event.owner_id, BudgetCategory.name,
                      BudgetCategory.planned_amount)
            .order_by(BudgetCategory.id)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            CategorySpend(r[0], r[1], r[2], r[3], _to_money(r[4]), _to_money(r[5]))
            for r in rows
        ]


def _to_money(value: object) -> Decimal:
    """Normalise a DB numeric (Decimal, float on SQLite sums, int) to an exact 2dp Decimal."""
    return Decimal(str(value)).quantize(_CENTS)
