"""OpenAPI fragment: audit logs."""
from app.models.enums import AuditAction, AuditEntityType
from app.openapi.common import error_responses, ok, operation, page_schema, pagination_params, path_param, query_param, ref

TAG = "Audit logs"

SCHEMAS = {
    "AuditLog": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "event_id": {"type": "integer"},
            "actor_id": {"type": "integer"},
            "entity_type": {"type": "string", "enum": [e.value for e in AuditEntityType]},
            "entity_id": {"type": "integer"},
            "action": {"type": "string", "enum": [a.value for a in AuditAction]},
            "created_at": {"type": "string", "format": "date-time"},
        },
    },
    "AuditLogPage": page_schema("AuditLog"),
}

_params = [path_param("event_id", "Event id")] + pagination_params(["created_at", "id"], "id")
for _param in _params:
    if _param["name"] == "order":
        _param["schema"] = {**_param["schema"], "default": "desc"}
_params += [
    query_param("entity_type", {"type": "string", "enum": [e.value for e in AuditEntityType]}),
    query_param("action", {"type": "string", "enum": [a.value for a in AuditAction]}),
]

PATHS = {
    "/api/v1/events/{event_id}/audit-logs": {
        "get": operation(
            "List audit logs of an event (owner only)", TAG,
            {**ok("Page of audit rows", ref("AuditLogPage")), **error_responses(401, 404, 422)},
            parameters=_params,
        ),
    },
}
