"""Event queries beyond the generic repository (owner-scoped listing)."""
from __future__ import annotations

from sqlalchemy import select

from app.core.pagination import Page, PageRequest
from app.models import Event
from app.repositories.core_repos import EventRepository

SORT_COLUMNS = {
    "id": Event.id,
    "name": Event.name,
    "start_at": Event.start_at,
    "end_at": Event.end_at,
    "budget": Event.budget,
}


class OwnedEventRepository(EventRepository):
    """Events filtered by owner (extends the core EventRepository)."""

    async def list_for_owner(self, owner_id: int, request: PageRequest) -> Page[Event]:
        stmt = select(Event).where(Event.owner_id == owner_id)
        return await self.paginate(stmt, request, SORT_COLUMNS)
