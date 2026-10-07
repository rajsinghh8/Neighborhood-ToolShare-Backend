"""NotificationScheduler: due-soon, overdue, budget threshold, de-duplication, isolation between users."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.events.publisher import InMemoryEventPublisher
from app.models import BudgetCategory, Expense, Notification, Task
from app.models.enums import NotificationType, TaskStatus
from app.scheduler.notification_scheduler import NotificationScheduler
from tests.helpers_notifications import fetch_all, insert_all, owner_of, user_id_by_email

NOW = datetime(2030, 6, 1, 12, 0, 0)
TOPIC = "test.notifications"


@pytest.fixture
def scheduler(ctx) -> NotificationScheduler:
    return NotificationScheduler(ctx.new_uow, TOPIC)


def _task(event_id: int, title: str, due_at: datetime | None, status: TaskStatus = TaskStatus.PENDING) -> Task:
    return Task(event_id=event_id, title=title, status=status, due_at=due_at)


async def _category(ctx, event_id: int, planned: str, *expenses: str) -> BudgetCategory:
    (category,) = await insert_all(ctx, [BudgetCategory(event_id=event_id, name=f"cat-{planned}", planned_amount=Decimal(planned))])
    if expenses:
        await insert_all(ctx, [
            Expense(event_id=event_id, category_id=category.id, description="e", amount=Decimal(a),
                    incurred_on=date(2030, 5, 1))
            for a in expenses
        ])
    return category


async def _notifications(ctx) -> list[Notification]:
    return await fetch_all(ctx, Notification)


# ------------------------------------------------------------------ tasks
async def test_nothing_to_do_returns_zero(scheduler, event_id):
    assert await scheduler.run_once(NOW) == 0


async def test_due_soon_window_boundaries(scheduler, ctx, event_id):
    tasks = await insert_all(ctx, [
        _task(event_id, "at-now", NOW),
        _task(event_id, "in-1h", NOW + timedelta(hours=1)),
        _task(event_id, "at-24h", NOW + timedelta(hours=24)),
        _task(event_id, "after-24h", NOW + timedelta(hours=24, seconds=1)),
        _task(event_id, "no-due-date", None),
    ])
    assert await scheduler.run_once(NOW) == 3
    rows = await _notifications(ctx)
    assert {r.dedup_key for r in rows} == {
        f"task_due_soon:{t.id}:{t.due_at.isoformat()}" for t in tasks[:3]
    }
    assert all(r.type == NotificationType.TASK_DUE_SOON and r.is_read is False for r in rows)


async def test_overdue(scheduler, ctx, event_id):
    late, very_late = await insert_all(ctx, [
        _task(event_id, "late", NOW - timedelta(seconds=1)),
        _task(event_id, "very late", NOW - timedelta(days=30), TaskStatus.IN_PROGRESS),
    ])
    assert await scheduler.run_once(NOW) == 2
    rows = await _notifications(ctx)
    assert {r.type for r in rows} == {NotificationType.TASK_OVERDUE}
    assert {r.dedup_key for r in rows} == {
        f"task_overdue:{late.id}:{late.due_at.isoformat()}",
        f"task_overdue:{very_late.id}:{very_late.due_at.isoformat()}",
    }


async def test_completed_tasks_are_skipped(scheduler, ctx, event_id):
    await insert_all(ctx, [
        _task(event_id, "done late", NOW - timedelta(days=1), TaskStatus.COMPLETED),
        _task(event_id, "done soon", NOW + timedelta(hours=2), TaskStatus.COMPLETED),
    ])
    assert await scheduler.run_once(NOW) == 0
    assert await _notifications(ctx) == []


async def test_notification_addressed_to_event_owner_with_event_and_message(scheduler, ctx, event_id):
    owner = await owner_of(ctx, event_id)
    await insert_all(ctx, [_task(event_id, "Book the band", NOW + timedelta(hours=3))])
    assert await scheduler.run_once(NOW) == 1
    (row,) = await _notifications(ctx)
    assert row.user_id == owner and row.event_id == event_id
    assert "Book the band" in row.message


async def test_deduplication_second_run_creates_nothing(scheduler, ctx, event_id):
    await insert_all(ctx, [
        _task(event_id, "soon", NOW + timedelta(hours=1)),
        _task(event_id, "late", NOW - timedelta(hours=1)),
    ])
    await _category(ctx, event_id, "100.00", "95.00")
    assert await scheduler.run_once(NOW) == 3
    assert await scheduler.run_once(NOW) == 0
    assert await scheduler.run_once(NOW + timedelta(minutes=5)) == 0
    assert len(await _notifications(ctx)) == 3


async def test_due_soon_task_later_becomes_overdue_and_notifies_again(scheduler, ctx, event_id):
    await insert_all(ctx, [_task(event_id, "soon", NOW + timedelta(hours=1))])
    assert await scheduler.run_once(NOW) == 1
    assert await scheduler.run_once(NOW + timedelta(hours=2)) == 1
    types = sorted(r.type.value for r in await _notifications(ctx))
    assert types == ["task_due_soon", "task_overdue"]


async def test_changed_due_date_is_a_new_source_state(scheduler, ctx, event_id):
    (task,) = await insert_all(ctx, [_task(event_id, "soon", NOW + timedelta(hours=1))])
    assert await scheduler.run_once(NOW) == 1
    uow = ctx.new_uow()
    try:
        async with uow.transaction():
            row = await uow.session.get(Task, task.id)
            row.due_at = NOW + timedelta(hours=2)
    finally:
        await uow.close()
    assert await scheduler.run_once(NOW) == 1
    assert len(await _notifications(ctx)) == 2


async def test_default_now_is_current_utc(scheduler, ctx, event_id):
    await insert_all(ctx, [
        _task(event_id, "ancient", datetime(2000, 1, 1)),
        _task(event_id, "far future", datetime(2099, 1, 1)),
    ])
    assert await scheduler.run_once() == 1
    (row,) = await _notifications(ctx)
    assert row.type == NotificationType.TASK_OVERDUE


async def test_aware_now_is_converted_to_naive_utc(scheduler, ctx, event_id):
    await insert_all(ctx, [_task(event_id, "soon", NOW + timedelta(hours=1))])
    aware = NOW.replace(tzinfo=timezone.utc)
    assert await scheduler.run_once(aware) == 1


# ----------------------------------------------------------------- budgets
async def test_budget_threshold_exact_boundary(scheduler, ctx, event_id):
    below = await _category(ctx, event_id, "100.00", "89.99")
    assert await scheduler.run_once(NOW) == 0
    exact = await _category(ctx, event_id, "100.00", "90.00")
    assert await scheduler.run_once(NOW) == 1
    (row,) = await _notifications(ctx)
    assert row.type == NotificationType.BUDGET_THRESHOLD
    assert row.dedup_key == f"budget_threshold:{exact.id}:100.00"
    assert below.id != exact.id


async def test_budget_threshold_crossed_by_additional_expense(scheduler, ctx, event_id):
    category = await _category(ctx, event_id, "100.00", "89.99")
    assert await scheduler.run_once(NOW) == 0
    await insert_all(ctx, [Expense(event_id=event_id, category_id=category.id, description="penny",
                                   amount=Decimal("0.01"), incurred_on=date(2030, 5, 2))])
    assert await scheduler.run_once(NOW) == 1
    assert await scheduler.run_once(NOW) == 0


async def test_budget_threshold_uses_decimal_arithmetic(scheduler, ctx, event_id):
    # 90% of 33.33 is 29.997: 29.99 is below, 30.00 is above.
    await _category(ctx, event_id, "33.33", "29.99")
    assert await scheduler.run_once(NOW) == 0
    await _category(ctx, event_id, "33.33", "30.00")
    assert await scheduler.run_once(NOW) == 1
    # sums of several expenses that are inexact as floats: 0.90 + 1.80 == 2.70 == 90% of 3.00
    await _category(ctx, event_id, "3.00", "0.90", "1.80")
    assert await scheduler.run_once(NOW) == 1


async def test_budget_over_100_percent_and_zero_planned_and_no_spend(scheduler, ctx, event_id):
    over = await _category(ctx, event_id, "50.00", "80.00")
    await _category(ctx, event_id, "0.00", "10.00")      # planned 0 -> never
    await _category(ctx, event_id, "500.00")              # nothing spent -> no
    assert await scheduler.run_once(NOW) == 1
    (row,) = await _notifications(ctx)
    assert row.dedup_key == f"budget_threshold:{over.id}:50.00"


async def test_budget_key_changes_when_planned_amount_changes(scheduler, ctx, event_id):
    category = await _category(ctx, event_id, "100.00", "95.00")
    assert await scheduler.run_once(NOW) == 1
    uow = ctx.new_uow()
    try:
        async with uow.transaction():
            (await uow.session.get(BudgetCategory, category.id)).planned_amount = Decimal("100.50")
    finally:
        await uow.close()
    assert await scheduler.run_once(NOW) == 1
    keys = {r.dedup_key for r in await _notifications(ctx)}
    assert keys == {f"budget_threshold:{category.id}:100.00", f"budget_threshold:{category.id}:100.50"}


# ---------------------------------------------------------------- isolation
async def test_other_users_unaffected(scheduler, ctx, client, event_id, other_token):
    other_event = await client.post("/api/v1/events", {
        "name": "Quiet", "start_at": "2030-03-01T10:00:00Z", "end_at": "2030-03-01T12:00:00Z",
        "guest_capacity": 1, "budget": "10.00",
    }, token=other_token)
    assert other_event.status == 201
    other_event_id = other_event.body["id"]
    await insert_all(ctx, [
        _task(event_id, "mine soon", NOW + timedelta(hours=1)),
        _task(other_event_id, "theirs done", NOW + timedelta(hours=1), TaskStatus.COMPLETED),
    ])
    await _category(ctx, other_event_id, "100.00", "10.00")

    assert await scheduler.run_once(NOW) == 1
    mine = await client.get("/api/v1/notifications")
    theirs = await client.get("/api/v1/notifications", token=other_token)
    assert mine.body["total"] == 1
    assert theirs.body["total"] == 0
    assert mine.body["items"][0]["user_id"] == await owner_of(ctx, event_id)


async def test_each_user_notified_for_their_own_events(scheduler, ctx, client, event_id, other_token):
    other_event = await client.post("/api/v1/events", {
        "name": "Theirs", "start_at": "2030-03-01T10:00:00Z", "end_at": "2030-03-01T12:00:00Z",
        "guest_capacity": 1, "budget": "10.00",
    }, token=other_token)
    other_event_id = other_event.body["id"]
    await insert_all(ctx, [
        _task(event_id, "A", NOW - timedelta(hours=1)),
        _task(other_event_id, "B", NOW - timedelta(hours=1)),
    ])
    assert await scheduler.run_once(NOW) == 2
    by_user = {r.user_id: r for r in await _notifications(ctx)}
    assert set(by_user) == {await owner_of(ctx, event_id), await user_id_by_email(ctx, "intruder@example.com")}
    assert by_user[await owner_of(ctx, other_event_id)].event_id == other_event_id


# --------------------------------------------------------- events and safety
async def test_notification_events_published_post_commit_with_topic(scheduler, ctx, event_id):
    assert isinstance(ctx.publisher, InMemoryEventPublisher)
    ctx.publisher.events.clear()
    await insert_all(ctx, [_task(event_id, "soon", NOW + timedelta(hours=1))])
    await scheduler.run_once(NOW)
    published = [e for e in ctx.publisher.events if e.topic == TOPIC]
    assert len(published) == 1
    assert published[0].event_type == "notification.created"
    assert published[0].payload["type"] == "task_due_soon"
    await scheduler.run_once(NOW)  # de-duplicated: nothing new is published
    assert len([e for e in ctx.publisher.events if e.topic == TOPIC]) == 1


async def test_run_safely_creates_notifications(scheduler, ctx, event_id):
    await insert_all(ctx, [_task(event_id, "late", datetime(2001, 1, 1))])
    await scheduler.run_safely()
    assert len(await _notifications(ctx)) == 1


async def test_run_safely_swallows_failures(caplog):
    def broken_uow():
        raise RuntimeError("db down")

    await NotificationScheduler(broken_uow, TOPIC).run_safely()  # must not raise
    assert any("Notification scheduler run failed" in r.message for r in caplog.records)


async def test_one_failing_notification_does_not_block_others(ctx, event_id, monkeypatch):
    from app.services import notification_recorder

    await insert_all(ctx, [
        _task(event_id, "first", NOW + timedelta(hours=1)),
        _task(event_id, "second", NOW + timedelta(hours=2)),
    ])
    original = notification_recorder.NotificationRecorder.notify
    calls = {"n": 0}

    async def flaky(self, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return await original(self, *args, **kwargs)

    monkeypatch.setattr(notification_recorder.NotificationRecorder, "notify", flaky)
    assert await NotificationScheduler(ctx.new_uow, TOPIC).run_once(NOW) == 1
    assert len(await _notifications(ctx)) == 1
