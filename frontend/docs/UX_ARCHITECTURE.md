# Revenue Autopsy — Frontend UX Architecture & Design Specification (Phase 14A)

---

## 1. Product Vision & Design Philosophy

**Revenue Autopsy** is an enterprise-grade **Revenue Incident Response & Orchestration Engine**. It is not a passive analytics dashboard or generic chart repository; it is an active operational workspace designed for payment operations, engineering, and finance leads.

### 1.1 Core Principles
- **Incident as the Primary Entity**: The entire user journey revolves around detected revenue anomalies: *Signal → Incident → Investigation → Revenue at Risk → Recovery Plan → Deterministic Policy → Execution → Verification → Economic Outcome*.
- **Clarity Over Clutter**: Inspired by the precision and restrained elegance of modern financial infrastructure (Stripe, Razorpay) without clone aesthetics.
- **Light Enterprise Canvas**: Clean, high-contrast, neutral canvas with generous whitespace, crisp 1px borders, subtle surface elevations, and semantic color used *exclusively* for operational meaning (Emerald for Verified/Success, Amber for Approval Required, Rose for Critical/Deny/Failed, Indigo for In-Flight/Active).
- **Zero Hallucinated Metrics**: No decorative pseudo-metrics or AI gimmickry. Every displayed number is grounded in deterministic backend calculations using standard currency decimal precision.
- **Explicit Trust Boundaries**: Visual distinction between **AI Proposal** (untrusted proposal from LangGraph Investigator/Planner) and **Deterministic Policy Authorization** (fail-closed rule validation).

---

## 2. Information Architecture & Sitemap

```
Revenue Autopsy Platform
├── Public Website (Marketing & Product Narrative)
│   ├── /                      (Hero, Incident-to-Recovery Flow, Feature Highlights)
│   ├── /how-it-works          (Interactive Incident Simulation Walkthrough)
│   └── /security              (Deterministic Policy Boundaries & Tenant Isolation)
│
└── Operational Workspace (/app)
    ├── Workspace Top Bar      (Tenant Merchant Switcher, Operational Status, Notifications)
    ├── Navigation Sidebar
    │   ├── Overview           (/app/overview)
    │   ├── Revenue Health     (/app/health)
    │   ├── Revenue at Risk    (/app/revenue-at-risk)
    │   ├── Operations
    │   │   ├── Incidents      (/app/incidents)
    │   │   │   └── :id        (/app/incidents/:id — PRIMARY OPERATIONAL SCREEN)
    │   │   ├── Actions        (/app/actions)
    │   │   └── Outcomes       (/app/outcomes)
    │   ├── Control
    │   │   ├── Policies       (/app/policies)
    │   │   └── Audit Trail    (/app/audit-trail)
    │   └── System
    │       ├── Integrations   (/app/integrations)
    │       └── Settings       (/app/settings)
```

---

## 3. Public Website Specification

### 3.1 Hero Section
- **Core Narrative**: *"When revenue drops, find out why. Then recover it."*
- **Sub-headline**: *"Autonomous diagnostic intelligence meets deterministic financial policy. Revenue Autopsy investigates payment drops, proposes bounded mitigations, enforces strict authorization rules, and verifies recovered revenue."*
- **Primary CTAs**:
  - `[ Explore Interactive Incident ]` (Loads sandbox demo incident in app)
  - `[ View Architecture & Security ]`

### 3.2 Interactive Revenue-Incident Flow Visual
An interactive horizontal lifecycle pipeline illustrating a live incident moving through the system:

```
[ 1. Signal ] ──> [ 2. Incident ] ──> [ 3. Investigation ] ──> [ 4. Revenue at Risk ] ──> [ 5. Recovery Plan ] ──> [ 6. Policy Check ] ──> [ 7. Execution ] ──> [ 8. Verification ] ──> [ 9. Recovered ]
```

- **Interactive State**: Users can click any stage of the pipeline to inspect real operational data payloads (e.g., clicking *Policy Check* displays the deterministic rule evaluation rejecting unauthorized actions or requesting human approval).

---

## 4. Screen-by-Screen Specifications

### 4.1 Overview (`/app/overview`)
Not a generic KPI dashboard; provides instant triage situational awareness:
1. **Active Incidents Strip**: Summary cards partitioned by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) with real-time counters and total active `revenue_at_risk`.
2. **Economic Recovery Summary**: Total revenue at risk, verified recovered revenue, verified protected revenue, and aggregate recovery rate for the active period.
3. **Live Incident Triage Table**: Ranked list of open incidents requiring attention, showing detected time, incident type, root cause summary, risk amount, and current lifecycle stage.
4. **Autonomous Operational Status**: Real-time health of AI Gateway, Deterministic Policy Engine, and Provider Execution Adapters (e.g. Razorpay Test Mode / Simulation).

