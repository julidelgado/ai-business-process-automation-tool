from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConnectorCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    connector_type: Literal["smtp", "http", "crm_internal"]
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ConnectorUpdateRequest(BaseModel):
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class ConnectorResponse(BaseModel):
    id: str
    name: str
    connector_type: str
    is_active: bool
    has_config: bool
    created_at: datetime
    updated_at: datetime
