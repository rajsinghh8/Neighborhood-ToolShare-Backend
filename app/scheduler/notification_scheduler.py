"""Periodic job creating due-soon / overdue / budget-threshold notifications (de-duplicated)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable

from app.core.unit_of_work import UnitOfWork
from app.models.enums import NotificationType
from app.repositories.scheduler_repository import SchedulerRepository
from app.schemas.common import format_money
from app.services.notification_recorder import NotificationRecorder

logger = logging.getLogger(__name__)

DUE_SOON_WINDOW = timedelta(hours=24)
BUDGET_THRESHOLD_RATIO = Decimal("0.9")


@dataclass(frozen=True)
class _Pending:
    """One notification the scheduler wants to create."""

    user_id: int
    event_id: int
    type: NotificationType
    message: str
    dedup_key: str


class NotificationScheduler:
    """Scans tasks and budgets and notifies event owners. Safe to run repeatedly."""

    def __init__(self, new_uow: Callable[[], UnitOfWork], topic: str) -> None:
        self._new_uow = new_uow
        self._topic = topic

    async def run_safely(self) -> None:
        """Entry point for PeriodicCallback: never raises."""
        try:
            created = await self.run_once()
            logger.info("Notification scheduler run finished created=%s", created)
        except Exception:  # noqa: BLE001 - boundary: a failed run must not stop the periodic callback
            logger.exception("Notification scheduler run failed")

    async def run_once(self, now: datetime | None = None) -> int:
        """Create all due notifications; returns how many new rows were inserted."""
        current = _naive_utc(now)
        candidates = await self._collect(current)
        created = 0
        for pending in candidates:
            if await self._create(pending):
                created += 1
        return created

    async def _collect(self, now: datetime) -> list[_Pending]:
        uow = self._new_uow()
        try:
            repo = SchedulerRepository(uow.session)
            pending: list[_Pending] = []
            for task in await repo.tasks_due_until(now + DUE_SOON_WINDOW):
                if task.due_at < now:
                    kind, label, prefix = NotificationType.TASK_OVERDUE, "is overdue", "task_overdue"
                else:
                    kind, label, prefix = NotificationType.TASK_DUE_SOON, "is due within 24 hours", "task_due_soon"
                pending.append(_Pending(
                    task.owner_id, task.event_id, kind,
                    f"Task '{task.title}' {label} (due {task.due_at.isoformat()}Z)",
                    f"{prefix}:{task.task_id}:{task.due_at.isoformat()}",
                ))
            for cat in await repo.category_spend():
                if cat.planned_amount > 0 and cat.actual_amount >= BUDGET_THRESHOLD_RATIO * cat.planned_amount:
                    pending.append(_Pending(
                        cat.owner_id, cat.event_id, NotificationType.BUDGET_THRESHOLD,
                        f"Budget category '{cat.name}' has used {format_money(cat.actual_amount)} "
                        f"of {format_money(cat.planned_amount)} (90% threshold reached)",
                        f"budget_threshold:{cat.category_id}:{format_money(cat.planned_amount)}",
                    ))
            return pending
        finally:
            await uow.close()

    async def _create(self, pending: _Pending) -> bool:
        """Insert one notification in its own transaction; failures are logged, not raised."""
        uow = self._new_uow()
        try:
            async with uow.transaction():
                row = await NotificationRecorder(uow, self._topic).notify(
                    pending.user_id, pending.event_id, pending.type, pending.message, pending.dedup_key)
            return row is not None
        except Exception:  # noqa: BLE001 - boundary: one bad notification must not block the others
            logger.exception("Failed to create notification key=%s", pending.dedup_key)
            return False
        finally:
            await uow.close()


def _naive_utc(value: datetime | None) -> datetime:
    """Naive-UTC ``now`` (the storage convention); aware inputs are converted."""
    if value is None:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value
