from erspec.models.core import EntityMention

from ers.application.dtos import (
    DecisionFilters,
    DecisionSummary,
    EntityMentionPreview,
    PaginatedResult,
    PaginationParams,
)
from ers.application.exceptions import NotFoundError
from ers.application.ports.decision_repository import DecisionRepository
from ers.application.ports.entity_mention_repository import EntityMentionRepository
from ers.application.services.audit_service import AuditService
from ers.domain.models import CurationDecision


class DecisionCurationService:
    """Orchestrates curation actions and decision queries."""

    def __init__(
        self,
        decision_repository: DecisionRepository,
        entity_mention_repository: EntityMentionRepository,
        audit_service: AuditService,
    ) -> None:
        self._decision_repository = decision_repository
        self._entity_mention_repository = entity_mention_repository
        self._audit_service = audit_service

    async def _get_decision_or_raise(self, decision_id: str) -> CurationDecision:
        decision = await self._decision_repository.find_by_id(decision_id)
        if decision is None:
            raise NotFoundError("Decision", decision_id)
        return decision

    async def list_decisions(
        self,
        filters: DecisionFilters,
        pagination: PaginationParams,
    ) -> PaginatedResult[DecisionSummary]:
        """List decisions with filtering, pagination, and embedded entity data."""
        paginated = await self._decision_repository.find_with_filters(
            filters=filters,
            pagination=pagination,
        )

        identifiers = [d.about_entity_mention for d in paginated.results]
        entity_mentions = await self._entity_mention_repository.find_by_identifiers(
            identifiers,
        )
        mention_map = self._index_by_identifier(entity_mentions)

        decision_summaries = [
            self._to_decision_summary(decision, mention_map)
            for decision in paginated.results
        ]

        return PaginatedResult(
            count=paginated.count,
            previous=paginated.previous,
            next=paginated.next,
            results=decision_summaries,
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

    @staticmethod
    def _index_by_identifier(
        entity_mentions: list[EntityMention],
    ) -> dict[tuple[str, str, str], EntityMention]:
        return {
            (
                em.identifier.source_id,
                em.identifier.request_id,
                em.identifier.entity_type,
            ): em
            for em in entity_mentions
        }

    @staticmethod
    def _to_decision_summary(
        decision: CurationDecision,
        mention_map: dict[tuple[str, str, str], EntityMention],
    ) -> DecisionSummary:
        emi = decision.about_entity_mention
        key = (emi.source_id, emi.request_id, emi.entity_type)
        mention = mention_map.get(key)

        return DecisionSummary(
            id=decision.id,
            status=decision.status,
            about_entity_mention=EntityMentionPreview(
                identifier=emi,
                parsed_representation=(
                    mention.parsed_representation if mention else None
                ),
            ),
            accepted_candidate=decision.accepted_candidate,
            created_at=decision.created_at,
        )
