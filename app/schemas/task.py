"""Request/response schemas for tasks."""
from __future__ import annotations

from pydantic import Field, model_validator

from app.models.enums import TaskPriority, TaskStatus
from app.schemas.common import ApiModel, NameStr, UtcDatetime

_ID_MAX = 2_147_483_647


class TaskCreate(ApiModel):
    """POST body. ``title`` is required; everything else has a default."""

    title: NameStr
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_at: UtcDatetime | None = None
    depends_on_task_id: int | None = Field(default=None, ge=1, le=_ID_MAX)


class TaskUpdate(ApiModel):
    """PUT/PATCH body: only the provided fields change. ``due_at`` and the dependency may be nulled."""

    title: NameStr | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: UtcDatetime | None = None
    depends_on_task_id: int | None = Field(default=None, ge=1, le=_ID_MAX)

    @model_validator(mode="after")
    def _non_nullable_fields(self) -> "TaskUpdate":
        """``title``, ``status`` and ``priority`` can be omitted but never explicitly null."""
        for name in ("title", "status", "priority"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} must not be null")
        return self


class TaskOut(ApiModel):
    """Task representation returned by the API."""

    id: int
    event_id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    due_at: UtcDatetime | None = None
    depends_on_task_id: int | None = None
