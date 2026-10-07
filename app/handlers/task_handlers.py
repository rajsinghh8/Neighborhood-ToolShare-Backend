"""HTTP handlers for /api/v1/events/{event_id}/tasks."""
from __future__ import annotations

from app.handlers.base import BaseHandler
from app.handlers.paths import EVENT_BASE, ID
from app.models.enums import TaskPriority, TaskStatus
from app.repositories.task_repository import SORT_COLUMNS
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services.task_service import TaskService


class TaskCollectionHandler(BaseHandler):
    """List and create tasks of an event."""

    async def get(self, event_id: str) -> None:
        request = self.page_request(SORT_COLUMNS.keys(), default_sort="id")
        status = self.query_enum("status", TaskStatus)
        priority = self.query_enum("priority", TaskPriority)
        page = await self.service(TaskService).list_tasks(
            self.current_user_id, int(event_id), request, status, priority)
        self.send_page(page, TaskOut)

    async def post(self, event_id: str) -> None:
        data = self.parse_body(TaskCreate)
        task = await self.service(TaskService).create_task(self.current_user_id, int(event_id), data)
        self.send_json(TaskOut.model_validate(task).to_json(), 201)


class TaskItemHandler(BaseHandler):
    """Read, update and delete one task."""

    async def get(self, event_id: str, task_id: str) -> None:
        task = await self.service(TaskService).get_task(self.current_user_id, int(event_id), int(task_id))
        self.send_json(TaskOut.model_validate(task).to_json())

    async def put(self, event_id: str, task_id: str) -> None:
        data = self.parse_body(TaskUpdate)
        task = await self.service(TaskService).update_task(
            self.current_user_id, int(event_id), int(task_id), data)
        self.send_json(TaskOut.model_validate(task).to_json())

    async def patch(self, event_id: str, task_id: str) -> None:
        await self.put(event_id, task_id)

    async def delete(self, event_id: str, task_id: str) -> None:
        await self.service(TaskService).delete_task(self.current_user_id, int(event_id), int(task_id))
        self.send_no_content()


ROUTES = [
    (EVENT_BASE + r"/tasks/?", TaskCollectionHandler),
    (EVENT_BASE + r"/tasks/(?P<task_id>" + ID + r")/?", TaskItemHandler),
]
