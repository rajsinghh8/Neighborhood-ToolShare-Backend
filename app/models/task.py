from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import TaskPriority, TaskStatus
from app.models.types import str_enum


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[TaskStatus] = mapped_column(str_enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority: Mapped[TaskPriority] = mapped_column(str_enum(TaskPriority), default=TaskPriority.MEDIUM, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    depends_on_task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    event: Mapped["Event"] = relationship(back_populates="tasks", lazy="raise")
    depends_on: Mapped["Task | None"] = relationship(
        back_populates="dependents", remote_side="Task.id", lazy="raise"
    )
    dependents: Mapped[list["Task"]] = relationship(back_populates="depends_on", lazy="raise", passive_deletes=True)

    def __repr__(self) -> str:
        return f"Task(id={self.id!r}, event_id={self.event_id!r}, status={self.status!r})"
