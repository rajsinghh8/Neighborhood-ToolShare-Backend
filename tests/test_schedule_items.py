"""Schedule item API tests + pure overlap predicate tests."""
from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import select

from app.models import AuditLog
from app.models.enums import AuditAction, AuditEntityType
from app.services.schedule_item_service import intervals_overlap


def d(h: int, m: int = 0, day: int = 1) -> datetime:
    return datetime(2030, 1, day, h, m)


# ------------------------------------------------------------------ pure predicate
@pytest.mark.parametrize("a, b, expected", [
    ((d(10), d(12)), (d(11), d(13)), True),      # partial overlap
    ((d(10), d(12)), (d(10), d(12)), True),      # identical
    ((d(10), d(14)), (d(11), d(12)), True),      # containment
    ((d(11), d(12)), (d(10), d(14)), True),      # contained
    ((d(10), d(12)), (d(12), d(13)), False),     # touching end/start
    ((d(12), d(13)), (d(10), d(12)), False),     # touching start/end
    ((d(10), d(11)), (d(12), d(13)), False),     # disjoint
    ((d(10), d(12)), (d(11, 59), d(13)), True),  # one-minute overlap
])
def test_intervals_overlap(a, b, expected):
    assert intervals_overlap(*a, *b) is expected
    assert intervals_overlap(*b, *a) is expected


# ------------------------------------------------------------------ helpers
def url(event_id: int, item_id: int | None = None) -> str:
    base = f"/api/v1/events/{event_id}/schedule-items"
    return base if item_id is None else f"{base}/{item_id}"


def body(title: str, start: str, end: str) -> dict:
    return {"title": title, "start_at": start, "end_at": end}


async def make(client, event_id: int, title: str, start: str, end: str) -> dict:
    res = await client.post(url(event_id), body(title, start, end))
    assert res.status == 201, res.body
    return res.body


async def audit_rows(ctx, event_id: int) -> list[AuditLog]:
    async with ctx.database.session() as session:
        rows = await session.execute(select(AuditLog).where(
            AuditLog.event_id == event_id, AuditLog.entity_type == AuditEntityType.SCHEDULE_ITEM
        ).order_by(AuditLog.id))
        return list(rows.scalars().all())


# ------------------------------------------------------------------ create
async def test_create_returns_201_and_entity(client, event_id):
    res = await client.post(url(event_id), body("Opening", "2030-01-01T10:00:00Z", "2030-01-01T11:00:00Z"))
    assert res.status == 201
    assert res.body["id"] > 0
    assert res.body["event_id"] == event_id
    assert res.body["title"] == "Opening"
    assert res.body["start_at"] == "2030-01-01T10:00:00Z"
    assert res.body["end_at"] == "2030-01-01T11:00:00Z"


async def test_create_converts_offsets_to_utc(client, event_id):
    item = await make(client, event_id, "Offset", "2030-01-01T12:00:00+02:00", "2030-01-01T13:00:00+02:00")
    assert item["start_at"] == "2030-01-01T10:00:00Z"


@pytest.mark.parametrize("payload", [
    {"title": "x", "start_at": "2030-01-01T11:00:00Z", "end_at": "2030-01-01T10:00:00Z"},   # end before start
    {"title": "x", "start_at": "2030-01-01T11:00:00Z", "end_at": "2030-01-01T11:00:00Z"},   # zero length
    {"title": "", "start_at": "2030-01-01T10:00:00Z", "end_at": "2030-01-01T11:00:00Z"},    # empty title
    {"start_at": "2030-01-01T10:00:00Z", "end_at": "2030-01-01T11:00:00Z"},                 # missing title
    {"title": "x", "end_at": "2030-01-01T11:00:00Z"},                                       # missing start
    {"title": "x", "start_at": "garbage", "end_at": "2030-01-01T11:00:00Z"},                # bad date
])
async def test_create_invalid_returns_422(client, event_id, payload):
    res = await client.post(url(event_id), payload)
    assert res.status == 422
    assert res.body["status"] == 422
    assert res.body["path"] == url(event_id)


async def test_create_invalid_json_returns_400(client, event_id):
    res = await client.post(url(event_id), "{not json")
    assert res.status == 400


async def test_create_overlap_returns_422(client, event_id):
    await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    for start, end in [("2030-01-01T11:00:00Z", "2030-01-01T13:00:00Z"),
                       ("2030-01-01T09:00:00Z", "2030-01-01T10:30:00Z"),
                       ("2030-01-01T10:30:00Z", "2030-01-01T11:30:00Z"),
                       ("2030-01-01T09:00:00Z", "2030-01-01T13:00:00Z"),
                       ("2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")]:
        res = await client.post(url(event_id), body("B", start, end))
        assert res.status == 422, (start, end, res.body)
    listing = await client.get(url(event_id))
    assert listing.body["total"] == 1


