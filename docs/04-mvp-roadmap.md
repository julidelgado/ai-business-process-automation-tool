# MVP Roadmap

## Phase 0 - Setup
- Initialize monorepo layout.
- Add local Docker Compose stack.
- Define coding standards and CI basics.

Exit criteria:
- Services boot locally and health checks pass.

## Phase 1 - Core Data and APIs
- Implement workflow, version, run, and step models.
- Build CRUD APIs for workflows.
- Add run query and log APIs.

Exit criteria:
- Workflow definitions can be created, versioned, and retrieved.

## Phase 2 - NL Planning
- Add planner adapter and prompt templates.
- Implement schema-constrained response parsing.
- Add validation and warnings.

Exit criteria:
- Prompt can generate valid workflow JSON for target MVP intents.

## Phase 3 - Runtime Engine
- Build trigger ingestion.
- Build orchestrator and worker processing.
- Add retry and dead-letter handling.

Exit criteria:
- End-to-end run executes with logs and final status.

## Phase 4 - Connectors
- CRM connector (initial provider or internal CRM table).
- SMTP email connector.
- Generic HTTP connector.

Exit criteria:
- Example onboarding workflow executes against real connector config.

## Phase 5 - Frontend
- Prompt-to-workflow UX.
- Review/edit/approve workflow UI.
- Run history and run details timeline.

Exit criteria:
- User can create and run workflow from UI without direct API use.

## Phase 6 - Hardening
- Security checks, audit events, and failure alerts.
- Integration tests and load smoke tests.
- Documentation and deployment instructions.

Exit criteria:
- Stable MVP ready for pilot users.
