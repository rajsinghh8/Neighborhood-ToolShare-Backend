"""OpenAPI fragment: guests."""
from __future__ import annotations

from app.openapi.common import (error_responses, json_body, ok, operation, page_schema, pagination_params,
                                path_param, query_param, ref)

TAG = "Guests"
_STATUSES = ["pending", "accepted", "declined"]
_EMAIL = {"type": "string", "nullable": True, "description": "Must contain '@' when provided"}

SCHEMAS = {
    "Guest": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}, "event_id": {"type": "integer"}, "name": {"type": "string"},
            "email": {"type": "string", "nullable": True},
            "invitation_status": {"type": "string", "enum": _STATUSES},
        },
    },
    "GuestCreate": {
        "type": "object", "required": ["name"],
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 255}, "email": _EMAIL,
            "invitation_status": {"type": "string", "enum": _STATUSES, "default": "pending"},
        },
    },
    "GuestUpdate": {
        "type": "object",
        "description": "Only provided fields change. Changing invitation_status is audited "
                       "(status_change) and notifies the event owner.",
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 255}, "email": _EMAIL,
            "invitation_status": {"type": "string", "enum": _STATUSES},
        },
    },
    "GuestPage": page_schema("Guest"),
}

_EVENT = path_param("event_id", "Event id (must be owned by the caller)")
_GUEST = path_param("guest_id", "Guest id")
_UPDATE_RESPONSES = {**ok("Updated guest", ref("Guest")), **error_responses(401, 404, 422)}

PATHS = {
    "/api/v1/events/{event_id}/guests": {
        "get": operation(
            "List guests of an event", TAG,
            {**ok("Page of guests", ref("GuestPage")), **error_responses(401, 404, 422)},
            [_EVENT, *pagination_params(["id", "name", "invitation_status"], "id"),
             query_param("invitation_status", {"type": "string", "enum": _STATUSES}, "Filter by status")]),
        "post": operation(
            "Add a guest (422 when the event capacity would be exceeded)", TAG,
            {**ok("Created guest", ref("Guest"), 201), **error_responses(401, 404, 422)},
            [_EVENT], json_body(ref("GuestCreate"))),
    },
    "/api/v1/events/{event_id}/guests/{guest_id}": {
        "get": operation("Get a guest", TAG,
                         {**ok("Guest", ref("Guest")), **error_responses(401, 404)}, [_EVENT, _GUEST]),
        "put": operation("Update a guest (partial)", TAG, _UPDATE_RESPONSES, [_EVENT, _GUEST],
                         json_body(ref("GuestUpdate"))),
        "patch": operation("Update a guest (partial)", TAG, _UPDATE_RESPONSES, [_EVENT, _GUEST],
                           json_body(ref("GuestUpdate"))),
        "delete": operation("Delete a guest", TAG,
                            {**ok("Deleted", None, 204), **error_responses(401, 404)}, [_EVENT, _GUEST]),
    },
}
