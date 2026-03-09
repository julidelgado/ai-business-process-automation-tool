from fastapi import APIRouter, Depends

from app.api import audit, connectors, planner, runs, triggers, workflows
from app.api.deps import require_api_key

api_router = APIRouter(dependencies=[Depends(require_api_key)])
api_router.include_router(planner.router)
api_router.include_router(workflows.router)
api_router.include_router(runs.router)
api_router.include_router(triggers.router)
api_router.include_router(connectors.router)
api_router.include_router(audit.router)
