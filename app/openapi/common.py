"""Helpers for the hand-written OpenAPI spec fragments (one ``paths_<group>.py`` per group)."""
from __future__ import annotations

from typing import Any

JSON = "application/json"

ERROR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "status": {"type": "integer"},
        "error": {"type": "string"},
        "message": {"type": "string"},
        "path": {"type": "string"},
    },
}

_ERROR_DESCRIPTIONS = {
    400: "Bad request", 401: "Missing or invalid token", 404: "Not found",
    409: "Conflict", 422: "Validation failed",
}


def ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/components/schemas/{name}"}


def error_responses(*codes: int) -> dict[str, Any]:
    return {
        str(code): {"description": _ERROR_DESCRIPTIONS.get(code, "Error"),
                    "content": {JSON: {"schema": ref("Error")}}}
        for code in codes
    }


def ok(description: str, schema: dict[str, Any] | None = None, status: int = 200) -> dict[str, Any]:
    response: dict[str, Any] = {"description": description}
    if schema is not None:
        response["content"] = {JSON: {"schema": schema}}
    return {str(status): response}


def json_body(schema: dict[str, Any], required: bool = True) -> dict[str, Any]:
    return {"required": required, "content": {JSON: {"schema": schema}}}


def path_param(name: str, description: str = "") -> dict[str, Any]:
    return {"name": name, "in": "path", "required": True, "description": description or name,
            "schema": {"type": "integer"}}


def query_param(name: str, schema: dict[str, Any], description: str = "") -> dict[str, Any]:
    return {"name": name, "in": "query", "required": False, "description": description or name,
            "schema": schema}


def pagination_params(sort_fields: list[str] | None = None, default_sort: str = "id") -> list[dict[str, Any]]:
    params = [
        query_param("page", {"type": "integer", "minimum": 1, "default": 1}, "1-based page number"),
        query_param("size", {"type": "integer", "minimum": 1, "default": 20}, "Page size (alias: limit)"),
        query_param("offset", {"type": "integer", "minimum": 0}, "Explicit row offset (overrides page)"),
    ]
    if sort_fields:
        params.append(query_param("sort", {"type": "string", "enum": sort_fields, "default": default_sort}))
        params.append(query_param("order", {"type": "string", "enum": ["asc", "desc"], "default": "asc"}))
    return params


def page_schema(item_schema_name: str) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": ref(item_schema_name)},
            "total": {"type": "integer"}, "page": {"type": "integer"}, "size": {"type": "integer"},
            "limit": {"type": "integer"}, "offset": {"type": "integer"},
        },
    }


def operation(summary: str, tag: str, responses: dict[str, Any], parameters: list[dict[str, Any]] | None = None,
              request_body: dict[str, Any] | None = None, secured: bool = True) -> dict[str, Any]:
    op: dict[str, Any] = {"summary": summary, "tags": [tag], "responses": responses}
    if parameters:
        op["parameters"] = parameters
    if request_body:
        op["requestBody"] = request_body
    op["security"] = [{"bearerAuth": []}] if secured else []
    return op
