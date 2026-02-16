from ers.application.dtos import DecisionFilters, PaginatedResult
from ers.application.exceptions import NotFoundError
from ers.application.ports.decision_repository import DecisionRepository
from ers.application.services.audit_service import AuditService
from ers.domain.models import CurationDecision


class DecisionCurationService:
    """Orchestrates curation actions and decision queries."""

    def __init__(
        self,
        decision_repository: DecisionRepository,
        audit_service: AuditService,
    ) -> None:
        self._decision_repository = decision_repository
        self._audit_service = audit_service

    async def _get_decision_or_raise(self, decision_id: str) -> CurationDecision:
        decision = await self._decision_repository.find_by_id(decision_id)
        if decision is None:
            raise NotFoundError("Decision", decision_id)
        return decision

    async def list_decisions(
        self,
        filters: DecisionFilters,
        page: int,
        per_page: int,
    ) -> PaginatedResult[CurationDecision]:
        """List decisions with filtering and pagination."""
        return await self._decision_repository.find_with_filters(
            filters=filters,
            page=page,
            per_page=per_page,
        )

    async def get_decision(self, decision_id: str) -> CurationDecision:
        """Retrieve a single decision by ID.

        Raises:
            NotFoundError: If the decision does not exist.
        """
        return await self._get_decision_or_raise(decision_id)

    async def accept_decision(self, decision_id: str, actor: str) -> CurationDecision:
        """Accept the top candidate for a decision.

        Raises:
            NotFoundError: If the decision does not exist.
            InvalidStateTransitionError: If not pending review.
        """
        decision = await self._get_decision_or_raise(decision_id)
        updated = decision.accept()
        await self._decision_repository.save(updated)
        await self._audit_service.log_accept(actor=actor, decision=updated)
        return updated

    async def reject_decision(self, decision_id: str, actor: str) -> CurationDecision:
        """Reject all candidates for a decision.

        Raises:
            NotFoundError: If the decision does not exist.
            InvalidStateTransitionError: If not pending review.
        """
        decision = await self._get_decision_or_raise(decision_id)
        updated = decision.reject()
        await self._decision_repository.save(updated)
        await self._audit_service.log_reject(actor=actor, decision=updated)
        return updated

    async def assign_decision(
        self, decision_id: str, cluster_id: str, actor: str
    ) -> CurationDecision:
        """Assign a decision to an alternative cluster.

        Raises:
            NotFoundError: If the decision does not exist.
            InvalidStateTransitionError: If not pending review.
            InvalidClusterError: If cluster_id is not in candidates.
        """
        decision = await self._get_decision_or_raise(decision_id)
        from_cluster_id = decision.accepted_candidate.cluster_id
        updated = decision.assign(cluster_id)
        await self._decision_repository.save(updated)
        await self._audit_service.log_assign(
            actor=actor,
            decision=updated,
            from_cluster_id=from_cluster_id,
        )
        return updated
