from abc import abstractmethod

from ers.application.dtos import DecisionFilters, PaginatedResult
from ers.application.ports.repositories import ReadRepository, WriteRepository
from ers.domain.models import CurationDecision


class DecisionRepository(
    ReadRepository[CurationDecision, str],
    WriteRepository[CurationDecision, str],
):
    """Repository for decision persistence and querying."""

    @abstractmethod
    def find_with_filters(
        self,
        filters: DecisionFilters,
        page: int,
        per_page: int,
    ) -> PaginatedResult[CurationDecision]:
        """Find decisions matching filters with pagination."""
