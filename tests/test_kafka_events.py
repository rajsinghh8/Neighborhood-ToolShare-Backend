"""Domain events: post-commit publishing, publisher adapters, consumer dispatch, wire format."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal

import pytest

from app.events.consumer import KafkaEventConsumer
from app.events.domain import DomainEvent
from app.events.publisher import InMemoryEventPublisher, KafkaEventPublisher, NoopEventPublisher
from app.models.enums import AuditAction, AuditEntityType, NotificationType
from app.services.audit_recorder import AuditRecorder
from app.services.notification_recorder import NotificationRecorder
from tests.helpers_notifications import owner_of

AUDIT_TOPIC = "eventforge.audit"
NOTIFICATION_TOPIC = "eventforge.notifications"


# ------------------------------------------------------------ DomainEvent
def test_to_json_bytes_shape():
    event = DomainEvent(topic="t", key="k", event_type="thing.happened", payload={"a": 1, "b": "x"})
    body = json.loads(event.to_json_bytes().decode("utf-8"))
    assert set(body) == {"event_type", "occurred_at", "payload"}
    assert body["event_type"] == "thing.happened"
    assert body["payload"] == {"a": 1, "b": "x"}
    datetime.fromisoformat(body["occurred_at"])  # ISO-8601, parseable


def test_to_json_bytes_is_bytes_and_stringifies_unknown_types():
    event = DomainEvent(topic="t", key="k", event_type="e",
                        payload={"amount": Decimal("12.50"), "at": datetime(2030, 1, 1, 10, 0)})
    raw = event.to_json_bytes()
    assert isinstance(raw, bytes)
    payload = json.loads(raw)["payload"]
    assert payload == {"amount": "12.50", "at": "2030-01-01 10:00:00"}


def test_domain_event_is_immutable_and_has_timestamp():
    event = DomainEvent(topic="t", key="k", event_type="e", payload={})
    with pytest.raises(Exception):
        event.topic = "other"  # type: ignore[misc]
    assert event.occurred_at


# ------------------------------------------------ post-commit publication
async def test_audit_event_published_after_commit(ctx, event_id):
    owner = await owner_of(ctx, event_id)
    assert isinstance(ctx.publisher, InMemoryEventPublisher)
    ctx.publisher.events.clear()
    uow = ctx.new_uow()
    try:
        async with uow.transaction():
            await AuditRecorder(uow, AUDIT_TOPIC).record(event_id, owner, AuditEntityType.TASK, 7, AuditAction.CREATE)
            assert ctx.publisher.events == []  # nothing leaves before the commit
    finally:
        await uow.close()
    (published,) = ctx.publisher.events
    assert published.topic == AUDIT_TOPIC and published.key == str(event_id)
    assert published.event_type == "audit.recorded"
    assert published.payload == {"event_id": event_id, "actor_id": owner, "entity_type": "task",
                                 "entity_id": 7, "action": "create"}


async def test_notification_event_published_after_commit(ctx, event_id):
    owner = await owner_of(ctx, event_id)
    ctx.publisher.events.clear()
    uow = ctx.new_uow()
    try:
        async with uow.transaction():
            row = await NotificationRecorder(uow, NOTIFICATION_TOPIC).notify(
                owner, event_id, NotificationType.TASK_OVERDUE, "late", "k1")
            assert ctx.publisher.events == []
    finally:
        await uow.close()
    (published,) = ctx.publisher.events
    assert published.topic == NOTIFICATION_TOPIC and published.key == str(owner)
    assert published.event_type == "notification.created"
    assert published.payload["notification_id"] == row.id
    assert published.payload["type"] == "task_overdue" and published.payload["message"] == "late"


async def test_duplicate_notification_publishes_nothing(ctx, event_id):
    owner = await owner_of(ctx, event_id)
    for _ in range(2):
        uow = ctx.new_uow()
        try:
            async with uow.transaction():
                await NotificationRecorder(uow, NOTIFICATION_TOPIC).notify(
                    owner, event_id, NotificationType.TASK_OVERDUE, "late", "same-key")
        finally:
            await uow.close()
    assert [e.event_type for e in ctx.publisher.events if e.topic == NOTIFICATION_TOPIC] == ["notification.created"]


async def test_events_not_published_on_rollback(ctx, event_id):
    owner = await owner_of(ctx, event_id)
    ctx.publisher.events.clear()
    uow = ctx.new_uow()
    try:
        with pytest.raises(RuntimeError):
            async with uow.transaction():
                await AuditRecorder(uow, AUDIT_TOPIC).record(event_id, owner, AuditEntityType.GUEST, 1, AuditAction.DELETE)
                await NotificationRecorder(uow, NOTIFICATION_TOPIC).notify(
                    owner, event_id, NotificationType.BUDGET_THRESHOLD, "m", "rb")
                raise RuntimeError("fail after queueing events")
        assert ctx.publisher.events == []
        # a later successful transaction on the same unit of work must not leak the discarded events
        async with uow.transaction():
            pass
    finally:
        await uow.close()
    assert ctx.publisher.events == []


async def test_failed_flush_publishes_nothing(ctx, event_id):
    """A DB-level failure (FK violation) inside the transaction discards queued events."""
    ctx.publisher.events.clear()
    uow = ctx.new_uow()
    try:
        with pytest.raises(Exception):
            async with uow.transaction():
                await AuditRecorder(uow, AUDIT_TOPIC).record(
                    999999, 1, AuditEntityType.TASK, 1, AuditAction.CREATE)  # event 999999 does not exist
    finally:
        await uow.close()
    assert ctx.publisher.events == []


# ---------------------------------------------------------- publishers
async def test_kafka_publisher_without_producer_does_not_raise():
    publisher = KafkaEventPublisher("localhost:1")
    await publisher.publish(DomainEvent(topic="t", key="k", event_type="e", payload={}))
    await publisher.stop()  # stop without start is also safe


async def test_noop_publisher_does_not_raise():
    publisher = NoopEventPublisher()
    await publisher.start()
    await publisher.publish(DomainEvent(topic="t", key="k", event_type="e", payload={}))
    await publisher.stop()


class _FakeProducer:
    def __init__(self, fail: bool = False) -> None:
        self.sent: list[tuple[str, bytes, bytes]] = []
        self.fail = fail
        self.stopped = False

    async def send_and_wait(self, topic: str, value: bytes, key: bytes) -> None:
        if self.fail:
            raise ConnectionError("broker gone")
        self.sent.append((topic, value, key))

    async def stop(self) -> None:
        self.stopped = True


async def test_kafka_publisher_sends_topic_key_and_json_bytes():
    publisher = KafkaEventPublisher("x")
    producer = _FakeProducer()
    publisher._producer = producer
    event = DomainEvent(topic="eventforge.audit", key="42", event_type="audit.recorded", payload={"n": 1})
    await publisher.publish(event)
    ((topic, value, key),) = producer.sent
    assert topic == "eventforge.audit" and key == b"42" and value == event.to_json_bytes()
    await publisher.stop()
    assert producer.stopped and publisher._producer is None


async def test_kafka_publisher_swallows_send_errors(caplog):
    publisher = KafkaEventPublisher("x")
    publisher._producer = _FakeProducer(fail=True)
    with caplog.at_level(logging.ERROR):
        await publisher.publish(DomainEvent(topic="t", key="k", event_type="e", payload={}))
    assert any("Failed to publish" in r.message for r in caplog.records)


async def test_inmemory_publisher_records_in_order():
    publisher = InMemoryEventPublisher()
    first = DomainEvent(topic="a", key="1", event_type="x", payload={})
    second = DomainEvent(topic="b", key="2", event_type="y", payload={})
    await publisher.publish(first)
    await publisher.publish(second)
    assert publisher.events == [first, second]


# ------------------------------------------------------------ consumer
def _consumer(received: list | None = None) -> KafkaEventConsumer:
    handler = (lambda topic, body: received.append((topic, body))) if received is not None else None
    if handler is None:
        return KafkaEventConsumer("localhost:1", ["t"], "g")
    return KafkaEventConsumer("localhost:1", ["t"], "g", handler=handler)


def test_dispatch_valid_message_calls_handler():
    received: list = []
    event = DomainEvent(topic="t", key="k", event_type="audit.recorded", payload={"event_id": 1})
    _consumer(received)._dispatch("eventforge.audit", event.to_json_bytes())
    ((topic, body),) = received
    assert topic == "eventforge.audit"
    assert body["event_type"] == "audit.recorded" and body["payload"] == {"event_id": 1}


@pytest.mark.parametrize("raw", [b"not json at all", b"\xff\xfe\x00", b"", b"{unterminated", b"[1, 2, 3]", b"42"])
def test_dispatch_malformed_message_is_discarded(raw, caplog):
    received: list = []
    with caplog.at_level(logging.WARNING):
        _consumer(received)._dispatch("t", raw)  # must not raise
    assert received == []
    assert any("Discarding" in r.message for r in caplog.records)


def test_default_handler_logs_consumed_event(caplog):
    event = DomainEvent(topic="t", key="k", event_type="notification.created", payload={"user_id": 5})
    with caplog.at_level(logging.INFO):
        _consumer()._dispatch("eventforge.notifications", event.to_json_bytes())
    assert any("Consumed event" in r.message and "notification.created" in r.message for r in caplog.records)


async def test_consumer_stop_without_start_is_safe():
    await _consumer().stop()
