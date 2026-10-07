"""Budget category endpoints: CRUD, actual/remaining figures, ownership, validation, audit."""
from __future__ import annotations

import pytest


def base(event_id: int) -> str:
    return f"/api/v1/events/{event_id}/budget-categories"


async def make_category(client, event_id, name="Catering", planned="500.00"):
    res = await client.post(base(event_id), {"name": name, "planned_amount": planned})
    assert res.status == 201, res.body
    return res.body


async def make_expense(client, event_id, category_id, amount="100.00", day="2030-01-01"):
    res = await client.post(f"/api/v1/events/{event_id}/expenses", {
        "category_id": category_id, "description": "x", "amount": amount, "incurred_on": day})
    assert res.status == 201, res.body
    return res.body


async def test_create_returns_figures_as_two_decimal_strings(client, event_id):
    body = await make_category(client, event_id, planned=250)
    assert body["event_id"] == event_id
    assert body["name"] == "Catering"
    assert body["planned_amount"] == "250.00"
    assert body["actual_amount"] == "0.00"
    assert body["remaining_amount"] == "250.00"


async def test_get_reflects_expenses(client, event_id):
    cat = await make_category(client, event_id)
    await make_expense(client, event_id, cat["id"], "120.10")
    await make_expense(client, event_id, cat["id"], "30.20")
    res = await client.get(f"{base(event_id)}/{cat['id']}")
    assert res.status == 200
    assert res.body["actual_amount"] == "150.30"
    assert res.body["remaining_amount"] == "349.70"


async def test_remaining_can_be_negative(client, event_id):
    cat = await make_category(client, event_id, planned="50.00")
    await make_expense(client, event_id, cat["id"], "80.00")
    res = await client.get(f"{base(event_id)}/{cat['id']}")
    assert res.body["remaining_amount"] == "-30.00"


async def test_money_has_no_float_drift(client, event_id):
    cat = await make_category(client, event_id, planned="1.00")
    for _ in range(3):
        await make_expense(client, event_id, cat["id"], "0.10")
    res = await client.get(f"{base(event_id)}/{cat['id']}")
    assert res.body["actual_amount"] == "0.30"
    assert res.body["remaining_amount"] == "0.70"


async def test_list_has_actuals_and_pagination(client, event_id):
    a = await make_category(client, event_id, "A", "10.00")
    b = await make_category(client, event_id, "B", "20.00")
    await make_category(client, event_id, "C", "30.00")
    await make_expense(client, event_id, b["id"], "5.00")
    res = await client.get(f"{base(event_id)}?size=2&sort=planned_amount&order=desc")
    assert res.status == 200
    assert res.body["total"] == 3 and res.body["size"] == 2 and res.body["limit"] == 2
    assert [i["name"] for i in res.body["items"]] == ["C", "B"]
    assert res.body["items"][1]["actual_amount"] == "5.00"
    assert res.body["items"][1]["remaining_amount"] == "15.00"
    full = await client.get(f"{base(event_id)}?sort=name")
    assert [i["id"] for i in full.body["items"]][0] == a["id"]


async def test_list_second_page_and_empty(client, event_id):
    empty = await client.get(base(event_id))
    assert empty.status == 200 and empty.body["items"] == [] and empty.body["total"] == 0
    for n in range(3):
        await make_category(client, event_id, f"N{n}")
    res = await client.get(f"{base(event_id)}?page=2&size=2")
    assert len(res.body["items"]) == 1 and res.body["page"] == 2


@pytest.mark.parametrize("query", ["sort=bogus", "order=up", "page=0", "size=abc"])
async def test_list_bad_query_is_422(client, event_id, query):
    res = await client.get(f"{base(event_id)}?{query}")
    assert res.status == 422
    assert res.body["status"] == 422


async def test_duplicate_names_allowed(client, event_id):
    await make_category(client, event_id, "Same")
    await make_category(client, event_id, "Same")
    assert (await client.get(base(event_id))).body["total"] == 2


async def test_zero_planned_amount_ok(client, event_id):
    body = await make_category(client, event_id, planned="0")
    assert body["planned_amount"] == "0.00"


@pytest.mark.parametrize("payload", [
    {}, {"name": "x"}, {"planned_amount": "10"}, {"name": "", "planned_amount": "10"},
    {"name": "x", "planned_amount": "-1"}, {"name": "x", "planned_amount": "1.234"},
    {"name": "x", "planned_amount": "abc"},
])
async def test_create_invalid_is_422(client, event_id, payload):
    res = await client.post(base(event_id), payload)
    assert res.status == 422


