"""Notification endpoints: list/filter/sort/paginate, get, mark read, delete, ownership."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.models import Notification
from app.models.enums import NotificationType
from tests.helpers_notifications import insert_all, owner_of, user_id_by_email

BASE = "/api/v1/notifications"


def _notification(user_id: int, event_id: int | None, n: int, is_read: bool = False,
                  type_: NotificationType = NotificationType.TASK_DUE_SOON) -> Notification:
    return Notification(
        user_id=user_id, event_id=event_id, type=type_, message=f"message {n}", is_read=is_read,
        dedup_key=f"k{n}", created_at=datetime(2030, 1, 1, 12, 0, 0) + timedelta(minutes=n),
    )


async def _seed(ctx, event_id: int, count: int = 5) -> tuple[int, list[Notification]]:
    user_id = await owner_of(ctx, event_id)
    rows = await insert_all(ctx, [_notification(user_id, event_id, n, is_read=n % 2 == 0) for n in range(count)])
    return user_id, rows


async def test_requires_authentication(anon):
    assert (await anon.get(BASE)).status == 401
    assert (await anon.get(f"{BASE}/1")).status == 401
    assert (await anon.patch(f"{BASE}/1", {"is_read": True})).status == 401
    assert (await anon.delete(f"{BASE}/1")).status == 401


async def test_list_empty(client):
    res = await client.get(BASE)
    assert res.status == 200
    assert res.body["items"] == [] and res.body["total"] == 0
    assert res.body["page"] == 1 and res.body["size"] == res.body["limit"] == 20


async def test_list_shape_and_default_sort_newest_first(client, ctx, event_id):
    user_id, rows = await _seed(ctx, event_id)
    res = await client.get(BASE)
    assert res.status == 200
    assert res.body["total"] == 5
    assert [i["id"] for i in res.body["items"]] == [r.id for r in reversed(rows)]
    first = res.body["items"][0]
    assert set(first) == {"id", "user_id", "event_id", "type", "message", "is_read", "dedup_key", "created_at"}
    assert first["user_id"] == user_id and first["event_id"] == event_id
    assert first["type"] == "task_due_soon"
    assert first["created_at"].endswith("Z")


async def test_list_sort_ascending_and_by_id(client, ctx, event_id):
    _, rows = await _seed(ctx, event_id)
    asc = await client.get(f"{BASE}?sort=created_at&order=asc")
    assert [i["id"] for i in asc.body["items"]] == [r.id for r in rows]
    by_id = await client.get(f"{BASE}?sort=id&order=desc")
    assert [i["id"] for i in by_id.body["items"]] == sorted((r.id for r in rows), reverse=True)


async def test_list_pagination(client, ctx, event_id):
    _, rows = await _seed(ctx, event_id)
    ids_newest_first = [r.id for r in reversed(rows)]
    page2 = await client.get(f"{BASE}?page=2&size=2")
    assert page2.status == 200
    assert page2.body["total"] == 5 and page2.body["page"] == 2 and page2.body["size"] == 2
    assert [i["id"] for i in page2.body["items"]] == ids_newest_first[2:4]
    by_offset = await client.get(f"{BASE}?limit=2&offset=4")
    assert [i["id"] for i in by_offset.body["items"]] == ids_newest_first[4:]


async def test_list_filter_is_read(client, ctx, event_id):
    await _seed(ctx, event_id)  # n=0,2,4 read; n=1,3 unread
    read = await client.get(f"{BASE}?is_read=true")
    unread = await client.get(f"{BASE}?is_read=false")
    assert read.body["total"] == 3 and all(i["is_read"] for i in read.body["items"])
    assert unread.body["total"] == 2 and not any(i["is_read"] for i in unread.body["items"])


async def test_list_invalid_params_422(client):
    for query in ("is_read=maybe", "sort=message", "order=sideways", "page=0", "size=abc"):
        res = await client.get(f"{BASE}?{query}")
        assert res.status == 422, query
        assert res.body["status"] == 422 and res.body["path"] == BASE


async def test_list_only_own_notifications(client, ctx, event_id, other_token):
    await _seed(ctx, event_id, count=2)
    other_id = await user_id_by_email(ctx, "intruder@example.com")
    await insert_all(ctx, [_notification(other_id, None, 99)])
    mine = await client.get(BASE)
    theirs = await client.get(BASE, token=other_token)
    assert mine.body["total"] == 2
    assert theirs.body["total"] == 1 and theirs.body["items"][0]["event_id"] is None


async def test_get_notification(client, ctx, event_id):
    _, rows = await _seed(ctx, event_id, count=1)
    res = await client.get(f"{BASE}/{rows[0].id}")
    assert res.status == 200
    assert res.body["id"] == rows[0].id and res.body["message"] == "message 0"


async def test_get_missing_404(client):
    res = await client.get(f"{BASE}/424242")
    assert res.status == 404
    assert res.body["status"] == 404 and res.body["path"] == f"{BASE}/424242"


async def test_other_users_notification_is_404_for_every_verb(client, ctx, event_id, other_token):
    _, rows = await _seed(ctx, event_id, count=1)
    url = f"{BASE}/{rows[0].id}"
    assert (await client.get(url, token=other_token)).status == 404
    assert (await client.patch(url, {"is_read": True}, token=other_token)).status == 404
    assert (await client.delete(url, token=other_token)).status == 404
    still = await client.get(url)
    assert still.status == 200 and still.body["is_read"] is True  # n=0 was seeded as read; untouched


async def test_mark_read_and_unread(client, ctx, event_id):
    _, rows = await _seed(ctx, event_id, count=2)  # row[1] is unread
    url = f"{BASE}/{rows[1].id}"
    res = await client.patch(url, {"is_read": True})
    assert res.status == 200 and res.body["is_read"] is True
    assert (await client.get(url)).body["is_read"] is True
    res = await client.patch(url, {"is_read": False})
    assert res.status == 200 and res.body["is_read"] is False
    assert (await client.get(url)).body["is_read"] is False


async def test_patch_validation(client, ctx, event_id):
    _, rows = await _seed(ctx, event_id, count=1)
    url = f"{BASE}/{rows[0].id}"
    assert (await client.patch(url, {})).status == 422
    assert (await client.patch(url, {"is_read": "yes"})).status == 422
    assert (await client.patch(url, {"is_read": None})).status == 422
    assert (await client.patch(url, "not json")).status == 400
    assert (await client.patch(url, [1, 2])).status == 400


async def test_delete_notification(client, ctx, event_id):
    _, rows = await _seed(ctx, event_id, count=2)
    url = f"{BASE}/{rows[0].id}"
    res = await client.delete(url)
    assert res.status == 204 and res.body is None
    assert (await client.get(url)).status == 404
    assert (await client.delete(url)).status == 404
    assert (await client.get(BASE)).body["total"] == 1


async def test_deleting_event_removes_its_notifications(client, ctx, event_id):
    """FK cascade: notifications tied to a deleted event disappear (event delete endpoint may not exist yet)."""
    from sqlalchemy import delete
    from app.models import Event

    await _seed(ctx, event_id, count=2)
    uow = ctx.new_uow()
    try:
        async with uow.transaction():
            await uow.session.execute(delete(Event).where(Event.id == event_id))
    finally:
        await uow.close()
    assert (await client.get(BASE)).body["total"] == 0
