/**
 * Revenue Autopsy REST API Service Layer
 * Typed boundary strictly consuming Phase 15 FastAPI REST endpoints (/api/v1/*).
 * Zero AI keys or provider secrets in frontend.
 */

import {
  FullIncidentContext,
  Incident,
  Evidence,
  ActionPlan,
  Outcome,
  ExecutionResult,
  ProvenanceEvent,
  InvestigationWorkflowResponse,
} from '../types/domain';
import { MOCK_INCIDENTS_CONTEXT, MOCK_MERCHANT } from './mockData';

export const DEFAULT_MERCHANT_ID = '00000000-0000-0000-0000-000000000001';

export class APIError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

class RevenueAutopsyAPI {
  private baseUrl = '/api/v1';
  private merchantId: string = DEFAULT_MERCHANT_ID;

  setMerchantId(id: string) {
    this.merchantId = id;
  }

  getMerchantId(): string {
    return this.merchantId;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Merchant-ID': this.merchantId,
      ...(options.headers as Record<string, string> || {}),
    };

    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorMessage = `HTTP ${res.status} ${res.statusText}`;
      let errorData = null;
      try {
        errorData = await res.json();
        if (errorData?.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Response wasn't JSON
      }
      throw new APIError(res.status, errorMessage, errorData);
    }

    return (await res.json()) as T;
  }

  async getMerchant() {
    return {
      ...MOCK_MERCHANT,
      merchant_id: this.merchantId,
    };
  }

  async checkHealth(): Promise<{ status: string; version: string; database?: string }> {
    const res = await fetch('/health');
    if (!res.ok) {
      throw new APIError(res.status, `Health check failed with status ${res.status}`);
    }
    return res.json();
  }

  // 1. Incidents
  async getIncidents(limit = 50): Promise<Incident[]> {
    return this.request<Incident[]>(`/incidents?limit=${limit}`);
  }

  async getIncidentById(incidentId: string): Promise<FullIncidentContext> {
    // If an explicitly offline sandbox scenario is selected (non-UUID string alias), load from mockData
    if (MOCK_INCIDENTS_CONTEXT[incidentId]) {
      return JSON.parse(JSON.stringify(MOCK_INCIDENTS_CONTEXT[incidentId]));
    }
    return this.request<FullIncidentContext>(`/incidents/${incidentId}`);
  }

  async getIncidentEvidence(incidentId: string): Promise<Evidence[]> {
    if (MOCK_INCIDENTS_CONTEXT[incidentId]) {
      return JSON.parse(JSON.stringify(MOCK_INCIDENTS_CONTEXT[incidentId].evidences));
    }
    return this.request<Evidence[]>(`/incidents/${incidentId}/evidence`);
  }

  // 2. Autonomous Investigation & Policy Engine
  async runInvestigation(
    incidentId: string,
    options?: {
      baseline_hourly_rate?: number;
      current_hourly_rate?: number;
      duration_hours?: number;
      correlation_id?: string;
    }
  ): Promise<InvestigationWorkflowResponse> {
    return this.request<InvestigationWorkflowResponse>(`/incidents/${incidentId}/investigate`, {
      method: 'POST',
      body: JSON.stringify(options || {}),
    });
  }

  // 3. Action Plans
  async getActionPlan(actionId: string): Promise<ActionPlan> {
    return this.request<ActionPlan>(`/actions/${actionId}`);
  }

  // 4. Operator Authorization Sign-off
  async authorizeAction(actionId: string, notes?: string): Promise<ActionPlan> {
    return this.request<ActionPlan>(`/actions/${actionId}/authorize`, {
      method: 'POST',
      body: JSON.stringify({ notes: notes || 'Authorized via Incident Cockpit' }),
    });
  }

  // 5. Guarded Execution
  async executeAction(actionId: string): Promise<ExecutionResult> {
    return this.request<ExecutionResult>(`/actions/${actionId}/execute`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  // 6. Post-Execution Telemetry Verification
  async verifyOutcome(actionId: string): Promise<Outcome> {
    return this.request<Outcome>(`/actions/${actionId}/verify`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  // 7. Chronological Provenance & Audit Stream
  async getIncidentProvenance(incidentId: string): Promise<ProvenanceEvent[]> {
    return this.request<ProvenanceEvent[]>(`/incidents/${incidentId}/provenance`);
  }

  // 8. Outcomes Ledger
  async getOutcomes(limit = 50): Promise<Outcome[]> {
    return this.request<Outcome[]>(`/outcomes?limit=${limit}`);
  }
}

export const api = new RevenueAutopsyAPI();
