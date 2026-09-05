import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import get_current_merchant_id
from app.api.dependencies.services import (
    get_incident_service,
    get_investigation_service,
    get_orchestration_service,
    get_uow,
)
from app.api.schemas.actions import ActionPlanResponse, PolicyEvaluationResponse
from app.api.schemas.incidents import (
    EvidenceResponse,
    FullIncidentContextResponse,
    IncidentResponse,
    InvestigationResultResponse,
    InvestigationWorkflowResponse,
    RunInvestigationRequest,
)
from app.api.schemas.outcomes import OutcomeResponse
from app.api.schemas.provenance import ProvenanceEventResponse
from app.application.errors import (
    AIProviderUnavailableWorkflowError,
    InvestigationWorkflowError,
    InvestigationWorkflowFailedError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.services.incident_service import IncidentService
from app.application.services.investigation_service import InvestigationService
from app.application.services.orchestration_service import IncidentOrchestrationService
from app.domain.actions.enums import ActionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    limit: int = Query(50, ge=1, le=100),
    merchant_id: UUID = Depends(get_current_merchant_id),
    incident_service: IncidentService = Depends(get_incident_service),
) -> List[IncidentResponse]:
    """List all incidents associated with the authenticated merchant tenant context."""
    incidents = await incident_service.list_merchant_incidents(merchant_id=merchant_id, limit=limit)
    return [IncidentResponse.model_validate(inc) for inc in incidents]


@router.get("/{incident_id}", response_model=FullIncidentContextResponse)
async def get_incident_cockpit(
    incident_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    uow: UnitOfWork = Depends(get_uow),
) -> FullIncidentContextResponse:
    """Retrieve full aggregated incident cockpit context (Incident, Evidence, Action, Policy, Outcome)."""
    async with uow:
        incident = await uow.incidents.get_by_id(incident_id)
        if not incident or incident.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found.",
            )

        evidences = await uow.evidence.list_by_incident(incident_id)
        actions = await uow.action_plans.list_by_incident(incident_id)
        latest_action = actions[-1] if actions else None

        latest_outcome = None
        if latest_action:
            latest_outcome = await uow.outcomes.get_by_action_id(latest_action.action_id)

        # Build investigation result if available from action / evidence metadata
        investigation_result = None
        if latest_action and latest_action.rationale:
            investigation_result = InvestigationResultResponse(
                incident_id=incident_id,
                primary_cause=latest_action.rationale,
                secondary_causes=[],
                confidence=float(latest_action.confidence),
                confidence_rationale=f"Attributed to {latest_action.action_type.value} operational disruption.",
                affected_cohorts=[latest_action.target] if latest_action.target else [],
                evidence_keys_used=[str(e.evidence_id) for e in evidences],
                is_conclusive=True,
            )

        # Policy decision derived from action plan status / metadata
        policy_decision = None
        if latest_action:
            policy_decision = PolicyEvaluationResponse(
                decision_id=latest_action.action_id,
                action_id=latest_action.action_id,
                incident_id=incident_id,
                merchant_id=merchant_id,
                decision="allow" if latest_action.status == ActionStatus.APPROVED or not latest_action.approval_required else "require_approval",
                reasons=[f"Action {latest_action.action_type.value} evaluated under active tenant limits."],
                rule_results=[],
                evaluated_limits={"expected_recovery": str(latest_action.expected_recovery)},
                policy_version="1.0.0",
                evaluated_at=latest_action.created_at,
            )

        return FullIncidentContextResponse(
            incident=IncidentResponse.model_validate(incident),
            evidences=[EvidenceResponse.model_validate(e) for e in evidences],
            investigation=investigation_result,
            proposed_action=ActionPlanResponse.model_validate(latest_action) if latest_action else None,
            policy_decision=policy_decision,
            execution_result=None,
            outcome=OutcomeResponse.model_validate(latest_outcome) if latest_outcome else None,
        )


@router.get("/{incident_id}/evidence", response_model=List[EvidenceResponse])
async def list_incident_evidence(
    incident_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    incident_service: IncidentService = Depends(get_incident_service),
    investigation_service: InvestigationService = Depends(get_investigation_service),
) -> List[EvidenceResponse]:
    """List all diagnostic evidence payloads associated with an incident."""
    incident = await incident_service.get_incident(incident_id)
    if incident.merchant_id != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    evidences = await investigation_service.get_incident_evidence(incident_id)
    return [EvidenceResponse.model_validate(e) for e in evidences]


