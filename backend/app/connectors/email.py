import logging
import smtplib
from email.message import EmailMessage

from app.connectors.base import ConnectorExecutionError
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _compose_body(payload: dict) -> str:
    variables = payload.get("variables", {})
    first_name = variables.get("first_name", "")
    template_id = payload.get("template_id", "default")
    if template_id == "welcome_v1":
        return f"Hello {first_name},\n\nWelcome! Your onboarding is now active.\n"
    return payload.get("body", f"Hello {first_name},\n\nThis is your automated notification.\n")


def execute_email_action(action: str, payload: dict, connector_config: dict | None = None) -> dict:
    if action != "email.send":
        raise ConnectorExecutionError(f"Unsupported email action: {action}")

    to = payload.get("to")
    if not to:
        raise ConnectorExecutionError("email.send requires `to`")

    settings = get_settings()
    config = connector_config or {}
    dry_run = bool(config.get("dry_run", settings.smtp_dry_run))

    subject = payload.get("subject", "Automated notification")
    body = _compose_body(payload)
    sender = config.get("from_email", settings.smtp_from_email)

    if dry_run:
        logger.info("Dry-run email -> to=%s subject=%s", to, subject)
        return {"sent": False, "dry_run": True, "to": to, "subject": subject}

    host = config.get("host", settings.smtp_host)
    port = int(config.get("port", settings.smtp_port))
    username = config.get("username", settings.smtp_username)
    password = config.get("password", settings.smtp_password)
    use_tls = bool(config.get("use_tls", True))

    if not host:
        raise ConnectorExecutionError("SMTP host is missing and dry_run is disabled")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host=host, port=port, timeout=settings.request_timeout_seconds) as client:
        if use_tls:
            client.starttls()
        if username and password:
            client.login(username, password)
        client.send_message(message)

    return {"sent": True, "dry_run": False, "to": to, "subject": subject}
