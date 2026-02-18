from abc import ABC, abstractmethod

from ers.application.dtos import (
    CurationStatistics,
    RegistryStatistics,
    StatisticsFilters,
)


class StatisticsRepository(ABC):
    """Repository for aggregated statistics queries."""

    @abstractmethod
    async def get_curation_statistics(
        self,
        filters: StatisticsFilters,
    ) -> CurationStatistics:
        """Aggregate decision counts by status."""

    @abstractmethod
    async def get_registry_statistics(
        self,
        filters: StatisticsFilters,
    ) -> RegistryStatistics:
        """Aggregate entity mention and canonical entity counts."""
