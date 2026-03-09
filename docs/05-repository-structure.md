# Repository Structure

```text
Project 2 - AI Business Process Automation Tool/
  backend/
    app/
      api/
      core/
      models/
      services/
      workflows/
      workers/
      connectors/
    tests/
      unit/
      integration/
  frontend/
    src/
      app/
      pages/
      components/
      features/
      lib/
  infra/
    docker/
    scripts/
  docs/
  examples/
    prompts/
    workflow-specs/
```

## Directory Responsibilities
- `backend/app/api`: REST endpoints and request/response schemas.
- `backend/app/workflows`: orchestration logic and DAG execution.
- `backend/app/connectors`: provider adapters (CRM, email, HTTP).
- `backend/tests`: backend unit and integration tests.
- `frontend/src/features`: domain-specific UI modules.
- `infra/docker`: Compose and container artifacts.
- `docs`: architecture and planning artifacts.
- `examples`: prompts and sample workflow definitions.