---

### 4.2 Incidents List (`/app/incidents`)
Filterable, high-density incident queue with instant search:
- **Filters**: Severity (`Critical`, `High`, `Medium`, `Low`), Status (`Detected`, `Investigating`, `Action Proposed`, `Action Approved`, `Resolved`, `Closed`), Incident Type (`Payment Drop Spike`, `Auth Failure Surge`, `Settlement Delay`, `Dispute Spike`, `Webhook Latency`), Time Range, Min Revenue at Risk.
- **Columns**:
  - `Incident ID & Title` (with detected timestamp and merchant context)
  - `Incident Type` (with type icon badge)
  - `Severity` (semantic color badge)
  - `Revenue at Risk` (tabular numeral currency)
  - `Status` (lifecycle pill badge)
  - `Confidence Score` (percentage badge)
  - `Actions / Next Step` (e.g. "Review Action Plan", "Executing", "Verified")

---

### 4.3 Incident Detail (`/app/incidents/:id`) — PRIMARY OPERATIONAL SCREEN
A unified 3-column operational cockpit presenting the complete lifecycle of a single incident:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Header: Incident ID #inc_8f92a | Type: Payment Drop Spike | Severity: HIGH | Status: RESOLVED | Detected: 12 mins ago      │
├────────────────────────────────────────┬───────────────────────────────────────────┬────────────────────────────────────────┤
│ LEFT COLUMN: Diagnostic Evidence       │ CENTER COLUMN: Investigation & Recovery   │ RIGHT COLUMN: Execution & Verification │
├────────────────────────────────────────┼───────────────────────────────────────────┼────────────────────────────────────────┤
│ 1. Incident Metrics Data               │ 1. Root Cause Summary                     │ 1. Action Plan Status                  │
│    - Revenue at Risk: ₹45,000.00       │    - Primary Cause: Gateway Timeout       │    - Type: GATEWAY_REROUTE             │
│    - Confidence: 90%                   │    - Affected Cohorts: HDFC_NETBANKING    │    - Target: gateway_axis_secondary    │
│    - Currency: INR                     │    - Conclusive: True (90% Conf)          │    - Expected Recovery: ₹35,000.00     │
│                                        │                                           │                                        │
│ 2. Telemetry Stream & Evidence         │ 2. Deterministic Policy Boundary (Banner) │ 2. Execution Record                    │
│    - ev_1: Error rate surge 14.2%      │    - Policy Decision: ALLOW               │    - Provider: Razorpay Test Mode      │
│    - ev_2: P99 latency 4,200ms         │    - Rules Passed: 6/6                    │    - Reference: ord_test_98712         │
│    - ev_3: Webhook delay 8,400ms       │    - Policy Version: 1.0.0                │    - Status: SUCCESS / SIMULATED       │
│                                        │                                           │                                        │
│ 3. Affected Cohort Breakdown           │ 3. Proposed Intervention Plan             │ 3. Economic Verification Outcome       │
│    - HDFC Netbanking (82% errors)      │    - Risk Level: LOW                      │    - Status: VERIFIED_SUCCESS          │
│    - Axis Bank (Normal, 0.4% errors)   │    - Expected Recovery: ₹35,000.00        │    - Recovered Revenue: ₹0.00          │
│                                        │    - Approval Required: False             │    - Protected Revenue: ₹35,000.00     │
│                                        │    - [ Authorize / Execute Action ]       │    - Recovery Rate: 77.78%             │
│                                        │                                           │    - Remaining Risk: ₹10,000.00        │
├────────────────────────────────────────┴───────────────────────────────────────────┴────────────────────────────────────────┤
│ BOTTOM: End-to-End Chronological Operational Audit Trail (Signal → Evidence → AI → Policy → Executor → Outcome)            │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.4 Actions (`/app/actions`)
Dedicated view of all proposed, approved, executing, and completed mitigation action plans:
- Visual state breakdown:
  - `PROPOSED`: AI proposed, awaiting policy check.
  - `POLICY_CHECK_PENDING`: Policy evaluated, manual human authorization required.
  - `APPROVED`: Policy approved (auto or human), ready for execution.
  - `EXECUTING`: Action in-flight with execution provider.
  - `COMPLETED`: Execution succeeded / simulated truthfully.
  - `REJECTED`: Policy denied or human rejected.
  - `FAILED`: Execution adapter failed closed.
