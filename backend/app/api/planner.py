from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.planner import PlannerRequest, PlannerResponse
from app.services.planner import PlannerService

router = APIRouter(prefix="/planner", tags=["planner"])
planner = PlannerService()


@router.post("/generate", response_model=PlannerResponse)
def generate_workflow_spec(payload: PlannerRequest, _: DbSession) -> PlannerResponse:
    return planner.generate(payload.prompt)
