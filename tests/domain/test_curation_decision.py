import pytest

# TODO: replace with actual package imports once released
from ere.models.ers import DecisionAction, DecisionStatus
from ers.domain.exceptions import (
    InvalidClusterError,
    InvalidStateTransitionError,
    NoCandidatesError,
)
from tests.factories import ClusterReferenceFactory, CurationDecisionFactory


class TestCurationDecisionTopCandidate:
    def test_top_candidate_returns_highest_confidence(self):
        candidates = [
            ClusterReferenceFactory.build(confidenceScore=0.5),
            ClusterReferenceFactory.build(confidenceScore=0.9),
            ClusterReferenceFactory.build(confidenceScore=0.7),
        ]
        decision = CurationDecisionFactory.build(candidates=candidates)

        assert decision.top_candidate.confidenceScore == 0.9

    def test_top_candidate_returns_none_when_no_candidates(self):
        decision = CurationDecisionFactory.build(candidates=[])

        assert decision.top_candidate is None

    def test_top_candidate_with_single_candidate(self):
        candidate = ClusterReferenceFactory.build(confidenceScore=0.6)
        decision = CurationDecisionFactory.build(candidates=[candidate])

        assert decision.top_candidate == candidate


class TestCurationDecisionAccept:
    def test_accept_when_pending_sets_status_to_manually_reviewed(
        self, pending_decision_with_candidates
    ):
        result = pending_decision_with_candidates.accept()

        assert result.status == DecisionStatus.MANUALLY_REVIEWED

    def test_accept_when_pending_sets_action_to_accept_top(
        self, pending_decision_with_candidates
    ):
        result = pending_decision_with_candidates.accept()

        assert result.action == DecisionAction.ACCEPT_TOP

    def test_accept_when_pending_sets_accepted_candidate_to_top(
        self, pending_decision_with_candidates
    ):
        result = pending_decision_with_candidates.accept()

        assert result.acceptedCandidate.confidenceScore == 0.9

    def test_accept_returns_new_instance(self, pending_decision_with_candidates):
        result = pending_decision_with_candidates.accept()

        assert result is not pending_decision_with_candidates

    def test_accept_preserves_original_decision(self, pending_decision_with_candidates):
        original_status = pending_decision_with_candidates.status
        pending_decision_with_candidates.accept()

        assert pending_decision_with_candidates.status == original_status

    def test_accept_when_already_reviewed_raises_invalid_state_transition(
        self, reviewed_decision
    ):
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            reviewed_decision.accept()

        assert exc_info.value.current_status == DecisionStatus.MANUALLY_REVIEWED
        assert exc_info.value.attempted_action == DecisionAction.ACCEPT_TOP.value

    def test_accept_when_auto_confident_raises_invalid_state_transition(
        self, auto_confident_decision
    ):
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            auto_confident_decision.accept()

        assert exc_info.value.current_status == DecisionStatus.AUTOMATIC_CONFIDENT

    def test_accept_with_no_candidates_raises_no_candidates_error(self):
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.PENDING_MANUAL_REVIEW,
            candidates=[],
        )

        with pytest.raises(NoCandidatesError) as exc_info:
            decision.accept()

        assert exc_info.value.decision_id == decision.id


class TestCurationDecisionReject:
    def test_reject_when_pending_sets_status_to_manually_reviewed(
        self, pending_decision
    ):
        result = pending_decision.reject()

        assert result.status == DecisionStatus.MANUALLY_REVIEWED

    def test_reject_when_pending_sets_action_to_reject_all(self, pending_decision):
        result = pending_decision.reject()

        assert result.action == DecisionAction.REJECT_ALL

    def test_reject_when_pending_has_no_accepted_candidate(self, pending_decision):
        result = pending_decision.reject()

        assert result.acceptedCandidate is None

    def test_reject_when_already_reviewed_raises_invalid_state_transition(
        self, reviewed_decision
    ):
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            reviewed_decision.reject()

        assert exc_info.value.current_status == DecisionStatus.MANUALLY_REVIEWED
        assert exc_info.value.attempted_action == DecisionAction.REJECT_ALL.value

    def test_reject_when_auto_confident_raises_invalid_state_transition(
        self, auto_confident_decision
    ):
        with pytest.raises(InvalidStateTransitionError):
            auto_confident_decision.reject()


class TestCurationDecisionAssign:
    def test_assign_when_pending_sets_status_to_manually_reviewed(
        self, pending_decision_with_candidates
    ):
        target_cluster_id = pending_decision_with_candidates.candidates[1].clusterId

        result = pending_decision_with_candidates.assign(target_cluster_id)

        assert result.status == DecisionStatus.MANUALLY_REVIEWED

    def test_assign_when_pending_sets_action_to_accept_alternative(
        self, pending_decision_with_candidates
    ):
        target_cluster_id = pending_decision_with_candidates.candidates[1].clusterId

        result = pending_decision_with_candidates.assign(target_cluster_id)

        assert result.action == DecisionAction.ACCEPT_ALTERNATIVE

    def test_assign_sets_accepted_candidate_to_selected_cluster(
        self, pending_decision_with_candidates
    ):
        target_cluster = pending_decision_with_candidates.candidates[1]

        result = pending_decision_with_candidates.assign(target_cluster.clusterId)

        assert result.acceptedCandidate == target_cluster

    def test_assign_with_invalid_cluster_raises_invalid_cluster_error(
        self, pending_decision_with_candidates
    ):
        invalid_cluster_id = "nonexistent-cluster"

        with pytest.raises(InvalidClusterError) as exc_info:
            pending_decision_with_candidates.assign(invalid_cluster_id)

        assert exc_info.value.cluster_id == invalid_cluster_id
        assert exc_info.value.decision_id == pending_decision_with_candidates.id

    def test_assign_when_already_reviewed_raises_invalid_state_transition(
        self, reviewed_decision
    ):
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            reviewed_decision.assign("some-cluster")

        assert exc_info.value.current_status == DecisionStatus.MANUALLY_REVIEWED
        assert (
            exc_info.value.attempted_action == DecisionAction.ACCEPT_ALTERNATIVE.value
        )
