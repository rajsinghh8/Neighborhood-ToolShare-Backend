"""OpenAPI fragment: notifications."""
from app.models.enums import NotificationType
from app.openapi.common import (
    error_responses, json_body, ok, operation, page_schema, pagination_params, path_param, query_param, ref,
)

TAG = "Notifications"
_SORT = ["created_at", "id", "is_read"]

SCHEMAS = {
    "Notification": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "user_id": {"type": "integer"},
            "event_id": {"type": "integer", "nullable": True},
            "type": {"type": "string", "enum": [t.value for t in NotificationType]},
            "message": {"type": "string"},
            "is_read": {"type": "boolean"},
            "dedup_key": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"},
        },
    },
    "NotificationUpdate": {
        "type": "object",
        "required": ["is_read"],
        "properties": {"is_read": {"type": "boolean"}},
    },
    "NotificationPage": page_schema("Notification"),
}

_ID = path_param("notification_id", "Notification id")

_list_params = pagination_params(_SORT, "created_at")
for _param in _list_params:
    if _param["name"] == "order":
        _param["schema"] = {**_param["schema"], "default": "desc"}
_list_params.append(query_param("is_read", {"type": "boolean"}, "Filter by read state"))

PATHS = {
    "/api/v1/notifications": {
        "get": operation(
            "List the current user's notifications", TAG,
            {**ok("Page of notifications", ref("NotificationPage")), **error_responses(401, 422)},
            parameters=_list_params,
        ),
    },
    "/api/v1/notifications/{notification_id}": {
        "get": operation(
            "Get a notification", TAG,
            {**ok("The notification", ref("Notification")), **error_responses(401, 404)},
            parameters=[_ID],
        ),
        "patch": operation(
            "Mark a notification read/unread", TAG,
            {**ok("Updated notification", ref("Notification")), **error_responses(400, 401, 404, 422)},
            parameters=[_ID], request_body=json_body(ref("NotificationUpdate")),
        ),
        "delete": operation(
            "Delete a notification", TAG,
            {**ok("Deleted", status=204), **error_responses(401, 404)},
            parameters=[_ID],
        ),
    },
}
