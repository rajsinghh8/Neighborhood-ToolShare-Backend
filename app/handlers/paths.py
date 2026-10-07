"""URL pattern building blocks shared by every handler module."""
API_PREFIX = "/api/v1"
ID = r"\d{1,9}"

EVENT_BASE = API_PREFIX + r"/events/(?P<event_id>" + ID + ")"
VENDOR_BASE = EVENT_BASE + r"/vendors/(?P<vendor_id>" + ID + ")"
