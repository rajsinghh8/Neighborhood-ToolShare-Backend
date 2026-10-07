"""OpenAPI fragment: tasks of an event."""
from app.openapi.common import (error_responses, json_body, ok, operation, page_schema, pagination_params,
                                path_param, query_param, ref)

TAG = "Tasks"
STATUSES = ["pending", "in_progress", "completed"]
PRIORITIES = ["low", "medium", "high"]
_DATETIME = {"type": "string", "format": "date-time", "nullable": True, "example": "2030-01-01T09:00:00Z"}

SCHEMAS = {
    "Task": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}, "event_id": {"type": "integer"}, "title": {"type": "string"},
            "status": {"type": "string", "enum": STATUSES}, "priority": {"type": "string", "enum": PRIORITIES},
            "due_at": _DATETIME, "depends_on_task_id": {"type": "integer", "nullable": True},
        },
    },
    "TaskCreate": {
        "type": "object", "required": ["title"],
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 255},
            "status": {"type": "string", "enum": STATUSES, "default": "pending"},
            "priority": {"type": "string", "enum": PRIORITIES, "default": "medium"},
            "due_at": _DATETIME,
            "depends_on_task_id": {"type": "integer", "nullable": True,
                                   "description": "Task of the same event; no self reference or cycles"},
        },
    },
    "TaskUpdate": {
        "type": "object",
        "description": "Only provided fields change. Status transitions: pending->in_progress, "
                       "in_progress->pending|completed, completed->in_progress.",
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 255},
            "status": {"type": "string", "enum": STATUSES},
            "priority": {"type": "string", "enum": PRIORITIES},
            "due_at": _DATETIME,
            "depends_on_task_id": {"type": "integer", "nullable": True},
        },
    },
    "TaskPage": page_schema("Task"),
}

_EVENT = path_param("event_id", "Event id")
_TASK = path_param("task_id", "Task id")
_SORTS = ["due_at", "priority", "status", "id"]

PATHS = {
    "/api/v1/events/{event_id}/tasks": {
        "get": operation(
            "List tasks of an event", TAG, {**ok("Page of tasks", ref("TaskPage")), **error_responses(401, 404, 422)},
            parameters=[_EVENT, *pagination_params(_SORTS, "id"),
                        query_param("status", {"type": "string", "enum": STATUSES}, "Filter by status"),
                        query_param("priority", {"type": "string", "enum": PRIORITIES}, "Filter by priority")]),
        "post": operation(
            "Create a task", TAG, {**ok("Task created", ref("Task"), 201), **error_responses(401, 404, 422)},
            parameters=[_EVENT], request_body=json_body(ref("TaskCreate"))),
    },
    "/api/v1/events/{event_id}/tasks/{task_id}": {
        "get": operation("Get a task", TAG, {**ok("Task", ref("Task")), **error_responses(401, 404)},
                         parameters=[_EVENT, _TASK]),
        "put": operation("Update a task", TAG, {**ok("Updated task", ref("Task")), **error_responses(401, 404, 422)},
                         parameters=[_EVENT, _TASK], request_body=json_body(ref("TaskUpdate"))),
        "patch": operation("Partially update a task", TAG,
                           {**ok("Updated task", ref("Task")), **error_responses(401, 404, 422)},
                           parameters=[_EVENT, _TASK], request_body=json_body(ref("TaskUpdate"))),
        "delete": operation("Delete a task (dependents lose their dependency)", TAG,
                            {**ok("Deleted", status=204), **error_responses(401, 404)},
                            parameters=[_EVENT, _TASK]),
    },
}
