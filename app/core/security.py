"""Password hashing (bcrypt) and JWT (HS256) token service."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.errors import UnauthorizedError

logger = logging.getLogger(__name__)

# bcrypt only looks at the first 72 bytes of a password.
_BCRYPT_MAX_BYTES = 72


class PasswordHasher:
    """bcrypt hashing; plaintext passwords are never stored or logged."""

    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, password: str) -> str:
        raw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=self._rounds)).decode("ascii")

    def verify(self, password: str, password_hash: str) -> bool:
        raw = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
        try:
            return bcrypt.checkpw(raw, password_hash.encode("ascii"))
        except ValueError:
            logger.warning("Stored password hash is malformed")
            return False


class TokenService:
    """Issues and verifies access tokens. Subject is the user id. No refresh tokens."""

    def __init__(self, secret: str, algorithm: str = "HS256", expire_minutes: int = 30) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    @property
    def expires_in_seconds(self) -> int:
        return self._expire_minutes * 60

    def issue(self, user_id: int) -> str:
        now = datetime.now(timezone.utc)
        claims = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=self._expire_minutes),
        }
        return jwt.encode(claims, self._secret, algorithm=self._algorithm)

    def verify(self, token: str) -> int:
        """Return the user id, or raise UnauthorizedError."""
        try:
            claims = jwt.decode(token, self._secret, algorithms=[self._algorithm],
                                options={"require": ["exp", "sub"]})
            return int(claims["sub"])
        except jwt.ExpiredSignatureError as exc:
            raise UnauthorizedError("Token has expired") from exc
        except (jwt.InvalidTokenError, ValueError) as exc:
            raise UnauthorizedError("Invalid authentication token") from exc
