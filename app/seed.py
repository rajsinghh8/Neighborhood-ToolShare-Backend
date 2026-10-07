"""Optional demo data (enabled with SEED_DEMO_DATA=true)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from app.container import AppContext
from app.models import Event, User
from app.repositories.core_repos import EventRepository, UserRepository

logger = logging.getLogger(__name__)

DEMO_EMAIL = "demo@eventforge.local"
DEMO_PASSWORD = "DemoPass123"


async def seed_demo_data(ctx: AppContext) -> None:
    """Create one demo user with one event, unless the demo user already exists."""
    uow = ctx.new_uow()
    try:
        users = UserRepository(uow.session)
        if await users.get_by_email(DEMO_EMAIL) is not None:
            return
        async with uow.transaction():
            user = await users.add(User(email=DEMO_EMAIL, password_hash=ctx.hasher.hash(DEMO_PASSWORD),
                                        name="Demo User"))
            start = datetime.utcnow() + timedelta(days=30)
            await EventRepository(uow.session).add(Event(
                owner_id=user.id, name="Demo Launch Party", description="Seeded demo event",
                start_at=start, end_at=start + timedelta(hours=4), guest_capacity=50,
                budget=Decimal("5000.00"),
            ))
        logger.info("Seeded demo user %s", DEMO_EMAIL)
    finally:
        await uow.close()
