"""ORM helpers shared by the notification / audit / scheduler tests (direct inserts, no API)."""
from __future__ import annotations

from typing import Iterable, TypeVar

from sqlalchemy import select

from app.container import AppContext
from app.models import Event, User

T = TypeVar("T")


async def insert_all(ctx: AppContext, rows: Iterable[T]) -> list[T]:
    """Persist ORM rows in one transaction and return them (ids populated)."""
    items = list(rows)
    uow = ctx.new_uow()
    try:
        async with uow.transaction():
            uow.session.add_all(items)
            await uow.session.flush()
        return items
    finally:
        await uow.close()


async def owner_of(ctx: AppContext, event_id: int) -> int:
    """User id owning the event."""
    uow = ctx.new_uow()
    try:
        return (await uow.session.execute(select(Event.owner_id).where(Event.id == event_id))).scalar_one()
    finally:
        await uow.close()


async def user_id_by_email(ctx: AppContext, email: str) -> int:
    """User id for a registered email."""
    uow = ctx.new_uow()
    try:
        return (await uow.session.execute(select(User.id).where(User.email == email))).scalar_one()
    finally:
        await uow.close()


async def fetch_all(ctx: AppContext, model: type[T]) -> list[T]:
    """All rows of a model ordered by id."""
    uow = ctx.new_uow()
    try:
        return list((await uow.session.execute(select(model).order_by(model.id))).scalars().all())
    finally:
        await uow.close()
