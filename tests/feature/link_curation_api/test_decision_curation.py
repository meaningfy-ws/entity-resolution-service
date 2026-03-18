"""Step definitions for decision_curation.feature.

Tests the POST accept/reject/assign endpoints through the FastAPI test client.
Repository mocks let real DecisionCurationService + UserActionService logic
run end-to-end.
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


@scenario(FEATURE, "Accept the top candidate for a decision")
def test_accept():
    pass


@scenario(FEATURE, "Accept a non-existent decision")
def test_accept_not_found():
    pass


@scenario(FEATURE, "Accept a decision that was already curated")
def test_accept_already_curated():
    pass


@scenario(FEATURE, "Reject all candidates for a decision")
def test_reject():
    pass


@scenario(FEATURE, "Reject a non-existent decision")
def test_reject_not_found():
    pass


@scenario(FEATURE, "Assign a decision to an alternative cluster")
def test_assign():
    pass


@scenario(FEATURE, "Assign to a cluster not in candidates")
def test_assign_invalid():
    pass


@scenario(FEATURE, "Assign a non-existent decision")
def test_assign_not_found():
    pass


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------


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


@given(parsers.parse('a decision exists with an alternative candidate "{cluster_id}"'))
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


@when("the curator accepts the decision", target_fixture="response")
def accept_decision(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    return client.post(f"{DECISIONS_URL}/{ctx['decision_id']}/accept")


@when(
    "the curator attempts to accept a decision that does not exist",
    target_fixture="response",
)
def accept_nonexistent(
    client: TestClient,
    decision_repository: AsyncMock,
) -> Any:
    decision_repository.find_by_id.return_value = None
    return client.post(f"{DECISIONS_URL}/nonexistent/accept")


@when("the curator attempts to accept the decision", target_fixture="response")
def attempt_accept(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    return client.post(f"{DECISIONS_URL}/{ctx['decision_id']}/accept")


@when("the curator rejects the decision", target_fixture="response")
def reject_decision(
    client: TestClient,
    ctx: dict[str, Any],
) -> Any:
    return client.post(f"{DECISIONS_URL}/{ctx['decision_id']}/reject")


@when(
    "the curator attempts to reject a decision that does not exist",
    target_fixture="response",
)
def reject_nonexistent(
    client: TestClient,
    decision_repository: AsyncMock,
) -> Any:
    decision_repository.find_by_id.return_value = None
    return client.post(f"{DECISIONS_URL}/nonexistent/reject")


@when(
    parsers.parse('the curator assigns the decision to cluster "{cluster_id}"'),
    target_fixture="response",
)
def assign_decision(
    client: TestClient,
    ctx: dict[str, Any],
    cluster_id: str,
) -> Any:
    return client.post(
        f"{DECISIONS_URL}/{ctx['decision_id']}/assign",
        json={"cluster_id": cluster_id},
    )


@when(
    "the curator attempts to assign a decision that does not exist to a cluster",
    target_fixture="response",
)
def assign_nonexistent(
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


@then("the system confirms the action with no content")
def confirms_no_content(response: Any) -> None:
    assert response.status_code == 204
    assert response.content == b""


@then(parsers.parse('a user action of type "{action_type}" is recorded'))
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
    parsers.parse('a user action of type "{action_type}" is recorded for cluster "{cluster_id}"'),
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


@then("the system responds with a not found error")
def not_found_response(response: Any) -> None:
    assert response.status_code == 404


@then("the system responds with a conflict error indicating already curated")
def conflict_already_curated(response: Any) -> None:
    assert response.status_code == 409


@then("the system responds with a conflict error indicating an invalid cluster")
def conflict_invalid_cluster(response: Any) -> None:
    assert response.status_code == 409
