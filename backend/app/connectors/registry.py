import json

from sqlalchemy.orm import Session

from app.connectors.base import ConnectorExecutionError
from app.connectors.crm import execute_crm_action
from app.connectors.email import execute_email_action
from app.connectors.http_action import execute_http_action
from app.core.security import decrypt_payload
from app.models.entities import ConnectorAccount


def _load_connector_config(db: Session, connector_name: str | None) -> dict | None:
    if not connector_name:
        return None
    account = db.query(ConnectorAccount).filter(ConnectorAccount.name == connector_name).one_or_none()
    if account is None or not account.is_active or not account.config_encrypted:
        return None
    try:
        return json.loads(decrypt_payload(account.config_encrypted))
    except Exception:  # noqa: BLE001
        return None


def execute_connector_action(action: str, payload: dict, *, db: Session) -> dict:
    connector_name = payload.get("connector_name")
    connector_config = _load_connector_config(db, connector_name)

    if action.startswith("crm."):
        return execute_crm_action(action, payload, db)
    if action.startswith("email."):
        return execute_email_action(action, payload, connector_config)
    if action.startswith("http."):
        return execute_http_action(action, payload)
    raise ConnectorExecutionError(f"Unsupported connector action: {action}")
