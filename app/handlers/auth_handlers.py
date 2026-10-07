"""Public authentication endpoints: register and login."""
from __future__ import annotations

from app.handlers.base import BaseHandler
from app.handlers.paths import API_PREFIX
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.services.auth_service import AuthService


class RegisterHandler(BaseHandler):
    """POST /api/v1/auth/register."""

    public = True

    async def post(self) -> None:
        body = self.parse_body(RegisterRequest)
        user = await self.service(AuthService).register(body.email, body.password, body.name)
        self.send_json(RegisterResponse.model_validate(user).to_json(), 201)


class LoginHandler(BaseHandler):
    """POST /api/v1/auth/login."""

    public = True

    async def post(self) -> None:
        body = self.parse_body(LoginRequest)
        token = await self.service(AuthService).login(body.email, body.password)
        self.send_json(TokenResponse.model_validate(token).to_json())


ROUTES = [
    (API_PREFIX + r"/auth/register", RegisterHandler),
    (API_PREFIX + r"/auth/login", LoginHandler),
]