async def test_touching_boundaries_are_allowed(client, event_id):
    await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    await make(client, event_id, "Before", "2030-01-01T09:00:00Z", "2030-01-01T10:00:00Z")
    await make(client, event_id, "After", "2030-01-01T12:00:00Z", "2030-01-01T13:00:00Z")
    assert (await client.get(url(event_id))).body["total"] == 3


async def test_overlap_only_checked_within_same_event(client, event_id):
    other = await client.post("/api/v1/events", {
        "name": "Other", "start_at": "2030-01-01T10:00:00Z", "end_at": "2030-01-01T18:00:00Z",
        "guest_capacity": 1, "budget": "10.00"})
    assert other.status == 201
    await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    await make(client, other.body["id"], "Same slot other event", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")


# ------------------------------------------------------------------ read
async def test_get_item(client, event_id):
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    res = await client.get(url(event_id, item["id"]))
    assert res.status == 200
    assert res.body == item


async def test_get_missing_item_404(client, event_id):
    res = await client.get(url(event_id, 99999))
    assert res.status == 404
    assert res.body["status"] == 404


async def test_item_of_other_event_404(client, event_id):
    other = await client.post("/api/v1/events", {
        "name": "Other", "start_at": "2030-01-01T10:00:00Z", "end_at": "2030-01-01T18:00:00Z",
        "guest_capacity": 1, "budget": "10.00"})
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    other_id = other.body["id"]
    assert (await client.get(url(other_id, item["id"]))).status == 404
    assert (await client.put(url(other_id, item["id"]), {"title": "x"})).status == 404
    assert (await client.delete(url(other_id, item["id"]))).status == 404
    assert (await client.get(url(event_id, item["id"]))).status == 200


# ------------------------------------------------------------------ list
async def test_list_default_sort_start_at_asc_and_envelope(client, event_id):
    await make(client, event_id, "C", "2030-01-01T14:00:00Z", "2030-01-01T15:00:00Z")
    await make(client, event_id, "A", "2030-01-01T08:00:00Z", "2030-01-01T09:00:00Z")
    await make(client, event_id, "B", "2030-01-01T10:00:00Z", "2030-01-01T11:00:00Z")
    res = await client.get(url(event_id))
    assert res.status == 200
    assert [i["title"] for i in res.body["items"]] == ["A", "B", "C"]
    assert res.body["total"] == 3
    assert res.body["page"] == 1
    assert res.body["size"] == 20
    assert res.body["limit"] == 20
    assert res.body["offset"] == 0


async def test_list_sort_desc_and_by_id(client, event_id):
    await make(client, event_id, "C", "2030-01-01T14:00:00Z", "2030-01-01T15:00:00Z")
    await make(client, event_id, "A", "2030-01-01T08:00:00Z", "2030-01-01T09:00:00Z")
    desc = await client.get(url(event_id) + "?sort=start_at&order=desc")
    assert [i["title"] for i in desc.body["items"]] == ["C", "A"]
    by_id = await client.get(url(event_id) + "?sort=id")
    assert [i["title"] for i in by_id.body["items"]] == ["C", "A"]


async def test_list_pagination(client, event_id):
    for hour in range(8, 13):
        await make(client, event_id, f"H{hour}", f"2030-01-01T{hour:02d}:00:00Z", f"2030-01-01T{hour:02d}:30:00Z")
    page2 = await client.get(url(event_id) + "?page=2&size=2")
    assert [i["title"] for i in page2.body["items"]] == ["H10", "H11"]
    assert page2.body["total"] == 5
    assert page2.body["page"] == 2
    assert page2.body["size"] == 2
    offset = await client.get(url(event_id) + "?limit=2&offset=4")
    assert [i["title"] for i in offset.body["items"]] == ["H12"]


@pytest.mark.parametrize("query", ["sort=title", "order=sideways", "page=0", "size=abc",
                                   "startDate=nope", "startDate=2030-02-01&endDate=2030-01-01"])
async def test_list_bad_query_422(client, event_id, query):
    res = await client.get(url(event_id) + "?" + query)
    assert res.status == 422


async def test_list_date_range_filter_on_start_date(client, event_id):
    await make(client, event_id, "D1", "2030-01-01T23:00:00Z", "2030-01-02T01:00:00Z")
    await make(client, event_id, "D2", "2030-01-02T10:00:00Z", "2030-01-02T11:00:00Z")
    await make(client, event_id, "D3", "2030-01-03T00:00:00Z", "2030-01-03T01:00:00Z")
    await make(client, event_id, "D4", "2030-01-04T09:00:00Z", "2030-01-04T10:00:00Z")

    def titles(res):
        return [i["title"] for i in res.body["items"]]

    both = await client.get(url(event_id) + "?startDate=2030-01-02&endDate=2030-01-03")
    assert titles(both) == ["D2", "D3"]
    assert both.body["total"] == 2
    only_start = await client.get(url(event_id) + "?startDate=2030-01-03")
    assert titles(only_start) == ["D3", "D4"]
    only_end = await client.get(url(event_id) + "?endDate=2030-01-01")
    assert titles(only_end) == ["D1"]
    single = await client.get(url(event_id) + "?startDate=2030-01-04&endDate=2030-01-04")
    assert titles(single) == ["D4"]
    empty = await client.get(url(event_id) + "?startDate=2031-01-01")
    assert empty.body["items"] == [] and empty.body["total"] == 0


# ------------------------------------------------------------------ update
async def test_update_title_only(client, event_id):
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    res = await client.put(url(event_id, item["id"]), {"title": "Renamed"})
    assert res.status == 200
    assert res.body["title"] == "Renamed"
    assert res.body["start_at"] == item["start_at"]
    assert res.body["end_at"] == item["end_at"]


async def test_update_same_range_does_not_conflict_with_itself(client, event_id):
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    res = await client.put(url(event_id, item["id"]), body("A2", "2030-01-01T10:30:00Z", "2030-01-01T11:30:00Z"))
    assert res.status == 200
    assert res.body["start_at"] == "2030-01-01T10:30:00Z"


async def test_update_overlap_with_other_item_422(client, event_id):
    await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    b = await make(client, event_id, "B", "2030-01-01T13:00:00Z", "2030-01-01T14:00:00Z")
    res = await client.put(url(event_id, b["id"]), {"start_at": "2030-01-01T11:00:00Z"})
    assert res.status == 422
    unchanged = await client.get(url(event_id, b["id"]))
    assert unchanged.body["start_at"] == "2030-01-01T13:00:00Z"
    touching = await client.put(url(event_id, b["id"]), {"start_at": "2030-01-01T12:00:00Z"})
    assert touching.status == 200


async def test_update_invalid_range_422(client, event_id):
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    # merged result invalid: new end before stored start
    res = await client.put(url(event_id, item["id"]), {"end_at": "2030-01-01T09:00:00Z"})
    assert res.status == 422
    res = await client.put(url(event_id, item["id"]), {"title": None})
    assert res.status == 422
    res = await client.put(url(event_id, item["id"]), {"title": "   "})
    assert res.status == 422


async def test_patch_updates(client, event_id):
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    res = await client.patch(url(event_id, item["id"]), {"title": "P"})
    assert res.status == 200 and res.body["title"] == "P"


# ------------------------------------------------------------------ delete
async def test_delete_then_slot_is_free(client, event_id):
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    res = await client.delete(url(event_id, item["id"]))
    assert res.status == 204
    assert res.body is None
    assert (await client.get(url(event_id, item["id"]))).status == 404
    assert (await client.delete(url(event_id, item["id"]))).status == 404
    await make(client, event_id, "Again", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")


# ------------------------------------------------------------------ security
async def test_unauthenticated_401(anon, event_id):
    assert (await anon.get(url(event_id))).status == 401
    assert (await anon.post(url(event_id), body("A", "2030-01-01T10:00:00Z", "2030-01-01T11:00:00Z"))).status == 401
    assert (await anon.get(url(event_id, 1))).status == 401


async def test_foreign_event_404_for_every_operation(client, event_id, other_token):
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    assert (await client.get(url(event_id), token=other_token)).status == 404
    assert (await client.post(url(event_id), body("X", "2030-02-01T10:00:00Z", "2030-02-01T11:00:00Z"),
                              token=other_token)).status == 404
    assert (await client.get(url(event_id, item["id"]), token=other_token)).status == 404
    assert (await client.put(url(event_id, item["id"]), {"title": "hack"}, token=other_token)).status == 404
    assert (await client.delete(url(event_id, item["id"]), token=other_token)).status == 404
    assert (await client.get(url(event_id, item["id"]))).body["title"] == "A"


async def test_unknown_event_404(client):
    assert (await client.get(url(987654))).status == 404
    assert (await client.post(url(987654), body("A", "2030-01-01T10:00:00Z", "2030-01-01T11:00:00Z"))).status == 404


# ------------------------------------------------------------------ audit
async def test_audit_rows_for_create_update_delete(ctx, client, event_id):
    item = await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    await client.put(url(event_id, item["id"]), {"title": "B"})
    await client.delete(url(event_id, item["id"]))
    rows = await audit_rows(ctx, event_id)
    assert [r.action for r in rows] == [AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE]
    assert all(r.entity_id == item["id"] for r in rows)
    assert all(r.actor_id is not None for r in rows)


async def test_failed_operations_are_not_audited(ctx, client, event_id):
    await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    res = await client.post(url(event_id), body("B", "2030-01-01T11:00:00Z", "2030-01-01T13:00:00Z"))
    assert res.status == 422
    assert len(await audit_rows(ctx, event_id)) == 1


async def test_audit_events_published(ctx, client, event_id):
    await make(client, event_id, "A", "2030-01-01T10:00:00Z", "2030-01-01T12:00:00Z")
    published = [e for e in ctx.publisher.events if e.payload.get("entity_type") == "schedule_item"]
    assert len(published) == 1
    assert published[0].payload["action"] == AuditAction.CREATE.value
