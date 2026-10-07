"""Event CRUD, pagination, ownership isolation, detail aggregates and validation."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.models import BudgetCategory, Expense, Guest
from app.models.enums import InvitationStatus

EVENTS = "/api/v1/events"


def payload(**overrides):
    body = {"name": "Conf", "description": "desc", "start_at": "2031-05-01T09:00:00Z",
            "end_at": "2031-05-01T17:00:00Z", "guest_capacity": 10, "budget": "500.5"}
    body.update(overrides)
    return body


async def test_create_event_returns_201_with_normalized_fields(client):
    res = await client.post(EVENTS, payload())
    assert res.status == 201
    body = res.body
    assert body["name"] == "Conf" and body["description"] == "desc"
    assert body["start_at"] == "2031-05-01T09:00:00Z" and body["end_at"] == "2031-05-01T17:00:00Z"
    assert body["guest_capacity"] == 10
    assert body["budget"] == "500.50"  # money is always a 2-dp string
    assert isinstance(body["id"], int) and isinstance(body["owner_id"], int)


async def test_money_accepts_json_number_and_string_and_serializes_2dp(client):
    a = await client.post(EVENTS, payload(budget=100))
    b = await client.post(EVENTS, payload(budget="0.1"))
    c = await client.post(EVENTS, payload(budget=0))
    assert [a.body["budget"], b.body["budget"], c.body["budget"]] == ["100.00", "0.10", "0.00"]


async def test_timezone_offsets_are_converted_to_utc(client):
    res = await client.post(EVENTS, payload(start_at="2031-05-01T12:00:00+03:00", end_at="2031-05-01T20:00:00+03:00"))
    assert res.status == 201
    assert res.body["start_at"] == "2031-05-01T09:00:00Z"


async def test_get_event_detail_with_empty_aggregates(client, event_id):
    res = await client.get(f"{EVENTS}/{event_id}")
    assert res.status == 200
    assert res.body["id"] == event_id
    assert res.body["accepted_guest_count"] == 0
    assert res.body["budget_breakdown"] == {"planned": "1000.00", "actual": "0.00", "remaining": "1000.00"}


async def test_detail_breakdown_and_accepted_guests(client, ctx, event_id):
    async with ctx.database.session() as session:
        category = BudgetCategory(event_id=event_id, name="Food", planned_amount=Decimal("400.00"))
        session.add(category)
        await session.flush()
        for amount in (Decimal("100.25"), Decimal("50.10")):
            session.add(Expense(event_id=event_id, category_id=category.id, description="x",
                                amount=amount, incurred_on=date(2030, 1, 1)))
        session.add_all([
            Guest(event_id=event_id, name="A", invitation_status=InvitationStatus.ACCEPTED),
            Guest(event_id=event_id, name="B", invitation_status=InvitationStatus.ACCEPTED),
            Guest(event_id=event_id, name="C", invitation_status=InvitationStatus.PENDING),
        ])
        await session.commit()
    res = await client.get(f"{EVENTS}/{event_id}")
    assert res.status == 200
    assert res.body["accepted_guest_count"] == 2
    assert res.body["budget_breakdown"] == {"planned": "1000.00", "actual": "150.35", "remaining": "849.65"}


async def test_remaining_can_be_negative(client, ctx):
    created = await client.post(EVENTS, payload(budget="10.00"))
    eid = created.body["id"]
    async with ctx.database.session() as session:
        category = BudgetCategory(event_id=eid, name="Food", planned_amount=Decimal("5.00"))
        session.add(category)
        await session.flush()
        session.add(Expense(event_id=eid, category_id=category.id, description="x",
                            amount=Decimal("25.00"), incurred_on=date(2030, 1, 1)))
        await session.commit()
    res = await client.get(f"{EVENTS}/{eid}")
    assert res.body["budget_breakdown"]["remaining"] == "-15.00"


async def test_list_returns_pagination_envelope(client, event_id):
    res = await client.get(EVENTS)
    assert res.status == 200
    assert set(res.body) == {"items", "total", "page", "size", "limit", "offset"}
    assert res.body["total"] == 1 and res.body["page"] == 1
    assert res.body["size"] == res.body["limit"] == 20 and res.body["offset"] == 0
    assert res.body["items"][0]["id"] == event_id


async def test_list_paging_and_sorting(client):
    for i, budget in enumerate(["30.00", "10.00", "20.00"]):
        assert (await client.post(EVENTS, payload(name=f"E{i}", budget=budget))).status == 201
    page1 = await client.get(f"{EVENTS}?size=2&page=1&sort=budget&order=asc")
    page2 = await client.get(f"{EVENTS}?size=2&page=2&sort=budget&order=asc")
    assert [e["budget"] for e in page1.body["items"]] == ["10.00", "20.00"]
    assert [e["budget"] for e in page2.body["items"]] == ["30.00"]
    assert page1.body["total"] == page2.body["total"] == 3
    assert page2.body["page"] == 2 and page2.body["offset"] == 2
    desc = await client.get(f"{EVENTS}?sort=name&order=desc&limit=1")
    assert desc.body["items"][0]["name"] == "E2" and desc.body["size"] == 1
    by_offset = await client.get(f"{EVENTS}?size=1&offset=2")
    assert by_offset.body["offset"] == 2 and len(by_offset.body["items"]) == 1


async def test_list_invalid_query_params_422(client):
    for query in ("sort=password", "order=sideways", "page=0", "size=0", "page=abc", "offset=-1"):
        assert (await client.get(f"{EVENTS}?{query}")).status == 422, query


async def test_list_size_is_capped(client):
    res = await client.get(f"{EVENTS}?size=1000")
    assert res.status == 200 and res.body["size"] == 100


async def test_list_only_shows_own_events(client, other_token, event_id):
    res = await client.get(EVENTS, token=other_token)
    assert res.status == 200 and res.body["total"] == 0 and res.body["items"] == []


async def test_foreign_event_is_404_for_get_put_delete(client, other_token, event_id):
    path = f"{EVENTS}/{event_id}"
    assert (await client.get(path, token=other_token)).status == 404
    assert (await client.put(path, {"name": "hijack"}, token=other_token)).status == 404
    assert (await client.delete(path, token=other_token)).status == 404
    still = await client.get(path)
    assert still.status == 200 and still.body["name"] == "Gala"


async def test_missing_event_is_404_with_envelope(client):
    res = await client.get(f"{EVENTS}/999999")
    assert res.status == 404
    assert {"timestamp", "status", "error", "message", "path"} <= set(res.body)


async def test_put_updates_only_sent_fields(client, event_id):
    res = await client.put(f"{EVENTS}/{event_id}", {"name": "Renamed", "budget": 2500})
    assert res.status == 200
    assert res.body["name"] == "Renamed" and res.body["budget"] == "2500.00"
    assert res.body["guest_capacity"] == 3 and res.body["description"] == "d"
    assert res.body["start_at"] == "2030-01-01T10:00:00Z"
    again = await client.get(f"{EVENTS}/{event_id}")
    assert again.body["name"] == "Renamed"
    assert again.body["budget_breakdown"]["planned"] == "2500.00"


async def test_put_can_clear_description(client, event_id):
    res = await client.put(f"{EVENTS}/{event_id}", {"description": None})
    assert res.status == 200 and res.body["description"] is None


async def test_put_validates_merged_period(client, event_id):
    # end before the existing start_at
    assert (await client.put(f"{EVENTS}/{event_id}", {"end_at": "2029-01-01T00:00:00Z"})).status == 422
    # start after existing end_at
    assert (await client.put(f"{EVENTS}/{event_id}", {"start_at": "2031-01-01T00:00:00Z"})).status == 422
    # moving both is fine
    ok = await client.put(f"{EVENTS}/{event_id}", {"start_at": "2031-01-01T00:00:00Z", "end_at": "2031-01-02T00:00:00Z"})
    assert ok.status == 200


async def test_put_rejects_nulls_and_invalid_values(client, event_id):
    path = f"{EVENTS}/{event_id}"
    for body in ({"name": None}, {"budget": None}, {"budget": "-1"}, {"guest_capacity": -1}, {"name": ""}):
        assert (await client.put(path, body)).status == 422, body


async def test_put_capacity_cannot_drop_below_guest_count(client, ctx, event_id):
    async with ctx.database.session() as session:
        session.add_all([Guest(event_id=event_id, name=f"G{i}") for i in range(3)])
        await session.commit()
    path = f"{EVENTS}/{event_id}"
    assert (await client.put(path, {"guest_capacity": 2})).status == 422
    assert (await client.put(path, {"guest_capacity": 3})).status == 200
    assert (await client.put(path, {"guest_capacity": 50})).status == 200


async def test_delete_event_204_then_404_and_cascades(client, ctx, event_id):
    async with ctx.database.session() as session:
        session.add(Guest(event_id=event_id, name="G"))
        await session.commit()
    res = await client.delete(f"{EVENTS}/{event_id}")
    assert res.status == 204 and res.body is None
    assert (await client.get(f"{EVENTS}/{event_id}")).status == 404
    assert (await client.delete(f"{EVENTS}/{event_id}")).status == 404
    async with ctx.database.session() as session:
        assert (await session.execute(select(Guest).where(Guest.event_id == event_id))).first() is None


async def test_create_validation_errors_422(client):
    bad_bodies = [
        payload(end_at="2031-05-01T09:00:00Z"),            # end == start
        payload(end_at="2031-05-01T08:00:00Z"),            # end < start
        payload(budget="-5"),
        payload(budget="1.234"),
        payload(budget="abc"),
        payload(guest_capacity=-1),
        payload(guest_capacity="many"),
        payload(name=""),
        payload(start_at="yesterday"),
        {k: v for k, v in payload().items() if k != "name"},
        {k: v for k, v in payload().items() if k != "budget"},
        {},
    ]
    for body in bad_bodies:
        res = await client.post(EVENTS, body)
        assert res.status == 422, body
        assert res.body["status"] == 422


async def test_description_is_optional(client):
    body = payload()
    del body["description"]
    res = await client.post(EVENTS, body)
    assert res.status == 201 and res.body["description"] is None


async def test_events_require_authentication(anon, event_id):
    assert (await anon.get(EVENTS)).status == 401
    assert (await anon.post(EVENTS, payload())).status == 401
    assert (await anon.get(f"{EVENTS}/{event_id}")).status == 401
    assert (await anon.put(f"{EVENTS}/{event_id}", {"name": "x"})).status == 401
    assert (await anon.delete(f"{EVENTS}/{event_id}")).status == 401


async def test_events_are_not_audited(client, ctx, event_id):
    await client.put(f"{EVENTS}/{event_id}", {"name": "n"})
    await client.delete(f"{EVENTS}/{event_id}")
    assert ctx.publisher.events == []
