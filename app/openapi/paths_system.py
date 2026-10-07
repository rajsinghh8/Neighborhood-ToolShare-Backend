"""OpenAPI fragment: health, docs, spec."""
from app.openapi.common import ok, operation

PATHS = {
    "/health": {"get": operation("Health check", "System", ok("Service is up"), secured=False)},
    "/openapi.json": {"get": operation("OpenAPI document (root alias)", "System", ok("OpenAPI 3 JSON"), secured=False)},
    "/docs": {"get": operation("Swagger UI (root alias)", "System", ok("Swagger UI HTML"), secured=False)},
    "/api/v1/openapi.json": {"get": operation("OpenAPI document", "System", ok("OpenAPI 3 JSON"), secured=False)},
    "/api/v1/docs": {"get": operation("Swagger UI", "System", ok("Swagger UI HTML"), secured=False)},
}
