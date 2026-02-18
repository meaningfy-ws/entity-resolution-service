from ers.application.ports.repositories import AsyncWriteRepository
from ers.domain.models import CurationAuditLog


class AuditLogRepository(AsyncWriteRepository[CurationAuditLog, str]):
    """Repository for persisting audit log entries."""
