"""Kafka consumer: logs and handles audit/notification events."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable

logger = logging.getLogger(__name__)

MessageHandler = Callable[[str, dict], None]


def log_domain_message(topic: str, body: dict) -> None:
    """Default handler: record that the event was observed."""
    logger.info("Consumed event topic=%s type=%s payload=%s", topic, body.get("event_type"), body.get("payload"))


class KafkaEventConsumer:
    """Background consumer task; failures never affect the HTTP API."""

    def __init__(self, bootstrap_servers: str, topics: list[str], group_id: str,
                 handler: MessageHandler = log_domain_message) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topics = topics
        self._group_id = group_id
        self._handler = handler
        self._consumer = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        from aiokafka import AIOKafkaConsumer

        consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        try:
            await consumer.start()
        except Exception as exc:  # noqa: BLE001 - boundary: broker down must not stop the API
            logger.warning("Kafka consumer unavailable (%s); not consuming", exc)
            try:
                await consumer.stop()
            except Exception:  # noqa: BLE001
                logger.debug("Consumer stop after failed start also failed", exc_info=True)
            return
        self._consumer = consumer
        self._task = asyncio.create_task(self._run(), name="kafka-consumer")
        logger.info("Kafka consumer started topics=%s group=%s", self._topics, self._group_id)

    async def _run(self) -> None:
        try:
            async for message in self._consumer:
                self._dispatch(message.topic, message.value)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - boundary: log and end the background task
            logger.exception("Kafka consumer loop terminated")

    def _dispatch(self, topic: str, raw: bytes) -> None:
        try:
            body = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            logger.warning("Discarding malformed message on topic=%s", topic)
            return
        self._handler(topic, body)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
