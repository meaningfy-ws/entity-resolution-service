from ers.application.ports.repositories import WriteRepository
from ers.domain.models import CurationAuditLog


class AuditLogRepository(WriteRepository[CurationAuditLog, str]):
    """Repository for persisting audit log entries."""
