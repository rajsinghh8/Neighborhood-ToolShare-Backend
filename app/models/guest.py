from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import InvitationStatus
from app.models.types import str_enum


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invitation_status: Mapped[InvitationStatus] = mapped_column(
        str_enum(InvitationStatus), default=InvitationStatus.PENDING, index=True
    )

    event: Mapped["Event"] = relationship(back_populates="guests", lazy="raise")

    def __repr__(self) -> str:
        return f"Guest(id={self.id!r}, event_id={self.event_id!r}, status={self.invitation_status!r})"
