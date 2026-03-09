from sqlalchemy.orm import Session

from app.connectors.base import ConnectorExecutionError
from app.models.entities import CRMContact


def execute_crm_action(action: str, payload: dict, db: Session) -> dict:
    if action != "crm.create_contact":
        raise ConnectorExecutionError(f"Unsupported CRM action: {action}")

    email = payload.get("email")
    if not email:
        raise ConnectorExecutionError("crm.create_contact requires `email`")

    first_name = payload.get("first_name")
    last_name = payload.get("last_name")

    contact = db.query(CRMContact).filter(CRMContact.email == email).one_or_none()
    created = False
    if contact is None:
        contact = CRMContact(email=email, first_name=first_name, last_name=last_name, source="workflow")
        db.add(contact)
        created = True
    else:
        contact.first_name = first_name or contact.first_name
        contact.last_name = last_name or contact.last_name

    db.flush()
    return {"contact_id": contact.id, "email": contact.email, "created": created}
