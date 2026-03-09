# Backend

FastAPI backend service for the AI Business Process Automation Tool.

## Run local (without Docker)
1. Create virtual environment.
2. Install dependencies:
   `python -m pip install -r requirements-dev.txt`
3. Start API:
   `uvicorn app.main:app --reload --port 8000`
4. Start worker:
   `python -m app.workers.runner`

## Health
- `GET /health`

## API (requires `X-API-Key`)
- `POST /api/v1/planner/generate`
- `POST /api/v1/workflows/from-spec`
- `POST /api/v1/workflows/{workflow_id}/versions`
- `POST /api/v1/workflows/{workflow_id}/activate/{version_number}`
- `POST /api/v1/workflows/{workflow_id}/run/manual`
- `POST /api/v1/triggers/webhook/{workflow_id}`
- `GET /api/v1/runs`
- `GET /api/v1/runs/{run_id}/steps`
- `POST /api/v1/runs/process`
- `GET/POST/PUT /api/v1/connectors`
- `GET /api/v1/audit`
