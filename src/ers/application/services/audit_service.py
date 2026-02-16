from ers.application.ports.audit_log_repository import AuditLogRepository
from ers.domain.models import CurationAuditLog, CurationDecision
from ers.domain.utils import generate_id


class AuditService:
    """Creates and persists audit log entries for curation actions."""

    def __init__(self, audit_log_repository: AuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    def log_accept(self, actor: str, decision: CurationDecision) -> None:
        """Record an accept action in the audit trail."""
        audit_log = CurationAuditLog.for_accept(
            audit_id=generate_id(),
            actor=actor,
            decision=decision,
        )
        self._audit_log_repository.save(audit_log)

    def log_reject(self, actor: str, decision: CurationDecision) -> None:
        """Record a reject action in the audit trail."""
        audit_log = CurationAuditLog.for_reject(
            audit_id=generate_id(),
            actor=actor,
            decision=decision,
        )
        self._audit_log_repository.save(audit_log)

    def log_assign(
        self,
        actor: str,
        decision: CurationDecision,
        from_cluster_id: str | None,
    ) -> None:
        """Record an assign action in the audit trail."""
        audit_log = CurationAuditLog.for_assign(
            audit_id=generate_id(),
            actor=actor,
            decision=decision,
            from_cluster_id=from_cluster_id,
        )
        self._audit_log_repository.save(audit_log)
