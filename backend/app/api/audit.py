from fastapi import APIRouter

from app.api.deps import DbSession
from app.models.entities import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/")
def list_audit_events(db: DbSession, limit: int = 100) -> list[dict]:
    events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(min(limit, 500)).all()
    return [
        {
            "id": event.id,
            "actor": event.actor,
            "action": event.action,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "metadata": event.metadata_json,
            "created_at": event.created_at,
        }
        for event in events
    ]