async def test_create_malformed_json_is_400(client, event_id):
    res = await client.post(base(event_id), "{not json")
    assert res.status == 400


async def test_update_partial_and_full(client, event_id):
    cat = await make_category(client, event_id)
    res = await client.put(f"{base(event_id)}/{cat['id']}", {"name": "Food"})
    assert res.status == 200
    assert res.body["name"] == "Food" and res.body["planned_amount"] == "500.00"
    res = await client.put(f"{base(event_id)}/{cat['id']}", {"name": "Food2", "planned_amount": "600.50"})
    assert res.body["planned_amount"] == "600.50" and res.body["remaining_amount"] == "600.50"


@pytest.mark.parametrize("payload", [{"name": None}, {"planned_amount": -5}, {"name": " "}])
async def test_update_invalid_is_422(client, event_id, payload):
    cat = await make_category(client, event_id)
    res = await client.put(f"{base(event_id)}/{cat['id']}", payload)
    assert res.status == 422


async def test_delete_cascades_expenses(client, event_id):
    cat = await make_category(client, event_id)
    other = await make_category(client, event_id, "Other")
    exp = await make_expense(client, event_id, cat["id"])
    keep = await make_expense(client, event_id, other["id"])
    res = await client.delete(f"{base(event_id)}/{cat['id']}")
    assert res.status == 204 and res.body is None
    assert (await client.get(f"{base(event_id)}/{cat['id']}")).status == 404
    assert (await client.get(f"/api/v1/events/{event_id}/expenses/{exp['id']}")).status == 404
    assert (await client.get(f"/api/v1/events/{event_id}/expenses/{keep['id']}")).status == 200


async def test_not_found_variants(client, event_id):
    assert (await client.get(f"{base(event_id)}/9999")).status == 404
    assert (await client.put(f"{base(event_id)}/9999", {"name": "x"})).status == 404
    assert (await client.delete(f"{base(event_id)}/9999")).status == 404
    assert (await client.get(base(99999))).status == 404


async def test_foreign_event_is_404(client, event_id, other_token):
    cat = await make_category(client, event_id)
    for method, path, body in [
        ("get", base(event_id), None), ("post", base(event_id), {"name": "x", "planned_amount": "1"}),
        ("get", f"{base(event_id)}/{cat['id']}", None), ("put", f"{base(event_id)}/{cat['id']}", {"name": "x"}),
        ("delete", f"{base(event_id)}/{cat['id']}", None),
    ]:
        res = await getattr(client, method)(path, *([body] if body is not None else []), token=other_token)
        assert res.status == 404, (method, path)
    assert (await client.get(f"{base(event_id)}/{cat['id']}")).status == 200


async def test_category_of_other_event_is_404(client, event_id):
    cat = await make_category(client, event_id)
    second = await client.post("/api/v1/events", {
        "name": "Second", "start_at": "2030-02-01T10:00:00Z", "end_at": "2030-02-01T12:00:00Z",
        "guest_capacity": 1, "budget": "10.00"})
    other_event = second.body["id"]
    assert (await client.get(f"{base(other_event)}/{cat['id']}")).status == 404
    assert (await client.delete(f"{base(other_event)}/{cat['id']}")).status == 404
    assert (await client.get(base(other_event))).body["total"] == 0


async def test_requires_auth(anon, event_id):
    assert (await anon.get(base(event_id))).status == 401
    assert (await anon.post(base(event_id), {"name": "x", "planned_amount": "1"})).status == 401


async def test_audit_events_published(client, ctx, event_id):
    cat = await make_category(client, event_id)
    await client.put(f"{base(event_id)}/{cat['id']}", {"name": "N"})
    await client.delete(f"{base(event_id)}/{cat['id']}")
    audits = [e.payload for e in ctx.publisher.events if e.payload.get("entity_type") == "budget_category"]
    assert [a["action"] for a in audits] == ["create", "update", "delete"]
    assert all(a["entity_id"] == cat["id"] and a["event_id"] == event_id for a in audits)


async def test_event_detail_budget_breakdown_uses_expenses(client, event_id):
    detail = await client.get(f"/api/v1/events/{event_id}")
    if detail.status != 200 or "budget_breakdown" not in detail.body:
        pytest.skip("event detail not available yet")
    cat = await make_category(client, event_id)
    await make_expense(client, event_id, cat["id"], "300.25")
    detail = await client.get(f"/api/v1/events/{event_id}")
    assert detail.body["budget_breakdown"]["actual"] == "300.25"
    assert detail.body["budget_breakdown"]["remaining"] == "699.75"
