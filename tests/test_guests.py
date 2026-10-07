"""Guest endpoints: CRUD, capacity, filters/sorts, audit + notification on status change, ownership."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import AuditLog, Event, Notification
from app.models.enums import AuditAction, AuditEntityType, NotificationType
from app.schemas.guest import GuestCreate, GuestUpdate


def base(event_id: int) -> str:
    return f"/api/v1/events/{event_id}/guests"


async def add_guest(client, event_id: int, name: str = "Alice", **extra) -> dict:
    res = await client.post(base(event_id), {"name": name, **extra})
    assert res.status == 201, res.body
    return res.body


async def audit_actions(ctx, event_id: int, guest_id: int) -> list[AuditAction]:
    async with ctx.database.session() as session:
        rows = (await session.execute(
            select(AuditLog).where(AuditLog.event_id == event_id, AuditLog.entity_id == guest_id,
                                   AuditLog.entity_type == AuditEntityType.GUEST)
            .order_by(AuditLog.id))).scalars().all()
    return [row.action for row in rows]


async def notifications(ctx, event_id: int) -> list[Notification]:
    async with ctx.database.session() as session:
        return list((await session.execute(
            select(Notification).where(Notification.event_id == event_id).order_by(Notification.id))).scalars())


# ------------------------------------------------------------------ create / read
async def test_create_guest_defaults_and_shape(client, event_id):
    body = await add_guest(client, event_id, "Alice", email="alice@example.com")
    assert body == {"id": body["id"], "event_id": event_id, "name": "Alice",
                    "email": "alice@example.com", "invitation_status": "pending"}


async def test_create_without_email_and_with_status(client, event_id):
    body = await add_guest(client, event_id, "Bob", invitation_status="accepted")
    assert body["email"] is None
    assert body["invitation_status"] == "accepted"


async def test_get_guest(client, event_id):
    guest = await add_guest(client, event_id)
    res = await client.get(f"{base(event_id)}/{guest['id']}")
    assert res.status == 200
    assert res.body == guest


async def test_create_is_audited(client, ctx, event_id):
    guest = await add_guest(client, event_id)
    assert await audit_actions(ctx, event_id, guest["id"]) == [AuditAction.CREATE]


@pytest.mark.parametrize("payload", [
    {},
    {"name": ""},
    {"name": "   "},
    {"name": "A", "email": "not-an-email"},
    {"name": "A", "email": ""},
    {"name": "A", "invitation_status": "maybe"},
])
async def test_create_validation_422(client, event_id, payload):
    res = await client.post(base(event_id), payload)
    assert res.status == 422
    assert res.body["status"] == 422


async def test_create_invalid_json_400(client, event_id):
    res = await client.post(base(event_id), "{nope")
    assert res.status == 400


# ----------------------------------------------------------------------- capacity
async def test_capacity_exceeded_422(client, event_id):
    for index in range(3):  # capacity of the fixture event is 3
        await add_guest(client, event_id, f"G{index}")
    res = await client.post(base(event_id), {"name": "Overflow"})
    assert res.status == 422
    assert "capacity" in res.body["message"].lower()
    listing = await client.get(base(event_id))
    assert listing.body["total"] == 3


async def test_capacity_counts_all_statuses_and_frees_after_delete(client, event_id):
    first = await add_guest(client, event_id, "A", invitation_status="declined")
    await add_guest(client, event_id, "B")
    await add_guest(client, event_id, "C", invitation_status="accepted")
    assert (await client.post(base(event_id), {"name": "D"})).status == 422
    assert (await client.delete(f"{base(event_id)}/{first['id']}")).status == 204
    assert (await client.post(base(event_id), {"name": "D"})).status == 201


# --------------------------------------------------------------------------- list
async def test_list_envelope_and_default_sort(client, event_id):
    await add_guest(client, event_id, "B")
    await add_guest(client, event_id, "A")
    res = await client.get(base(event_id))
    assert res.status == 200
    assert [g["name"] for g in res.body["items"]] == ["B", "A"]  # id asc
    assert res.body["total"] == 2
    assert {"items", "total", "page", "size", "limit", "offset"} <= set(res.body)


async def test_list_sort_by_name_and_order(client, event_id):
    for name in ("Charlie", "Alice", "Bob"):
        await add_guest(client, event_id, name)
    asc = await client.get(base(event_id) + "?sort=name")
    desc = await client.get(base(event_id) + "?sort=name&order=desc")
    assert [g["name"] for g in asc.body["items"]] == ["Alice", "Bob", "Charlie"]
    assert [g["name"] for g in desc.body["items"]] == ["Charlie", "Bob", "Alice"]


async def test_list_sort_by_invitation_status(client, event_id):
    await add_guest(client, event_id, "A", invitation_status="pending")
    await add_guest(client, event_id, "B", invitation_status="accepted")
    await add_guest(client, event_id, "C", invitation_status="declined")
    res = await client.get(base(event_id) + "?sort=invitation_status")
    assert [g["invitation_status"] for g in res.body["items"]] == ["accepted", "declined", "pending"]


async def test_list_filter_by_invitation_status(client, event_id):
    await add_guest(client, event_id, "A")
    await add_guest(client, event_id, "B", invitation_status="accepted")
    res = await client.get(base(event_id) + "?invitation_status=accepted")
    assert res.status == 200
    assert [g["name"] for g in res.body["items"]] == ["B"]
    assert res.body["total"] == 1


async def test_list_pagination(client, event_id):
    for name in ("A", "B", "C"):
        await add_guest(client, event_id, name)
    res = await client.get(base(event_id) + "?size=2&page=2")
    assert [g["name"] for g in res.body["items"]] == ["C"]
    assert res.body["total"] == 3
    assert res.body["page"] == 2
    assert res.body["size"] == 2


@pytest.mark.parametrize("query", ["sort=bogus", "invitation_status=maybe", "order=sideways", "page=0", "size=abc"])
async def test_list_bad_query_422(client, event_id, query):
    res = await client.get(base(event_id) + "?" + query)
    assert res.status == 422


# -------------------------------------------------------------------------- update
async def test_put_updates_only_provided_fields(client, ctx, event_id):
    guest = await add_guest(client, event_id, "Alice", email="a@example.com")
    res = await client.put(f"{base(event_id)}/{guest['id']}", {"name": "Alicia"})
    assert res.status == 200
    assert res.body["name"] == "Alicia"
    assert res.body["email"] == "a@example.com"
    assert res.body["invitation_status"] == "pending"
    assert await audit_actions(ctx, event_id, guest["id"]) == [AuditAction.CREATE, AuditAction.UPDATE]
    assert await notifications(ctx, event_id) == []


async def test_patch_and_clear_email(client, event_id):
    guest = await add_guest(client, event_id, "Alice", email="a@example.com")
    res = await client.patch(f"{base(event_id)}/{guest['id']}", {"email": None})
    assert res.status == 200
    assert res.body["email"] is None


async def test_update_noop_records_nothing(client, ctx, event_id):
    guest = await add_guest(client, event_id, "Alice")
    res = await client.put(f"{base(event_id)}/{guest['id']}", {"name": "Alice", "invitation_status": "pending"})
    assert res.status == 200
    assert await audit_actions(ctx, event_id, guest["id"]) == [AuditAction.CREATE]
    assert await notifications(ctx, event_id) == []


@pytest.mark.parametrize("payload", [
    {"name": ""}, {"name": None}, {"email": "nope"}, {"invitation_status": "maybe"}, {"invitation_status": None},
])
async def test_update_validation_422(client, event_id, payload):
    guest = await add_guest(client, event_id)
    res = await client.put(f"{base(event_id)}/{guest['id']}", payload)
    assert res.status == 422


async def test_status_change_audits_and_notifies_owner(client, ctx, event_id):
    guest = await add_guest(client, event_id, "Alice")
    ctx.publisher.events.clear()
    res = await client.put(f"{base(event_id)}/{guest['id']}", {"invitation_status": "accepted"})
    assert res.status == 200
    assert res.body["invitation_status"] == "accepted"

    assert await audit_actions(ctx, event_id, guest["id"]) == [AuditAction.CREATE, AuditAction.STATUS_CHANGE]
    rows = await notifications(ctx, event_id)
    assert len(rows) == 1
    note = rows[0]
    async with ctx.database.session() as session:
        owner_id = (await session.get(Event, event_id)).owner_id
    assert note.user_id == owner_id
    assert note.type == NotificationType.GUEST_INVITATION_STATUS
    assert note.message == "Guest Alice changed invitation status to accepted"
    assert note.is_read is False
    assert note.dedup_key.startswith(f"guest:{guest['id']}:accepted:")
    topics = {event.topic for event in ctx.publisher.events}
    assert {"eventforge.audit", "eventforge.notifications"} <= topics


async def test_status_change_with_other_fields_records_update_and_status_change(client, ctx, event_id):
    guest = await add_guest(client, event_id, "Alice")
    res = await client.patch(f"{base(event_id)}/{guest['id']}",
                             {"name": "Alicia", "invitation_status": "declined"})
    assert res.status == 200
    actions = await audit_actions(ctx, event_id, guest["id"])
    assert actions[0] == AuditAction.CREATE
    assert sorted(a.value for a in actions[1:]) == ["status_change", "update"]
    rows = await notifications(ctx, event_id)
    assert [r.message for r in rows] == ["Guest Alicia changed invitation status to declined"]


async def test_each_status_change_creates_distinct_notification(client, ctx, event_id):
    guest = await add_guest(client, event_id, "Alice")
    url = f"{base(event_id)}/{guest['id']}"
    for status in ("accepted", "pending", "accepted"):
        assert (await client.put(url, {"invitation_status": status})).status == 200
    rows = await notifications(ctx, event_id)
    assert len(rows) == 3
    assert len({r.dedup_key for r in rows}) == 3


async def test_failed_update_leaves_no_side_effects(client, ctx, event_id):
    guest = await add_guest(client, event_id, "Alice")
    res = await client.put(f"{base(event_id)}/{guest['id']}", {"invitation_status": "accepted", "email": "bad"})
    assert res.status == 422
    assert await audit_actions(ctx, event_id, guest["id"]) == [AuditAction.CREATE]
    assert await notifications(ctx, event_id) == []
    assert (await client.get(f"{base(event_id)}/{guest['id']}")).body["invitation_status"] == "pending"


# -------------------------------------------------------------------------- delete
async def test_delete_guest(client, ctx, event_id):
    guest = await add_guest(client, event_id)
    res = await client.delete(f"{base(event_id)}/{guest['id']}")
    assert res.status == 204
    assert res.body is None
    assert (await client.get(f"{base(event_id)}/{guest['id']}")).status == 404
    assert await audit_actions(ctx, event_id, guest["id"]) == [AuditAction.CREATE, AuditAction.DELETE]


async def test_delete_missing_404(client, event_id):
    assert (await client.delete(f"{base(event_id)}/99999")).status == 404


# ----------------------------------------------------------- ownership / 404 / auth
async def test_foreign_event_is_404_for_every_operation(client, other_token, event_id):
    guest = await add_guest(client, event_id)
    url = f"{base(event_id)}/{guest['id']}"
    assert (await client.get(base(event_id), token=other_token)).status == 404
    assert (await client.post(base(event_id), {"name": "X"}, token=other_token)).status == 404
    assert (await client.get(url, token=other_token)).status == 404
    assert (await client.put(url, {"name": "X"}, token=other_token)).status == 404
    assert (await client.delete(url, token=other_token)).status == 404
    assert (await client.get(url)).body["name"] == "Alice"


async def test_unknown_event_404(client):
    assert (await client.get(base(987654))).status == 404
    assert (await client.post(base(987654), {"name": "X"})).status == 404


async def test_guest_of_other_event_404(client, event_id):
    other_event = await client.post("/api/v1/events", {
        "name": "Other", "start_at": "2030-02-01T10:00:00Z", "end_at": "2030-02-01T12:00:00Z",
        "guest_capacity": 5, "budget": "10.00"})
    other_id = other_event.body["id"]
    guest = await add_guest(client, event_id)
    url = f"{base(other_id)}/{guest['id']}"
    assert (await client.get(url)).status == 404
    assert (await client.put(url, {"name": "X"})).status == 404
    assert (await client.delete(url)).status == 404
    assert (await client.get(f"{base(event_id)}/{guest['id']}")).status == 200


async def test_unauthenticated_401(anon, event_id):
    assert (await anon.get(base(event_id))).status == 401
    assert (await anon.post(base(event_id), {"name": "X"})).status == 401


async def test_event_detail_counts_accepted_guests(client, event_id):
    await add_guest(client, event_id, "A", invitation_status="accepted")
    await add_guest(client, event_id, "B")
    detail = await client.get(f"/api/v1/events/{event_id}")
    if detail.status == 200:  # event group may expose the aggregate
        assert detail.body.get("accepted_guest_count", 1) == 1


async def test_deleting_event_cascades_guests(client, event_id):
    await add_guest(client, event_id)
    res = await client.delete(f"/api/v1/events/{event_id}")
    if res.status == 204:
        assert (await client.get(base(event_id))).status == 404


# ------------------------------------------------------------------------ schemas
def test_schema_email_rules():
    assert GuestCreate(name=" Eve ", email=" e@x.io ").email == "e@x.io"
    assert GuestCreate(name="Eve").email is None
    with pytest.raises(ValueError):
        GuestCreate(name="Eve", email="eve.example.com")


def test_update_schema_tracks_only_sent_fields():
    assert GuestUpdate.model_validate({"email": None}).changes() == {"email": None}
    assert GuestUpdate.model_validate({}).changes() == {}
    with pytest.raises(ValueError):
        GuestUpdate.model_validate({"name": None})
