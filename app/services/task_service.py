"""Task business rules: status transitions, dependency validation, audit trail."""
from __future__ import annotations

import logging
from typing import Any

from app.core.errors import BusinessRuleError, NotFoundError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import Task
from app.models.enums import AuditAction, AuditEntityType, TaskPriority, TaskStatus
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.audit_recorder import AuditRecorder
from app.services.event_access import EventAccess

logger = logging.getLogger(__name__)


class TaskStatusTransitions:
    """Pure transition table: pending -> in_progress -> completed, with back-steps.

    Staying in the same status is always allowed (it is not a change).
    """

    _ALLOWED: dict[TaskStatus, frozenset[TaskStatus]] = {
        TaskStatus.PENDING: frozenset({TaskStatus.IN_PROGRESS}),
        TaskStatus.IN_PROGRESS: frozenset({TaskStatus.PENDING, TaskStatus.COMPLETED}),
        TaskStatus.COMPLETED: frozenset({TaskStatus.IN_PROGRESS}),
    }

    @classmethod
    def can_transition(cls, current: TaskStatus, target: TaskStatus) -> bool:
        """True when ``target`` equals ``current`` or is a permitted next status."""
        return current == target or target in cls._ALLOWED[current]

    @classmethod
    def ensure(cls, current: TaskStatus, target: TaskStatus) -> None:
        """Raise :class:`BusinessRuleError` for an illegal transition."""
        if not cls.can_transition(current, target):
            raise BusinessRuleError(
                f"Illegal status transition: {current.value} -> {target.value}")


class TaskService:
    """Use-cases for tasks of an event owned by the calling user."""

    def __init__(self, uow: UnitOfWork, access: EventAccess, audit: AuditRecorder) -> None:
        self._uow = uow
        self._access = access
        self._audit = audit
        self._tasks = TaskRepository(uow.session)

    # ------------------------------------------------------------------ reads
    async def list_tasks(self, user_id: int, event_id: int, request: PageRequest,
                         status: TaskStatus | None = None,
                         priority: TaskPriority | None = None) -> Page[Task]:
        """Paginated, filtered tasks of an owned event."""
        await self._access.require_owned(event_id, user_id)
        return await self._tasks.list_for_event(event_id, request, status, priority)

    async def get_task(self, user_id: int, event_id: int, task_id: int) -> Task:
        """One task of an owned event or NotFoundError."""
        await self._access.require_owned(event_id, user_id)
        return await self._require_task(event_id, task_id)

    # ----------------------------------------------------------------- writes
    async def create_task(self, user_id: int, event_id: int, data: TaskCreate) -> Task:
        """Create a task (any initial status is accepted) and audit it."""
        await self._access.require_owned(event_id, user_id)
        await self._validate_dependency(event_id, None, data.depends_on_task_id)
        async with self._uow.transaction():
            task = await self._tasks.add(Task(
                event_id=event_id, title=data.title, status=data.status, priority=data.priority,
                due_at=data.due_at, depends_on_task_id=data.depends_on_task_id,
            ))
            await self._audit.record(event_id, user_id, AuditEntityType.TASK, task.id, AuditAction.CREATE)
        logger.info("Task created id=%s event_id=%s", task.id, event_id)
        return task

    async def update_task(self, user_id: int, event_id: int, task_id: int, data: TaskUpdate) -> Task:
        """Apply the provided fields; audit UPDATE and/or STATUS_CHANGE."""
        await self._access.require_owned(event_id, user_id)
        task = await self._require_task(event_id, task_id)
        changes = data.changes()

        old_status = task.status
        new_status: TaskStatus = changes.get("status", old_status)
        TaskStatusTransitions.ensure(old_status, new_status)
        if "depends_on_task_id" in changes:
            await self._validate_dependency(event_id, task.id, changes["depends_on_task_id"])

        other_changed = False
        async with self._uow.transaction():
            for name, value in changes.items():
                if name == "status" or getattr(task, name) == value:
                    continue
                setattr(task, name, value)
                other_changed = True
            status_changed = new_status != old_status
            if status_changed:
                task.status = new_status
            await self._tasks.flush()
            if other_changed:
                await self._audit.record(event_id, user_id, AuditEntityType.TASK, task.id, AuditAction.UPDATE)
            if status_changed:
                await self._audit.record(event_id, user_id, AuditEntityType.TASK, task.id,
                                         AuditAction.STATUS_CHANGE)
        logger.info("Task updated id=%s event_id=%s status_changed=%s", task.id, event_id, status_changed)
        return task

    async def delete_task(self, user_id: int, event_id: int, task_id: int) -> None:
        """Delete a task; dependents get ``depends_on_task_id = NULL`` through the FK."""
        await self._access.require_owned(event_id, user_id)
        task = await self._require_task(event_id, task_id)
        async with self._uow.transaction():
            await self._tasks.delete(task.id)
            await self._audit.record(event_id, user_id, AuditEntityType.TASK, task_id, AuditAction.DELETE)
        logger.info("Task deleted id=%s event_id=%s", task_id, event_id)

    # ---------------------------------------------------------------- helpers
    async def _require_task(self, event_id: int, task_id: int) -> Task:
        task = await self._tasks.get_in_event(event_id, task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task

    async def _validate_dependency(self, event_id: int, task_id: int | None, depends_on: int | None) -> None:
        """Dependency must exist in the same event, not be the task itself, and not close a cycle."""
        if depends_on is None:
            return
        if task_id is not None and depends_on == task_id:
            raise BusinessRuleError("A task cannot depend on itself")
        if await self._tasks.get_in_event(event_id, depends_on) is None:
            raise BusinessRuleError("depends_on_task_id must reference a task of the same event")
        if task_id is not None and await self._creates_cycle(task_id, depends_on):
            raise BusinessRuleError("Task dependency would create a cycle")

    async def _creates_cycle(self, task_id: int, depends_on: int) -> bool:
        """Walk the dependency chain from ``depends_on``; reaching ``task_id`` means a cycle."""
        seen: set[int] = set()
        current: Any = depends_on
        while current is not None and current not in seen:
            if current == task_id:
                return True
            seen.add(current)
            current = await self._tasks.get_dependency_id(current)
        return False
