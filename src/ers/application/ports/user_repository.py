from abc import abstractmethod

from ers.application.ports.repositories import AsyncReadRepository, AsyncWriteRepository
from ers.domain.user import User


class UserRepository(AsyncReadRepository[User, str], AsyncWriteRepository[User, str]):
    """Port for user persistence operations."""

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Find a user by email address. Returns None if not found."""

    @abstractmethod
    async def find_all(self) -> list[User]:
        """Return all users."""

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user by id. Returns True if deleted, False if not found."""
