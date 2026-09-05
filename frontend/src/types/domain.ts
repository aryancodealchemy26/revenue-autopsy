/**
 * Domain Type Definitions for Revenue Autopsy
 * Strictly aligned 1:1 with Backend Pydantic Schemas (Phases 5-13)
 */

export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';
export type IncidentStatus = 'detected' | 'investigating' | 'action_proposed' | 'action_approved' | 'resolved' | 'closed';
export type IncidentType = 
  | 'payment_drop_spike' 
  | 'authorization_failure_surge' 
  | 'settlement_delay' 
  | 'dispute_spike' 
  | 'webhook_latency_spike';

export type EvidenceType = 
  | 'telemetry_metric' 
  | 'log_excerpt' 
  | 'api_trace' 
  | 'statistical_anomaly';

export type ActionType = 
  | 'gateway_reroute' 
  | 'retry_payment' 
  | 'merchant_alert' 
  | 'webhook_resync' 
  | 'rate_limit_adjustment';

export type RiskLevel = 'low' | 'medium' | 'high';
export type ActionStatus = 
  | 'proposed' 
  | 'policy_check_pending' 
  | 'approved' 
  | 'rejected' 
  | 'executing' 
  | 'completed' 
  | 'failed';

export type PolicyDecision = 'allow' | 'require_approval' | 'deny';
export type PolicyRuleCode = 
  | 'input_integrity' 
  | 'action_allowlist' 
  | 'monetary_limit' 
  | 'risk_threshold' 
  | 'confidence_threshold' 
  | 'merchant_permission' 
  | 'duplicate_protection';

export type ExecutionStatus = 'success' | 'failed' | 'simulated';
export type OutcomeType = 
  | 'revenue_recovered' 
  | 'revenue_protected' 
  | 'partial_recovery' 
  | 'no_impact' 
  | 'failed_recovery';

export type OutcomeStatus = 'measured' | 'verified' | 'audited';
export type VerificationStatus = 'verified_success' | 'verified_failure' | 'inconclusive' | 'pending';

export interface Evidence {
  evidence_id: string;
  incident_id: string;
  evidence_type: EvidenceType;
  source: string;
  observed_at: string;
  summary: string;
  metrics_data: Record<string, any>;
}

export interface Incident {
  incident_id: string;
  merchant_id: string;
  incident_type: IncidentType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  detected_at: string;
  revenue_at_risk: string; // Decimal string representation
  currency: string;
  confidence: string;     // Decimal string (0.00 to 1.00)
  description: string;
  evidences?: Evidence[];
}

export interface InvestigationResult {
  incident_id: string;
  primary_cause: string;
  secondary_causes: string[];
  confidence: number;
  confidence_rationale: string;
  affected_cohorts: string[];
  evidence_keys_used: string[];
  is_conclusive: boolean;
}

export interface ActionPlan {
  action_id: string;
  incident_id: string;
  action_type: ActionType;
  target: string;
  expected_recovery: string; // Decimal string
  currency: string;
  risk_level: RiskLevel;
  confidence: string;        // Decimal string
  approval_required: boolean;
  status: ActionStatus;
  rationale: string;
  created_at: string;
}

export interface PolicyRuleResult {
  rule_code: PolicyRuleCode;
  passed: boolean;
  decision_impact: PolicyDecision;
  message: string;
  evaluated_data: Record<string, any>;
}

export interface PolicyEvaluationResult {
  decision_id: string;
  action_id: string;
  incident_id: string;
  merchant_id: string;
  decision: PolicyDecision;
  reasons: string[];
  rule_results: PolicyRuleResult[];
  evaluated_limits: Record<string, any>;
  policy_version: string;
  evaluated_at: string;
}

export interface ExecutionResult {
  execution_id: string;
  merchant_id: string;
  incident_id: string;
  action_id: string;
  provider: string;
  action_type: ActionType;
  status: ExecutionStatus;
  is_simulated: boolean;
  provider_reference?: string;
  error_message?: string;
  idempotency_key: string;
  executed_at: string;
  details: Record<string, any>;
}

export interface Outcome {
  outcome_id: string;
  incident_id: string;
  action_id: string;
  outcome_type: OutcomeType;
  amount: string; // Decimal string
  currency: string;
  status: OutcomeStatus;
  measured_at: string;
  reference_data: {
    merchant_id?: string;
    incident_id?: string;
    action_id?: string;
    execution_id?: string;
    execution_status?: string;
    execution_provider?: string;
    is_simulated?: boolean;
    verification_status?: VerificationStatus;
    revenue_at_risk?: string;
    recovered_revenue?: string;
    protected_revenue?: string;
    total_impact?: string;
    recovery_rate?: string;
    remaining_revenue_at_risk?: string;
    correlation_id?: string;
    evidence_ids?: string[];
    [key: string]: any;
  };
}

export interface ProvenanceEvent {
  step: string;
  actor: string;
  timestamp: string;
  status: string;
  summary: string;
}

export interface InvestigationWorkflowResponse {
  incident: Incident;
  investigation: InvestigationResult | null;
  revenue_at_risk_calculated: string;
  proposed_action: ActionPlan | null;
  policy_decision: PolicyEvaluationResult | null;
}

export interface FullIncidentContext {
  incident: Incident;
  evidences: Evidence[];
  investigation?: InvestigationResult;
  proposed_action?: ActionPlan;
  policy_decision?: PolicyEvaluationResult;
  execution_result?: ExecutionResult;
  outcome?: Outcome;
}

