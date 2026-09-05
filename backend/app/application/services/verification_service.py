"""Verification application service coordinating outcome recording and measurement retrieval."""

from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Optional
from uuid import UUID, uuid4

from app.application.dtos.outcomes import RecordOutcomeDTO
from app.application.errors import (
    ActionPlanNotFoundError,
    ApplicationError,
    DuplicateOutcomeError,
    IncidentNotFoundError,
    MerchantNotFoundError,
    OutcomeNotFoundError,
    TenantMismatchError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.verification_provider import VerificationEvidenceProviderPort
from app.application.state_machines import validate_incident_transition
from app.domain.actions.enums import ActionType
from app.domain.execution.enums import ExecutionStatus
from app.domain.execution.models import ExecutionResult
from app.domain.incidents.enums import IncidentStatus
from app.domain.outcomes.calculator import calculate_economic_impact
from app.domain.outcomes.enums import OutcomeStatus, OutcomeType, VerificationStatus
from app.domain.outcomes.models import Outcome
from app.infrastructure.verification.deterministic_provider import (
    DeterministicVerificationEvidenceProvider,
)

logger = logging.getLogger(__name__)


class VerificationService:
    """Application service for deterministically verifying execution outcomes and computing economic impact."""

    def __init__(
        self,
        uow: UnitOfWork,
        evidence_provider: Optional[VerificationEvidenceProviderPort] = None,
    ):
        self._uow = uow
        self._evidence_provider = evidence_provider or DeterministicVerificationEvidenceProvider()

    async def verify_execution_outcome(
        self,
        merchant_id: UUID,
        incident_id: UUID,
        action_id: UUID,
        execution_result: ExecutionResult,
        correlation_id: Optional[str] = None,
    ) -> Outcome:
        """Deterministically verify an ExecutionResult against post-execution telemetry and record an Outcome."""
        async with self._uow:
            # 1. Retrieve entities
            merchant = await self._uow.merchants.get_by_id(merchant_id)
            if not merchant:
                raise MerchantNotFoundError(merchant_id)

            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            action_plan = await self._uow.action_plans.get_by_id(action_id)
            if not action_plan:
                raise ActionPlanNotFoundError(action_id)

            # 2. Strict Tenant and Ownership Validation
            if incident.merchant_id != merchant.merchant_id:
                raise TenantMismatchError(
                    f"Incident merchant '{incident.merchant_id}' does not match caller merchant '{merchant.merchant_id}'."
                )

            if action_plan.incident_id != incident.incident_id:
                raise TenantMismatchError(
                    f"Action incident '{action_plan.incident_id}' does not match target incident '{incident.incident_id}'."
                )

            # 3. Duplicate Outcome Protection (Idempotency)
            existing_outcome = await self._uow.outcomes.get_by_action_id(action_id)
            if existing_outcome:
                raise DuplicateOutcomeError(action_id)

            # 4. Retrieve Post-Execution Telemetry
            post_evidence = await self._evidence_provider.get_post_execution_evidence(
                merchant_id=merchant.merchant_id,
                incident_id=incident.incident_id,
                action_id=action_plan.action_id,
                executed_at=execution_result.executed_at,
                correlation_id=correlation_id,
            )

            for ev in post_evidence:
                await self._uow.evidence.save(ev)

            # 5. Deterministic Verification & Economic Impact Quantification
            now = datetime.now(timezone.utc)
            if execution_result.status == ExecutionStatus.FAILED:
                verification_status = VerificationStatus.VERIFIED_FAILURE
                outcome_type = OutcomeType.FAILED_RECOVERY
                impact = calculate_economic_impact(
                    revenue_at_risk=incident.revenue_at_risk,
                    recovered_amount=Decimal("0.00"),
                    protected_amount=Decimal("0.00"),
                )
            else:
                # Execution was SUCCESS or SIMULATED: verify telemetry indicators
                telemetry_healthy = False
                telemetry_inconclusive = True

                for ev in post_evidence:
                    metrics = ev.metrics_data or {}
                    success_rate = metrics.get("post_execution_success_rate")
                    error_rate = metrics.get("post_execution_error_rate")
                    gw_status = metrics.get("gateway_status")
                    traffic_ratio = metrics.get("traffic_recovery_ratio")

                    if gw_status == "healthy" or (success_rate is not None and success_rate >= 0.90) or (traffic_ratio is not None and traffic_ratio >= 0.80):
                        telemetry_healthy = True
                        telemetry_inconclusive = False
                        break
                    elif gw_status == "unhealthy" or (error_rate is not None and error_rate >= 0.50):
                        telemetry_healthy = False
                        telemetry_inconclusive = False
                        break

                if telemetry_healthy:
                    verification_status = VerificationStatus.VERIFIED_SUCCESS
                    if action_plan.action_type in (
                        ActionType.GATEWAY_REROUTE,
                        ActionType.RATE_LIMIT_ADJUSTMENT,
                        ActionType.MERCHANT_ALERT,
                    ):
                        outcome_type = OutcomeType.REVENUE_PROTECTED
                        impact = calculate_economic_impact(
                            revenue_at_risk=incident.revenue_at_risk,
                            recovered_amount=Decimal("0.00"),
                            protected_amount=action_plan.expected_recovery,
                        )
                    else:
                        outcome_type = OutcomeType.REVENUE_RECOVERED
                        impact = calculate_economic_impact(
                            revenue_at_risk=incident.revenue_at_risk,
                            recovered_amount=action_plan.expected_recovery,
                            protected_amount=Decimal("0.00"),
                        )
                elif not telemetry_inconclusive and not telemetry_healthy:
                    verification_status = VerificationStatus.VERIFIED_FAILURE
                    outcome_type = OutcomeType.FAILED_RECOVERY
                    impact = calculate_economic_impact(
                        revenue_at_risk=incident.revenue_at_risk,
                        recovered_amount=Decimal("0.00"),
                        protected_amount=Decimal("0.00"),
                    )
                else:
                    verification_status = VerificationStatus.INCONCLUSIVE
                    outcome_type = OutcomeType.NO_IMPACT
                    impact = calculate_economic_impact(
                        revenue_at_risk=incident.revenue_at_risk,
                        recovered_amount=Decimal("0.00"),
                        protected_amount=Decimal("0.00"),
                    )

            # 6. Build Auditable Reference Payload
            reference_data = {
                "merchant_id": str(merchant.merchant_id),
                "incident_id": str(incident.incident_id),
                "action_id": str(action_plan.action_id),
                "execution_id": str(execution_result.execution_id),
                "execution_status": execution_result.status.value,
                "execution_provider": execution_result.provider,
                "is_simulated": execution_result.is_simulated,
                "verification_status": verification_status.value,
                "revenue_at_risk": str(impact.revenue_at_risk),
                "recovered_revenue": str(impact.recovered_revenue),
                "protected_revenue": str(impact.protected_revenue),
                "total_impact": str(impact.total_impact),
                "recovery_rate": str(impact.recovery_rate),
                "remaining_revenue_at_risk": str(impact.remaining_revenue_at_risk),
                "correlation_id": correlation_id,
                "evidence_ids": [str(ev.evidence_id) for ev in post_evidence],
            }

            outcome = Outcome(
                outcome_id=uuid4(),
                incident_id=incident.incident_id,
                action_id=action_plan.action_id,
                outcome_type=outcome_type,
                amount=impact.total_impact,
                currency=incident.currency,
                status=OutcomeStatus.VERIFIED,
                measured_at=now,
                reference_data=reference_data,
            )

            # 7. Update Incident status if successfully resolved
            if verification_status == VerificationStatus.VERIFIED_SUCCESS and incident.status == IncidentStatus.ACTION_APPROVED:
                validate_incident_transition(incident.status, IncidentStatus.RESOLVED)
                incident.status = IncidentStatus.RESOLVED
                await self._uow.incidents.save(incident)

            # 8. Persist and Commit
            saved_outcome = await self._uow.outcomes.save(outcome)
            await self._uow.commit()

            return saved_outcome

    async def record_outcome(
        self, incident_id: UUID, action_id: UUID, dto: RecordOutcomeDTO
    ) -> Outcome:
        """Record and persist a measured outcome for an executed action."""
        async with self._uow:
            # 1. Verify Incident exists
            incident = await self._uow.incidents.get_by_id(incident_id)
            if not incident:
                raise IncidentNotFoundError(incident_id)

            # 2. Verify ActionPlan exists and matches Incident
            plan = await self._uow.action_plans.get_by_id(action_id)
            if not plan:
                raise ActionPlanNotFoundError(action_id)
            if plan.incident_id != incident_id:
                raise ApplicationError(
                    f"ActionPlan '{action_id}' does not belong to Incident '{incident_id}'."
                )

            # 3. Construct domain Outcome
            outcome = Outcome(
                outcome_id=dto.outcome_id,
                incident_id=incident_id,
                action_id=action_id,
                outcome_type=dto.outcome_type,
                amount=dto.amount,
                currency=dto.currency,
                status=dto.status,
                measured_at=dto.measured_at,
                reference_data=dto.reference_data,
            )

            # 4. Persist and commit
            saved = await self._uow.outcomes.save(outcome)
            await self._uow.commit()
            return saved

    async def get_outcome(self, outcome_id: UUID) -> Outcome:
        """Retrieve an Outcome by ID."""
        async with self._uow:
            outcome = await self._uow.outcomes.get_by_id(outcome_id)
            if not outcome:
                raise OutcomeNotFoundError(outcome_id)
            return outcome

    async def get_action_outcome(self, action_id: UUID) -> Optional[Outcome]:
        """Retrieve the Outcome associated with a specific ActionPlan."""
        async with self._uow:
            plan = await self._uow.action_plans.get_by_id(action_id)
            if not plan:
                raise ActionPlanNotFoundError(action_id)

            return await self._uow.outcomes.get_by_action_id(action_id)
