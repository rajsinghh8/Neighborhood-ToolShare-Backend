"""Entry point: ``python -m app.main`` — runs in the foreground (the event loop never returns)."""
from __future__ import annotations

import asyncio
import logging

from tornado.httpserver import HTTPServer
from tornado.ioloop import PeriodicCallback

from app.config import Settings
from app.container import AppContext, build_context
from app.core.logging_config import configure_logging
from app.events.consumer import KafkaEventConsumer
from app.events.publisher import EventPublisher, KafkaEventPublisher, NoopEventPublisher
from app.routes import make_application
from app.scheduler.notification_scheduler import NotificationScheduler
from app.seed import seed_demo_data

logger = logging.getLogger(__name__)


def build_publisher(settings: Settings) -> EventPublisher:
    if settings.kafka_enabled:
        return KafkaEventPublisher(settings.kafka_bootstrap_servers)
    return NoopEventPublisher()


async def serve(settings: Settings) -> None:
    ctx: AppContext = build_context(settings, build_publisher(settings))
    await ctx.database.create_schema()
    if settings.seed_demo_data:
        await seed_demo_data(ctx)

    await ctx.publisher.start()
    consumer = None
    if settings.kafka_enabled:
        consumer = KafkaEventConsumer(
            settings.kafka_bootstrap_servers,
            [settings.kafka_audit_topic, settings.kafka_notification_topic],
            settings.kafka_consumer_group,
        )
        await consumer.start()

    scheduler = NotificationScheduler(ctx.new_uow, settings.kafka_notification_topic)
    periodic = None
    if settings.scheduler_enabled:
        periodic = PeriodicCallback(scheduler.run_safely, settings.scheduler_interval_ms)
        periodic.start()

    server = HTTPServer(make_application(ctx))
    server.listen(settings.port, address=settings.host)
    logger.info("EventForge listening on %s:%s", settings.host, settings.port)
    try:
        await asyncio.Event().wait()
    finally:
        if periodic is not None:
            periodic.stop()
        server.stop()
        if consumer is not None:
            await consumer.stop()
        await ctx.publisher.stop()
        await ctx.database.dispose()


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    try:
        asyncio.run(serve(settings))
    except KeyboardInterrupt:
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
