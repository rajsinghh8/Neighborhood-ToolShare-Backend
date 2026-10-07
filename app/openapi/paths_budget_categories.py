"""OpenAPI fragment: budget categories."""
from app.openapi.common import (error_responses, json_body, ok, operation, page_schema, pagination_params,
                                path_param, ref)

TAG = "Budget categories"
_MONEY = {"type": "string", "example": "250.00", "description": "Decimal with 2 places"}
_SORT = ["id", "name", "planned_amount"]

SCHEMAS = {
    "BudgetCategory": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}, "event_id": {"type": "integer"}, "name": {"type": "string"},
            "planned_amount": _MONEY, "actual_amount": _MONEY,
            "remaining_amount": {**_MONEY, "description": "planned_amount - actual_amount (may be negative)"},
        },
    },
    "BudgetCategoryCreate": {
        "type": "object", "required": ["name", "planned_amount"],
        "properties": {"name": {"type": "string", "minLength": 1, "maxLength": 255},
                       "planned_amount": {"type": "number", "minimum": 0, "description": "Number or string, max 2 decimals"}},
    },
    "BudgetCategoryUpdate": {
        "type": "object",
        "properties": {"name": {"type": "string", "minLength": 1, "maxLength": 255},
                       "planned_amount": {"type": "number", "minimum": 0}},
    },
    "BudgetCategoryPage": page_schema("BudgetCategory"),
}

_EVENT = path_param("event_id", "Event id")
_CATEGORY = path_param("category_id", "Budget category id")

PATHS = {
    "/api/v1/events/{event_id}/budget-categories": {
        "get": operation("List budget categories of an event", TAG,
                         {**ok("Page of categories", ref("BudgetCategoryPage")), **error_responses(401, 404, 422)},
                         [_EVENT, *pagination_params(_SORT, "id")]),
        "post": operation("Create a budget category", TAG,
                          {**ok("Created", ref("BudgetCategory"), 201), **error_responses(401, 404, 422)},
                          [_EVENT], json_body(ref("BudgetCategoryCreate"))),
    },
    "/api/v1/events/{event_id}/budget-categories/{category_id}": {
        "get": operation("Get a budget category with actual and remaining amounts", TAG,
                         {**ok("Category", ref("BudgetCategory")), **error_responses(401, 404)},
                         [_EVENT, _CATEGORY]),
        "put": operation("Update a budget category (only sent fields change)", TAG,
                         {**ok("Updated", ref("BudgetCategory")), **error_responses(401, 404, 422)},
                         [_EVENT, _CATEGORY], json_body(ref("BudgetCategoryUpdate"))),
        "delete": operation("Delete a budget category and its expenses", TAG,
                            {**ok("Deleted", None, 204), **error_responses(401, 404)}, [_EVENT, _CATEGORY]),
    },
}
