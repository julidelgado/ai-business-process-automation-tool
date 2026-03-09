from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbSession, get_actor
from app.core.config import get_settings
from app.models.entities import Workflow, WorkflowVersion
from app.schemas.run import RunResponse
from app.schemas.workflow import (
    ManualRunRequest,
    WorkflowCreateFromSpecRequest,
    WorkflowResponse,
    WorkflowVersionResponse,
)
from app.services.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/workflows", tags=["workflows"])
engine = WorkflowEngine()


def _to_workflow_response(workflow: Workflow, active_version: int | None) -> WorkflowResponse:
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        active_version=active_version,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


@router.get("/", response_model=list[WorkflowResponse])
def list_workflows(
    db: DbSession,
    limit: int = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[WorkflowResponse]:
    settings = get_settings()
    effective_limit = limit if limit is not None else settings.default_page_size
    workflows = db.query(Workflow).order_by(Workflow.created_at.desc()).offset(offset).limit(effective_limit).all()
    output: list[WorkflowResponse] = []
    for workflow in workflows:
        active = (
            db.query(WorkflowVersion)
            .filter(WorkflowVersion.workflow_id == workflow.id, WorkflowVersion.is_active.is_(True))
            .one_or_none()
        )
        output.append(_to_workflow_response(workflow, active.version_number if active else None))
    return output


@router.post("/from-spec", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_from_spec(
    payload: WorkflowCreateFromSpecRequest,
    db: DbSession,
    actor: str = Depends(get_actor),
) -> WorkflowResponse:
    try:
        workflow, version = engine.create_workflow_from_spec(db, request=payload, actor=actor)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_workflow_response(workflow, version.version_number)


@router.post("/{workflow_id}/versions", response_model=WorkflowVersionResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_version(
    workflow_id: str,
    payload: WorkflowCreateFromSpecRequest,
    db: DbSession,
    actor: str = Depends(get_actor),
) -> WorkflowVersionResponse:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).one_or_none()
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    version = engine.create_new_version(db, workflow=workflow, spec=payload.spec, actor=actor)
    return WorkflowVersionResponse(
        id=version.id,
        workflow_id=version.workflow_id,
        version_number=version.version_number,
        is_active=version.is_active,
        spec_json=version.spec_json,
        created_at=version.created_at,
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: str, db: DbSession) -> WorkflowResponse:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).one_or_none()
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    active = (
        db.query(WorkflowVersion)
        .filter(WorkflowVersion.workflow_id == workflow.id, WorkflowVersion.is_active.is_(True))
        .one_or_none()
    )
    return _to_workflow_response(workflow, active.version_number if active else None)


@router.get("/{workflow_id}/versions", response_model=list[WorkflowVersionResponse])
def list_workflow_versions(workflow_id: str, db: DbSession) -> list[WorkflowVersionResponse]:
    versions = (
        db.query(WorkflowVersion)
        .filter(WorkflowVersion.workflow_id == workflow_id)
        .order_by(WorkflowVersion.version_number.desc())
        .all()
    )
    return [
        WorkflowVersionResponse(
            id=version.id,
            workflow_id=version.workflow_id,
            version_number=version.version_number,
            is_active=version.is_active,
            spec_json=version.spec_json,
            created_at=version.created_at,
        )
        for version in versions
    ]


@router.post("/{workflow_id}/activate/{version_number}", response_model=WorkflowVersionResponse)
def activate_workflow_version(
    workflow_id: str,
    version_number: int,
    db: DbSession,
    actor: str = Depends(get_actor),
) -> WorkflowVersionResponse:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).one_or_none()
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    try:
        version = engine.activate_version(db, workflow=workflow, version_number=version_number, actor=actor)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WorkflowVersionResponse(
        id=version.id,
        workflow_id=version.workflow_id,
        version_number=version.version_number,
        is_active=version.is_active,
        spec_json=version.spec_json,
        created_at=version.created_at,
    )


@router.post("/{workflow_id}/run/manual", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def create_manual_run(
    workflow_id: str,
    payload: ManualRunRequest,
    db: DbSession,
    actor: str = Depends(get_actor),
) -> RunResponse:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).one_or_none()
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    try:
        version = engine.get_active_version(db, workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    run = engine.create_run(
        db,
        workflow=workflow,
        version=version,
        trigger_type="manual",
        payload=payload.payload,
        actor=actor,
    )
    engine.process_pending_steps(db, limit=10)
    db.refresh(run)
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
