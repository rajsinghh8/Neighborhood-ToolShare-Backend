"""Budget category use cases: CRUD scoped to an owned event, with actual/remaining figures."""
from __future__ import annotations

import logging

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import BudgetCategory
from app.models.enums import AuditAction, AuditEntityType
from app.repositories.budget_category_repository import BudgetCategoryRepository
from app.repositories.stats import StatsRepository
from app.schemas.budget_category import BudgetCategoryCreate, BudgetCategoryOut, BudgetCategoryUpdate
from app.services.audit_recorder import AuditRecorder
from app.services.event_access import EventAccess

logger = logging.getLogger(__name__)


class BudgetCategoryService:
    """Rules for budget categories. Every call first checks event ownership (404 otherwise)."""

    def __init__(self, uow: UnitOfWork, access: EventAccess, audit: AuditRecorder) -> None:
        self._uow = uow
        self._access = access
        self._audit = audit
        self._categories = BudgetCategoryRepository(uow.session)
        self._stats = StatsRepository(uow.session)

    async def list(self, event_id: int, user_id: int, request: PageRequest) -> Page[BudgetCategoryOut]:
        """Page of categories, each with actual and remaining amounts (single aggregate query)."""
        await self._access.require_owned(event_id, user_id)
        page = await self._categories.list_for_event(event_id, request)
        actuals = await self._stats.category_actuals([c.id for c in page.items])
        items = [BudgetCategoryOut.build(c, actuals[c.id]) for c in page.items]
        return Page(items=items, total=page.total, request=page.request)

    async def get(self, event_id: int, category_id: int, user_id: int) -> BudgetCategoryOut:
        """One category with actual and remaining amounts."""
        await self._access.require_owned(event_id, user_id)
        category = await self._require(event_id, category_id)
        return await self._to_out(category)

    async def create(self, event_id: int, user_id: int, data: BudgetCategoryCreate) -> BudgetCategoryOut:
        """Create a category (audited)."""
        await self._access.require_owned(event_id, user_id)
        async with self._uow.transaction():
            category = await self._categories.add(
                BudgetCategory(event_id=event_id, name=data.name, planned_amount=data.planned_amount))
            await self._audit.record(event_id, user_id, AuditEntityType.BUDGET_CATEGORY,
                                     category.id, AuditAction.CREATE)
        logger.info("Budget category created id=%s event_id=%s", category.id, event_id)
        return await self._to_out(category)

    async def update(self, event_id: int, category_id: int, user_id: int,
                     data: BudgetCategoryUpdate) -> BudgetCategoryOut:
        """Apply the sent fields to a category (audited)."""
        await self._access.require_owned(event_id, user_id)
        category = await self._require(event_id, category_id)
        async with self._uow.transaction():
            for field_name, value in data.changes().items():
                setattr(category, field_name, value)
            await self._categories.flush()
            await self._audit.record(event_id, user_id, AuditEntityType.BUDGET_CATEGORY,
                                     category.id, AuditAction.UPDATE)
        logger.info("Budget category updated id=%s event_id=%s", category.id, event_id)
        return await self._to_out(category)

    async def delete(self, event_id: int, category_id: int, user_id: int) -> None:
        """Delete a category; its expenses are removed by the database FK cascade (audited)."""
        await self._access.require_owned(event_id, user_id)
        category = await self._require(event_id, category_id)
        async with self._uow.transaction():
            await self._categories.delete(category.id)
            await self._audit.record(event_id, user_id, AuditEntityType.BUDGET_CATEGORY,
                                     category_id, AuditAction.DELETE)
        logger.info("Budget category deleted id=%s event_id=%s", category_id, event_id)

    async def _require(self, event_id: int, category_id: int) -> BudgetCategory:
        category = await self._categories.get_in_event(category_id, event_id)
        if category is None:
            raise NotFoundError("Budget category not found")
        return category

    async def _to_out(self, category: BudgetCategory) -> BudgetCategoryOut:
        actual = await self._stats.category_actual_spend(category.id)
        return BudgetCategoryOut.build(category, actual)
