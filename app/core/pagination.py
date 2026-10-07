"""Offset pagination primitives shared by every list endpoint."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")

SORT_ASC = "asc"
SORT_DESC = "desc"


@dataclass(frozen=True)
class PageRequest:
    """Validated pagination + sort request.

    ``page`` is 1-based. ``offset`` is derived from ``page`` and ``size`` unless
    the client passed an explicit ``offset`` query param.
    """

    page: int
    size: int
    offset: int
    sort_by: str
    sort_dir: str = SORT_ASC


@dataclass(frozen=True)
class Page(Generic[T]):
    """One page of results plus the total row count (from a separate count query)."""

    items: Sequence[T]
    total: int
    request: PageRequest
    extra: dict = field(default_factory=dict)

    def to_envelope(self, serialized_items: list) -> dict:
        return {
            "items": serialized_items,
            "total": self.total,
            "page": self.request.page,
            "size": self.request.size,
            "limit": self.request.size,
            "offset": self.request.offset,
        }
