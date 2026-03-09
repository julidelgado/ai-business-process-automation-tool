# Build Checklist (Implementation Start)

## Repository Setup
- [x] Initialize git repo and main branch policy.
- [x] Add backend dependency management and lockfile.
- [x] Add frontend dependency management and lockfile.
- [x] Add Docker Compose for postgres, redis, api, worker, frontend.

## Backend Foundation
- [x] FastAPI app skeleton with health endpoint.
- [x] Database migrations and base models.
- [x] Workflow CRUD endpoints.
- [x] Run and step log endpoints.

## AI Planning
- [x] Planner provider interface.
- [x] Ollama adapter implementation.
- [x] Prompt template and schema validation.
- [x] Confidence and warning surface.

## Runtime Engine
- [x] Event trigger ingestion endpoint.
- [x] Orchestrator DAG scheduler.
- [x] Worker execution handlers.
- [x] Retry and dead-letter support.

## Connectors
- [x] CRM connector v1.
- [x] SMTP connector v1.
- [x] HTTP connector v1.

## Frontend
- [x] Prompt to workflow generation page.
- [x] Workflow review and activation page.
- [x] Run history and run detail timeline.

## Hardening
- [x] Secrets handling and redaction.
- [x] Audit trail events.
- [x] Integration tests and CI pipeline.
