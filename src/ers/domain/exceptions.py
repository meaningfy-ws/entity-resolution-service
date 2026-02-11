class DomainError(Exception):
    """Base exception for all domain-level errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidStateTransitionError(DomainError):
    """Raised when a decision state transition is not allowed."""

    def __init__(
        self,
        current_status: str,
        attempted_action: str,
    ) -> None:
        self.current_status = current_status
        self.attempted_action = attempted_action
        message = (
            f"Cannot perform '{attempted_action}' on decision "
            f"with status '{current_status}'"
        )
        super().__init__(message)


class InvalidClusterError(DomainError):
    """Raised when a cluster reference is invalid for the operation."""

    def __init__(self, cluster_id: str, decision_id: str) -> None:
        self.cluster_id = cluster_id
        self.decision_id = decision_id
        message = (
            f"Cluster '{cluster_id}' is not a valid candidate "
            f"for decision '{decision_id}'"
        )
        super().__init__(message)


class NoCandidatesError(DomainError):
    """Raised when a decision has no candidates to accept."""

    def __init__(self, decision_id: str) -> None:
        self.decision_id = decision_id
        message = f"Decision '{decision_id}' has no candidates"
        super().__init__(message)
