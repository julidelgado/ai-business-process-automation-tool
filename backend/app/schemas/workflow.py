from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.planner import WorkflowSpec


class WorkflowCreateFromSpecRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    source_prompt: str | None = None
    spec: WorkflowSpec


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    status: str
    active_version: int | None = None
    created_at: datetime
    updated_at: datetime


class WorkflowVersionResponse(BaseModel):
    id: str
    workflow_id: str
    version_number: int
    is_active: bool
    spec_json: dict
    created_at: datetime


class ManualRunRequest(BaseModel):
    payload: dict = Field(default_factory=dict)
