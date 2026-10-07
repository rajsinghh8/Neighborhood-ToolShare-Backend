"""Writes audit rows inside the caller's transaction and queues a Kafka audit event."""
from __future__ import annotations

import logging

from app.core.unit_of_work import UnitOfWork
from app.events.domain import DomainEvent
from app.models import AuditLog
from app.models.enums import AuditAction, AuditEntityType
from app.repositories.core_repos import AuditLogRepository

logger = logging.getLogger(__name__)

AUDIT_EVENT_TYPE = "audit.recorded"


class AuditRecorder:
    """Injected into every mutating service. Call inside ``uow.transaction()``."""

    def __init__(self, uow: UnitOfWork, topic: str = "eventforge.audit") -> None:
        self._uow = uow
        self._repo = AuditLogRepository(uow.session)
        self._topic = topic

    async def record(self, event_id: int, actor_id: int, entity_type: AuditEntityType,
                     entity_id: int, action: AuditAction) -> AuditLog:
        """Persist an audit row; ``entity_id`` must already be assigned (flush new entities first)."""
        row = await self._repo.add(AuditLog(
            event_id=event_id, actor_id=actor_id, entity_type=entity_type,
            entity_id=entity_id, action=action,
        ))
        self._uow.add_event(DomainEvent(
            topic=self._topic,
            key=str(event_id),
            event_type=AUDIT_EVENT_TYPE,
            payload={
                "event_id": event_id, "actor_id": actor_id, "entity_type": entity_type.value,
                "entity_id": entity_id, "action": action.value,
            },
        ))
        logger.info("Audit event_id=%s actor_id=%s %s %s id=%s", event_id, actor_id,
                    action.value, entity_type.value, entity_id)
        return row
