"""Shared fixtures: in-process Tornado server on an ephemeral port + SQLite file DB + HTTP helper."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from typing import Any

import pytest
import pytest_asyncio
from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest
from tornado.httpserver import HTTPServer
from tornado.testing import bind_unused_port

from app.config import Settings
from app.container import AppContext, build_context
from app.events.publisher import InMemoryEventPublisher
from app.routes import make_application


@dataclass
class Response:
    status: int
    body: Any


class ApiClient:
    """Tiny JSON client. ``token`` is sent as a Bearer header when set."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.token: str | None = None
        self._http = AsyncHTTPClient()

    async def request(self, method: str, path: str, body: Any = None, token: str | None = "default",
                      headers: dict[str, str] | None = None) -> Response:
        hdrs = {"Content-Type": "application/json"}
        use_token = self.token if token == "default" else token
        if use_token:
            hdrs["Authorization"] = f"Bearer {use_token}"
        hdrs.update(headers or {})
        data = body if isinstance(body, (str, bytes)) else (json.dumps(body) if body is not None else None)
        req = HTTPRequest(self.base_url + path, method=method, headers=hdrs, body=data, raise_error=False)
        res = await self._http.fetch(req, raise_error=False)
        parsed: Any = None
        if res.body:
            try:
                parsed = json.loads(res.body)
            except ValueError:
                parsed = res.body.decode("utf-8", "replace")
        return Response(res.code, parsed)

    async def get(self, path: str, **kw) -> Response:
        return await self.request("GET", path, **kw)

    async def post(self, path: str, body: Any = None, **kw) -> Response:
        return await self.request("POST", path, body, **kw)

    async def put(self, path: str, body: Any = None, **kw) -> Response:
        return await self.request("PUT", path, body, **kw)

    async def patch(self, path: str, body: Any = None, **kw) -> Response:
        return await self.request("PATCH", path, body, **kw)

    async def delete(self, path: str, **kw) -> Response:
        return await self.request("DELETE", path, **kw)

    async def register_and_login(self, email: str = "owner@example.com", password: str = "Passw0rd!x",
                                 name: str = "Owner") -> str:
        """Register + login; returns the access token (does not change ``self.token``)."""
        reg = await self.post("/api/v1/auth/register", {"email": email, "password": password, "name": name}, token=None)
        assert reg.status == 201, reg.body
        login = await self.post("/api/v1/auth/login", {"email": email, "password": password}, token=None)
        assert login.status == 200, login.body
        return login.body["access_token"]


@pytest.fixture
def db_file():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except OSError:
        pass


@pytest_asyncio.fixture
async def ctx(db_file) -> AppContext:
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_file}", jwt_secret="test-secret-test-secret-test-secret",
        kafka_enabled=False, scheduler_enabled=False, db_connect_retries=1, log_level="WARNING",
    )
    context = build_context(settings, InMemoryEventPublisher())
    await context.database.create_schema()
    yield context
    await context.database.dispose()


@pytest_asyncio.fixture
async def server(ctx):
    sock, port = bind_unused_port()
    http_server = HTTPServer(make_application(ctx))
    http_server.add_sockets([sock])
    yield f"http://127.0.0.1:{port}"
    http_server.stop()


@pytest_asyncio.fixture
async def client(server) -> ApiClient:
    """Authenticated client (token for owner@example.com already set)."""
    api = ApiClient(server)
    api.token = await api.register_and_login()
    return api


@pytest_asyncio.fixture
async def anon(server) -> ApiClient:
    return ApiClient(server)


@pytest_asyncio.fixture
async def other_token(server) -> str:
    """Token for a second user (for ownership/404 tests)."""
    return await ApiClient(server).register_and_login("intruder@example.com", "Passw0rd!x", "Intruder")


@pytest_asyncio.fixture
async def event_id(client) -> int:
    """An event owned by the default client: capacity 3, budget 1000.00, in the future."""
    res = await client.post("/api/v1/events", {
        "name": "Gala", "description": "d", "start_at": "2030-01-01T10:00:00Z",
        "end_at": "2030-01-01T18:00:00Z", "guest_capacity": 3, "budget": "1000.00",
    })
    assert res.status == 201, res.body
    return res.body["id"]
