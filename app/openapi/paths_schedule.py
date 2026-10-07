"""OpenAPI fragment: schedule items."""
from app.openapi.common import (error_responses, json_body, ok, operation, page_schema, pagination_params,
                                path_param, query_param, ref)

TAG = "Schedule items"
BASE = "/api/v1/events/{event_id}/schedule-items"
ITEM = BASE + "/{item_id}"

_DATE = {"type": "string", "format": "date"}
_EVENT = path_param("event_id", "Event id")
_ITEM = path_param("item_id", "Schedule item id")

SCHEMAS = {
    "ScheduleItem": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}, "event_id": {"type": "integer"}, "title": {"type": "string"},
            "start_at": {"type": "string", "format": "date-time"},
            "end_at": {"type": "string", "format": "date-time"},
        },
    },
    "ScheduleItemCreate": {
        "type": "object", "required": ["title", "start_at", "end_at"],
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 255},
            "start_at": {"type": "string", "format": "date-time"},
            "end_at": {"type": "string", "format": "date-time", "description": "Must be after start_at"},
        },
    },
    "ScheduleItemUpdate": {
        "type": "object",
        "description": "Partial update; only provided fields change. The merged range must be valid and "
                       "must not overlap other items of the event.",
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 255},
            "start_at": {"type": "string", "format": "date-time"},
            "end_at": {"type": "string", "format": "date-time"},
        },
    },
    "ScheduleItemPage": page_schema("ScheduleItem"),
}

PATHS = {
    BASE: {
        "get": operation(
            "List schedule items of an event", TAG,
            {**ok("Page of schedule items", ref("ScheduleItemPage")), **error_responses(401, 404, 422)},
            [_EVENT, *pagination_params(["start_at", "id"], "start_at"),
             query_param("startDate", _DATE, "Only items whose start_at date is on/after this date"),
             query_param("endDate", _DATE, "Only items whose start_at date is on/before this date")]),
        "post": operation(
            "Create a schedule item", TAG,
            {**ok("Created", ref("ScheduleItem"), 201), **error_responses(401, 404, 422)},
            [_EVENT], json_body(ref("ScheduleItemCreate"))),
    },
    ITEM: {
        "get": operation("Get a schedule item", TAG,
                         {**ok("Schedule item", ref("ScheduleItem")), **error_responses(401, 404)},
                         [_EVENT, _ITEM]),
        "put": operation("Update a schedule item", TAG,
                         {**ok("Updated", ref("ScheduleItem")), **error_responses(401, 404, 422)},
                         [_EVENT, _ITEM], json_body(ref("ScheduleItemUpdate"))),
        "patch": operation("Partially update a schedule item", TAG,
                           {**ok("Updated", ref("ScheduleItem")), **error_responses(401, 404, 422)},
                           [_EVENT, _ITEM], json_body(ref("ScheduleItemUpdate"))),
        "delete": operation("Delete a schedule item", TAG,
                            {**ok("Deleted", None, 204), **error_responses(401, 404)},
                            [_EVENT, _ITEM]),
    },
}
