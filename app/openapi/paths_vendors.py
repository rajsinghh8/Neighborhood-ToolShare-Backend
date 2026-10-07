"""OpenAPI fragment: vendors."""
from app.openapi.common import (error_responses, json_body, ok, operation, page_schema, pagination_params,
                                path_param, ref)

TAG = "Vendors"
_MONEY = {"type": "string", "example": "1500.00", "description": "Decimal with 2 places"}
_COLLECTION = "/api/v1/events/{event_id}/vendors"
_ITEM = "/api/v1/events/{event_id}/vendors/{vendor_id}"
_EVENT = path_param("event_id", "Event id")
_VENDOR = path_param("vendor_id", "Vendor id")

SCHEMAS = {
    "Vendor": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}, "event_id": {"type": "integer"}, "name": {"type": "string"},
            "service": {"type": "string", "nullable": True},
            "total_amount": _MONEY,
            "total_paid": {**_MONEY, "description": "Sum of all payments"},
            "totalPaid": {**_MONEY, "description": "Alias of total_paid"},
            "outstanding": {**_MONEY, "description": "total_amount - total_paid"},
        },
    },
    "VendorCreate": {
        "type": "object", "required": ["name", "total_amount"],
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 255},
            "service": {"type": "string", "maxLength": 255, "nullable": True},
            "total_amount": {"type": "string", "description": "Decimal >= 0, max 2 places (number also accepted)"},
        },
    },
    "VendorUpdate": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 255},
            "service": {"type": "string", "maxLength": 255, "nullable": True},
            "total_amount": {"type": "string", "description": "Cannot be lower than the amount already paid"},
        },
    },
    "VendorPage": page_schema("Vendor"),
}

PATHS = {
    _COLLECTION: {
        "get": operation(
            "List vendors of an event", TAG, {**ok("Page of vendors", ref("VendorPage")), **error_responses(401, 404, 422)},
            [_EVENT, *pagination_params(["name", "id"], "id")]),
        "post": operation(
            "Create a vendor", TAG,
            {**ok("Created vendor", ref("Vendor"), 201), **error_responses(401, 404, 422)},
            [_EVENT], json_body(ref("VendorCreate"))),
    },
    _ITEM: {
        "get": operation("Get vendor with total_paid and outstanding", TAG,
                         {**ok("Vendor", ref("Vendor")), **error_responses(401, 404)}, [_EVENT, _VENDOR]),
        "put": operation(
            "Update a vendor (total_amount may not drop below total paid)", TAG,
            {**ok("Updated vendor", ref("Vendor")), **error_responses(401, 404, 422)},
            [_EVENT, _VENDOR], json_body(ref("VendorUpdate"))),
        "delete": operation("Delete a vendor and its payments", TAG,
                            {**ok("Deleted", status=204), **error_responses(401, 404)}, [_EVENT, _VENDOR]),
    },
}
