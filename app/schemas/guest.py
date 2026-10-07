"""Guest request/response schemas."""
from __future__ import annotations

from pydantic import Field, field_validator

from app.models.enums import InvitationStatus
from app.schemas.common import ApiModel, NameStr


def _check_email(value: str | None) -> str | None:
    """Loose validation: when given, the email must contain an ``@``."""
    if value is None:
        return None
    value = value.strip()
    if "@" not in value or len(value) > 255:
        raise ValueError("email must contain '@' and be at most 255 characters")
    return value


class GuestCreate(ApiModel):
    """Body of POST /events/{id}/guests."""

    name: NameStr
    email: str | None = None
    invitation_status: InvitationStatus = InvitationStatus.PENDING

    _validate_email = field_validator("email")(_check_email)


class GuestUpdate(ApiModel):
    """Body of PUT/PATCH; only provided fields change. ``name``/``invitation_status`` cannot be null."""

    # Defaults are never validated by pydantic, so omitted fields stay out of ``model_fields_set``
    # while an explicit ``null`` is rejected by the field type.
    name: NameStr = Field(default=None)  # type: ignore[assignment]
    email: str | None = None
    invitation_status: InvitationStatus = Field(default=None)  # type: ignore[assignment]

    _validate_email = field_validator("email")(_check_email)


class Guest(ApiModel):
    """Guest representation."""

    id: int
    event_id: int
    name: str
    email: str | None
    invitation_status: InvitationStatus
