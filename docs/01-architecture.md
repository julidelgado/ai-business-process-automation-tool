# Architecture

## System Components
1. API Service (FastAPI)
- Receives user prompts and workflow CRUD requests.
- Exposes endpoints for workflow runs, logs, and connector config.

2. AI Planner Service
- Converts natural language instructions into workflow JSON.
- Uses strict output schema and confidence scoring.
- Provider adapter allows Ollama now, other LLMs later.

3. Validation and Policy Engine
- Validates schema, connector capabilities, field mappings, and safety rules.
- Blocks unsafe actions before activation.

4. Workflow Orchestrator
- Consumes trigger events.
- Resolves next executable step based on DAG dependencies.
- Enqueues step tasks with retry policy.

5. Worker Service
- Executes step handlers (CRM, email, HTTP).
- Writes structured step logs and status transitions.

6. Data Layer
- PostgreSQL for workflows, runs, step logs, connector configs.
- Redis for queueing and transient orchestration state.

7. Frontend (React)
- Prompt input + generated workflow review UI.
- Run history, step timeline, and failure diagnostics.

## High-Level Flow
1. User submits natural language automation intent.
2. Planner returns candidate workflow JSON.
3. Validator checks schema and policy constraints.
4. User approves and activates workflow version.
5. Trigger event fires.
6. Orchestrator creates workflow run and schedules first steps.
7. Workers execute actions and report status.
8. UI shows run progress and failures in real time.

## Core Data Entities
- workflow
- workflow_version
- trigger
- step_definition
- workflow_run
- step_run
- connector_account
- audit_event

## Deployment Model (MVP)
- `api` container
- `worker` container
- `frontend` container
- `postgres` container
- `redis` container

All services run via Docker Compose in local/dev mode.
