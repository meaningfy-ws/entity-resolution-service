from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class ReadRepository(ABC, Generic[T, ID]):
    """Abstract read-only repository."""

    @abstractmethod
    def find_by_id(self, entity_id: ID) -> T | None:
        """Find an entity by its identifier. Returns None if not found."""


class WriteRepository(ABC, Generic[T, ID]):
    """Abstract write repository."""

    @abstractmethod
    def save(self, entity: T) -> T:
        """Persist an entity. Handles both creation and updates."""
