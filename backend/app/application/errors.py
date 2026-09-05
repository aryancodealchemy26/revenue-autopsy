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
