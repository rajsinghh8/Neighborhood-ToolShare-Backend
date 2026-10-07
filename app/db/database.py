"""Async SQLAlchemy engine/session wiring."""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base for every persistence model."""


class Database:
    """Owns the engine and hands out sessions. Injected, never imported as a global."""

    def __init__(self, url: str, connect_retries: int = 30) -> None:
        self._url = url
        self._connect_retries = connect_retries
        self._engine: AsyncEngine = create_async_engine(url, pool_pre_ping=True)
        if url.startswith("sqlite"):
            self._enable_sqlite_foreign_keys(self._engine)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)

    @staticmethod
    def _enable_sqlite_foreign_keys(engine: AsyncEngine) -> None:
        @event.listens_for(engine.sync_engine, "connect")
        def _set_pragma(dbapi_connection, _record) -> None:  # pragma: no cover - trivial
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def session(self) -> AsyncSession:
        return self._session_factory()

    async def create_schema(self) -> None:
        """Create tables, waiting for the database to accept connections."""
        import app.models  # noqa: F401  (registers every model on Base.metadata)

        last_error: Exception | None = None
        for attempt in range(1, self._connect_retries + 1):
            try:
                async with self._engine.begin() as connection:
                    await connection.run_sync(Base.metadata.create_all)
                logger.info("Database schema ready")
                return
            except Exception as exc:  # noqa: BLE001 - boundary: retry any connect failure, logged
                last_error = exc
                logger.warning("Database not ready (attempt %d/%d): %s", attempt, self._connect_retries, exc)
                await asyncio.sleep(2)
        raise RuntimeError("Database never became ready") from last_error

    async def dispose(self) -> None:
        await self._engine.dispose()
