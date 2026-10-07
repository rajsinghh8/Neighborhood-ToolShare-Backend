"""Collects every handler module's ROUTES into the Tornado application."""
from __future__ import annotations

import importlib

from tornado import web

from app.container import AppContext
from app.handlers.base import NotFoundHandler

HANDLER_MODULES = [
    "system_handlers", "auth_handlers", "event_handlers", "task_handlers", "guest_handlers",
    "budget_category_handlers", "expense_handlers", "schedule_handlers",
    "vendor_handlers", "vendor_payment_handlers", "notification_handlers", "audit_handlers",
]


def make_application(ctx: AppContext) -> web.Application:
    """Build the Tornado app; each route gets the shared AppContext."""
    rules = []
    for module_name in HANDLER_MODULES:
        module = importlib.import_module(f"app.handlers.{module_name}")
        for pattern, handler_cls in module.ROUTES:
            rules.append((pattern, handler_cls, {"ctx": ctx}))
    return web.Application(
        rules,
        default_handler_class=NotFoundHandler,
        default_handler_args={"ctx": ctx},
    )
