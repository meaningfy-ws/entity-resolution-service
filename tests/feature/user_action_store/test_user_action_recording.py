"""Step definitions for user_action_recording.feature.

Tests the domain-level UserActionFactory and the UserActionService recording
methods with mocked repositories.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from erspec.models.core import UserActionType
from pytest_bdd import given, parsers, scenario, then, when

from ers.curation.domain.exceptions import InvalidClusterError
from ers.curation.domain.models import UserActionFactory as DomainUserActionFactory
from tests.unit.factories import ClusterReferenceFactory, DecisionFactory

FEATURE = str(Path(__file__).resolve().parent / "user_action_recording.feature")


# ---------------------------------------------------------------------------
# Scenario bindings
# ---------------------------------------------------------------------------


@scenario(FEATURE, "Record an accept action for the top candidate")
def test_record_accept():
    pass


@scenario(FEATURE, "Accept action records the actor identity")
def test_accept_records_actor():
    pass


@scenario(FEATURE, "Record a reject action for all candidates")
def test_record_reject():
    pass


@scenario(FEATURE, "Record an assign action for an alternative candidate")
def test_record_assign_alternative():
    pass


@scenario(FEATURE, "Assign to a cluster not in candidates is rejected")
def test_assign_invalid_cluster():
    pass


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------


@given("a resolution decision exists for an entity mention")
def decision_exists(ctx: dict[str, Any]) -> None:
    candidates = ClusterReferenceFactory.batch(3)
    ctx["decision"] = DecisionFactory.build(
        current_placement=candidates[0],
        candidates=candidates,
    )


@given("the decision has candidate clusters with confidence scores")
def decision_has_candidates(ctx: dict[str, Any]) -> None:
    assert len(ctx["decision"].candidates) > 0


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------


@given("the decision has not been curated on its current version")
def decision_not_curated(
    ctx: dict[str, Any],
    user_action_repository: MagicMock,
) -> None:
    ctx["decision"] = ctx["decision"].model_copy(update={"updated_at": None})
    user_action_repository.has_current_action.return_value = False


@given(parsers.parse('the decision has an alternative candidate "{cluster_id}"'))
def decision_has_alternative(ctx: dict[str, Any], cluster_id: str) -> None:
    alternative = ClusterReferenceFactory.build(cluster_id=cluster_id)
    existing = ctx["decision"].candidates
    ctx["decision"] = ctx["decision"].model_copy(
        update={"candidates": [*existing, alternative]},
    )


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------


@when("the curator accepts the top candidate")
def curator_accepts(ctx: dict[str, Any]) -> None:
    ctx["actor"] = "curator@example.com"
    ctx["user_action"] = DomainUserActionFactory.create_accept(
        actor=ctx["actor"],
        decision=ctx["decision"],
    )


@when(parsers.parse('the curator "{actor}" accepts the top candidate'))
def curator_with_identity_accepts(ctx: dict[str, Any], actor: str) -> None:
    ctx["actor"] = actor
    ctx["user_action"] = DomainUserActionFactory.create_accept(
        actor=actor,
        decision=ctx["decision"],
    )


@when("the curator rejects all candidates")
def curator_rejects(ctx: dict[str, Any]) -> None:
    ctx["actor"] = "curator@example.com"
    ctx["user_action"] = DomainUserActionFactory.create_reject(
        actor=ctx["actor"],
        decision=ctx["decision"],
    )


@when(parsers.parse('the curator assigns the decision to cluster "{cluster_id}"'))
def curator_assigns(ctx: dict[str, Any], cluster_id: str) -> None:
    ctx["actor"] = "curator@example.com"
    try:
        ctx["user_action"] = DomainUserActionFactory.create_assign(
            actor=ctx["actor"],
            decision=ctx["decision"],
            cluster_id=cluster_id,
        )
        ctx["error"] = None
    except InvalidClusterError as exc:
        ctx["user_action"] = None
        ctx["error"] = exc


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


@then(parsers.parse('a user action is recorded with action type "{action_type}"'))
def action_recorded_with_type(ctx: dict[str, Any], action_type: str) -> None:
    type_map = {
        "accept top": UserActionType.ACCEPT_TOP,
        "reject all": UserActionType.REJECT_ALL,
        "accept alternative": UserActionType.ACCEPT_ALTERNATIVE,
    }
    assert ctx["user_action"] is not None
    assert ctx["user_action"].action_type == type_map[action_type]


@then("the selected cluster matches the decision's current placement")
def selected_cluster_matches_placement(ctx: dict[str, Any]) -> None:
    assert ctx["user_action"].selected_cluster == ctx["decision"].current_placement


@then("the action captures all candidates as a snapshot")
def action_captures_candidates(ctx: dict[str, Any]) -> None:
    assert ctx["user_action"].candidates == ctx["decision"].candidates


@then(parsers.parse('the recorded user action has actor "{actor}"'))
def action_has_actor(ctx: dict[str, Any], actor: str) -> None:
    assert ctx["user_action"].actor == actor


@then("the selected cluster is empty")
def selected_cluster_is_empty(ctx: dict[str, Any]) -> None:
    assert ctx["user_action"].selected_cluster is None


@then(parsers.parse('the selected cluster is "{cluster_id}"'))
def selected_cluster_is(ctx: dict[str, Any], cluster_id: str) -> None:
    assert ctx["user_action"].selected_cluster.cluster_id == cluster_id


@then("the action is rejected because the cluster is not a valid candidate")
def action_rejected_invalid_cluster(ctx: dict[str, Any]) -> None:
    assert ctx["user_action"] is None
    assert isinstance(ctx["error"], InvalidClusterError)
