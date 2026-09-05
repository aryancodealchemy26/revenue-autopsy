"""Execution domain enums."""

from enum import Enum


class ExecutionStatus(str, Enum):
    """Lifecycle and completion status of an ActionPlan execution attempt."""

    SUCCESS = "success"
    FAILED = "failed"
    SIMULATED = "simulated"
