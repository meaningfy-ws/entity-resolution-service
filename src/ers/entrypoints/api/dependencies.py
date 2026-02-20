from typing import Annotated

from fastapi import Depends

from ers.application.ports.audit_log_repository import AuditLogRepository
from ers.application.ports.canonical_entity_repository import (
    CanonicalEntityRepository,
)
from ers.application.ports.decision_repository import DecisionRepository
from ers.application.ports.entity_mention_repository import EntityMentionRepository
from ers.application.ports.statistics_repository import StatisticsRepository
from ers.application.services import (
    AuditService,
    CanonicalEntityService,
    DecisionCurationService,
    EntityService,
    StatisticsService,
)


# Repository providers


async def get_decision_repository() -> DecisionRepository:
    raise NotImplementedError("Decision repository adapter not configured")


async def get_entity_mention_repository() -> EntityMentionRepository:
    raise NotImplementedError("EntityMention repository adapter not configured")


async def get_canonical_entity_repository() -> CanonicalEntityRepository:
    raise NotImplementedError("CanonicalEntity repository adapter not configured")


async def get_audit_log_repository() -> AuditLogRepository:
    raise NotImplementedError("AuditLog repository adapter not configured")


async def get_statistics_repository() -> StatisticsRepository:
    raise NotImplementedError("Statistics repository adapter not configured")


# Service providers


async def get_audit_service(
    repo: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> AuditService:
    return AuditService(audit_log_repository=repo)


async def get_decision_curation_service(
    decision_repo: Annotated[DecisionRepository, Depends(get_decision_repository)],
    entity_repo: Annotated[
        EntityMentionRepository, Depends(get_entity_mention_repository)
    ],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> DecisionCurationService:
    return DecisionCurationService(
        decision_repository=decision_repo,
        entity_mention_repository=entity_repo,
        audit_service=audit_service,
    )


async def get_canonical_entity_service(
    decision_repo: Annotated[DecisionRepository, Depends(get_decision_repository)],
    canonical_repo: Annotated[
        CanonicalEntityRepository, Depends(get_canonical_entity_repository)
    ],
    entity_repo: Annotated[
        EntityMentionRepository, Depends(get_entity_mention_repository)
    ],
) -> CanonicalEntityService:
    return CanonicalEntityService(
        decision_repository=decision_repo,
        canonical_entity_repository=canonical_repo,
        entity_mention_repository=entity_repo,
    )


async def get_entity_service(
    entity_repo: Annotated[
        EntityMentionRepository, Depends(get_entity_mention_repository)
    ],
) -> EntityService:
    return EntityService(entity_mention_repository=entity_repo)


async def get_statistics_service(
    stats_repo: Annotated[StatisticsRepository, Depends(get_statistics_repository)],
) -> StatisticsService:
    return StatisticsService(statistics_repository=stats_repo)
