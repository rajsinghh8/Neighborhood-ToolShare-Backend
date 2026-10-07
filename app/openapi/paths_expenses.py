"""OpenAPI fragment: expenses."""
from app.openapi.common import (error_responses, json_body, ok, operation, page_schema, pagination_params,
                                path_param, query_param, ref)

TAG = "Expenses"
_SORT = ["incurred_on", "amount", "id"]
_DATE = {"type": "string", "format": "date"}

SCHEMAS = {
    "Expense": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}, "event_id": {"type": "integer"}, "category_id": {"type": "integer"},
            "description": {"type": "string"},
            "amount": {"type": "string", "example": "42.50", "description": "Decimal with 2 places"},
            "incurred_on": _DATE,
        },
    },
    "ExpenseCreate": {
        "type": "object", "required": ["category_id", "description", "amount", "incurred_on"],
        "properties": {
            "category_id": {"type": "integer", "description": "Must belong to the same event (else 422)"},
            "description": {"type": "string", "minLength": 1, "maxLength": 500},
            "amount": {"type": "number", "exclusiveMinimum": 0, "description": "Number or string, max 2 decimals"},
            "incurred_on": _DATE,
        },
    },
    "ExpenseUpdate": {
        "type": "object",
        "properties": {
            "category_id": {"type": "integer"}, "description": {"type": "string", "maxLength": 500},
            "amount": {"type": "number", "exclusiveMinimum": 0}, "incurred_on": _DATE,
        },
    },
    "ExpensePage": page_schema("Expense"),
}

_EVENT = path_param("event_id", "Event id")
_EXPENSE = path_param("expense_id", "Expense id")

PATHS = {
    "/api/v1/events/{event_id}/expenses": {
        "get": operation("List expenses of an event", TAG,
                         {**ok("Page of expenses", ref("ExpensePage")), **error_responses(401, 404, 422)},
                         [_EVENT, *pagination_params(_SORT, "incurred_on"),
                          query_param("startDate", _DATE, "incurred_on >= startDate (inclusive)"),
                          query_param("endDate", _DATE, "incurred_on <= endDate (inclusive); startDate > endDate -> 422")]),
        "post": operation("Create an expense", TAG,
                          {**ok("Created", ref("Expense"), 201), **error_responses(401, 404, 422)},
                          [_EVENT], json_body(ref("ExpenseCreate"))),
    },
    "/api/v1/events/{event_id}/expenses/{expense_id}": {
        "get": operation("Get an expense", TAG, {**ok("Expense", ref("Expense")), **error_responses(401, 404)},
                         [_EVENT, _EXPENSE]),
        "put": operation("Update an expense (only sent fields change)", TAG,
                         {**ok("Updated", ref("Expense")), **error_responses(401, 404, 422)},
                         [_EVENT, _EXPENSE], json_body(ref("ExpenseUpdate"))),
        "delete": operation("Delete an expense", TAG,
                            {**ok("Deleted", None, 204), **error_responses(401, 404)}, [_EVENT, _EXPENSE]),
    },
}
