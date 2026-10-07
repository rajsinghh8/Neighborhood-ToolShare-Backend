"""Auth endpoints, JWT claims, password storage and token rejection."""
from __future__ import annotations

import time

import jwt
from sqlalchemy import select

from app.core.security import TokenService
from app.models import User

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
VALID = {"email": "Ann@Example.com", "password": "Sup3rSecret", "name": "Ann"}


async def test_register_success_returns_id_and_lowercases_email(anon, ctx):
    res = await anon.post(REGISTER, VALID)
    assert res.status == 201
    assert set(res.body) == {"id"} and isinstance(res.body["id"], int)
    async with ctx.database.session() as session:
        user = (await session.execute(select(User).where(User.id == res.body["id"]))).scalar_one()
    assert user.email == "ann@example.com"
    assert user.name == "Ann"


async def test_password_is_stored_hashed(anon, ctx):
    res = await anon.post(REGISTER, VALID)
    async with ctx.database.session() as session:
        user = (await session.execute(select(User).where(User.id == res.body["id"]))).scalar_one()
    assert user.password_hash != VALID["password"]
    assert user.password_hash.startswith("$2")
    assert VALID["password"] not in user.password_hash
    assert ctx.hasher.verify(VALID["password"], user.password_hash)


async def test_register_response_never_leaks_password(anon):
    res = await anon.post(REGISTER, VALID)
    assert "password" not in str(res.body).lower()


async def test_register_duplicate_email_is_409_case_insensitive(anon):
    assert (await anon.post(REGISTER, VALID)).status == 201
    dup = await anon.post(REGISTER, {**VALID, "email": "ann@example.com"})
    assert dup.status == 409
    assert dup.body["status"] == 409 and dup.body["path"] == REGISTER


async def test_register_validation_errors_are_422(anon):
    cases = [
        {**VALID, "email": "not-an-email"},
        {**VALID, "email": ""},
        {**VALID, "password": "short"},
        {**VALID, "name": "   "},
        {"email": "a@b.co", "password": "longenough"},
        {"password": "longenough", "name": "x"},
        {},
    ]
    for body in cases:
        res = await anon.post(REGISTER, body)
        assert res.status == 422, body
        assert res.body["status"] == 422 and res.body["message"]


async def test_register_invalid_json_is_400(anon):
    res = await anon.post(REGISTER, "{not json")
    assert res.status == 400


async def test_login_success_returns_bearer_token(anon):
    await anon.post(REGISTER, VALID)
    res = await anon.post(LOGIN, {"email": "ANN@example.com", "password": VALID["password"]})
    assert res.status == 200
    assert res.body["token_type"] == "bearer"
    assert res.body["expires_in"] == 1800
    assert res.body["access_token"]


async def test_jwt_subject_is_user_id_and_has_expiry(anon, ctx):
    reg = await anon.post(REGISTER, VALID)
    login = await anon.post(LOGIN, {"email": VALID["email"], "password": VALID["password"]})
    claims = jwt.decode(login.body["access_token"], ctx.settings.jwt_secret, algorithms=["HS256"])
    assert claims["sub"] == str(reg.body["id"])
    assert "iat" in claims
    assert 1700 <= claims["exp"] - time.time() <= 1801


async def test_login_wrong_password_and_unknown_user_are_indistinguishable_401(anon):
    await anon.post(REGISTER, VALID)
    wrong_pw = await anon.post(LOGIN, {"email": VALID["email"], "password": "WrongPassword1"})
    unknown = await anon.post(LOGIN, {"email": "nobody@example.com", "password": "WrongPassword1"})
    assert wrong_pw.status == unknown.status == 401
    assert wrong_pw.body["message"] == unknown.body["message"]


async def test_login_validation_422(anon):
    assert (await anon.post(LOGIN, {"email": "a@b.co"})).status == 422
    assert (await anon.post(LOGIN, {})).status == 422


async def test_missing_token_is_401(anon):
    res = await anon.get("/api/v1/events")
    assert res.status == 401
    assert res.body["status"] == 401


async def test_garbage_and_wrong_scheme_tokens_are_401(anon):
    assert (await anon.get("/api/v1/events", token="garbage.token.value")).status == 401
    res = await anon.get("/api/v1/events", token=None, headers={"Authorization": "Basic abc"})
    assert res.status == 401
    res = await anon.get("/api/v1/events", token=None, headers={"Authorization": "Bearer "})
    assert res.status == 401


async def test_token_signed_with_other_secret_is_401(anon):
    forged = TokenService("another-secret-another-secret-123456", "HS256", 30).issue(1)
    assert (await anon.get("/api/v1/events", token=forged)).status == 401


async def test_expired_token_is_401(anon, ctx):
    await anon.post(REGISTER, VALID)
    expired = TokenService(ctx.settings.jwt_secret, "HS256", -1).issue(1)
    res = await anon.get("/api/v1/events", token=expired)
    assert res.status == 401
    assert "expired" in res.body["message"].lower()


async def test_valid_token_is_accepted(anon, ctx):
    reg = await anon.post(REGISTER, VALID)
    token = ctx.tokens.issue(reg.body["id"])
    assert (await anon.get("/api/v1/events", token=token)).status == 200


async def test_public_endpoints_need_no_token(anon):
    assert (await anon.get("/health")).status == 200
    spec = await anon.get("/api/v1/openapi.json")
    assert spec.status == 200 and spec.body["openapi"].startswith("3")
    assert "/api/v1/auth/login" in spec.body["paths"]
    assert "/api/v1/events/{event_id}" in spec.body["paths"]
    assert (await anon.get("/api/v1/docs")).status == 200
    assert (await anon.get("/docs")).status == 200
    assert (await anon.get("/openapi.json")).status == 200
