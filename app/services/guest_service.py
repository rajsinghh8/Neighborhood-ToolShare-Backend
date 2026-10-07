"""Guest business rules: capacity, invitation-status change audit + owner notification."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.errors import BusinessRuleError, NotFoundError
from app.core.pagination import Page, PageRequest
from app.core.unit_of_work import UnitOfWork
from app.models import Guest
from app.models.enums import AuditAction, AuditEntityType, InvitationStatus, NotificationType
from app.repositories.guest_repository import GuestRepository
from app.repositories.stats import StatsRepository
from app.schemas.guest import GuestCreate, GuestUpdate
from app.services.audit_recorder import AuditRecorder
from app.services.event_access import EventAccess
from app.services.notification_recorder import NotificationRecorder

logger = logging.getLogger(__name__)


class GuestService:
    """Use cases for guests of an event owned by the calling user."""

    def __init__(self, uow: UnitOfWork, access: EventAccess, audit: AuditRecorder,
                 notifier: NotificationRecorder) -> None:
        self._uow = uow
        self._access = access
        self._audit = audit
        self._notifier = notifier
        self._guests = GuestRepository(uow.session)
        self._stats = StatsRepository(uow.session)

    async def list_guests(self, user_id: int, event_id: int, request: PageRequest,
                          status: InvitationStatus | None) -> Page[Guest]:
        """Paginated guests of an owned event."""
        await self._access.require_owned(event_id, user_id)
        return await self._guests.list_for_event(event_id, request, status)

    async def get_guest(self, user_id: int, event_id: int, guest_id: int) -> Guest:
        """One guest of an owned event (404 otherwise)."""
        await self._access.require_owned(event_id, user_id)
        return await self._require_guest(event_id, guest_id)

    async def create_guest(self, user_id: int, event_id: int, data: GuestCreate) -> Guest:
        """Create a guest; rejects (422) when the event's capacity would be exceeded."""
        event = await self._access.require_owned(event_id, user_id)
        async with self._uow.transaction():
            total = await self._stats.guest_count(event_id)
            if total + 1 > event.guest_capacity:
                raise BusinessRuleError(
                    f"Guest capacity of {event.guest_capacity} would be exceeded")
            guest = await self._guests.add(Guest(
                event_id=event_id, name=data.name, email=data.email,
                invitation_status=data.invitation_status))
            await self._audit.record(event_id, user_id, AuditEntityType.GUEST, guest.id, AuditAction.CREATE)
        logger.info("Guest created id=%s event_id=%s", guest.id, event_id)
        return guest

    async def update_guest(self, user_id: int, event_id: int, guest_id: int, data: GuestUpdate) -> Guest:
        """Apply the provided fields; a status change is audited and notified to the owner."""
        event = await self._access.require_owned(event_id, user_id)
        guest = await self._require_guest(event_id, guest_id)
        changes: dict[str, Any] = data.changes()
        old_status = guest.invitation_status
        new_status = changes.pop("invitation_status", old_status)
        status_changed = new_status != old_status
        other_changes = {f: v for f, v in changes.items() if getattr(guest, f) != v}
        other_changed = bool(other_changes)
        async with self._uow.transaction():
            for field, value in other_changes.items():
                setattr(guest, field, value)
            if status_changed:
                guest.invitation_status = new_status
            await self._guests.flush()
            if other_changed:
                await self._audit.record(event_id, user_id, AuditEntityType.GUEST, guest.id, AuditAction.UPDATE)
            if status_changed:
                await self._audit.record(event_id, user_id, AuditEntityType.GUEST, guest.id,
                                         AuditAction.STATUS_CHANGE)
                await self._notifier.notify(
                    event.owner_id, event_id, NotificationType.GUEST_INVITATION_STATUS,
                    f"Guest {guest.name} changed invitation status to {new_status.value}",
                    f"guest:{guest.id}:{new_status.value}:{uuid.uuid4().hex}")
        logger.info("Guest updated id=%s event_id=%s status_changed=%s", guest.id, event_id, status_changed)
        return guest

    async def delete_guest(self, user_id: int, event_id: int, guest_id: int) -> None:
        """Delete a guest of an owned event."""
        await self._access.require_owned(event_id, user_id)
        guest = await self._require_guest(event_id, guest_id)
        async with self._uow.transaction():
            await self._guests.delete(guest.id)
            await self._audit.record(event_id, user_id, AuditEntityType.GUEST, guest_id, AuditAction.DELETE)
        logger.info("Guest deleted id=%s event_id=%s", guest_id, event_id)

    async def _require_guest(self, event_id: int, guest_id: int) -> Guest:
        guest = await self._guests.get_for_event(event_id, guest_id)
        if guest is None:
            raise NotFoundError("Guest not found")
        return guest
