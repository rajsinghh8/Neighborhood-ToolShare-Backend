"""Request/response schemas for registration and login."""
from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, Field, StringConstraints

from app.schemas.common import ApiModel, NameStr

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(value: str) -> str:
    """Trim, lower-case and loosely validate an e-mail address."""
    cleaned = value.strip().lower()
    if not _EMAIL_RE.match(cleaned):
        raise ValueError("must be a valid e-mail address")
    return cleaned


EmailStr = Annotated[str, StringConstraints(max_length=255), AfterValidator(_normalize_email)]


class RegisterRequest(ApiModel):
    """POST /auth/register body."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    name: NameStr


class LoginRequest(ApiModel):
    """POST /auth/login body (e-mail is not format-checked so bad input is just 'bad credentials')."""

    email: Annotated[str, Field(min_length=1, max_length=255)]
    password: Annotated[str, Field(min_length=1, max_length=128)]


class RegisterResponse(ApiModel):
    """201 body of registration."""

    id: int


class TokenResponse(ApiModel):
    """200 body of login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