- Interactive Action Modal: Allows authorized operators to review policy limits snapshot and click `[ Approve & Execute ]` or `[ Reject Plan ]`.

---

### 4.5 Outcomes (`/app/outcomes`)
Verified economic results ledger:
- Lists all completed interventions with:
  - `Outcome ID` & Associated `Incident ID`
  - `Outcome Type` (`REVENUE_RECOVERED`, `REVENUE_PROTECTED`, `PARTIAL_RECOVERY`, `NO_IMPACT`, `FAILED_RECOVERY`)
  - `Total Impact Amount` (in INR / merchant currency)
  - `Recovered Amount` vs `Protected Amount`
  - `Recovery Rate` percentage
  - `Verification Timestamp`
  - `Auditable Reference Payload` (clickable JSON viewer showing post-execution telemetry IDs, execution IDs, and correlation keys).

---

### 4.6 Policies (`/app/policies`)
Visual rulebook inspector explaining the deterministic safety boundaries:
- **Visual AI-to-Policy Boundary**: Demonstrates that LLM suggestions are untrusted inputs evaluated against fixed deterministic rules.
- **Active Rule Inventory**:
  - `INPUT_INTEGRITY`: Tenant isolation, non-negative amounts, recovery $\le$ revenue at risk.
  - `ACTION_ALLOWLIST`: Permitted action types (`GATEWAY_REROUTE`, `RETRY_PAYMENT`, `MERCHANT_ALERT`, `WEBHOOK_RESYNC`, `RATE_LIMIT_ADJUSTMENT`).
  - `MONETARY_LIMIT`: Auto-allow cap ($\le \text{₹}50,000$), manual approval range, absolute cap ($\le \text{₹}5,00,000$).
  - `RISK_THRESHOLD`: High-risk mandatory human approval, medium-risk cap ($\text{₹}25,000$).
  - `CONFIDENCE_THRESHOLD`: Auto-allow ($\ge 0.70$), approval required ($0.40 - 0.70$), deny ($< 0.40$).
  - `DUPLICATE_PROTECTION`: Active concurrent action rejection on identical targets.

---

### 4.7 Audit Trail (`/app/audit-trail`)
End-to-end provenance tracker:
- Search by `incident_id`, `action_id`, `execution_id`, `correlation_id`, or `merchant_id`.
- Visual tree / step-by-step audit record:
  $$\text{Incident} \longrightarrow \text{Evidence} \longrightarrow \text{Investigation} \longrightarrow \text{ActionPlan} \longrightarrow \text{PolicyDecision} \longrightarrow \text{ExecutionResult} \longrightarrow \text{Outcome}$$

---

### 4.8 Revenue Health (`/app/health`)
Grounded telemetry streams:
- Route failure rates over time.
- P95 / P99 payment gateway latency.
- Webhook delivery lag.
- Merchant authorization rate trends.

---

### 4.9 Integrations & Settings (`/app/integrations`, `/app/settings`)
Exposes only supported capabilities:
- **Razorpay Integration**: Test Mode credentials (`Key ID`, masked `Key Secret`), Webhook status, environment mode indicator (`TEST MODE` badge).
- **Merchant Settings**: Currency configuration (`INR`, `USD`, `EUR`), webhook notification endpoints.

---

## 5. Design System Tokens & Foundations (Light Enterprise)

### 5.1 Color Palette
```css
:root {
  /* Neutral Canvas & Surfaces */
  --bg-canvas: #FAFAFA;
  --bg-surface: #FFFFFF;
  --bg-surface-subtle: #F8FAFC;
  --bg-surface-hover: #F1F5F9;

  /* Text Hierarchy */
  --text-primary: #0F172A;   /* Slate 900 */
  --text-secondary: #475569; /* Slate 600 */
  --text-muted: #94A3B8;     /* Slate 400 */
  --text-inverse: #FFFFFF;

  /* Borders & Dividers */
  --border-subtle: #F1F5F9;
  --border-default: #E2E8F0;
  --border-strong: #CBD5E1;

  /* Primary Brand / Accent */
  --accent-primary: #0F172A; /* Restrained slate / dark enterprise button */
  --accent-primary-hover: #1E293B;
  --accent-interactive: #2563EB; /* Royal blue for clickable links */

  /* Semantic Status Tokens */
  --status-success-bg: #ECFDF5;
  --status-success-text: #065F46;
  --status-success-border: #A7F3D0;

  --status-warning-bg: #FFFBEB;
  --status-warning-text: #92400E;
  --status-warning-border: #FDE68A;

  --status-danger-bg: #FEF2F2;
  --status-danger-text: #991B1B;
  --status-danger-border: #FECACA;

  --status-info-bg: #EEF2FF;
  --status-info-text: #3730A3;
  --status-info-border: #C7D2FE;
}
```

