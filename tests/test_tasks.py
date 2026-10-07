"""Tasks: transition table (unit), CRUD, filters/sorting, dependencies, ownership, audit."""
from __future__ import annotations

import pytest

from app.core.errors import BusinessRuleError
from app.models.enums import TaskStatus
from app.services.task_service import TaskStatusTransitions

P, I, C = TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED


# ------------------------------------------------------------------ unit tests
@pytest.mark.parametrize("current,target,allowed", [
    (P, I, True), (I, P, True), (I, C, True), (C, I, True),
    (P, C, False), (C, P, False),
    (P, P, True), (I, I, True), (C, C, True),
])
def test_transition_table(current, target, allowed):
    assert TaskStatusTransitions.can_transition(current, target) is allowed


def test_ensure_raises_for_illegal_transition():
    with pytest.raises(BusinessRuleError):
        TaskStatusTransitions.ensure(P, C)
    TaskStatusTransitions.ensure(P, I)


# ------------------------------------------------------------------ helpers
def url(event_id: int, task_id: int | None = None) -> str:
    base = f"/api/v1/events/{event_id}/tasks"
    return base if task_id is None else f"{base}/{task_id}"


async def make(client, event_id: int, **body) -> dict:
    body.setdefault("title", "Task")
    res = await client.post(url(event_id), body)
    assert res.status == 201, res.body
    return res.body


def audit_actions(ctx, entity_id: int) -> list[str]:
    return [e.payload["action"] for e in ctx.publisher.events
            if e.event_type == "audit.recorded" and e.payload["entity_type"] == "task"
            and e.payload["entity_id"] == entity_id]


# ------------------------------------------------------------------ create/read
async def test_create_defaults_and_fields(client, event_id):
    task = await make(client, event_id, title="  Book venue  ")
    assert task["title"] == "Book venue"
    assert task["status"] == "pending"
    assert task["priority"] == "medium"
    assert task["due_at"] is None
    assert task["depends_on_task_id"] is None
    assert task["event_id"] == event_id


async def test_create_with_due_at_normalised_to_utc(client, event_id):
    task = await make(client, event_id, due_at="2030-01-01T12:00:00+02:00", status="completed", priority="high")
    assert task["due_at"] == "2030-01-01T10:00:00Z"
    assert task["status"] == "completed"
    assert task["priority"] == "high"


async def test_get_task(client, event_id):
    task = await make(client, event_id)
    res = await client.get(url(event_id, task["id"]))
    assert res.status == 200
    assert res.body == task


@pytest.mark.parametrize("body", [
    {}, {"title": ""}, {"title": "   "}, {"title": "x", "status": "done"},
    {"title": "x", "priority": "urgent"}, {"title": "x", "due_at": "not-a-date"},
    {"title": "x", "depends_on_task_id": "abc"},
])
async def test_create_invalid_payload_422(client, event_id, body):
    res = await client.post(url(event_id), body)
    assert res.status == 422, res.body
    assert res.body["status"] == 422


async def test_create_invalid_json_400(client, event_id):
    res = await client.post(url(event_id), "{not json")
    assert res.status == 400


async def test_unknown_task_404(client, event_id):
    assert (await client.get(url(event_id, 9999))).status == 404
    assert (await client.put(url(event_id, 9999), {"title": "x"})).status == 404
    assert (await client.delete(url(event_id, 9999))).status == 404


# ------------------------------------------------------------------ update/status
async def test_update_fields_and_clear_due_at(client, ctx, event_id):
    task = await make(client, event_id, due_at="2030-01-01T09:00:00Z")
    res = await client.put(url(event_id, task["id"]), {"title": "Renamed", "priority": "low", "due_at": None})
    assert res.status == 200, res.body
    assert res.body["title"] == "Renamed"
    assert res.body["priority"] == "low"
    assert res.body["due_at"] is None
    assert audit_actions(ctx, task["id"]) == ["create", "update"]


async def test_partial_update_keeps_other_fields(client, event_id):
    task = await make(client, event_id, priority="high", due_at="2030-01-01T09:00:00Z")
    res = await client.put(url(event_id, task["id"]), {"title": "New"})
    assert res.body["priority"] == "high"
    assert res.body["due_at"] == "2030-01-01T09:00:00Z"


@pytest.mark.parametrize("field", ["title", "status", "priority"])
async def test_update_null_for_required_field_422(client, event_id, field):
    task = await make(client, event_id)
    res = await client.put(url(event_id, task["id"]), {field: None})
    assert res.status == 422


async def test_status_change_audited_as_status_change_only(client, ctx, event_id):
    task = await make(client, event_id)
    res = await client.put(url(event_id, task["id"]), {"status": "in_progress"})
    assert res.status == 200
    assert res.body["status"] == "in_progress"
    assert audit_actions(ctx, task["id"]) == ["create", "status_change"]


