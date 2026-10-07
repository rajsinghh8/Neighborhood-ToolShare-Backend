"""Expense use cases: CRUD scoped to an owned event; the category must belong to the same event."""
from __future__ import annotations

import logging
from datetime import date

from app.core.errors import BusinessRuleError, NotFoundError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import Expense
from app.models.enums import AuditAction, AuditEntityType
from app.repositories.budget_category_repository import BudgetCategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.audit_recorder import AuditRecorder
from app.services.event_access import EventAccess

logger = logging.getLogger(__name__)


class ExpenseService:
    """Rules for expenses. Ownership is checked first (404), then the child's event match (404)."""

    def __init__(self, uow: UnitOfWork, access: EventAccess, audit: AuditRecorder) -> None:
        self._uow = uow
        self._access = access
        self._audit = audit
        self._expenses = ExpenseRepository(uow.session)
        self._categories = BudgetCategoryRepository(uow.session)

    async def list(self, event_id: int, user_id: int, request: PageRequest,
                   start: date | None, end: date | None) -> Page[Expense]:
        """Page of expenses, optionally limited to ``incurred_on`` in [start, end] (inclusive)."""
        await self._access.require_owned(event_id, user_id)
        return await self._expenses.list_for_event(event_id, request, start, end)

    async def get(self, event_id: int, expense_id: int, user_id: int) -> Expense:
        """One expense of the event."""
        await self._access.require_owned(event_id, user_id)
        return await self._require(event_id, expense_id)

    async def create(self, event_id: int, user_id: int, data: ExpenseCreate) -> Expense:
        """Create an expense (audited). Foreign/unknown category -> 422."""
        await self._access.require_owned(event_id, user_id)
        await self._require_category(event_id, data.category_id)
        async with self._uow.transaction():
            expense = await self._expenses.add(Expense(
                event_id=event_id, category_id=data.category_id, description=data.description,
                amount=data.amount, incurred_on=data.incurred_on))
            await self._audit.record(event_id, user_id, AuditEntityType.EXPENSE, expense.id, AuditAction.CREATE)
        logger.info("Expense created id=%s event_id=%s", expense.id, event_id)
        return expense

    async def update(self, event_id: int, expense_id: int, user_id: int, data: ExpenseUpdate) -> Expense:
        """Apply the sent fields (audited). A changed category must belong to the event."""
        await self._access.require_owned(event_id, user_id)
        expense = await self._require(event_id, expense_id)
        changes = data.changes()
        if "category_id" in changes:
            await self._require_category(event_id, changes["category_id"])
        async with self._uow.transaction():
            for field_name, value in changes.items():
                setattr(expense, field_name, value)
            await self._expenses.flush()
            await self._audit.record(event_id, user_id, AuditEntityType.EXPENSE, expense.id, AuditAction.UPDATE)
        logger.info("Expense updated id=%s event_id=%s", expense.id, event_id)
        return expense

    async def delete(self, event_id: int, expense_id: int, user_id: int) -> None:
        """Delete an expense (audited)."""
        await self._access.require_owned(event_id, user_id)
        expense = await self._require(event_id, expense_id)
        async with self._uow.transaction():
            await self._expenses.delete(expense.id)
            await self._audit.record(event_id, user_id, AuditEntityType.EXPENSE, expense_id, AuditAction.DELETE)
        logger.info("Expense deleted id=%s event_id=%s", expense_id, event_id)

    async def _require(self, event_id: int, expense_id: int) -> Expense:
        expense = await self._expenses.get_in_event(expense_id, event_id)
        if expense is None:
            raise NotFoundError("Expense not found")
        return expense

    async def _require_category(self, event_id: int, category_id: int) -> None:
        if await self._categories.get_in_event(category_id, event_id) is None:
            raise BusinessRuleError("category_id must refer to a budget category of this event")
