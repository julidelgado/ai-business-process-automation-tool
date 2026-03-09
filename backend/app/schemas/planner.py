from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

_STEP_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


class PlannerRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=3000)


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_seconds: int = Field(default=10, ge=1, le=3600)


class TriggerSpec(BaseModel):
    type: Literal["webhook", "manual", "schedule"]
    event: str | None = None
    cron: str | None = None

    @model_validator(mode="after")
    def validate_fields(self) -> "TriggerSpec":
        if self.type == "webhook" and not self.event:
            raise ValueError("webhook trigger requires an event")
        if self.type == "schedule" and not self.cron:
            raise ValueError("schedule trigger requires a cron expression")
        return self


class StepSpec(BaseModel):
    id: str = Field(min_length=2, max_length=120)
    type: Literal["crm.create_contact", "email.send", "http.request"]
    depends_on: list[str] = Field(default_factory=list)
    input: dict[str, Any] = Field(default_factory=dict)
    retry: RetryPolicy | None = None

    @field_validator("id")
    @classmethod
    def validate_step_id(cls, value: str) -> str:
        if not _STEP_ID_RE.match(value):
            raise ValueError(
                "step id must start with a lowercase letter and contain only lowercase letters, digits, hyphens, or underscores"
            )
        return value

    @field_validator("depends_on")
    @classmethod
    def unique_depends_on(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


class WorkflowSpec(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    version: int = Field(default=1, ge=1)
    trigger: TriggerSpec
    steps: list[StepSpec] = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph(self) -> "WorkflowSpec":
        ids = [step.id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("step ids must be unique")

        id_set = set(ids)
        for step in self.steps:
            missing = [dep for dep in step.depends_on if dep not in id_set]
            if missing:
                raise ValueError(f"step '{step.id}' has unknown dependencies: {missing}")

        visited: set[str] = set()
        stack: set[str] = set()
        graph = {step.id: step.depends_on for step in self.steps}

        def visit(node: str) -> None:
            if node in stack:
                raise ValueError("dependency cycle detected in workflow steps")
            if node in visited:
                return
            stack.add(node)
            for dep in graph[node]:
                visit(dep)
            stack.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)

        return self


class PlannerResponse(BaseModel):
    spec: WorkflowSpec
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    provider: str
