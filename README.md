
```
Revenue-Autopsy
├─ backend
│  ├─ alembic
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions
│  │     └─ 001_initial_schema.py
│  ├─ alembic.ini
│  ├─ app
│  │  ├─ agents
│  │  │  ├─ graph
│  │  │  │  ├─ nodes.py
│  │  │  │  ├─ state.py
│  │  │  │  ├─ workflow.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ investigator
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ schemas.py
│  │  │  │  ├─ tools.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ planner
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ schemas.py
│  │  │  │  └─ __init__.py
│  │  │  └─ __init__.py
│  │  ├─ ai
│  │  │  ├─ errors.py
│  │  │  ├─ gateway.py
│  │  │  ├─ guardrails
│  │  │  │  ├─ redaction.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ ports
│  │  │  │  ├─ provider.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ providers
│  │  │  │  ├─ base.py
│  │  │  │  ├─ factory.py
│  │  │  │  ├─ fake_provider.py
│  │  │  │  ├─ openai_provider.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ schemas
│  │  │  │  ├─ messages.py
│  │  │  │  ├─ tools.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ tools.py
│  │  │  └─ __init__.py
│  │  ├─ api
│  │  │  ├─ dependencies
│  │  │  │  ├─ ai.py
│  │  │  │  ├─ services.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ routes
│  │  │  │  ├─ health.py
│  │  │  │  └─ __init__.py
│  │  │  └─ __init__.py
│  │  ├─ application
│  │  │  ├─ dtos
│  │  │  │  ├─ actions.py
│  │  │  │  ├─ incidents.py
│  │  │  │  ├─ investigations.py
│  │  │  │  ├─ outcomes.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ errors.py
│  │  │  ├─ ports
│  │  │  │  ├─ evidence_provider.py
│  │  │  │  ├─ execution_provider.py
│  │  │  │  ├─ policy_engine.py
│  │  │  │  ├─ repositories.py
│  │  │  │  ├─ unit_of_work.py
│  │  │  │  ├─ verification_provider.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ services
│  │  │  │  ├─ action_service.py
│  │  │  │  ├─ incident_service.py
│  │  │  │  ├─ investigation_service.py
│  │  │  │  ├─ orchestration_service.py
│  │  │  │  ├─ verification_service.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ state_machines.py
│  │  │  └─ __init__.py
│  │  ├─ core
│  │  │  ├─ config.py
│  │  │  ├─ errors.py
│  │  │  └─ __init__.py
│  │  ├─ domain
│  │  │  ├─ actions
│  │  │  │  ├─ enums.py
│  │  │  │  ├─ models.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ execution
│  │  │  │  ├─ enums.py
│  │  │  │  ├─ models.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ incidents
│  │  │  │  ├─ enums.py
│  │  │  │  ├─ models.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ merchants
│  │  │  │  ├─ enums.py
│  │  │  │  ├─ models.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ outcomes
│  │  │  │  ├─ calculator.py
│  │  │  │  ├─ enums.py
│  │  │  │  ├─ models.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ policies
│  │  │  │  ├─ enums.py
│  │  │  │  ├─ models.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ revenue
│  │  │  │  ├─ calculations.py
│  │  │  │  ├─ enums.py
│  │  │  │  ├─ models.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ shared.py
│  │  │  └─ __init__.py
│  │  ├─ execution
│  │  │  ├─ adapters
│  │  │  │  ├─ composite_adapter.py
│  │  │  │  ├─ razorpay_adapter.py
│  │  │  │  └─ simulation_adapter.py
│  │  │  ├─ executor.py
│  │  │  └─ __init__.py
│  │  ├─ infrastructure
│  │  │  ├─ database
│  │  │  │  ├─ base.py
│  │  │  │  ├─ mappers.py
│  │  │  │  ├─ models
│  │  │  │  │  ├─ action.py
│  │  │  │  │  ├─ incident.py
│  │  │  │  │  ├─ merchant.py
│  │  │  │  │  ├─ outcome.py
│  │  │  │  │  ├─ revenue.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  ├─ repositories
│  │  │  │  │  ├─ action.py
│  │  │  │  │  ├─ incident.py
│  │  │  │  │  ├─ merchant.py
│  │  │  │  │  ├─ outcome.py
│  │  │  │  │  ├─ revenue.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  ├─ session.py
│  │  │  │  ├─ unit_of_work.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ events
│  │  │  │  └─ __init__.py
│  │  │  ├─ evidence
│  │  │  │  ├─ deterministic_provider.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ verification
│  │  │  │  ├─ deterministic_provider.py
│  │  │  │  └─ __init__.py
│  │  │  └─ __init__.py
│  │  ├─ integrations
│  │  │  ├─ razorpay
│  │  │  │  └─ __init__.py
│  │  │  ├─ simulation
│  │  │  │  └─ __init__.py
│  │  │  └─ __init__.py
│  │  ├─ main.py
│  │  ├─ policies
│  │  │  ├─ engine.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ requirements.txt
│  └─ tests
│     ├─ agents
│     │  ├─ test_ai_failure_resilience.py
│     │  ├─ test_evidence_provider.py
│     │  ├─ test_insufficient_evidence_flow.py
│     │  ├─ test_investigator_agent.py
│     │  ├─ test_langgraph_workflow.py
│     │  ├─ test_orchestration_service.py
│     │  ├─ test_recovery_planner_agent.py
│     │  ├─ test_revenue_calculations.py
│     │  └─ __init__.py
│     ├─ ai
│     │  ├─ test_error_normalization.py
│     │  ├─ test_gateway.py
│     │  ├─ test_provider_adapters.py
│     │  ├─ test_retry_and_timeout.py
│     │  ├─ test_security_redaction.py
│     │  ├─ test_structured_output.py
│     │  ├─ test_tool_allowlist.py
│     │  └─ __init__.py
│     ├─ application
│     │  ├─ fakes.py
│     │  ├─ test_action_service.py
│     │  ├─ test_incident_service.py
│     │  ├─ test_investigation_service.py
│     │  ├─ test_state_transitions.py
│     │  ├─ test_unit_of_work.py
│     │  ├─ test_verification_service.py
│     │  └─ __init__.py
│     ├─ conftest.py
│     ├─ domain
│     │  ├─ test_actions.py
│     │  ├─ test_economic_calculator.py
│     │  ├─ test_incidents.py
│     │  ├─ test_merchants.py
│     │  ├─ test_outcomes.py
│     │  ├─ test_revenue.py
│     │  ├─ test_shared_validations.py
│     │  └─ __init__.py
│     ├─ execution
│     │  └─ test_executor.py
│     ├─ infrastructure
│     │  ├─ test_alembic_postgres.py
│     │  ├─ test_db_schema.py
│     │  ├─ test_mappers.py
│     │  ├─ test_repositories.py
│     │  └─ __init__.py
│     ├─ policies
│     │  └─ test_policy_engine.py
│     ├─ test_config.py
│     ├─ test_health.py
```

---

## Development Setup & Database Seeding

### 1. Database Migrations
Run Alembic migrations to establish the PostgreSQL schema:
```bash
cd backend
alembic upgrade head
```

### 2. Seed Development & Demo Data (Idempotent)
Populate the database with the deterministic sandbox merchant (`00000000-0000-0000-0000-000000000001`) and the 4 canonical demo incidents (with diagnostic telemetry evidence):
```bash
# In backend/ directory:
python -m app.scripts.seed
```

### 3. Run Backend API Server
```bash
cd backend
uvicorn app.main:app --port 8000 --reload
```

### 4. Run Frontend Cockpit
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` to access the Incident Cockpit.