"""Health check, OpenAPI JSON and Swagger UI (all public)."""
from __future__ import annotations

import json

from app.handlers.base import BaseHandler
from app.handlers.paths import API_PREFIX
from app.openapi import build_spec

SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>EventForge API - Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"/>
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
  window.onload = function () {
    window.ui = SwaggerUIBundle({url: "/openapi.json", dom_id: "#swagger-ui"});
  };
</script>
</body>
</html>
"""


class HealthHandler(BaseHandler):
    public = True

    async def get(self) -> None:
        self.send_json({"status": "ok"})


class OpenApiHandler(BaseHandler):
    """Serves the spec; exempt from JWT so Swagger UI can load it."""

    public = True

    def initialize(self, ctx) -> None:
        super().initialize(ctx)
        self._spec_json = json.dumps(build_spec())

    async def get(self) -> None:
        self.set_status(200)
        self.finish(self._spec_json)


class DocsHandler(BaseHandler):
    public = True

    async def get(self) -> None:
        self.set_header("Content-Type", "text/html; charset=UTF-8")
        self.finish(SWAGGER_HTML)


ROUTES = [
    ("/health", HealthHandler),
    ("/openapi.json", OpenApiHandler),
    ("/docs", DocsHandler),
    (API_PREFIX + "/openapi.json", OpenApiHandler),
    (API_PREFIX + "/docs", DocsHandler),
]
