"""Guest queries: event-scoped lookup, filtered/sorted listing."""
from __future__ import annotations

from sqlalchemy import select

from app.core.pagination import Page, PageRequest
from app.models import Guest
from app.models.enums import InvitationStatus
from app.repositories.base import BaseRepository

GUEST_SORT_FIELDS = ("id", "name", "invitation_status")


class GuestRepository(BaseRepository[Guest]):
    """Data access for :class:`Guest`."""

    model = Guest

    async def get_for_event(self, event_id: int, guest_id: int) -> Guest | None:
        """The guest only if it belongs to ``event_id``."""
        stmt = select(Guest).where(Guest.id == guest_id, Guest.event_id == event_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_event(self, event_id: int, request: PageRequest,
                             status: InvitationStatus | None = None) -> Page[Guest]:
        """Paginated guests of an event, optionally filtered by invitation status."""
        stmt = select(Guest).where(Guest.event_id == event_id)
        if status is not None:
            stmt = stmt.where(Guest.invitation_status == status)
        columns = {name: getattr(Guest, name) for name in GUEST_SORT_FIELDS}
        return await self.paginate(stmt, request, columns)
