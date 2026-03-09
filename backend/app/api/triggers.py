import hashlib
import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.deps import DbSession, get_actor
from app.core.config import get_settings
from app.models.entities import Workflow
from app.schemas.run import RunResponse, TriggerRequest
from app.services.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/triggers", tags=["triggers"])
engine = WorkflowEngine()


async def _verify_webhook_signature(
    request: Request,
    x_webhook_signature: Annotated[str | None, Header(alias="X-Webhook-Signature")] = None,
) -> None:
    settings = get_settings()
    if not settings.webhook_secret:
        return
    if not x_webhook_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Webhook-Signature header")
    body = await request.body()
    expected = "sha256=" + hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(x_webhook_signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")


@router.post("/webhook/{workflow_id}", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def trigger_workflow(
    workflow_id: str,
    payload: TriggerRequest,
    db: DbSession,
    actor: str = Depends(get_actor),
    _sig: None = Depends(_verify_webhook_signature),
) -> RunResponse:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).one_or_none()
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    try:
        active_version = engine.get_active_version(db, workflow_id=workflow.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    run = engine.create_run(
        db,
        workflow=workflow,
        version=active_version,
        trigger_type="webhook",
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
