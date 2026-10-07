"""Unit of work: one DB session, explicit transaction scope, post-commit event publishing."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Database
from app.events.domain import DomainEvent
from app.events.publisher import EventPublisher

logger = logging.getLogger(__name__)


class UnitOfWork:
    """Wraps a session. Mutations run inside ``async with uow.transaction():``.

    Domain events queued via :meth:`add_event` are published only after the commit
    succeeded, and discarded on rollback.
    """

    def __init__(self, database: Database, publisher: EventPublisher) -> None:
        self._session: AsyncSession = database.session()
        self._publisher = publisher
        self._pending_events: list[DomainEvent] = []

    @property
    def session(self) -> AsyncSession:
        return self._session

    def add_event(self, event: DomainEvent) -> None:
        self._pending_events.append(event)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        """Commit on success, roll back on any error; publish events after commit."""
        try:
            yield self._session
            await self._session.commit()
        except BaseException:
            await self._session.rollback()
            self._pending_events.clear()
            raise
        await self._publish_pending()

    async def _publish_pending(self) -> None:
        events, self._pending_events = self._pending_events, []
        for event in events:
            await self._publisher.publish(event)

    async def close(self) -> None:
        await self._session.close()
