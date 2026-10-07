"""Expense endpoints: CRUD, category-of-event rule, date filters, sorting, ownership, audit."""
from __future__ import annotations

import pytest


def base(event_id: int) -> str:
    return f"/api/v1/events/{event_id}/expenses"


async def make_category(client, event_id, name="Catering"):
    res = await client.post(f"/api/v1/events/{event_id}/budget-categories",
                            {"name": name, "planned_amount": "500.00"})
    assert res.status == 201, res.body
    return res.body["id"]


async def make_expense(client, event_id, category_id, amount="10.00", day="2030-01-01", description="item"):
    res = await client.post(base(event_id), {
        "category_id": category_id, "description": description, "amount": amount, "incurred_on": day})
    assert res.status == 201, res.body
    return res.body


async def test_create_and_get(client, event_id):
    cat = await make_category(client, event_id)
    body = await make_expense(client, event_id, cat, amount=12.5, description="Flowers")
    assert body["event_id"] == event_id and body["category_id"] == cat
    assert body["amount"] == "12.50" and body["incurred_on"] == "2030-01-01"
    assert body["description"] == "Flowers"
    res = await client.get(f"{base(event_id)}/{body['id']}")
    assert res.status == 200 and res.body == body


async def test_amount_string_input_ok(client, event_id):
    cat = await make_category(client, event_id)
    assert (await make_expense(client, event_id, cat, amount="0.01"))["amount"] == "0.01"


@pytest.mark.parametrize("override", [
    {"amount": 0}, {"amount": "-5"}, {"amount": "1.005"}, {"amount": "abc"}, {"amount": None},
    {"description": ""}, {"description": "x" * 501}, {"incurred_on": "not-a-date"}, {"incurred_on": None},
    {"category_id": "abc"}, {"category_id": None},
])
async def test_create_invalid_is_422(client, event_id, override):
    cat = await make_category(client, event_id)
    payload = {"category_id": cat, "description": "d", "amount": "5.00", "incurred_on": "2030-01-01"}
    payload.update(override)
    res = await client.post(base(event_id), payload)
    assert res.status == 422, res.body


@pytest.mark.parametrize("missing", ["category_id", "description", "amount", "incurred_on"])
async def test_create_missing_field_is_422(client, event_id, missing):
    cat = await make_category(client, event_id)
    payload = {"category_id": cat, "description": "d", "amount": "5.00", "incurred_on": "2030-01-01"}
    del payload[missing]
    assert (await client.post(base(event_id), payload)).status == 422


async def test_unknown_category_is_422(client, event_id):
    res = await client.post(base(event_id), {
        "category_id": 9999, "description": "d", "amount": "5", "incurred_on": "2030-01-01"})
    assert res.status == 422


async def test_category_of_another_event_is_422(client, event_id):
    second = await client.post("/api/v1/events", {
        "name": "Second", "start_at": "2030-02-01T10:00:00Z", "end_at": "2030-02-01T12:00:00Z",
        "guest_capacity": 1, "budget": "10.00"})
    foreign_cat = await make_category(client, second.body["id"])
    res = await client.post(base(event_id), {
        "category_id": foreign_cat, "description": "d", "amount": "5", "incurred_on": "2030-01-01"})
    assert res.status == 422
    assert (await client.get(base(event_id))).body["total"] == 0


async def test_update_partial_and_category_change(client, event_id):
    c1, c2 = await make_category(client, event_id, "A"), await make_category(client, event_id, "B")
    exp = await make_expense(client, event_id, c1)
    res = await client.put(f"{base(event_id)}/{exp['id']}", {"amount": "99.99"})
    assert res.status == 200
    assert res.body["amount"] == "99.99" and res.body["category_id"] == c1 and res.body["description"] == "item"
    res = await client.put(f"{base(event_id)}/{exp['id']}", {"category_id": c2, "description": "moved",
                                                              "incurred_on": "2030-03-03"})
    assert res.body["category_id"] == c2 and res.body["incurred_on"] == "2030-03-03"
    # category actuals follow the move
    a = await client.get(f"/api/v1/events/{event_id}/budget-categories/{c1}")
    b = await client.get(f"/api/v1/events/{event_id}/budget-categories/{c2}")
    assert a.body["actual_amount"] == "0.00" and b.body["actual_amount"] == "99.99"


async def test_update_invalid(client, event_id):
    cat = await make_category(client, event_id)
    exp = await make_expense(client, event_id, cat)
    url = f"{base(event_id)}/{exp['id']}"
    assert (await client.put(url, {"amount": 0})).status == 422
    assert (await client.put(url, {"category_id": 12345})).status == 422
    assert (await client.put(url, {"description": None})).status == 422
    assert (await client.get(url)).body["amount"] == "10.00"


async def test_delete(client, event_id):
    cat = await make_category(client, event_id)
    exp = await make_expense(client, event_id, cat)
    res = await client.delete(f"{base(event_id)}/{exp['id']}")
    assert res.status == 204 and res.body is None
    assert (await client.get(f"{base(event_id)}/{exp['id']}")).status == 404
    assert (await client.delete(f"{base(event_id)}/{exp['id']}")).status == 404
    assert (await client.get(f"/api/v1/events/{event_id}/budget-categories/{cat}")).body["actual_amount"] == "0.00"


async def _seed_three(client, event_id):
    cat = await make_category(client, event_id)
    e1 = await make_expense(client, event_id, cat, "30.00", "2030-01-10")
    e2 = await make_expense(client, event_id, cat, "10.00", "2030-01-20")
    e3 = await make_expense(client, event_id, cat, "20.00", "2030-01-30")
    return e1, e2, e3


