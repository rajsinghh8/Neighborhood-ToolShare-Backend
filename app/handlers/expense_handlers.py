"""HTTP handlers for /api/v1/events/{event_id}/expenses."""
from __future__ import annotations

from app.handlers.base import BaseHandler
from app.handlers.paths import EVENT_BASE, ID
from app.repositories.expense_repository import SORT_COLUMNS
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseUpdate
from app.services.expense_service import ExpenseService


class ExpenseCollectionHandler(BaseHandler):
    """List (with date-range filter) and create expenses of an event."""

    async def get(self, event_id: str) -> None:
        request = self.page_request(SORT_COLUMNS.keys(), default_sort="incurred_on")
        start, end = self.query_date_range()
        page = await self.service(ExpenseService).list(int(event_id), self.current_user_id, request, start, end)
        self.send_page(page, ExpenseOut)

    async def post(self, event_id: str) -> None:
        data = self.parse_body(ExpenseCreate)
        expense = await self.service(ExpenseService).create(int(event_id), self.current_user_id, data)
        self.send_json(ExpenseOut.model_validate(expense).to_json(), 201)


class ExpenseItemHandler(BaseHandler):
    """Read, update and delete one expense."""

    async def get(self, event_id: str, expense_id: str) -> None:
        expense = await self.service(ExpenseService).get(int(event_id), int(expense_id), self.current_user_id)
        self.send_json(ExpenseOut.model_validate(expense).to_json())

    async def put(self, event_id: str, expense_id: str) -> None:
        data = self.parse_body(ExpenseUpdate)
        expense = await self.service(ExpenseService).update(
            int(event_id), int(expense_id), self.current_user_id, data)
        self.send_json(ExpenseOut.model_validate(expense).to_json())

    async def delete(self, event_id: str, expense_id: str) -> None:
        await self.service(ExpenseService).delete(int(event_id), int(expense_id), self.current_user_id)
        self.send_no_content()


ROUTES = [
    (EVENT_BASE + r"/expenses", ExpenseCollectionHandler),
    (EVENT_BASE + r"/expenses/(?P<expense_id>" + ID + ")", ExpenseItemHandler),
]
