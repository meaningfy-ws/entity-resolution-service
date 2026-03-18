"""Step definitions for canonical_entity_preview.feature.

Tests the proposed and alternative canonical entity endpoints through
the FastAPI test client with mocked CanonicalEntityService.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from pytest_bdd import given, parsers, scenario, then, when
from starlette.testclient import TestClient

from ers.commons.domain.data_transfer_objects import PaginatedResult
from ers.commons.services.exceptions import NotFoundError
from ers.curation.domain.data_transfer_objects import (
    CanonicalEntityPreview,
    EntityMentionPreview,
)
from tests.unit.factories import EntityMentionIdentifierFactory

FEATURE = str(Path(__file__).resolve().parent / "canonical_entity_preview.feature")

DECISIONS_URL = "/api/v1/curation/decisions"


# ---------------------------------------------------------------------------
# Scenario bindings
# ---------------------------------------------------------------------------


@scenario(FEATURE, "View the proposed canonical entity for a decision")
def test_proposed_entity():
    pass


@scenario(FEATURE, "Proposed canonical entity for a non-existent decision")
def test_proposed_not_found():
    pass


@scenario(FEATURE, "View alternative canonical entities for a decision")
def test_alternatives():
    pass


@scenario(FEATURE, "Alternative canonical entities with pagination")
def test_alternatives_paginated():
    pass


@scenario(FEATURE, "Decision with no alternative candidates")
def test_no_alternatives():
    pass


@scenario(FEATURE, "Alternative canonical entities for a non-existent decision")
def test_alternatives_not_found():
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_preview(cluster_id: str, n_entities: int = 3) -> CanonicalEntityPreview:
    return CanonicalEntityPreview(
        cluster_id=cluster_id,
        confidence_score=0.9,
        similarity_score=0.85,
        top_entities=[
            EntityMentionPreview(
                identified_by=EntityMentionIdentifierFactory.build(),
                parsed_representation='{"name": "Entity"}',
            )
            for _ in range(n_entities)
        ],
    )


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------


@given(
    parsers.parse('a decision exists with a current placement in cluster "{cluster_id}"'),
)
def decision_with_placement(
    ctx: dict[str, Any],
    cluster_id: str,
    canonical_entity_service: AsyncMock,
) -> None:
    ctx["decision_id"] = "decision-1"
    ctx["cluster_id"] = cluster_id


@given(parsers.parse('cluster "{cluster_id}" contains {count:d} entity mentions'))
def cluster_has_mentions(
    ctx: dict[str, Any],
    cluster_id: str,
    count: int,
    canonical_entity_service: AsyncMock,
) -> None:
    preview = _make_preview(cluster_id, min(count, 5))
    canonical_entity_service.get_proposed_canonical_entity.return_value = preview


@given(parsers.parse("a decision exists with {count:d} candidate clusters"))
def decision_with_n_candidates(
    ctx: dict[str, Any],
    count: int,
    canonical_entity_service: AsyncMock,
) -> None:
    ctx["decision_id"] = "decision-1"
    ctx["candidate_count"] = count
    alternatives = [_make_preview(f"cluster-{i}") for i in range(1, count)]
    canonical_entity_service.get_alternative_canonical_entities.return_value = PaginatedResult(
        count=count - 1,
        results=alternatives,
    )


@given("the current placement is in the first candidate")
def current_is_first() -> None:
    pass


@given(
    parsers.parse("a decision exists with {count:d} candidate clusters including the current"),
)
def decision_with_candidates_and_current(
    ctx: dict[str, Any],
    count: int,
    canonical_entity_service: AsyncMock,
) -> None:
    ctx["decision_id"] = "decision-1"
    ctx["candidate_count"] = count


@given(
    "a decision exists with only 1 candidate cluster (the current placement)",
)
def decision_single_candidate(
    ctx: dict[str, Any],
    canonical_entity_service: AsyncMock,
) -> None:
    ctx["decision_id"] = "decision-1"
    canonical_entity_service.get_alternative_canonical_entities.return_value = PaginatedResult(
        count=0,
        results=[],
    )


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------


@when("the curator requests the proposed canonical entity", target_fixture="response")
def request_proposed(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    return client.get(
        f"{DECISIONS_URL}/{ctx['decision_id']}/proposed-canonical-entity",
    )


@when(
    "the curator requests the proposed canonical entity for a non-existent decision",
    target_fixture="response",
)
def request_proposed_not_found(
    client: TestClient,
    canonical_entity_service: AsyncMock,
) -> Any:
    canonical_entity_service.get_proposed_canonical_entity.side_effect = NotFoundError(
        "Decision",
        "nonexistent",
    )
    return client.get(
        f"{DECISIONS_URL}/nonexistent/proposed-canonical-entity",
    )


@when(
    "the curator requests alternative canonical entities",
    target_fixture="response",
)
def request_alternatives(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    return client.get(
        f"{DECISIONS_URL}/{ctx['decision_id']}/alternative-canonical-entities",
    )


@when(
    parsers.parse(
        "the curator requests alternative canonical entities for page {page:d} "
        "with {per_page:d} items per page"
    ),
    target_fixture="response",
)
def request_alternatives_paginated(
    client: TestClient,
    ctx: dict[str, Any],
    page: int,
    per_page: int,
    canonical_entity_service: AsyncMock,
) -> Any:
    alternatives = [_make_preview(f"cluster-{i}") for i in range(per_page)]
    total = ctx.get("candidate_count", 6) - 1
    canonical_entity_service.get_alternative_canonical_entities.return_value = PaginatedResult(
        count=total,
        next=page + 1 if page * per_page < total else None,
        results=alternatives,
    )
    return client.get(
        f"{DECISIONS_URL}/{ctx['decision_id']}/alternative-canonical-entities",
        params={"page": page, "per_page": per_page},
    )


@when(
    "the curator requests alternative canonical entities for a non-existent decision",
    target_fixture="response",
)
def request_alternatives_not_found(
    client: TestClient,
    canonical_entity_service: AsyncMock,
) -> Any:
    canonical_entity_service.get_alternative_canonical_entities.side_effect = NotFoundError(
        "Decision",
        "nonexistent",
    )
    return client.get(
        f"{DECISIONS_URL}/nonexistent/alternative-canonical-entities",
    )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


@then(parsers.parse('a preview is returned for cluster "{cluster_id}"'))
def preview_returned(response: Any, cluster_id: str) -> None:
    assert response.status_code == 200
    assert response.json()["cluster_id"] == cluster_id


@then(
    parsers.parse("the preview includes up to {limit:d} top entity mentions from the cluster"),
)
def preview_has_entities(response: Any, limit: int) -> None:
    entities = response.json()["top_entities"]
    assert len(entities) <= limit
    assert len(entities) > 0


@then(parsers.parse("{count:d} alternative entity previews are returned"))
def n_alternatives_returned(response: Any, count: int) -> None:
    assert response.status_code == 200
    assert len(response.json()["results"]) == count


@then("each preview includes the cluster identifier and top entity mentions")
def alternative_preview_fields(response: Any) -> None:
    for item in response.json()["results"]:
        assert "cluster_id" in item
        assert "top_entities" in item


@then(parsers.parse("{count:d} alternative previews are returned"))
def n_alt_previews_returned(response: Any, count: int) -> None:
    assert response.status_code == 200
    assert len(response.json()["results"]) == count


@then("a next page indicator is present")
def next_page_present(response: Any) -> None:
    assert response.json()["next"] is not None


@then("an empty result set is returned")
def empty_results(response: Any) -> None:
    assert response.status_code == 200
    assert response.json()["results"] == []


@then("the system responds with a not found error")
def not_found(response: Any) -> None:
    assert response.status_code == 404
