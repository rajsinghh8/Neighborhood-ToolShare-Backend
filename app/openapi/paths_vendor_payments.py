"""OpenAPI fragment: vendor payments."""
from app.openapi.common import (error_responses, json_body, ok, operation, page_schema, pagination_params,
                                path_param, ref)

TAG = "Vendor payments"
_COLLECTION = "/api/v1/events/{event_id}/vendors/{vendor_id}/payments"
_ITEM = _COLLECTION + "/{payment_id}"
_PARAMS = [path_param("event_id", "Event id"), path_param("vendor_id", "Vendor id")]
_PAYMENT = path_param("payment_id", "Payment id")

SCHEMAS = {
    "VendorPayment": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"}, "vendor_id": {"type": "integer"},
            "amount": {"type": "string", "example": "250.00"},
            "paid_on": {"type": "string", "format": "date"},
        },
    },
    "VendorPaymentCreate": {
        "type": "object", "required": ["amount", "paid_on"],
        "properties": {
            "amount": {"type": "string", "description": "Decimal > 0, max 2 places; sum of payments may not exceed the vendor total_amount"},
            "paid_on": {"type": "string", "format": "date"},
        },
    },
    "VendorPaymentUpdate": {
        "type": "object",
        "properties": {
            "amount": {"type": "string", "description": "Decimal > 0; re-validated against the vendor total excluding this payment"},
            "paid_on": {"type": "string", "format": "date"},
        },
    },
    "VendorPaymentPage": page_schema("VendorPayment"),
}

PATHS = {
    _COLLECTION: {
        "get": operation(
            "List payments of a vendor", TAG,
            {**ok("Page of payments", ref("VendorPaymentPage")), **error_responses(401, 404, 422)},
            [*_PARAMS, *pagination_params(["paid_on", "amount", "id"], "paid_on")]),
        "post": operation(
            "Record a payment (422 if it would exceed the vendor total_amount)", TAG,
            {**ok("Created payment", ref("VendorPayment"), 201), **error_responses(401, 404, 422)},
            _PARAMS, json_body(ref("VendorPaymentCreate"))),
    },
    _ITEM: {
        "get": operation("Get a payment", TAG,
                         {**ok("Payment", ref("VendorPayment")), **error_responses(401, 404)}, [*_PARAMS, _PAYMENT]),
        "put": operation(
            "Update a payment", TAG,
            {**ok("Updated payment", ref("VendorPayment")), **error_responses(401, 404, 422)},
            [*_PARAMS, _PAYMENT], json_body(ref("VendorPaymentUpdate"))),
        "delete": operation("Delete a payment", TAG,
                            {**ok("Deleted", status=204), **error_responses(401, 404)}, [*_PARAMS, _PAYMENT]),
    },
}
