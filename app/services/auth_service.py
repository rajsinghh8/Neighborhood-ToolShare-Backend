"""Registration and login rules."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import PasswordHasher, TokenService
from app.core.unit_of_work import UnitOfWork
from app.models import User
from app.repositories.core_repos import UserRepository

logger = logging.getLogger(__name__)

_BAD_CREDENTIALS = "Invalid email or password"
_dummy_hash: str | None = None


class AuthService:
    """Creates users (bcrypt-hashed passwords) and issues JWT access tokens."""

    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._uow = uow
        self._users = UserRepository(uow.session)
        self._hasher = hasher
        self._tokens = tokens

    async def register(self, email: str, password: str, name: str) -> User:
        """Create a user. ``email`` must already be normalised (lower-case). Duplicate -> 409."""
        if await self._users.get_by_email(email) is not None:
            raise ConflictError("Email is already registered")
        password_hash = await asyncio.to_thread(self._hasher.hash, password)
        try:
            async with self._uow.transaction():
                user = await self._users.add(User(email=email, password_hash=password_hash, name=name))
        except IntegrityError as exc:  # lost a race with a concurrent registration
            raise ConflictError("Email is already registered") from exc
        logger.info("User registered id=%s", user.id)
        return user

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Verify credentials and return the token payload; 401 without revealing which part failed."""
        user = await self._users.get_by_email(email.strip().lower())
        # Always run one bcrypt verification so unknown e-mails cost the same as wrong passwords.
        stored_hash = user.password_hash if user is not None else await self._get_dummy_hash()
        valid = await asyncio.to_thread(self._hasher.verify, password, stored_hash)
        if user is None or not valid:
            logger.info("Failed login attempt")
            raise UnauthorizedError(_BAD_CREDENTIALS)
        return {
            "access_token": self._tokens.issue(user.id),
            "token_type": "bearer",
            "expires_in": self._tokens.expires_in_seconds,
        }

    async def _get_dummy_hash(self) -> str:
        global _dummy_hash
        if _dummy_hash is None:
            _dummy_hash = await asyncio.to_thread(self._hasher.hash, "dummy-password-for-timing")
        return _dummy_hash
