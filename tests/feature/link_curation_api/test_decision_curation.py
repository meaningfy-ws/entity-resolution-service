"""Step definitions for decision_curation.feature.

Tests the decision detail view and POST accept/reject/assign endpoints through
the FastAPI test client.  Repository mocks let real DecisionCurationService +
UserActionService logic run end-to-end.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from pytest_bdd import given, parsers, scenario, then, when
from starlette.testclient import TestClient

from tests.unit.factories import ClusterReferenceFactory, DecisionFactory

FEATURE = str(Path(__file__).resolve().parent / "decision_curation.feature")

DECISIONS_URL = "/api/v1/curation/decisions"


# ---------------------------------------------------------------------------
# Scenario bindings
# ---------------------------------------------------------------------------


# --- View decision ---


@scenario(FEATURE, "View full details of a resolution decision")
def test_view_decision():
    pass


@scenario(FEATURE, "View details of a non-existent decision")
def test_view_decision_not_found():
    pass


# --- Recommend top candidate ---


@scenario(FEATURE, "Recommend placement of the top candidate for a decision")
def test_recommend_top():
    pass


@scenario(FEATURE, "Recommend top candidate for a non-existent decision")
def test_recommend_top_not_found():
    pass


@scenario(FEATURE, "Recommend top candidate for a decision already curated on its current version")
def test_recommend_top_already_curated():
    pass


# --- Recommend rejection ---


@scenario(FEATURE, "Recommend rejection of all candidates for a decision")
def test_recommend_rejection():
    pass


@scenario(FEATURE, "Recommend rejection for a non-existent decision")
def test_recommend_rejection_not_found():
    pass


# --- Recommend alternative cluster ---


@scenario(FEATURE, "Recommend placement in an alternative cluster")
def test_recommend_alternative():
    pass


@scenario(FEATURE, "Recommend a cluster that is not among the candidates")
def test_recommend_invalid_cluster():
    pass


@scenario(FEATURE, "Recommend alternative cluster placement for a non-existent decision")
def test_recommend_alternative_not_found():
    pass


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------


@given(
    "a resolution decision exists with entity mention preview, current placement, and ranked candidates",
)
def decision_with_full_context(
    ctx: dict[str, Any],
    decision_repository: AsyncMock,
    entity_mention_repository: AsyncMock,
) -> None:
    # TODO: Set up a decision with entity mention preview, current placement,
    #       ranked candidates with scores, and timestamps.  Wire both
    #       decision_repository.find_by_id and entity_mention_repository
    #       so the service can build a full detail response.
    pass


@given("a decision exists that has not been curated on its current version")
def decision_not_curated(
    ctx: dict[str, Any],
    decision_repository: AsyncMock,
    user_action_repository: AsyncMock,
) -> None:
    decision = DecisionFactory.build(id="decision-1")
    decision_repository.find_by_id.return_value = decision
    user_action_repository.has_current_action.return_value = False
    user_action_repository.save.return_value = None
    ctx["decision_id"] = "decision-1"


@given(parsers.parse('a decision exists with alternative candidate "{cluster_id}"'))
def decision_with_alternative(
    ctx: dict[str, Any],
    cluster_id: str,
    decision_repository: AsyncMock,
    user_action_repository: AsyncMock,
) -> None:
    alt_candidate = ClusterReferenceFactory.build(cluster_id=cluster_id)
    decision = DecisionFactory.build(
        id="decision-1",
        candidates=[ClusterReferenceFactory.build(), alt_candidate],
    )
    decision_repository.find_by_id.return_value = decision
    user_action_repository.has_current_action.return_value = False
    user_action_repository.save.return_value = None
    ctx["decision_id"] = "decision-1"
    ctx["alt_cluster"] = cluster_id


@given("the decision has not been curated on its current version")
def decision_uncurated() -> None:
    pass


@given("a decision exists that has already been curated on its current version")
def decision_already_curated(
    ctx: dict[str, Any],
    decision_repository: AsyncMock,
    user_action_repository: AsyncMock,
) -> None:
    decision = DecisionFactory.build(id="decision-1")
    decision_repository.find_by_id.return_value = decision
    user_action_repository.has_current_action.return_value = True
    ctx["decision_id"] = "decision-1"


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------


@when(
    "the curator requests the full details of that decision",
    target_fixture="response",
)
def request_decision_details(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    # TODO: Call the GET /decisions/{id} endpoint (or equivalent) that returns
    #       full decision details including entity mention preview, placement,
    #       candidates, and timestamps.
    pass


@when(
    "the curator requests the details of a decision that does not exist",
    target_fixture="response",
)
def request_nonexistent_decision_details(
    client: TestClient,
    decision_repository: AsyncMock,
) -> Any:
    # TODO: Call the GET /decisions/{id} endpoint for a non-existent ID.
    #       Wire decision_repository.find_by_id.return_value = None.
    pass


@when(
    "the curator recommends the top candidate placement for the decision",
    target_fixture="response",
)
def recommend_top(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    return client.post(f"{DECISIONS_URL}/{ctx['decision_id']}/accept")


@when(
    "the curator attempts to recommend the top candidate for a decision that does not exist",
    target_fixture="response",
)
def recommend_top_nonexistent(
    client: TestClient,
    decision_repository: AsyncMock,
) -> Any:
    decision_repository.find_by_id.return_value = None
    return client.post(f"{DECISIONS_URL}/nonexistent/accept")


@when(
    "the curator attempts to recommend the top candidate placement for the decision",
    target_fixture="response",
)
def attempt_recommend_top(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    return client.post(f"{DECISIONS_URL}/{ctx['decision_id']}/accept")


@when(
    "the curator recommends rejection of all candidates for the decision",
    target_fixture="response",
)
def recommend_rejection(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    return client.post(f"{DECISIONS_URL}/{ctx['decision_id']}/reject")


@when(
    "the curator attempts to recommend rejection of all candidates for a decision that does not exist",
    target_fixture="response",
)
def recommend_rejection_nonexistent(
    client: TestClient,
    decision_repository: AsyncMock,
) -> Any:
    decision_repository.find_by_id.return_value = None
    return client.post(f"{DECISIONS_URL}/nonexistent/reject")


@when(
    parsers.parse('the curator recommends placement in cluster "{cluster_id}"'),
    target_fixture="response",
)
def recommend_alternative(
    client: TestClient,
    ctx: dict[str, Any],
    cluster_id: str,
) -> Any:
    return client.post(
        f"{DECISIONS_URL}/{ctx['decision_id']}/assign",
        json={"cluster_id": cluster_id},
    )


@when(
    "the curator attempts to recommend alternative cluster placement for a decision that does not exist",
    target_fixture="response",
)
def recommend_alternative_nonexistent(
    client: TestClient,
    decision_repository: AsyncMock,
) -> Any:
    decision_repository.find_by_id.return_value = None
    return client.post(
        f"{DECISIONS_URL}/nonexistent/assign",
        json={"cluster_id": "any-cluster"},
    )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


# --- View decision assertions ---


@then("the decision details are returned including the entity mention preview")
def decision_details_returned(response: Any) -> None:
    # TODO: Assert 200 and that the response body contains the entity mention preview.
    pass


@then("the current placement is shown")
def current_placement_shown(response: Any) -> None:
    # TODO: Assert response body contains current_placement with cluster_id and scores.
    pass


@then("the ranked candidates with scores are listed")
def ranked_candidates_listed(response: Any) -> None:
    # TODO: Assert response body contains candidates list with confidence/similarity scores.
    pass


@then("the curation timestamps are included")
def curation_timestamps_included(response: Any) -> None:
    # TODO: Assert response body contains created_at and updated_at timestamps.
    pass


# --- Recommendation assertions ---


@then("the recommendation is recorded")
def recommendation_recorded(response: Any) -> None:
    assert response.status_code == 204
    assert response.content == b""


@then(parsers.parse('a recommendation of type "{action_type}" is recorded'))
def action_recorded(
    response: Any,
    action_type: str,
    user_action_repository: AsyncMock,
) -> None:
    user_action_repository.save.assert_called_once()
    saved_action = user_action_repository.save.call_args[0][0]
    type_map = {
        "accept top": "ACCEPT_TOP",
        "reject all": "REJECT_ALL",
    }
    assert saved_action.action_type == type_map[action_type]


@then(
    parsers.parse(
        'a recommendation of type "{action_type}" is recorded for cluster "{cluster_id}"'
    ),
)
def action_recorded_for_cluster(
    response: Any,
    action_type: str,
    cluster_id: str,
    user_action_repository: AsyncMock,
) -> None:
    user_action_repository.save.assert_called_once()
    saved_action = user_action_repository.save.call_args[0][0]
    assert saved_action.selected_cluster.cluster_id == cluster_id


# --- Error assertions ---


@then("the system responds with a not found error")
def not_found_response(response: Any) -> None:
    assert response.status_code == 404


@then("the system responds with a conflict error indicating already curated")
def conflict_already_curated(response: Any) -> None:
    assert response.status_code == 409


@then("the system responds with a conflict error indicating an invalid cluster")
def conflict_invalid_cluster(response: Any) -> None:
    assert response.status_code == 409
