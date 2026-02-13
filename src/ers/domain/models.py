from typing import Optional

# TODO: replace with actual imports from package once released
from erspec.models.core import (
    AuditAction,
    AuditLog,
    ClusterReference,
    Decision,
    DecisionAction,
    DecisionStatus,
)

from ers.domain.exceptions import (
    InvalidClusterError,
    InvalidStateTransitionError,
    NoCandidatesError,
)
from ers.domain.utils import utc_now, serialize_to_json


class CurationDecision(Decision):
    """Domain entity extending Decision with curation business logic.

    This class wraps the LinkML-generated Decision model and adds
    domain behavior for state transitions and validation rules.
    """

    @property
    def is_pending_review(self) -> bool:
        return self.status == DecisionStatus.PENDING_MANUAL_REVIEW

    @property
    def is_manually_reviewed(self) -> bool:
        return self.status == DecisionStatus.MANUALLY_REVIEWED

    @property
    def is_auto_confident(self) -> bool:
        return self.status == DecisionStatus.AUTOMATIC_CONFIDENT

    @property
    def top_candidate(self) -> Optional[ClusterReference]:
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda c: c.confidence_score)

    def _validate_can_curate(self, action: DecisionAction) -> None:
        """Validate that the decision can be curated with the given action."""
        if not self.is_pending_review:
            raise InvalidStateTransitionError(
                current_status=self.status,
                attempted_action=action.value,
            )

    def _find_candidate_by_cluster_id(
        self, cluster_id: str
    ) -> Optional[ClusterReference]:
        """Find a candidate by cluster ID."""
        for candidate in self.candidates:
            if candidate.cluster_id == cluster_id:
                return candidate
        return None

    def accept(self) -> "CurationDecision":
        """Accept the top candidate as the resolution.

        Returns a new CurationDecision with updated state.

        Raises:
            InvalidStateTransitionError: If decision is not pending review.
            NoCandidatesError: If there are no candidates to accept.
        """
        self._validate_can_curate(DecisionAction.ACCEPT_TOP)

        top = self.top_candidate
        if top is None:
            raise NoCandidatesError(self.id)
        return CurationDecision(
            id=self.id,
            about_entity_mention=self.about_entity_mention,
            candidates=self.candidates,
            status=DecisionStatus.MANUALLY_REVIEWED,
            action=DecisionAction.ACCEPT_TOP,
            accepted_candidate=top,
            created_at=self.created_at,
            updated_at=utc_now(),
        )

    def reject(self) -> "CurationDecision":
        """Reject all candidates.

        Returns a new CurationDecision with updated state.

        Raises:
            InvalidStateTransitionError: If decision is not pending review.
        """
        self._validate_can_curate(DecisionAction.REJECT_ALL)

        return CurationDecision(
            id=self.id,
            about_entity_mention=self.about_entity_mention,
            candidates=self.candidates,
            status=DecisionStatus.MANUALLY_REVIEWED,
            action=DecisionAction.REJECT_ALL,
            accepted_candidate=None,
            created_at=self.created_at,
            updated_at=utc_now(),
        )

    def assign(self, cluster_id: str) -> "CurationDecision":
        """Assign the entity to an alternative cluster.

        Args:
            cluster_id: The ID of the cluster to assign to.

        Returns a new CurationDecision with updated state.

        Raises:
            InvalidStateTransitionError: If decision is not pending review.
            InvalidClusterError: If cluster_id is not in candidates.
        """
        self._validate_can_curate(DecisionAction.ACCEPT_ALTERNATIVE)

        candidate = self._find_candidate_by_cluster_id(cluster_id)
        if candidate is None:
            raise InvalidClusterError(cluster_id, self.id)

        return CurationDecision(
            id=self.id,
            about_entity_mention=self.about_entity_mention,
            candidates=self.candidates,
            status=DecisionStatus.MANUALLY_REVIEWED,
            action=DecisionAction.ACCEPT_ALTERNATIVE,
            accepted_candidate=candidate,
            created_at=self.created_at,
            updated_at=utc_now(),
        )

    @classmethod
    def from_decision(cls, decision: Decision) -> "CurationDecision":
        """Create a CurationDecision from a base Decision model."""
        return cls(
            id=decision.id,
            about_entity_mention=decision.about_entity_mention,
            candidates=decision.candidates,
            status=decision.status,
            action=decision.action,
            accepted_candidate=decision.accepted_candidate,
            created_at=decision.created_at,
            updated_at=decision.updated_at,
        )


class CurationAuditLog(AuditLog):
    """Domain entity extending AuditLog with factory methods.

    Provides convenient factory methods for creating audit entries
    for different curation actions.
    """

    @classmethod
    def for_accept(
        cls,
        audit_id: str,
        actor: str,
        decision: CurationDecision,
    ) -> "CurationAuditLog":
        """Create an audit log entry for an accept action."""
        changes = {
            "accepted_cluster_id": (
                decision.accepted_candidate.cluster_id
                if decision.accepted_candidate
                else None
            ),
        }
        return cls(
            id=audit_id,
            actor=actor,
            action=AuditAction.ACCEPT,
            instance_type="Decision",
            instance_id=decision.id,
            changes=serialize_to_json(changes),
            created_at=utc_now(),
        )

    @classmethod
    def for_reject(
        cls,
        audit_id: str,
        actor: str,
        decision: CurationDecision,
    ) -> "CurationAuditLog":
        """Create an audit log entry for a reject action."""
        return cls(
            id=audit_id,
            actor=actor,
            action=AuditAction.REJECT,
            instance_type="Decision",
            instance_id=decision.id,
            changes=None,
            created_at=utc_now(),
        )

    @classmethod
    def for_assign(
        cls,
        audit_id: str,
        actor: str,
        decision: CurationDecision,
        from_cluster_id: Optional[str],
    ) -> "CurationAuditLog":
        """Create an audit log entry for an assign action."""
        changes = {
            "from_cluster_id": from_cluster_id,
            "to_cluster_id": (
                decision.accepted_candidate.cluster_id
                if decision.accepted_candidate
                else None
            ),
        }
        return cls(
            id=audit_id,
            actor=actor,
            action=AuditAction.ASSIGN,
            instance_type="Decision",
            instance_id=decision.id,
            changes=serialize_to_json(changes),
            created_at=utc_now(),
        )
