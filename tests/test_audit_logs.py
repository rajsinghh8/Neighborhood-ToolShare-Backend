"""Audit-log endpoint: owner-only access, shape, filters, sorting, pagination."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.models import AuditLog
from app.models.enums import AuditAction, AuditEntityType
from tests.helpers_notifications import insert_all, owner_of

T = AuditEntityType
A = AuditAction


def _url(event_id: int) -> str:
    return f"/api/v1/events/{event_id}/audit-logs"


def _row(event_id: int, actor_id: int, entity_type: T, entity_id: int, action: A, minute: int) -> AuditLog:
    return AuditLog(event_id=event_id, actor_id=actor_id, entity_type=entity_type, entity_id=entity_id,
                    action=action, created_at=datetime(2030, 1, 1, 9, 0, 0) + timedelta(minutes=minute))


async def _seed(ctx, event_id: int) -> list[AuditLog]:
    actor = await owner_of(ctx, event_id)
    return await insert_all(ctx, [
        _row(event_id, actor, T.TASK, 1, A.CREATE, 0),
        _row(event_id, actor, T.TASK, 1, A.STATUS_CHANGE, 1),
        _row(event_id, actor, T.GUEST, 2, A.CREATE, 2),
        _row(event_id, actor, T.EXPENSE, 3, A.DELETE, 3),
        _row(event_id, actor, T.TASK, 4, A.UPDATE, 4),
    ])


async def test_requires_authentication(anon, event_id):
    assert (await anon.get(_url(event_id))).status == 401


async def test_empty_list(client, event_id):
    res = await client.get(_url(event_id))
    assert res.status == 200
    assert res.body["items"] == [] and res.body["total"] == 0


async def test_shape_and_default_order_id_desc(client, ctx, event_id):
    rows = await _seed(ctx, event_id)
    res = await client.get(_url(event_id))
    assert res.status == 200 and res.body["total"] == 5
    assert [i["id"] for i in res.body["items"]] == [r.id for r in reversed(rows)]
    item = res.body["items"][-1]
    assert set(item) == {"id", "event_id", "actor_id", "entity_type", "entity_id", "action", "created_at"}
    assert item["entity_type"] == "task" and item["action"] == "create"
    assert item["event_id"] == event_id and item["created_at"].endswith("Z")


async def test_unknown_event_404(client):
    assert (await client.get(_url(987654))).status == 404


async def test_other_users_event_is_404(client, ctx, event_id, other_token):
    await _seed(ctx, event_id)
    res = await client.get(_url(event_id), token=other_token)
    assert res.status == 404
    assert res.body["status"] == 404 and res.body["path"] == _url(event_id)


async def test_only_logs_of_that_event(client, ctx, event_id):
    await _seed(ctx, event_id)
    second = await client.post("/api/v1/events", {
        "name": "Second", "start_at": "2030-02-01T10:00:00Z", "end_at": "2030-02-01T12:00:00Z",
        "guest_capacity": 1, "budget": "10.00",
    })
    assert second.status == 201
    other_event = second.body["id"]
    actor = await owner_of(ctx, other_event)
    await insert_all(ctx, [_row(other_event, actor, T.VENDOR, 9, A.CREATE, 10)])
    first_list = await client.get(_url(event_id))
    second_list = await client.get(_url(other_event))
    assert first_list.body["total"] == 5
    assert second_list.body["total"] == 1 and second_list.body["items"][0]["entity_type"] == "vendor"


async def test_filter_entity_type_and_action(client, ctx, event_id):
    await _seed(ctx, event_id)
    tasks = await client.get(_url(event_id) + "?entity_type=task")
    assert tasks.body["total"] == 3 and all(i["entity_type"] == "task" for i in tasks.body["items"])
    creates = await client.get(_url(event_id) + "?action=create")
    assert creates.body["total"] == 2
    both = await client.get(_url(event_id) + "?entity_type=task&action=status_change")
    assert both.body["total"] == 1 and both.body["items"][0]["action"] == "status_change"
    none = await client.get(_url(event_id) + "?entity_type=vendor")
    assert none.body["total"] == 0 and none.body["items"] == []


async def test_invalid_filters_and_sort_422(client, event_id):
    for query in ("entity_type=nope", "action=nope", "sort=actor_id", "order=up", "page=0", "size=0"):
        res = await client.get(_url(event_id) + "?" + query)
        assert res.status == 422, query


async def test_sort_created_at_asc_and_desc(client, ctx, event_id):
    rows = await _seed(ctx, event_id)
    asc = await client.get(_url(event_id) + "?sort=created_at&order=asc")
    assert [i["id"] for i in asc.body["items"]] == [r.id for r in rows]
    desc = await client.get(_url(event_id) + "?sort=created_at&order=desc")
    assert [i["id"] for i in desc.body["items"]] == [r.id for r in reversed(rows)]


async def test_pagination(client, ctx, event_id):
    rows = await _seed(ctx, event_id)
    newest_first = [r.id for r in reversed(rows)]
    page1 = await client.get(_url(event_id) + "?size=2")
    page3 = await client.get(_url(event_id) + "?size=2&page=3")
    assert [i["id"] for i in page1.body["items"]] == newest_first[:2]
    assert page1.body["total"] == 5 and page1.body["page"] == 1
    assert [i["id"] for i in page3.body["items"]] == newest_first[4:]
    beyond = await client.get(_url(event_id) + "?size=2&page=9")
    assert beyond.status == 200 and beyond.body["items"] == [] and beyond.body["total"] == 5
    capped = await client.get(_url(event_id) + "?size=1000")
    assert capped.body["size"] == 100


async def test_deleting_event_cascades_audit_rows(ctx, client, event_id):
    from sqlalchemy import delete, func, select
    from app.models import Event

    await _seed(ctx, event_id)
    uow = ctx.new_uow()
    try:
        async with uow.transaction():
            await uow.session.execute(delete(Event).where(Event.id == event_id))
        remaining = (await uow.session.execute(select(func.count()).select_from(AuditLog))).scalar_one()
    finally:
        await uow.close()
    assert remaining == 0
