from dataclasses import dataclass
from typing import Generic, TypeVar

from erspec.models.core import DecisionStatus

T = TypeVar("T")


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    """Paginated query result."""

    count: int
    previous: int | None
    next: int | None
    results: list[T]


@dataclass(frozen=True)
class DecisionFilters:
    """Filtering criteria for decision queries."""

    status: DecisionStatus | None = None
    entity_type: str | None = None
