from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.core.config import get_settings
from app.models.entities import StepRun, WorkflowRun
from app.schemas.run import RunResponse, StepRunResponse
from app.services.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/runs", tags=["runs"])
engine = WorkflowEngine()


@router.get("/", response_model=list[RunResponse])
def list_runs(
    db: DbSession,
    workflow_id: str | None = None,
    limit: int = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[RunResponse]:
    settings = get_settings()
    effective_limit = limit if limit is not None else settings.default_page_size
    query = db.query(WorkflowRun)
    if workflow_id:
        query = query.filter(WorkflowRun.workflow_id == workflow_id)
    runs = query.order_by(WorkflowRun.created_at.desc()).offset(offset).limit(effective_limit).all()
    return [
        RunResponse(
            id=run.id,
            workflow_id=run.workflow_id,
            workflow_version_id=run.workflow_version_id,
            trigger_type=run.trigger_type,
            status=run.status,
            trigger_payload=run.trigger_payload,
            error_message=run.error_message,
            started_at=run.started_at,
            finished_at=run.finished_at,
            created_at=run.created_at,
        )
        for run in runs
    ]


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: str, db: DbSession) -> RunResponse:
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunResponse(
        id=run.id,
        workflow_id=run.workflow_id,
        workflow_version_id=run.workflow_version_id,
        trigger_type=run.trigger_type,
        status=run.status,
        trigger_payload=run.trigger_payload,
        error_message=run.error_message,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )


@router.get("/{run_id}/steps", response_model=list[StepRunResponse])
def get_run_steps(run_id: str, db: DbSession) -> list[StepRunResponse]:
    steps = (
        db.query(StepRun)
        .filter(StepRun.workflow_run_id == run_id)
        .order_by(StepRun.scheduled_for.asc(), StepRun.step_id.asc())
        .all()
    )
    return [
        StepRunResponse(
            id=step.id,
            workflow_run_id=step.workflow_run_id,
            step_id=step.step_id,
            step_type=step.step_type,
            status=step.status,
            depends_on=step.depends_on,
            input_payload=step.input_payload,
            output_payload=step.output_payload,
            attempt_count=step.attempt_count,
            max_attempts=step.max_attempts,
            backoff_seconds=step.backoff_seconds,
            scheduled_for=step.scheduled_for,
            started_at=step.started_at,
            finished_at=step.finished_at,
            last_error=step.last_error,
        )
        for step in steps
    ]


@router.post("/process", response_model=dict[str, int])
def process_runs(db: DbSession) -> dict[str, int]:
    processed = engine.process_pending_steps(db, limit=50)
    return {"processed_steps": processed}
