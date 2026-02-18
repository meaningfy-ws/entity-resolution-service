from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from erspec.models.core import (
    ClusterReference,
    DecisionStatus,
    EntityMentionIdentifier,
    EntityType,
)

T = TypeVar("T")

MAX_PER_PAGE = 50
DEFAULT_PER_PAGE = 20


class FrozenDTO(BaseModel):
    """Base model for all application-layer DTOs."""

    model_config = ConfigDict(frozen=True)


class PaginationParams(FrozenDTO):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE)


class PaginatedResult(FrozenDTO, Generic[T]):
    """Paginated query result."""

    count: int
    previous: int | None = None
    next: int | None = None
    results: list[T]


class DecisionFilters(FrozenDTO):
    """Filtering criteria for decision queries."""

    status: DecisionStatus | None = None
    entity_type: str | None = None
    confidence_min: float | None
    confidence_max: float | None
    search: str | None = None
    ordering: str | None = None


class StatisticsFilters(FrozenDTO):
    """Filtering criteria for statistics queries."""

    entity_type: EntityType | None = None
    timeframe_start: datetime | None = None
    timeframe_end: datetime | None = None


class EntityMentionPreview(FrozenDTO):
    """Lightweight entity mention projection for display."""

    identifier: EntityMentionIdentifier
    parsed_representation: str | None = None


class DecisionSummary(FrozenDTO):
    """Decision summary for list display."""

    id: str
    status: DecisionStatus
    about_entity_mention: EntityMentionPreview
    accepted_candidate: ClusterReference
    created_at: datetime


class CanonicalEntityPreview(FrozenDTO):
    """Cluster preview with top entity mentions for display."""

    cluster_id: str
    confidence_score: float
    top_entities: list[EntityMentionPreview]


class CurationStatistics(FrozenDTO):
    """Statistics about the curation process."""

    total_decisions: int
    pending_review: int
    manually_reviewed: int
    automatic_confident: int


class RegistryStatistics(FrozenDTO):
    """Statistics about the entity registry."""

    total_entity_mentions: int
    total_canonical_entities: int
    average_cluster_size: float
    resolution_requests: int


class Statistics(FrozenDTO):
    """Aggregated statistics for the curation dashboard."""

    registry: RegistryStatistics
    curation: CurationStatistics


class ExecutionAcknowledgement(FrozenDTO):
    """Response confirming successful execution of a curation action."""

    success: bool
    message: str | None = None


class AssignRequest(FrozenDTO):
    """Request body for assigning an entity to an alternative cluster."""

    cluster_id: str
