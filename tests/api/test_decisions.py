from datetime import datetime, timezone
from unittest.mock import AsyncMock

from httpx import AsyncClient

from erspec.models.core import DecisionStatus
from ers.application.dtos import (
    CanonicalEntityPreview,
    DecisionSummary,
    EntityMentionPreview,
    PaginatedResult,
)
from ers.application.exceptions import NotFoundError
from ers.domain.exceptions import InvalidClusterError, InvalidStateTransitionError
from tests.factories import (
    ClusterReferenceFactory,
    EntityMentionIdentifierFactory,
)

BASE_URL = "/api/v1/curation/decisions"


class TestListDecisions:
    async def test_returns_paginated_results(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        identifier = EntityMentionIdentifierFactory.build()
        summary = DecisionSummary(
            id="decision-1",
            status=DecisionStatus.PENDING_MANUAL_REVIEW,
            about_entity_mention=EntityMentionPreview(
                identifier=identifier,
                parsed_representation="Example",
            ),
            accepted_candidate=ClusterReferenceFactory.build(),
            created_at=datetime.now(timezone.utc),
        )
        decision_curation_service.list_decisions.return_value = PaginatedResult(
            count=1, previous=None, next=None, results=[summary]
        )

        response = await client.get(BASE_URL)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == "decision-1"

    async def test_returns_empty_list(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.list_decisions.return_value = PaginatedResult(
            count=0, previous=None, next=None, results=[]
        )

        response = await client.get(BASE_URL)

        assert response.status_code == 200
        assert response.json()["count"] == 0
        assert response.json()["results"] == []

    async def test_passes_query_params_to_service(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.list_decisions.return_value = PaginatedResult(
            count=0, previous=None, next=None, results=[]
        )

        await client.get(
            BASE_URL,
            params={
                "status": "PENDING_MANUAL_REVIEW",
                "page": 2,
                "per_page": 10,
            },
        )

        call_args = decision_curation_service.list_decisions.call_args
        filters = call_args.kwargs["filters"]
        pagination = call_args.kwargs["pagination"]
        assert filters.status == DecisionStatus.PENDING_MANUAL_REVIEW
        assert pagination.page == 2
        assert pagination.per_page == 10


class TestAcceptDecision:
    async def test_accept_returns_acknowledgement(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.accept_decision.return_value = None

        response = await client.post(f"{BASE_URL}/decision-1/accept")

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_accept_not_found(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.accept_decision.side_effect = NotFoundError(
            "Decision", "decision-1"
        )

        response = await client.post(f"{BASE_URL}/decision-1/accept")

        assert response.status_code == 404

    async def test_accept_invalid_state(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.accept_decision.side_effect = (
            InvalidStateTransitionError(
                current_status="MANUALLY_REVIEWED",
                attempted_action="ACCEPT_TOP",
            )
        )

        response = await client.post(f"{BASE_URL}/decision-1/accept")

        assert response.status_code == 409


class TestRejectDecision:
    async def test_reject_returns_acknowledgement(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.reject_decision.return_value = None

        response = await client.post(f"{BASE_URL}/decision-1/reject")

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_reject_not_found(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.reject_decision.side_effect = NotFoundError(
            "Decision", "decision-1"
        )

        response = await client.post(f"{BASE_URL}/decision-1/reject")

        assert response.status_code == 404


class TestAssignDecision:
    async def test_assign_returns_acknowledgement(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.assign_decision.return_value = None

        response = await client.post(
            f"{BASE_URL}/decision-1/assign",
            json={"cluster_id": "cluster-abc"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        decision_curation_service.assign_decision.assert_called_once_with(
            "decision-1", cluster_id="cluster-abc", actor="anonymous"
        )

    async def test_assign_invalid_cluster(
        self,
        client: AsyncClient,
        decision_curation_service: AsyncMock,
    ) -> None:
        decision_curation_service.assign_decision.side_effect = InvalidClusterError(
            "cluster-bad", "decision-1"
        )

        response = await client.post(
            f"{BASE_URL}/decision-1/assign",
            json={"cluster_id": "cluster-bad"},
        )

        assert response.status_code == 422


class TestGetProposedCanonicalEntity:
    async def test_returns_proposed_entity(
        self,
        client: AsyncClient,
        canonical_entity_service: AsyncMock,
    ) -> None:
        preview = CanonicalEntityPreview(
            cluster_id="cluster-1",
            confidence_score=0.95,
            top_entities=[],
        )
        canonical_entity_service.get_proposed_canonical_entity.return_value = preview

        response = await client.get(f"{BASE_URL}/decision-1/proposed-canonical-entity")

        assert response.status_code == 200
        data = response.json()
        assert data["cluster_id"] == "cluster-1"
        assert data["confidence_score"] == 0.95

    async def test_not_found(
        self,
        client: AsyncClient,
        canonical_entity_service: AsyncMock,
    ) -> None:
        canonical_entity_service.get_proposed_canonical_entity.side_effect = (
            NotFoundError("Decision", "decision-1")
        )

        response = await client.get(f"{BASE_URL}/decision-1/proposed-canonical-entity")

        assert response.status_code == 404


class TestGetAlternativeCanonicalEntities:
    async def test_returns_paginated_alternatives(
        self,
        client: AsyncClient,
        canonical_entity_service: AsyncMock,
    ) -> None:
        preview = CanonicalEntityPreview(
            cluster_id="cluster-2",
            confidence_score=0.7,
            top_entities=[],
        )
        canonical_entity_service.get_alternative_canonical_entities.return_value = (
            PaginatedResult(count=1, previous=None, next=None, results=[preview])
        )

        response = await client.get(
            f"{BASE_URL}/decision-1/alternative-canonical-entities"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["cluster_id"] == "cluster-2"
