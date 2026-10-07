"""Task queries: event-scoped lookup, filtered/sorted listing, dependency chain walking."""
from __future__ import annotations

from sqlalchemy import case, select

from app.core.pagination import Page, PageRequest
from app.models import Task
from app.models.enums import TaskPriority, TaskStatus
from app.repositories.base import BaseRepository

# low < medium < high semantic ordering (alphabetical order would be wrong).
PRIORITY_RANK = case(
    (Task.priority == TaskPriority.LOW, 1),
    (Task.priority == TaskPriority.MEDIUM, 2),
    (Task.priority == TaskPriority.HIGH, 3),
    else_=0,
)

SORT_COLUMNS = {
    "due_at": Task.due_at,
    "priority": PRIORITY_RANK,
    "status": Task.status,
    "id": Task.id,
}


class TaskRepository(BaseRepository[Task]):
    """Persistence operations for :class:`Task`."""

    model = Task

    async def get_in_event(self, event_id: int, task_id: int) -> Task | None:
        """Task by id, only when it belongs to ``event_id``."""
        stmt = select(Task).where(Task.id == task_id, Task.event_id == event_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_event(self, event_id: int, request: PageRequest, status: TaskStatus | None = None,
                             priority: TaskPriority | None = None) -> Page[Task]:
        """Paginated tasks of one event with optional status/priority filters."""
        stmt = select(Task).where(Task.event_id == event_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        return await self.paginate(stmt, request, SORT_COLUMNS)

    async def get_dependency_id(self, task_id: int) -> int | None:
        """The ``depends_on_task_id`` of a task (``None`` when absent or unset)."""
        stmt = select(Task.depends_on_task_id).where(Task.id == task_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()