@router.post("/{incident_id}/investigate", response_model=InvestigationWorkflowResponse)
async def investigate_incident(
    incident_id: UUID,
    request: RunInvestigationRequest,
    merchant_id: UUID = Depends(get_current_merchant_id),
    incident_service: IncidentService = Depends(get_incident_service),
    orchestration_service: IncidentOrchestrationService = Depends(get_orchestration_service),
) -> InvestigationWorkflowResponse:
    """Trigger autonomous LangGraph investigation, root cause diagnosis, recovery planning, and deterministic policy evaluation."""
    incident = await incident_service.get_incident(incident_id)
    if incident.merchant_id != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    try:
        result_state = await orchestration_service.run_investigation_workflow(
            incident_id=incident_id,
            baseline_hourly_rate=request.baseline_hourly_rate,
            current_hourly_rate=request.current_hourly_rate,
            duration_hours=request.duration_hours,
            correlation_id=request.correlation_id,
        )
    except AIProviderUnavailableWorkflowError as e:
        logger.warning("AI provider unavailable during investigation of %s: %s", incident_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI investigation service is temporarily unavailable. Please retry shortly.",
        )
    except (InvestigationWorkflowFailedError, InvestigationWorkflowError) as e:
        logger.error("Investigation workflow failed for %s: %s", incident_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Investigation workflow failed to produce a valid diagnosis.",
        )

    # Reload updated incident
    updated_incident = await incident_service.get_incident(incident_id)

    inv_dto = result_state.get("investigation")
    inv_response = None
    if inv_dto:
        inv_response = InvestigationResultResponse(
            incident_id=incident_id,
            primary_cause=inv_dto.primary_cause,
            secondary_causes=inv_dto.secondary_causes,
            confidence=inv_dto.confidence,
            confidence_rationale=inv_dto.confidence_rationale,
            affected_cohorts=inv_dto.affected_cohorts,
            evidence_keys_used=inv_dto.evidence_keys_used,
            is_conclusive=inv_dto.is_conclusive,
        )

    proposed_action = result_state.get("proposed_action")
    action_response = ActionPlanResponse.model_validate(proposed_action) if proposed_action else None

    policy_decision = result_state.get("policy_decision")
    policy_response = PolicyEvaluationResponse.model_validate(policy_decision) if policy_decision else None

    return InvestigationWorkflowResponse(
        incident=IncidentResponse.model_validate(updated_incident),
        investigation=inv_response,
        revenue_at_risk_calculated=result_state.get("revenue_at_risk", updated_incident.revenue_at_risk),
        proposed_action=action_response,
        policy_decision=policy_response,
    )


@router.get("/{incident_id}/provenance", response_model=List[ProvenanceEventResponse])
async def get_incident_provenance(
    incident_id: UUID,
    merchant_id: UUID = Depends(get_current_merchant_id),
    uow: UnitOfWork = Depends(get_uow),
) -> List[ProvenanceEventResponse]:
    """Retrieve chronological provenance and audit stream for an incident."""
    async with uow:
        incident = await uow.incidents.get_by_id(incident_id)
        if not incident or incident.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found.",
            )

        evidences = await uow.evidence.list_by_incident(incident_id)
        actions = await uow.action_plans.list_by_incident(incident_id)

        events: List[ProvenanceEventResponse] = []

        # 1. Incident Detection
        events.append(
            ProvenanceEventResponse(
                step="1. Incident Signal Detected",
                actor="Signal Ingestion Engine",
                timestamp=incident.detected_at,
                status=incident.status.value.upper(),
                summary=f"{incident.incident_type.value} anomaly detected. Initial revenue at risk: {incident.revenue_at_risk} {incident.currency}.",
            )
        )

        # 2. Evidence Collected
        if evidences:
            events.append(
                ProvenanceEventResponse(
                    step="2. Evidence Collected",
                    actor="Telemetry & Logs Collector",
                    timestamp=evidences[0].observed_at,
                    status="COLLECTED",
                    summary=f"Collected {len(evidences)} diagnostic evidence payloads ({', '.join(e.evidence_type.value for e in evidences)}).",
                )
            )

        # 3. Actions & Outcomes
        for action in actions:
            events.append(
                ProvenanceEventResponse(
                    step="3. Action Plan Proposed",
                    actor="Recovery Planner Agent",
                    timestamp=action.created_at,
                    status=action.status.value.upper(),
                    summary=f"Formulated {action.action_type.value} plan targeting {action.target}. Expected recovery: {action.expected_recovery} {action.currency}.",
                )
            )

            outcome = await uow.outcomes.get_by_action_id(action.action_id)
            if outcome:
                events.append(
                    ProvenanceEventResponse(
                        step="4. Economic Verification",
                        actor="Verification Engine",
                        timestamp=outcome.measured_at,
                        status=outcome.status.value.upper(),
                        summary=f"Verified economic outcome: {outcome.amount} {outcome.currency} protected under outcome {outcome.outcome_type.value}.",
                    )
                )

        return events
