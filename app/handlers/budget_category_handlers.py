"""HTTP handlers for /api/v1/events/{event_id}/budget-categories."""
from __future__ import annotations

from app.handlers.base import BaseHandler
from app.handlers.paths import EVENT_BASE, ID
from app.repositories.budget_category_repository import SORT_COLUMNS
from app.schemas.budget_category import BudgetCategoryCreate, BudgetCategoryOut, BudgetCategoryUpdate
from app.services.budget_category_service import BudgetCategoryService


class BudgetCategoryCollectionHandler(BaseHandler):
    """List and create categories of an event."""

    async def get(self, event_id: str) -> None:
        request = self.page_request(SORT_COLUMNS.keys(), default_sort="id")
        page = await self.service(BudgetCategoryService).list(int(event_id), self.current_user_id, request)
        self.send_page(page, BudgetCategoryOut)

    async def post(self, event_id: str) -> None:
        data = self.parse_body(BudgetCategoryCreate)
        created = await self.service(BudgetCategoryService).create(int(event_id), self.current_user_id, data)
        self.send_json(created.to_json(), 201)


class BudgetCategoryItemHandler(BaseHandler):
    """Read, update and delete one category."""

    async def get(self, event_id: str, category_id: str) -> None:
        category = await self.service(BudgetCategoryService).get(
            int(event_id), int(category_id), self.current_user_id)
        self.send_json(category.to_json())

    async def put(self, event_id: str, category_id: str) -> None:
        data = self.parse_body(BudgetCategoryUpdate)
        category = await self.service(BudgetCategoryService).update(
            int(event_id), int(category_id), self.current_user_id, data)
        self.send_json(category.to_json())

    async def delete(self, event_id: str, category_id: str) -> None:
        await self.service(BudgetCategoryService).delete(int(event_id), int(category_id), self.current_user_id)
        self.send_no_content()


ROUTES = [
    (EVENT_BASE + r"/budget-categories", BudgetCategoryCollectionHandler),
    (EVENT_BASE + r"/budget-categories/(?P<category_id>" + ID + ")", BudgetCategoryItemHandler),
]
