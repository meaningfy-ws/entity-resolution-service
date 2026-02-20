from typing import Annotated

from fastapi import APIRouter, Depends

from ers.application.dtos import (
    AssignRequest,
    CanonicalEntityPreview,
    DecisionSummary,
    ExecutionAcknowledgement,
    PaginatedResult,
)
from ers.application.services import CanonicalEntityService, DecisionCurationService
from ers.entrypoints.api.auth import CurrentUser
from ers.entrypoints.api.dependencies import (
    get_canonical_entity_service,
    get_decision_curation_service,
)
from ers.entrypoints.api.v1.schemas import (
    DecisionFiltersDep,
    ErrorResponse,
    Pagination,
)

router = APIRouter(prefix="/curation/decisions", tags=["Decisions"])


@router.get("", response_model=PaginatedResult[DecisionSummary])
async def list_decisions(
    filters: DecisionFiltersDep,
    pagination: Pagination,
    service: Annotated[DecisionCurationService, Depends(get_decision_curation_service)],
) -> PaginatedResult[DecisionSummary]:
    return await service.list_decisions(filters=filters, pagination=pagination)


@router.get(
    "/{decision_id}/proposed-canonical-entity",
    response_model=CanonicalEntityPreview,
    responses={404: {"model": ErrorResponse}},
)
async def get_proposed_canonical_entity(
    decision_id: str,
    service: Annotated[CanonicalEntityService, Depends(get_canonical_entity_service)],
) -> CanonicalEntityPreview:
    return await service.get_proposed_canonical_entity(decision_id)


@router.get(
    "/{decision_id}/alternative-canonical-entities",
    response_model=PaginatedResult[CanonicalEntityPreview],
    responses={404: {"model": ErrorResponse}},
)
async def get_alternative_canonical_entities(
    decision_id: str,
    pagination: Pagination,
    service: Annotated[CanonicalEntityService, Depends(get_canonical_entity_service)],
) -> PaginatedResult[CanonicalEntityPreview]:
    return await service.get_alternative_canonical_entities(decision_id, pagination)


@router.post(
    "/{decision_id}/accept",
    response_model=ExecutionAcknowledgement,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def accept_decision(
    decision_id: str,
    user: CurrentUser,
    service: Annotated[DecisionCurationService, Depends(get_decision_curation_service)],
) -> ExecutionAcknowledgement:
    await service.accept_decision(decision_id, actor=user)
    return ExecutionAcknowledgement(success=True)


@router.post(
    "/{decision_id}/reject",
    response_model=ExecutionAcknowledgement,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def reject_decision(
    decision_id: str,
    user: CurrentUser,
    service: Annotated[DecisionCurationService, Depends(get_decision_curation_service)],
) -> ExecutionAcknowledgement:
    await service.reject_decision(decision_id, actor=user)
    return ExecutionAcknowledgement(success=True)


@router.post(
    "/{decision_id}/assign",
    response_model=ExecutionAcknowledgement,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def assign_decision(
    decision_id: str,
    body: AssignRequest,
    user: CurrentUser,
    service: Annotated[DecisionCurationService, Depends(get_decision_curation_service)],
) -> ExecutionAcknowledgement:
    await service.assign_decision(
        decision_id,
        cluster_id=body.cluster_id,
        actor=user,
    )
    return ExecutionAcknowledgement(success=True)
