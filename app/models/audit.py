from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import AuditAction, AuditEntityType
from app.models.types import str_enum


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[int] = mapped_column(Integer, index=True)
    entity_type: Mapped[AuditEntityType] = mapped_column(str_enum(AuditEntityType, length=30))
    entity_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[AuditAction] = mapped_column(str_enum(AuditAction))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    event: Mapped["Event"] = relationship(back_populates="audit_logs", lazy="raise")

    def __repr__(self) -> str:
        return f"AuditLog(id={self.id!r}, event_id={self.event_id!r}, action={self.action!r})"
