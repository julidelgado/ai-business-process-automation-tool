from datetime import datetime

from pydantic import BaseModel, Field


class TriggerRequest(BaseModel):
    payload: dict = Field(default_factory=dict)


class RunResponse(BaseModel):
    id: str
    workflow_id: str
    workflow_version_id: str
    trigger_type: str
    status: str
    trigger_payload: dict
    error_message: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    created_at: datetime


class StepRunResponse(BaseModel):
    id: str
    workflow_run_id: str
    step_id: str
    step_type: str
    status: str
    depends_on: list[str]
    input_payload: dict
    output_payload: dict | None = None
    attempt_count: int
    max_attempts: int
    backoff_seconds: int
    scheduled_for: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_error: str | None = None
