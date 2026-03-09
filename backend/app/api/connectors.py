import json

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbSession, get_actor
from app.core.config import get_settings
from app.core.security import encrypt_payload
from app.models.entities import ConnectorAccount
from app.schemas.connector import ConnectorCreateRequest, ConnectorResponse, ConnectorUpdateRequest
from app.services.audit import write_audit_event

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _to_response(connector: ConnectorAccount) -> ConnectorResponse:
    return ConnectorResponse(
        id=connector.id,
        name=connector.name,
        connector_type=connector.connector_type,
        is_active=connector.is_active,
        has_config=bool(connector.config_encrypted),
        created_at=connector.created_at,
        updated_at=connector.updated_at,
    )


@router.get("/", response_model=list[ConnectorResponse])
def list_connectors(
    db: DbSession,
    limit: int = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ConnectorResponse]:
    settings = get_settings()
    effective_limit = limit if limit is not None else settings.default_page_size
    connectors = (
        db.query(ConnectorAccount)
        .order_by(ConnectorAccount.created_at.desc())
        .offset(offset)
        .limit(effective_limit)
        .all()
    )
    return [_to_response(connector) for connector in connectors]


@router.post("/", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
def create_connector(
    payload: ConnectorCreateRequest,
    db: DbSession,
    actor: str = Depends(get_actor),
) -> ConnectorResponse:
    existing = db.query(ConnectorAccount).filter(ConnectorAccount.name == payload.name).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connector name already exists")

    connector = ConnectorAccount(
        name=payload.name,
        connector_type=payload.connector_type,
        config_encrypted=encrypt_payload(json.dumps(payload.config)),
        is_active=payload.is_active,
    )
    db.add(connector)
    write_audit_event(
        db,
        actor=actor,
        action="connector.created",
        entity_type="connector_account",
        entity_id=connector.id,
        metadata={"name": payload.name, "type": payload.connector_type},
    )
    db.commit()
    db.refresh(connector)
    return _to_response(connector)


@router.put("/{connector_id}", response_model=ConnectorResponse)
def update_connector(
    connector_id: str,
    payload: ConnectorUpdateRequest,
    db: DbSession,
    actor: str = Depends(get_actor),
) -> ConnectorResponse:
    connector = db.query(ConnectorAccount).filter(ConnectorAccount.id == connector_id).one_or_none()
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")

    if payload.config is not None:
        connector.config_encrypted = encrypt_payload(json.dumps(payload.config))
    if payload.is_active is not None:
        connector.is_active = payload.is_active

    write_audit_event(
        db,
        actor=actor,
        action="connector.updated",
        entity_type="connector_account",
        entity_id=connector.id,
        metadata={"is_active": connector.is_active},
    )
    db.commit()
    db.refresh(connector)
    return _to_response(connector)
