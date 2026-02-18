from abc import abstractmethod

from ers.application.dtos import DecisionFilters, PaginatedResult, PaginationParams
from ers.application.ports.repositories import AsyncReadRepository, AsyncWriteRepository
from ers.domain.models import CurationDecision


class DecisionRepository(
    AsyncReadRepository[CurationDecision, str],
    AsyncWriteRepository[CurationDecision, str],
):
    """Repository for decision persistence and querying."""

    @abstractmethod
    async def find_with_filters(
        self,
        filters: DecisionFilters,
        pagination: PaginationParams,
    ) -> PaginatedResult[CurationDecision]:
        """Find decisions matching filters with pagination."""
