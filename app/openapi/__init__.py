"""Assembles the hand-written OpenAPI 3 document from per-group fragments."""
from __future__ import annotations

import importlib
from typing import Any

from app.openapi.common import ERROR_SCHEMA

FRAGMENT_MODULES = [
    "paths_system", "paths_auth", "paths_events", "paths_tasks", "paths_guests",
    "paths_budget_categories", "paths_expenses", "paths_schedule", "paths_vendors",
    "paths_vendor_payments", "paths_notifications", "paths_audit",
]


def build_spec() -> dict[str, Any]:
    """Merge every fragment's ``PATHS`` and ``SCHEMAS`` into one document."""
    paths: dict[str, Any] = {}
    schemas: dict[str, Any] = {"Error": ERROR_SCHEMA}
    for name in FRAGMENT_MODULES:
        module = importlib.import_module(f"app.openapi.{name}")
        paths.update(module.PATHS)
        schemas.update(getattr(module, "SCHEMAS", {}))
    return {
        "openapi": "3.0.3",
        "info": {"title": "EventForge API", "version": "1.0.0",
                 "description": "Event planning: events, tasks, guests, budgets, vendors, notifications."},
        "servers": [{"url": "/"}],
        "paths": paths,
        "components": {
            "schemas": schemas,
            "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
        },
    }
