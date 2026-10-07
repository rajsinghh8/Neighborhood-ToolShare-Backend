"""OpenAPI fragment: events."""
from app.openapi.common import (error_responses, json_body, ok, operation, page_schema, pagination_params,
                                path_param, ref)

SORT_FIELDS = ["id", "name", "start_at", "end_at", "budget"]

_MONEY = {"type": "string", "example": "1000.00", "description": "Decimal with exactly 2 places"}
_DATETIME = {"type": "string", "format": "date-time", "example": "2030-01-01T10:00:00Z"}

SCHEMAS = {
    "Event": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}, "owner_id": {"type": "integer"}, "name": {"type": "string"},
            "description": {"type": "string", "nullable": True},
            "start_at": _DATETIME, "end_at": _DATETIME,
            "guest_capacity": {"type": "integer", "minimum": 0}, "budget": _MONEY,
        },
    },
    "EventCreate": {
        "type": "object", "required": ["name", "start_at", "end_at", "guest_capacity", "budget"],
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 255},
            "description": {"type": "string", "nullable": True},
            "start_at": _DATETIME, "end_at": {**_DATETIME, "description": "Must be after start_at"},
            "guest_capacity": {"type": "integer", "minimum": 0},
            "budget": {"type": "string", "example": "1000.00", "description": "Decimal >= 0, max 2 places (number also accepted)"},
        },
    },
    "EventUpdate": {
        "type": "object", "description": "Only provided fields are changed.",
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 255},
            "description": {"type": "string", "nullable": True},
            "start_at": _DATETIME, "end_at": _DATETIME,
            "guest_capacity": {"type": "integer", "minimum": 0,
                               "description": "Cannot be lower than the current number of guests"},
            "budget": {"type": "string", "example": "1500.00"},
        },
    },
    "BudgetBreakdown": {
        "type": "object",
        "properties": {"planned": _MONEY, "actual": _MONEY,
                       "remaining": {**_MONEY, "description": "planned - actual (may be negative)"}},
    },
    "EventDetail": {
        "allOf": [ref("Event"), {
            "type": "object",
            "properties": {"accepted_guest_count": {"type": "integer"},
                           "budget_breakdown": ref("BudgetBreakdown")},
        }],
    },
    "EventPage": page_schema("Event"),
}

_EVENT_ID = [path_param("event_id", "Event id")]

PATHS = {
    "/api/v1/events": {
        "get": operation(
            "List the caller's events", "Events",
            {**ok("Page of events", ref("EventPage")), **error_responses(401, 422)},
            parameters=pagination_params(SORT_FIELDS, "id")),
        "post": operation(
            "Create an event", "Events",
            {**ok("Event created", ref("Event"), 201), **error_responses(401, 422)},
            request_body=json_body(ref("EventCreate"))),
    },
    "/api/v1/events/{event_id}": {
        "get": operation(
            "Get an event with guest count and budget breakdown", "Events",
            {**ok("Event detail", ref("EventDetail")), **error_responses(401, 404)}, parameters=_EVENT_ID),
        "put": operation(
            "Update an event (partial)", "Events",
            {**ok("Updated event", ref("Event")), **error_responses(401, 404, 422)},
            parameters=_EVENT_ID, request_body=json_body(ref("EventUpdate"))),
        "delete": operation(
            "Delete an event and everything nested in it", "Events",
            {**ok("Deleted", status=204), **error_responses(401, 404)}, parameters=_EVENT_ID),
    },
}
