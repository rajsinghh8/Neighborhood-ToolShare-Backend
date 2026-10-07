from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))

    events: Mapped[list["Event"]] = relationship(back_populates="owner", lazy="raise", passive_deletes=True)
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", lazy="raise", passive_deletes=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
