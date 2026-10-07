"""Vendor endpoint tests."""
from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models import VendorPayment
from app.models.enums import AuditAction, AuditEntityType


def base(event_id: int) -> str:
    return f"/api/v1/events/{event_id}/vendors"


async def make_vendor(client, event_id: int, name: str = "Caterer", total: str = "1000.00", **extra) -> dict:
    res = await client.post(base(event_id), {"name": name, "service": "food", "total_amount": total, **extra})
    assert res.status == 201, res.body
    return res.body


def audit_events(ctx, entity_type: AuditEntityType) -> list[dict]:
    return [e.payload for e in ctx.publisher.events
            if e.event_type == "audit.recorded" and e.payload["entity_type"] == entity_type.value]


async def test_create_and_get_vendor_detail(client, event_id):
    created = await make_vendor(client, event_id, total="1500.5")
    assert created["event_id"] == event_id
    assert created["total_amount"] == "1500.50"
    assert created["total_paid"] == "0.00" and created["totalPaid"] == "0.00"
    assert created["outstanding"] == "1500.50"

    await client.post(f"{base(event_id)}/{created['id']}/payments", {"amount": "400.25", "paid_on": "2030-01-01"})
    res = await client.get(f"{base(event_id)}/{created['id']}")
    assert res.status == 200
    assert res.body["total_paid"] == "400.25"
    assert res.body["totalPaid"] == "400.25"
    assert res.body["outstanding"] == "1100.25"
    assert res.body["service"] == "food"


async def test_create_validation(client, event_id):
    assert (await client.post(base(event_id), {"total_amount": "10"})).status == 422
    assert (await client.post(base(event_id), {"name": "x"})).status == 422
    assert (await client.post(base(event_id), {"name": "", "total_amount": "10"})).status == 422
    assert (await client.post(base(event_id), {"name": "x", "total_amount": "-1"})).status == 422
    assert (await client.post(base(event_id), {"name": "x", "total_amount": "1.234"})).status == 422
    assert (await client.post(base(event_id), {"name": "x", "total_amount": "abc"})).status == 422
    assert (await client.post(base(event_id), "not json")).status == 400


async def test_create_accepts_numeric_amount_and_missing_service(client, event_id):
    res = await client.post(base(event_id), {"name": "DJ", "total_amount": 99.9})
    assert res.status == 201
    assert res.body["total_amount"] == "99.90"
    assert res.body["service"] is None


async def test_list_pagination_sort_and_totals(client, event_id):
    b = await make_vendor(client, event_id, "Bravo", "300.00")
    await make_vendor(client, event_id, "Alpha", "200.00")
    await make_vendor(client, event_id, "Charlie", "100.00")
    await client.post(f"{base(event_id)}/{b['id']}/payments", {"amount": "50.00", "paid_on": "2030-01-01"})

    res = await client.get(base(event_id) + "?sort=name")
    assert res.status == 200
    assert [v["name"] for v in res.body["items"]] == ["Alpha", "Bravo", "Charlie"]
    assert res.body["total"] == 3 and res.body["page"] == 1 and res.body["size"] == 20
    bravo = next(v for v in res.body["items"] if v["name"] == "Bravo")
    assert bravo["total_paid"] == "50.00" and bravo["outstanding"] == "250.00"

    res = await client.get(base(event_id) + "?sort=name&order=desc&size=2&page=2")
    assert [v["name"] for v in res.body["items"]] == ["Alpha"]
    assert res.body["total"] == 3 and res.body["limit"] == 2

    assert (await client.get(base(event_id) + "?sort=bogus")).status == 422
    assert (await client.get(base(event_id) + "?page=0")).status == 422


