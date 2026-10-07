"""Vendor payment endpoint and rule tests."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.errors import BusinessRuleError
from app.models.enums import AuditAction, AuditEntityType
from app.services.vendor_payment_service import ensure_within_total


def vbase(event_id: int, vendor_id: int) -> str:
    return f"/api/v1/events/{event_id}/vendors/{vendor_id}/payments"


@pytest.fixture
async def vendor_id(client, event_id) -> int:
    res = await client.post(f"/api/v1/events/{event_id}/vendors", {"name": "Caterer", "total_amount": "1000.00"})
    assert res.status == 201
    return res.body["id"]


async def pay(client, event_id, vendor_id, amount="100.00", paid_on="2030-01-01"):
    return await client.post(vbase(event_id, vendor_id), {"amount": amount, "paid_on": paid_on})


def test_ensure_within_total_unit():
    ensure_within_total(Decimal("10.00"), Decimal("4.00"), Decimal("6.00"))
    with pytest.raises(BusinessRuleError):
        ensure_within_total(Decimal("10.00"), Decimal("4.00"), Decimal("6.01"))
    with pytest.raises(BusinessRuleError):
        ensure_within_total(Decimal("0.00"), Decimal("0.00"), Decimal("0.01"))


async def test_create_get_list_payment(client, event_id, vendor_id, ctx):
    res = await pay(client, event_id, vendor_id, "250.5")
    assert res.status == 201
    assert res.body["vendor_id"] == vendor_id
    assert res.body["amount"] == "250.50"
    assert res.body["paid_on"] == "2030-01-01"
    pid = res.body["id"]

    got = await client.get(f"{vbase(event_id, vendor_id)}/{pid}")
    assert got.status == 200 and got.body == res.body

    await pay(client, event_id, vendor_id, "10.00", "2029-12-01")
    listing = await client.get(vbase(event_id, vendor_id))
    assert listing.status == 200
    assert listing.body["total"] == 2
    assert [p["paid_on"] for p in listing.body["items"]] == ["2029-12-01", "2030-01-01"]
    by_amount = await client.get(vbase(event_id, vendor_id) + "?sort=amount&order=desc&size=1")
    assert by_amount.body["items"][0]["amount"] == "250.50"
    assert by_amount.body["limit"] == 1
    assert (await client.get(vbase(event_id, vendor_id) + "?sort=nope")).status == 422

    audits = [e.payload for e in ctx.publisher.events
              if e.payload.get("entity_type") == AuditEntityType.VENDOR_PAYMENT.value]
    assert len(audits) == 2
    assert audits[0]["action"] == AuditAction.CREATE.value
    assert audits[0]["event_id"] == event_id and audits[0]["entity_id"] == pid


async def test_amount_and_date_validation(client, event_id, vendor_id):
    for amount in ("0", "0.00", "-5", "1.005", "abc", None):
        res = await client.post(vbase(event_id, vendor_id), {"amount": amount, "paid_on": "2030-01-01"})
        assert res.status == 422, amount
    assert (await client.post(vbase(event_id, vendor_id), {"amount": "5"})).status == 422
    assert (await client.post(vbase(event_id, vendor_id), {"amount": "5", "paid_on": "nope"})).status == 422
    assert (await client.get(vbase(event_id, vendor_id))).body["total"] == 0


async def test_boundary_exact_remaining_accepted_one_cent_more_rejected(client, event_id, vendor_id):
    assert (await pay(client, event_id, vendor_id, "999.99")).status == 201
    over = await pay(client, event_id, vendor_id, "0.02")
    assert over.status == 422
    assert over.body["status"] == 422
    exact = await pay(client, event_id, vendor_id, "0.01")
    assert exact.status == 201
    full = await client.get(f"/api/v1/events/{event_id}/vendors/{vendor_id}")
    assert full.body["total_paid"] == "1000.00"
    assert full.body["outstanding"] == "0.00"
    assert (await pay(client, event_id, vendor_id, "0.01")).status == 422


async def test_single_payment_one_cent_over_total(client, event_id, vendor_id):
    assert (await pay(client, event_id, vendor_id, "1000.01")).status == 422
    assert (await pay(client, event_id, vendor_id, "1000.00")).status == 201


async def test_many_small_payments_sum_exactly(client, event_id):
    """0.10 * 10 == 1.00 exactly (no float drift)."""
    vendor = (await client.post(f"/api/v1/events/{event_id}/vendors", {"name": "V", "total_amount": "1.00"})).body
    for _ in range(10):
        assert (await pay(client, event_id, vendor["id"], "0.10")).status == 201
    assert (await pay(client, event_id, vendor["id"], "0.01")).status == 422


async def test_update_payment_excludes_self(client, event_id, vendor_id):
    first = (await pay(client, event_id, vendor_id, "600.00")).body
    second = (await pay(client, event_id, vendor_id, "300.00")).body
    url = f"{vbase(event_id, vendor_id)}/{first['id']}"
    # 600 -> 700 fits (700 + 300 == 1000); self not double counted
    res = await client.put(url, {"amount": "700.00"})
    assert res.status == 200 and res.body["amount"] == "700.00"
    # one cent more than allowed
    assert (await client.put(url, {"amount": "700.01"})).status == 422
    # date-only update does not trigger amount checks
    res = await client.put(url, {"paid_on": "2030-05-05"})
    assert res.status == 200 and res.body["paid_on"] == "2030-05-05" and res.body["amount"] == "700.00"
    # other payment bounded by the first
    assert (await client.put(f"{vbase(event_id, vendor_id)}/{second['id']}", {"amount": "300.01"})).status == 422
    assert (await client.put(url, {"amount": "0"})).status == 422
    assert (await client.put(url, {"amount": None})).status == 422


async def test_update_audited(client, event_id, vendor_id, ctx):
    p = (await pay(client, event_id, vendor_id)).body
    await client.put(f"{vbase(event_id, vendor_id)}/{p['id']}", {"paid_on": "2030-02-02"})
    await client.delete(f"{vbase(event_id, vendor_id)}/{p['id']}")
    actions = [e.payload["action"] for e in ctx.publisher.events
               if e.payload.get("entity_type") == AuditEntityType.VENDOR_PAYMENT.value]
    assert actions == ["create", "update", "delete"]


async def test_delete_payment_frees_balance(client, event_id, vendor_id):
    p = (await pay(client, event_id, vendor_id, "1000.00")).body
    assert (await pay(client, event_id, vendor_id, "1.00")).status == 422
    url = f"{vbase(event_id, vendor_id)}/{p['id']}"
    assert (await client.delete(url)).status == 204
    assert (await client.get(url)).status == 404
    assert (await client.delete(url)).status == 404
    assert (await pay(client, event_id, vendor_id, "1.00")).status == 201


async def test_payment_must_belong_to_vendor(client, event_id, vendor_id):
    other = (await client.post(f"/api/v1/events/{event_id}/vendors", {"name": "O", "total_amount": "50"})).body
    p = (await pay(client, event_id, vendor_id)).body
    url = f"{vbase(event_id, other['id'])}/{p['id']}"
    assert (await client.get(url)).status == 404
    assert (await client.put(url, {"amount": "1"})).status == 404
    assert (await client.delete(url)).status == 404
    assert (await client.get(f"{vbase(event_id, vendor_id)}/{p['id']}")).status == 200


async def test_vendor_must_belong_to_event_and_ownership(client, event_id, vendor_id, other_token):
    other_event = (await client.post("/api/v1/events", {
        "name": "Other", "start_at": "2030-02-01T10:00:00Z", "end_at": "2030-02-01T12:00:00Z",
        "guest_capacity": 1, "budget": "10.00"})).body["id"]
    p = (await pay(client, event_id, vendor_id)).body
    assert (await client.get(vbase(other_event, vendor_id))).status == 404
    assert (await pay(client, other_event, vendor_id)).status == 404
    assert (await client.get(f"{vbase(other_event, vendor_id)}/{p['id']}")).status == 404
    assert (await client.get(vbase(event_id, 999999))).status == 404

    url = f"{vbase(event_id, vendor_id)}/{p['id']}"
    assert (await client.get(vbase(event_id, vendor_id), token=other_token)).status == 404
    assert (await client.post(vbase(event_id, vendor_id), {"amount": "1", "paid_on": "2030-01-01"},
                              token=other_token)).status == 404
    assert (await client.get(url, token=other_token)).status == 404
    assert (await client.put(url, {"amount": "1"}, token=other_token)).status == 404
    assert (await client.delete(url, token=other_token)).status == 404


async def test_requires_auth(anon, event_id, vendor_id):
    assert (await anon.get(vbase(event_id, vendor_id))).status == 401
    assert (await anon.post(vbase(event_id, vendor_id), {"amount": "1", "paid_on": "2030-01-01"})).status == 401