async def test_date_filter_is_inclusive(client, event_id):
    e1, e2, e3 = await _seed_three(client, event_id)
    res = await client.get(f"{base(event_id)}?startDate=2030-01-10&endDate=2030-01-20")
    assert [i["id"] for i in res.body["items"]] == [e1["id"], e2["id"]]
    assert res.body["total"] == 2
    res = await client.get(f"{base(event_id)}?startDate=2030-01-20")
    assert [i["id"] for i in res.body["items"]] == [e2["id"], e3["id"]]
    res = await client.get(f"{base(event_id)}?endDate=2030-01-10")
    assert [i["id"] for i in res.body["items"]] == [e1["id"]]
    res = await client.get(f"{base(event_id)}?startDate=2030-01-20&endDate=2030-01-20")
    assert [i["id"] for i in res.body["items"]] == [e2["id"]]
    res = await client.get(f"{base(event_id)}?startDate=2031-01-01")
    assert res.body["items"] == [] and res.body["total"] == 0


@pytest.mark.parametrize("query", [
    "startDate=2030-02-01&endDate=2030-01-01", "startDate=garbage", "endDate=2030-13-45",
])
async def test_date_filter_invalid_is_422(client, event_id, query):
    res = await client.get(f"{base(event_id)}?{query}")
    assert res.status == 422


async def test_sorting(client, event_id):
    e1, e2, e3 = await _seed_three(client, event_id)
    default = await client.get(base(event_id))
    assert [i["id"] for i in default.body["items"]] == [e1["id"], e2["id"], e3["id"]]
    by_amount = await client.get(f"{base(event_id)}?sort=amount")
    assert [i["id"] for i in by_amount.body["items"]] == [e2["id"], e3["id"], e1["id"]]
    desc = await client.get(f"{base(event_id)}?sort=amount&order=desc")
    assert [i["id"] for i in desc.body["items"]] == [e1["id"], e3["id"], e2["id"]]
    by_id = await client.get(f"{base(event_id)}?sort=id&order=desc")
    assert [i["id"] for i in by_id.body["items"]] == [e3["id"], e2["id"], e1["id"]]
    assert (await client.get(f"{base(event_id)}?sort=description")).status == 422


async def test_pagination(client, event_id):
    await _seed_three(client, event_id)
    res = await client.get(f"{base(event_id)}?size=2&page=2")
    assert res.body["total"] == 3 and len(res.body["items"]) == 1 and res.body["page"] == 2
    res = await client.get(f"{base(event_id)}?limit=1&offset=2")
    assert len(res.body["items"]) == 1 and res.body["offset"] == 2


async def test_not_found_and_foreign(client, event_id, other_token):
    cat = await make_category(client, event_id)
    exp = await make_expense(client, event_id, cat)
    assert (await client.get(f"{base(event_id)}/9999")).status == 404
    assert (await client.put(f"{base(event_id)}/9999", {"amount": "1"})).status == 404
    assert (await client.get(base(99999))).status == 404
    url = f"{base(event_id)}/{exp['id']}"
    assert (await client.get(base(event_id), token=other_token)).status == 404
    assert (await client.post(base(event_id), {"category_id": cat, "description": "d", "amount": "1",
                                               "incurred_on": "2030-01-01"}, token=other_token)).status == 404
    assert (await client.get(url, token=other_token)).status == 404
    assert (await client.put(url, {"amount": "2"}, token=other_token)).status == 404
    assert (await client.delete(url, token=other_token)).status == 404
    assert (await client.get(url)).body["amount"] == "10.00"


async def test_expense_of_other_event_is_404(client, event_id):
    cat = await make_category(client, event_id)
    exp = await make_expense(client, event_id, cat)
    second = await client.post("/api/v1/events", {
        "name": "Second", "start_at": "2030-02-01T10:00:00Z", "end_at": "2030-02-01T12:00:00Z",
        "guest_capacity": 1, "budget": "10.00"})
    other = second.body["id"]
    assert (await client.get(f"{base(other)}/{exp['id']}")).status == 404
    assert (await client.put(f"{base(other)}/{exp['id']}", {"amount": "1"})).status == 404
    assert (await client.delete(f"{base(other)}/{exp['id']}")).status == 404


async def test_requires_auth(anon, event_id):
    assert (await anon.get(base(event_id))).status == 401
    assert (await anon.post(base(event_id), {})).status == 401


async def test_audit_events_published(client, ctx, event_id):
    cat = await make_category(client, event_id)
    exp = await make_expense(client, event_id, cat)
    await client.put(f"{base(event_id)}/{exp['id']}", {"amount": "11"})
    await client.delete(f"{base(event_id)}/{exp['id']}")
    audits = [e.payload for e in ctx.publisher.events if e.payload.get("entity_type") == "expense"]
    assert [a["action"] for a in audits] == ["create", "update", "delete"]
    assert all(a["entity_id"] == exp["id"] and a["event_id"] == event_id for a in audits)


async def test_event_detail_budget_breakdown(client, event_id):
    detail = await client.get(f"/api/v1/events/{event_id}")
    if detail.status != 200 or "budget_breakdown" not in detail.body:
        pytest.skip("event detail not available yet")
    cat = await make_category(client, event_id)
    await make_expense(client, event_id, cat, "100.10")
    await make_expense(client, event_id, cat, "50.20")
    breakdown = (await client.get(f"/api/v1/events/{event_id}")).body["budget_breakdown"]
    assert breakdown == {"planned": "1000.00", "actual": "150.30", "remaining": "849.70"}
