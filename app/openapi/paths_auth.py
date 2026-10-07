"""OpenAPI fragment: authentication."""
from app.openapi.common import error_responses, json_body, ok, operation, ref

SCHEMAS = {
    "RegisterRequest": {
        "type": "object", "required": ["email", "password", "name"],
        "properties": {
            "email": {"type": "string", "format": "email", "maxLength": 255},
            "password": {"type": "string", "minLength": 8, "maxLength": 128, "format": "password"},
            "name": {"type": "string", "minLength": 1, "maxLength": 255},
        },
    },
    "RegisterResponse": {"type": "object", "properties": {"id": {"type": "integer"}}},
    "LoginRequest": {
        "type": "object", "required": ["email", "password"],
        "properties": {"email": {"type": "string"}, "password": {"type": "string", "format": "password"}},
    },
    "TokenResponse": {
        "type": "object",
        "properties": {
            "access_token": {"type": "string"},
            "token_type": {"type": "string", "example": "bearer"},
            "expires_in": {"type": "integer", "example": 1800},
        },
    },
}

PATHS = {
    "/api/v1/auth/register": {
        "post": operation(
            "Register a new user", "Auth",
            {**ok("User created", ref("RegisterResponse"), 201), **error_responses(409, 422)},
            request_body=json_body(ref("RegisterRequest")), secured=False),
    },
    "/api/v1/auth/login": {
        "post": operation(
            "Log in and obtain a JWT access token", "Auth",
            {**ok("Token issued", ref("TokenResponse")), **error_responses(401, 422)},
            request_body=json_body(ref("LoginRequest")), secured=False),
    },
}
