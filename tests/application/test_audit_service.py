from unittest.mock import MagicMock, create_autospec

import pytest
from erspec.models.core import AuditAction, DecisionAction, DecisionStatus

from ers.application.ports.audit_log_repository import AuditLogRepository
from ers.application.services.audit_service import AuditService
from ers.domain.models import CurationAuditLog
from tests.factories import ClusterReferenceFactory, CurationDecisionFactory


@pytest.fixture
def audit_log_repository() -> MagicMock:
    return create_autospec(AuditLogRepository, instance=True)


@pytest.fixture
def audit_service(audit_log_repository: MagicMock) -> AuditService:
    return AuditService(audit_log_repository=audit_log_repository)


class TestLogAccept:
    async def test_log_accept_creates_and_saves_audit_entry(
        self,
        audit_service: AuditService,
        audit_log_repository: MagicMock,
    ) -> None:
        top_candidate = ClusterReferenceFactory.build(confidence_score=0.9)
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.MANUALLY_REVIEWED,
            action=DecisionAction.ACCEPT_TOP,
            accepted_candidate=top_candidate,
        )

        await audit_service.log_accept(actor="curator-1", decision=decision)

        audit_log_repository.save.assert_called_once()
        saved_log: CurationAuditLog = audit_log_repository.save.call_args[0][0]
        assert saved_log.action == AuditAction.ACCEPT
        assert saved_log.actor == "curator-1"
        assert saved_log.instance_type == "Decision"
        assert saved_log.instance_id == decision.id


class TestLogReject:
    async def test_log_reject_creates_and_saves_audit_entry(
        self,
        audit_service: AuditService,
        audit_log_repository: MagicMock,
    ) -> None:
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.MANUALLY_REVIEWED,
            action=DecisionAction.REJECT_ALL,
        )

        await audit_service.log_reject(actor="curator-1", decision=decision)

        audit_log_repository.save.assert_called_once()
        saved_log: CurationAuditLog = audit_log_repository.save.call_args[0][0]
        assert saved_log.action == AuditAction.REJECT
        assert saved_log.instance_id == decision.id
        assert saved_log.changes is None


class TestLogAssign:
    async def test_log_assign_creates_and_saves_audit_entry(
        self,
        audit_service: AuditService,
        audit_log_repository: MagicMock,
    ) -> None:
        target = ClusterReferenceFactory.build(confidence_score=0.7)
        decision = CurationDecisionFactory.build(
            status=DecisionStatus.MANUALLY_REVIEWED,
            action=DecisionAction.ACCEPT_ALTERNATIVE,
            accepted_candidate=target,
        )

        await audit_service.log_assign(
            actor="curator-1",
            decision=decision,
            from_cluster_id="old-cluster-id",
        )

        audit_log_repository.save.assert_called_once()
        saved_log: CurationAuditLog = audit_log_repository.save.call_args[0][0]
        assert saved_log.action == AuditAction.ASSIGN
        assert saved_log.instance_id == decision.id
        assert "old-cluster-id" in saved_log.changes
        assert target.cluster_id in saved_log.changes