async def test_status_and_other_change_audits_both(client, ctx, event_id):
    task = await make(client, event_id)
    res = await client.put(url(event_id, task["id"]), {"status": "in_progress", "title": "Other"})
    assert res.status == 200
    assert audit_actions(ctx, task["id"]) == ["create", "update", "status_change"]


async def test_same_status_is_noop_without_audit(client, ctx, event_id):
    task = await make(client, event_id)
    res = await client.put(url(event_id, task["id"]), {"status": "pending"})
    assert res.status == 200
    assert audit_actions(ctx, task["id"]) == ["create"]


async def test_full_status_lifecycle(client, event_id):
    task = await make(client, event_id)
    path = url(event_id, task["id"])
    for target in ("in_progress", "completed", "in_progress", "pending"):
        res = await client.put(path, {"status": target})
        assert res.status == 200, (target, res.body)
        assert res.body["status"] == target


async def test_illegal_transition_422_and_unchanged(client, event_id):
    task = await make(client, event_id)
    path = url(event_id, task["id"])
    res = await client.put(path, {"status": "completed", "title": "Should not apply"})
    assert res.status == 422
    assert res.body["status"] == 422
    current = (await client.get(path)).body
    assert current["status"] == "pending"
    assert current["title"] == "Task"


async def test_completed_to_pending_illegal(client, event_id):
    task = await make(client, event_id, status="completed")
    res = await client.put(url(event_id, task["id"]), {"status": "pending"})
    assert res.status == 422


async def test_patch_works_like_put(client, event_id):
    task = await make(client, event_id)
    res = await client.patch(url(event_id, task["id"]), {"priority": "high"})
    assert res.status == 200
    assert res.body["priority"] == "high"


# ------------------------------------------------------------------ delete
async def test_delete_204_then_404_and_audited(client, ctx, event_id):
    task = await make(client, event_id)
    res = await client.delete(url(event_id, task["id"]))
    assert res.status == 204
    assert res.body is None
    assert (await client.get(url(event_id, task["id"]))).status == 404
    assert audit_actions(ctx, task["id"]) == ["create", "delete"]


async def test_delete_clears_dependents(client, event_id):
    parent = await make(client, event_id, title="parent")
    child = await make(client, event_id, title="child", depends_on_task_id=parent["id"])
    assert child["depends_on_task_id"] == parent["id"]
    assert (await client.delete(url(event_id, parent["id"]))).status == 204
    res = await client.get(url(event_id, child["id"]))
    assert res.status == 200
    assert res.body["depends_on_task_id"] is None


# ------------------------------------------------------------------ dependencies
async def test_dependency_must_exist(client, event_id):
    res = await client.post(url(event_id), {"title": "x", "depends_on_task_id": 9999})
    assert res.status == 422


async def test_dependency_must_be_same_event(client, event_id):
    other_event = (await client.post("/api/v1/events", {
        "name": "Other", "description": "d", "start_at": "2030-02-01T10:00:00Z",
        "end_at": "2030-02-01T18:00:00Z", "guest_capacity": 1, "budget": "10.00"})).body["id"]
    foreign = await make(client, other_event, title="foreign")
    res = await client.post(url(event_id), {"title": "x", "depends_on_task_id": foreign["id"]})
    assert res.status == 422
    task = await make(client, event_id)
    res = await client.put(url(event_id, task["id"]), {"depends_on_task_id": foreign["id"]})
    assert res.status == 422


async def test_self_dependency_422(client, event_id):
    task = await make(client, event_id)
    res = await client.put(url(event_id, task["id"]), {"depends_on_task_id": task["id"]})
    assert res.status == 422


async def test_direct_and_indirect_cycles_422(client, event_id):
    a = await make(client, event_id, title="a")
    b = await make(client, event_id, title="b", depends_on_task_id=a["id"])
    c = await make(client, event_id, title="c", depends_on_task_id=b["id"])
    # a -> c would close a <- b <- c <- a
    res = await client.put(url(event_id, a["id"]), {"depends_on_task_id": c["id"]})
    assert res.status == 422
    res = await client.put(url(event_id, a["id"]), {"depends_on_task_id": b["id"]})
    assert res.status == 422
    assert (await client.get(url(event_id, a["id"]))).body["depends_on_task_id"] is None


async def test_dependency_can_be_set_changed_and_cleared(client, event_id):
    a = await make(client, event_id, title="a")
    b = await make(client, event_id, title="b")
    c = await make(client, event_id, title="c")
    path = url(event_id, c["id"])
    assert (await client.put(path, {"depends_on_task_id": a["id"]})).body["depends_on_task_id"] == a["id"]
    assert (await client.put(path, {"depends_on_task_id": b["id"]})).body["depends_on_task_id"] == b["id"]
    assert (await client.put(path, {"depends_on_task_id": None})).body["depends_on_task_id"] is None


