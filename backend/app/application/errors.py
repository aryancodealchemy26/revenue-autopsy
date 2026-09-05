"""Application layer exception hierarchy."""

from uuid import UUID


class ApplicationError(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class EntityNotFoundError(ApplicationError):
    """Base exception when an entity is not found in the persistence layer."""

    def __init__(self, entity_name: str, entity_id: UUID):
        super().__init__(f"{entity_name} with id '{entity_id}' was not found.")
        self.entity_name = entity_name
        self.entity_id = entity_id


class MerchantNotFoundError(EntityNotFoundError):
    """Raised when a merchant entity cannot be found."""

    def __init__(self, merchant_id: UUID):
        super().__init__("Merchant", merchant_id)


class IncidentNotFoundError(EntityNotFoundError):
    """Raised when an incident entity cannot be found."""

    def __init__(self, incident_id: UUID):
        super().__init__("Incident", incident_id)


class EvidenceNotFoundError(EntityNotFoundError):
    """Raised when an evidence entity cannot be found."""

    def __init__(self, evidence_id: UUID):
        super().__init__("Evidence", evidence_id)


class ActionPlanNotFoundError(EntityNotFoundError):
    """Raised when an action plan entity cannot be found."""

    def __init__(self, action_id: UUID):
        super().__init__("ActionPlan", action_id)


class OutcomeNotFoundError(EntityNotFoundError):
    """Raised when an outcome entity cannot be found."""

    def __init__(self, outcome_id: UUID):
        super().__init__("Outcome", outcome_id)


class InvalidStateTransitionError(ApplicationError):
    """Raised when an invalid entity status transition is attempted."""

    def __init__(self, entity_name: str, current_status: str, target_status: str):
        super().__init__(
            f"Cannot transition {entity_name} from status '{current_status}' to '{target_status}'."
        )
        self.entity_name = entity_name
        self.current_status = current_status
        self.target_status = target_status


class RepositoryError(ApplicationError):
    """Raised when a repository operation encounters an unrecoverable failure."""

    pass


class ExecutionError(ApplicationError):
    """Base exception for action plan execution failures."""

    pass


class ActionNotApprovedError(ExecutionError):
    """Raised when an unapproved action plan is dispatched for execution."""

    def __init__(self, action_id: UUID, current_status: str):
        super().__init__(
            f"Action plan '{action_id}' is in status '{current_status}' and cannot be executed without approval."
        )
        self.action_id = action_id
        self.current_status = current_status


class DuplicateExecutionError(ExecutionError):
    """Raised when attempting to execute an action plan that has already been executed."""

    def __init__(self, action_id: UUID, current_status: str):
        super().__init__(
            f"Action plan '{action_id}' has already been processed with status '{current_status}'."
        )
        self.action_id = action_id
        self.current_status = current_status


class TenantMismatchError(ExecutionError):
    """Raised when tenant merchant boundaries are violated during execution."""

    def __init__(self, message: str):
        super().__init__(message)


class ProviderExecutionError(ExecutionError):
    """Raised when an external provider encounters an unrecoverable error during execution."""

    def __init__(self, provider: str, message: str):
        super().__init__(f"Provider '{provider}' execution failed: {message}")
        self.provider = provider
