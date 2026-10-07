"""Domain events published to Kafka after a transaction commits."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    """Immutable message: topic + key + JSON payload."""

    topic: str
    key: str
    event_type: str
    payload: dict[str, Any]
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json_bytes(self) -> bytes:
        body = {"event_type": self.event_type, "occurred_at": self.occurred_at, "payload": self.payload}
        return json.dumps(body, default=str).encode("utf-8")
