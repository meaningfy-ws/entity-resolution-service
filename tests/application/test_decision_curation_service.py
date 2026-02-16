from unittest.mock import MagicMock, create_autospec

import pytest
from erspec.models.core import DecisionAction, DecisionStatus

from ers.application.dtos import DecisionFilters, PaginatedResult
from ers.application.exceptions import NotFoundError
from ers.application.ports.decision_repository import DecisionRepository
from ers.application.services.audit_service import AuditService
from ers.application.services.decision_curation_service import (
    DecisionCurationService,
)
from ers.domain.exceptions import InvalidClusterError, InvalidStateTransitionError
from tests.factories import ClusterReferenceFactory, CurationDecisionFactory


@pytest.fixture
def decision_repository() -> MagicMock:
    return create_autospec(DecisionRepository, instance=True)


@pytest.fixture
def audit_service() -> MagicMock:
    return create_autospec(AuditService, instance=True)


@pytest.fixture
def service(
    decision_repository: MagicMock,
    audit_service: MagicMock,
) -> DecisionCurationService:
    return DecisionCurationService(
        decision_repository=decision_repository,
        audit_service=audit_service,
    )


class TestListDecisions:
    def test_list_decisions_delegates_to_repository(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
    ) -> None:
        filters = DecisionFilters(status=DecisionStatus.PENDING_MANUAL_REVIEW)
        expected = PaginatedResult(count=0, previous=None, next=None, results=[])
        decision_repository.find_with_filters.return_value = expected

        result = service.list_decisions(filters=filters, page=1, per_page=20)

        assert result == expected
        decision_repository.find_with_filters.assert_called_once_with(
            filters=filters, page=1, per_page=20
        )


class TestGetDecision:
    def test_get_decision_returns_decision(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
    ) -> None:
        decision = CurationDecisionFactory.build()
        decision_repository.find_by_id.return_value = decision

        result = service.get_decision(decision.id)

        assert result == decision

    def test_get_decision_not_found_raises_error(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
    ) -> None:
        decision_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            service.get_decision("nonexistent-id")

        assert exc_info.value.entity_type == "Decision"
        assert exc_info.value.entity_id == "nonexistent-id"


class TestAcceptDecision:
    def test_accept_decision_saves_and_logs(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
        audit_service: MagicMock,
    ) -> None:
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.PENDING_MANUAL_REVIEW,
        )
        decision_repository.find_by_id.return_value = decision

        result = service.accept_decision(decision.id, actor="curator-1")

        assert result.status == DecisionStatus.MANUALLY_REVIEWED
        assert result.action == DecisionAction.ACCEPT_TOP
        decision_repository.save.assert_called_once_with(result)
        audit_service.log_accept.assert_called_once_with(
            actor="curator-1", decision=result
        )

    def test_accept_decision_not_found_raises_error(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
        audit_service: MagicMock,
    ) -> None:
        decision_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.accept_decision("nonexistent-id", actor="curator-1")

        decision_repository.save.assert_not_called()
        audit_service.log_accept.assert_not_called()

    def test_accept_decision_invalid_state_propagates(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
        audit_service: MagicMock,
    ) -> None:
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.MANUALLY_REVIEWED,
        )
        decision_repository.find_by_id.return_value = decision

        with pytest.raises(InvalidStateTransitionError):
            service.accept_decision(decision.id, actor="curator-1")

        decision_repository.save.assert_not_called()
        audit_service.log_accept.assert_not_called()


class TestRejectDecision:
    def test_reject_decision_saves_and_logs(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
        audit_service: MagicMock,
    ) -> None:
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.PENDING_MANUAL_REVIEW,
        )
        decision_repository.find_by_id.return_value = decision

        result = service.reject_decision(decision.id, actor="curator-1")

        assert result.status == DecisionStatus.MANUALLY_REVIEWED
        assert result.action == DecisionAction.REJECT_ALL
        decision_repository.save.assert_called_once_with(result)
        audit_service.log_reject.assert_called_once_with(
            actor="curator-1", decision=result
        )

    def test_reject_decision_not_found_raises_error(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
    ) -> None:
        decision_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.reject_decision("nonexistent-id", actor="curator-1")


class TestAssignDecision:
    def test_assign_decision_saves_and_logs(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
        audit_service: MagicMock,
    ) -> None:
        target = ClusterReferenceFactory.build(confidence_score=0.5)
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.PENDING_MANUAL_REVIEW,
            accepted_candidate=ClusterReferenceFactory.build(confidence_score=0.80),
            candidates=[
                ClusterReferenceFactory.build(confidence_score=0.7),
                target,
            ],
        )
        decision_repository.find_by_id.return_value = decision

        result = service.assign_decision(
            decision.id, cluster_id=target.cluster_id, actor="curator-1"
        )

        assert result.status == DecisionStatus.MANUALLY_REVIEWED
        assert result.action == DecisionAction.ACCEPT_ALTERNATIVE
        assert result.accepted_candidate.cluster_id == target.cluster_id
        decision_repository.save.assert_called_once_with(result)
        audit_service.log_assign.assert_called_once_with(
            actor="curator-1",
            decision=result,
            from_cluster_id=decision.accepted_candidate.cluster_id,
        )

    def test_assign_decision_invalid_cluster_propagates(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
        audit_service: MagicMock,
    ) -> None:
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.PENDING_MANUAL_REVIEW,
        )
        decision_repository.find_by_id.return_value = decision

        with pytest.raises(InvalidClusterError):
            service.assign_decision(
                decision.id, cluster_id="nonexistent-cluster", actor="curator-1"
            )

        decision_repository.save.assert_not_called()
        audit_service.log_assign.assert_not_called()

    def test_assign_decision_not_found_raises_error(
        self,
        service: DecisionCurationService,
        decision_repository: MagicMock,
    ) -> None:
        decision_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            service.assign_decision(
                "nonexistent-id", cluster_id="some-cluster", actor="curator-1"
            )
