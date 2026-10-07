"""Event publishers: abstract port, Kafka adapter, no-op and in-memory implementations."""
from __future__ import annotations

import abc
import logging

from app.events.domain import DomainEvent

logger = logging.getLogger(__name__)


class EventPublisher(abc.ABC):
    """Port used by the unit of work. Implementations must never raise on send failure."""

    async def start(self) -> None:  # pragma: no cover - default no-op
        return None

    async def stop(self) -> None:  # pragma: no cover - default no-op
        return None

    @abc.abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Send one event. Must swallow-and-log transport errors (the write already committed)."""


class NoopEventPublisher(EventPublisher):
    """Used when Kafka is disabled or unreachable."""

    async def publish(self, event: DomainEvent) -> None:
        logger.debug("Kafka disabled; dropping event type=%s key=%s", event.event_type, event.key)


class InMemoryEventPublisher(EventPublisher):
    """Records events; used by tests."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


class KafkaEventPublisher(EventPublisher):
    """aiokafka producer. Degrades to a no-op if the broker is unreachable at start."""

    def __init__(self, bootstrap_servers: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer = None

    async def start(self) -> None:
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers, request_timeout_ms=10000)
        try:
            await producer.start()
        except Exception as exc:  # noqa: BLE001 - boundary: broker down must not stop the API
            logger.warning("Kafka producer unavailable (%s); events will be dropped", exc)
            try:
                await producer.stop()
            except Exception:  # noqa: BLE001
                logger.debug("Producer stop after failed start also failed", exc_info=True)
            return
        self._producer = producer
        logger.info("Kafka producer started (%s)", self._bootstrap_servers)

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def publish(self, event: DomainEvent) -> None:
        if self._producer is None:
            logger.debug("Kafka producer not running; dropping event type=%s", event.event_type)
            return
        try:
            await self._producer.send_and_wait(event.topic, event.to_json_bytes(), key=event.key.encode("utf-8"))
            logger.info("Published event type=%s topic=%s key=%s", event.event_type, event.topic, event.key)
        except Exception as exc:  # noqa: BLE001 - boundary: send failure is logged, write already committed
            logger.error("Failed to publish event type=%s topic=%s: %s", event.event_type, event.topic, exc)
