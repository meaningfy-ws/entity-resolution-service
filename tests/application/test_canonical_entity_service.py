from unittest.mock import MagicMock, create_autospec

import pytest

from ers.application.dtos import (
    CanonicalEntityPreview,
    PaginatedResult,
    PaginationParams,
)
from ers.application.exceptions import NotFoundError
from ers.application.ports.canonical_entity_repository import (
    CanonicalEntityRepository,
)
from ers.application.ports.decision_repository import DecisionRepository
from ers.application.ports.entity_mention_repository import EntityMentionRepository
from ers.application.services.canonical_entity_service import CanonicalEntityService
from tests.factories import (
    CanonicalEntityIdentifierFactory,
    ClusterReferenceFactory,
    CurationDecisionFactory,
    EntityMentionFactory,
    EntityMentionIdentifierFactory,
)


@pytest.fixture
def decision_repository() -> MagicMock:
    return create_autospec(DecisionRepository, instance=True)


@pytest.fixture
def canonical_entity_repository() -> MagicMock:
    return create_autospec(CanonicalEntityRepository, instance=True)


@pytest.fixture
def entity_mention_repository() -> MagicMock:
    return create_autospec(EntityMentionRepository, instance=True)


@pytest.fixture
def service(
    decision_repository: MagicMock,
    canonical_entity_repository: MagicMock,
    entity_mention_repository: MagicMock,
) -> CanonicalEntityService:
    return CanonicalEntityService(
        decision_repository=decision_repository,
        canonical_entity_repository=canonical_entity_repository,
        entity_mention_repository=entity_mention_repository,
    )


class TestGetProposedCanonicalEntity:
    async def test_returns_preview_with_embedded_entities(
        self,
        service: CanonicalEntityService,
        decision_repository: MagicMock,
        canonical_entity_repository: MagicMock,
        entity_mention_repository: MagicMock,
    ) -> None:
        member_ids = EntityMentionIdentifierFactory.batch(3)
        decision = CurationDecisionFactory.build()
        canonical = CanonicalEntityIdentifierFactory.build(
            identifier=decision.accepted_candidate.cluster_id,
            equivalent_to=member_ids,
        )
        mentions = [EntityMentionFactory.build(identifier=mid) for mid in member_ids]

        decision_repository.find_by_id.return_value = decision
        canonical_entity_repository.find_by_id.return_value = canonical
        entity_mention_repository.find_by_identifiers.return_value = mentions

        result = await service.get_proposed_canonical_entity(decision.id)

        assert isinstance(result, CanonicalEntityPreview)
        assert result.cluster_id == decision.accepted_candidate.cluster_id
        assert result.confidence_score == decision.accepted_candidate.confidence_score
        assert len(result.top_entities) == 3

    async def test_decision_not_found_raises_error(
        self,
        service: CanonicalEntityService,
        decision_repository: MagicMock,
    ) -> None:
        decision_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_proposed_canonical_entity("nonexistent")

        assert exc_info.value.entity_type == "Decision"

    async def test_canonical_entity_not_found_raises_error(
        self,
        service: CanonicalEntityService,
        decision_repository: MagicMock,
        canonical_entity_repository: MagicMock,
    ) -> None:
        decision = CurationDecisionFactory.build()
        decision_repository.find_by_id.return_value = decision
        canonical_entity_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_proposed_canonical_entity(decision.id)

        assert exc_info.value.entity_type == "CanonicalEntity"


class TestGetAlternativeCanonicalEntities:
    async def test_returns_paginated_alternatives(
        self,
        service: CanonicalEntityService,
        decision_repository: MagicMock,
        entity_mention_repository: MagicMock,
    ) -> None:
        accepted = ClusterReferenceFactory.build(confidence_score=0.9)
        alt1 = ClusterReferenceFactory.build(confidence_score=0.7)
        alt2 = ClusterReferenceFactory.build(confidence_score=0.5)
        decision = CurationDecisionFactory.build(
            accepted_candidate=accepted,
            candidates=[accepted, alt1, alt2],
        )
        decision_repository.find_by_id.return_value = decision

        entity_mention_repository.find_by_identifiers.return_value = (
            EntityMentionFactory.batch(2)
        )

        result = await service.get_alternative_canonical_entities(
            decision.id,
            pagination=PaginationParams(page=1, per_page=10),
        )

        assert isinstance(result, PaginatedResult)
        assert result.count == 2
        assert len(result.results) == 2
        assert result.next is None
        assert result.previous is None

    async def test_excludes_accepted_candidate(
        self,
        service: CanonicalEntityService,
        decision_repository: MagicMock,
        canonical_entity_repository: MagicMock,
        entity_mention_repository: MagicMock,
    ) -> None:
        accepted = ClusterReferenceFactory.build(confidence_score=0.9)
        alt = ClusterReferenceFactory.build(confidence_score=0.6)
        decision = CurationDecisionFactory.build(
            accepted_candidate=accepted,
            candidates=[accepted, alt],
        )
        decision_repository.find_by_id.return_value = decision

        canonical = CanonicalEntityIdentifierFactory.build(
            identifier=alt.cluster_id,
        )
        canonical_entity_repository.find_by_id.return_value = canonical
        entity_mention_repository.find_by_identifiers.return_value = (
            EntityMentionFactory.batch(2)
        )

        result = await service.get_alternative_canonical_entities(
            decision.id,
            pagination=PaginationParams(page=1, per_page=10),
        )

        assert result.count == 1
        assert result.results[0].cluster_id == alt.cluster_id

    async def test_pagination_returns_correct_page(
        self,
        service: CanonicalEntityService,
        decision_repository: MagicMock,
        canonical_entity_repository: MagicMock,
        entity_mention_repository: MagicMock,
    ) -> None:
        accepted = ClusterReferenceFactory.build(confidence_score=0.95)
        alternatives = ClusterReferenceFactory.batch(5)
        decision = CurationDecisionFactory.build(
            accepted_candidate=accepted,
            candidates=[accepted, *alternatives],
        )
        decision_repository.find_by_id.return_value = decision

        for alt in alternatives:
            canonical_entity_repository.find_by_id.return_value = (
                CanonicalEntityIdentifierFactory.build(identifier=alt.cluster_id)
            )
        entity_mention_repository.find_by_identifiers.return_value = (
            EntityMentionFactory.batch(2)
        )

        result = await service.get_alternative_canonical_entities(
            decision.id,
            pagination=PaginationParams(page=1, per_page=2),
        )

        assert result.count == 5
        assert len(result.results) == 2
        assert result.next == 2
        assert result.previous is None

    async def test_decision_not_found_raises_error(
        self,
        service: CanonicalEntityService,
        decision_repository: MagicMock,
    ) -> None:
        decision_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_alternative_canonical_entities(
                "nonexistent",
                pagination=PaginationParams(),
            )