# ------------------------------------------------------------------ list/filter/sort
async def seed(client, event_id) -> dict[str, int]:
    rows = [
        ("t1", "high", "pending", "2030-01-03T00:00:00Z"),
        ("t2", "low", "in_progress", "2030-01-01T00:00:00Z"),
        ("t3", "medium", "completed", "2030-01-02T00:00:00Z"),
        ("t4", "high", "in_progress", None),
    ]
    ids = {}
    for title, priority, status, due in rows:
        ids[title] = (await make(client, event_id, title=title, priority=priority, status=status, due_at=due))["id"]
    return ids


async def titles(client, query: str, event_id: int) -> list[str]:
    res = await client.get(url(event_id) + query)
    assert res.status == 200, res.body
    return [item["title"] for item in res.body["items"]]


async def test_list_envelope_and_default_order(client, event_id):
    await seed(client, event_id)
    res = await client.get(url(event_id))
    assert res.status == 200
    body = res.body
    assert body["total"] == 4
    assert body["page"] == 1 and body["size"] == 20 and body["limit"] == 20 and body["offset"] == 0
    assert [i["title"] for i in body["items"]] == ["t1", "t2", "t3", "t4"]


async def test_list_pagination(client, event_id):
    await seed(client, event_id)
    res = await client.get(url(event_id) + "?size=2&page=2")
    assert res.body["total"] == 4
    assert [i["title"] for i in res.body["items"]] == ["t3", "t4"]
    res = await client.get(url(event_id) + "?limit=1&offset=3")
    assert [i["title"] for i in res.body["items"]] == ["t4"]


async def test_sort_priority_is_semantic(client, event_id):
    await seed(client, event_id)
    asc = await titles(client, "?sort=priority&order=asc", event_id)
    assert asc[0] == "t2" and asc[1] == "t3" and set(asc[2:]) == {"t1", "t4"}
    desc = await titles(client, "?sort=priority&order=desc", event_id)
    assert set(desc[:2]) == {"t1", "t4"} and desc[2] == "t3" and desc[3] == "t2"


async def test_sort_due_at_and_id_desc(client, event_id):
    await seed(client, event_id)
    due = await titles(client, "?sort=due_at&order=desc", event_id)
    assert due[:3] == ["t1", "t3", "t2"]
    assert await titles(client, "?sort=id&order=desc", event_id) == ["t4", "t3", "t2", "t1"]


async def test_sort_status(client, event_id):
    await seed(client, event_id)
    result = await titles(client, "?sort=status&order=asc", event_id)
    assert result[0] == "t3"  # "completed" sorts first alphabetically


async def test_filters(client, event_id):
    await seed(client, event_id)
    assert await titles(client, "?status=in_progress", event_id) == ["t2", "t4"]
    assert await titles(client, "?priority=high", event_id) == ["t1", "t4"]
    assert await titles(client, "?priority=high&status=in_progress", event_id) == ["t4"]
    assert await titles(client, "?status=completed&priority=low", event_id) == []


@pytest.mark.parametrize("query", [
    "?status=bogus", "?priority=urgent", "?sort=title", "?order=sideways", "?page=0", "?size=abc",
])
async def test_list_invalid_query_422(client, event_id, query):
    res = await client.get(url(event_id) + query)
    assert res.status == 422


# ------------------------------------------------------------------ ownership/auth
async def test_requires_authentication(anon, event_id):
    assert (await anon.get(url(event_id))).status == 401
    assert (await anon.post(url(event_id), {"title": "x"})).status == 401


async def test_foreign_event_is_404_everywhere(client, other_token, event_id):
    task = await make(client, event_id)
    path = url(event_id, task["id"])
    assert (await client.get(url(event_id), token=other_token)).status == 404
    assert (await client.post(url(event_id), {"title": "x"}, token=other_token)).status == 404
    assert (await client.get(path, token=other_token)).status == 404
    assert (await client.put(path, {"title": "x"}, token=other_token)).status == 404
    assert (await client.delete(path, token=other_token)).status == 404
    assert (await client.get(path)).status == 200


async def test_missing_event_404(client):
    assert (await client.get(url(987654))).status == 404
    assert (await client.post(url(987654), {"title": "x"})).status == 404


async def test_task_of_other_event_is_404(client, event_id):
    other_event = (await client.post("/api/v1/events", {
        "name": "Other", "description": "d", "start_at": "2030-02-01T10:00:00Z",
        "end_at": "2030-02-01T18:00:00Z", "guest_capacity": 1, "budget": "10.00"})).body["id"]
    task = await make(client, event_id)
    path = url(other_event, task["id"])
    assert (await client.get(path)).status == 404
    assert (await client.put(path, {"title": "x"})).status == 404
    assert (await client.delete(path)).status == 404
    assert (await client.get(url(event_id, task["id"]))).status == 200
    assert (await client.get(url(other_event))).body["total"] == 0