async def test_update_vendor_partial_and_audited(client, event_id, ctx):
    vendor = await make_vendor(client, event_id)
    res = await client.put(f"{base(event_id)}/{vendor['id']}", {"name": "Better Caterer"})
    assert res.status == 200
    assert res.body["name"] == "Better Caterer"
    assert res.body["total_amount"] == "1000.00"
    res = await client.put(f"{base(event_id)}/{vendor['id']}", {"total_amount": "2000", "service": None})
    assert res.body["total_amount"] == "2000.00" and res.body["service"] is None
    assert res.body["outstanding"] == "2000.00"
    assert (await client.put(f"{base(event_id)}/{vendor['id']}", {"name": None})).status == 422
    assert (await client.put(f"{base(event_id)}/{vendor['id']}", {"total_amount": None})).status == 422

    audits = audit_events(ctx, AuditEntityType.VENDOR)
    assert [a["action"] for a in audits] == [AuditAction.CREATE.value, AuditAction.UPDATE.value,
                                              AuditAction.UPDATE.value]
    assert all(a["event_id"] == event_id and a["entity_id"] == vendor["id"] for a in audits)


async def test_update_total_amount_below_paid_rejected(client, event_id):
    vendor = await make_vendor(client, event_id, total="500.00")
    await client.post(f"{base(event_id)}/{vendor['id']}/payments", {"amount": "300.00", "paid_on": "2030-01-01"})
    url = f"{base(event_id)}/{vendor['id']}"
    res = await client.put(url, {"total_amount": "299.99"})
    assert res.status == 422
    assert res.body["status"] == 422
    assert (await client.get(url)).body["total_amount"] == "500.00"
    ok = await client.put(url, {"total_amount": "300.00"})
    assert ok.status == 200 and ok.body["outstanding"] == "0.00"


async def test_delete_vendor_cascades_payments_and_audits(client, event_id, ctx):
    vendor = await make_vendor(client, event_id)
    url = f"{base(event_id)}/{vendor['id']}"
    pay = await client.post(url + "/payments", {"amount": "10.00", "paid_on": "2030-01-01"})
    assert pay.status == 201
    assert (await client.delete(url)).status == 204
    assert (await client.get(url)).status == 404
    assert (await client.get(url + f"/payments/{pay.body['id']}")).status == 404
    async with ctx.database.session() as session:
        remaining = (await session.execute(select(func.count()).select_from(VendorPayment))).scalar_one()
    assert remaining == 0
    assert (await client.delete(url)).status == 404
    actions = [a["action"] for a in audit_events(ctx, AuditEntityType.VENDOR)]
    assert actions[-1] == AuditAction.DELETE.value


async def test_vendor_must_belong_to_event(client, event_id):
    other_event = (await client.post("/api/v1/events", {
        "name": "Other", "start_at": "2030-02-01T10:00:00Z", "end_at": "2030-02-01T12:00:00Z",
        "guest_capacity": 1, "budget": "10.00"})).body["id"]
    vendor = await make_vendor(client, event_id)
    url = f"{base(other_event)}/{vendor['id']}"
    assert (await client.get(url)).status == 404
    assert (await client.put(url, {"name": "x"})).status == 404
    assert (await client.delete(url)).status == 404
    assert (await client.get(f"{base(event_id)}/999999")).status == 404


async def test_foreign_and_missing_event_404(client, event_id, other_token):
    vendor = await make_vendor(client, event_id)
    url = f"{base(event_id)}/{vendor['id']}"
    assert (await client.get(base(event_id), token=other_token)).status == 404
    assert (await client.post(base(event_id), {"name": "x", "total_amount": "1"}, token=other_token)).status == 404
    assert (await client.get(url, token=other_token)).status == 404
    assert (await client.put(url, {"name": "x"}, token=other_token)).status == 404
    assert (await client.delete(url, token=other_token)).status == 404
    assert (await client.get(base(987654))).status == 404
    # still intact for the owner
    assert (await client.get(url)).status == 200


@pytest.mark.parametrize("method", ["get", "post"])
async def test_requires_auth(anon, event_id, method):
    res = await getattr(anon, method)(base(event_id)) if method == "get" else await anon.post(
        base(event_id), {"name": "x", "total_amount": "1"})
    assert res.status == 401
    assert res.body["status"] == 401