### 5.2 Typography Scale
- **Font Stack**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `sans-serif`
- **Monospace Stack (for IDs, Hashes, Currency numbers)**: `"JetBrains Mono"`, `"Fira Code"`, `SFMono-Regular`, `monospace`
- **Scale**:
  - Display Title: `28px` / `line-height: 36px` / `font-weight: 600`
  - Section Header (H1): `20px` / `line-height: 28px` / `font-weight: 600`
  - Card Title (H2): `16px` / `line-height: 24px` / `font-weight: 600`
  - Body Text: `14px` / `line-height: 20px` / `font-weight: 400`
  - Caption / Meta: `12px` / `line-height: 16px` / `font-weight: 500`
  - Code / Numbers: `13px` / `tabular-nums` / `font-weight: 500`

### 5.3 Spacing & Layout
- Grid unit: `4px` baseline
- Spacing scale: `4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`
- Border Radius: `4px` (subtle badges), `6px` (buttons, inputs), `8px` (cards, modals)
- Elevation Shadows:
  - `shadow-sm`: `0 1px 2px 0 rgba(0, 0, 0, 0.05)`
  - `shadow-md`: `0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04)`
  - `shadow-modal`: `0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)`

---

## 6. Backend Domain Model Mapping

| Frontend View / Component | Backend Domain Entity | Key Fields Displayed | Backend Status / Enums |
| :--- | :--- | :--- | :--- |
| **Incident List & Detail** | `Incident` | `incident_id`, `incident_type`, `severity`, `status`, `detected_at`, `revenue_at_risk`, `confidence`, `description` | `DETECTED`, `INVESTIGATING`, `ACTION_PROPOSED`, `ACTION_APPROVED`, `RESOLVED`, `CLOSED` |
| **Diagnostic Evidence** | `Evidence` | `evidence_id`, `evidence_type`, `source`, `observed_at`, `summary`, `metrics_data` | `TELEMETRY_METRIC`, `LOG_EXCERPT`, `API_TRACE`, `STATISTICAL_ANOMALY` |
| **Investigation Result** | `InvestigationResult` | `primary_cause`, `secondary_causes`, `confidence`, `confidence_rationale`, `affected_cohorts`, `is_conclusive` | Pydantic Schema output from LangGraph Agent |
| **Recovery Action Plan** | `ActionPlan` | `action_id`, `action_type`, `target`, `expected_recovery`, `risk_level`, `confidence`, `approval_required`, `status`, `rationale` | `PROPOSED`, `POLICY_CHECK_PENDING`, `APPROVED`, `REJECTED`, `EXECUTING`, `COMPLETED`, `FAILED` |
| **Policy Evaluation Box** | `PolicyEvaluationResult` | `decision_id`, `decision`, `reasons`, `rule_results`, `evaluated_limits`, `policy_version`, `evaluated_at` | `ALLOW`, `REQUIRE_APPROVAL`, `DENY` |
| **Execution Card** | `ExecutionResult` | `execution_id`, `provider`, `status`, `is_simulated`, `provider_reference`, `error_message`, `executed_at`, `idempotency_key` | `SUCCESS`, `FAILED`, `SIMULATED` |
| **Economic Outcome** | `Outcome` | `outcome_id`, `outcome_type`, `amount`, `status`, `measured_at`, `reference_data` (`recovered_revenue`, `protected_revenue`, `recovery_rate`, `remaining_risk`) | `REVENUE_RECOVERED`, `REVENUE_PROTECTED`, `PARTIAL_RECOVERY`, `NO_IMPACT`, `FAILED_RECOVERY` |

---

## 7. Interaction Principles & Safety Boundaries

1. **Button-to-API Direct Mapping**:
   - `[ Run Investigation ]` $\rightarrow$ `POST /api/v1/orchestration/investigate`
   - `[ Authorize Action ]` $\rightarrow$ transitions `ActionPlan` from `POLICY_CHECK_PENDING` to `APPROVED`
   - `[ Execute Mitigation ]` $\rightarrow$ calls `ActionExecutor.execute_action`
   - `[ Verify Outcome ]` $\rightarrow$ calls `VerificationService.verify_execution_outcome`
2. **Explicit Simulation Badges**: Every simulated action or outcome is visually tagged with a `SIMULATED SANDBOX` badge to guarantee transparency.
3. **Fail-Closed Confirmation Dialogs**: Actions requiring manual approval clearly present the policy limit rules that were triggered and require explicit confirmation before execution.
