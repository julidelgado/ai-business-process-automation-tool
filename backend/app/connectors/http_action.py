import httpx

from app.connectors.base import ConnectorExecutionError
from app.core.config import get_settings


def execute_http_action(action: str, payload: dict) -> dict:
    if action != "http.request":
        raise ConnectorExecutionError(f"Unsupported HTTP action: {action}")

    url = payload.get("url")
    if not url:
        raise ConnectorExecutionError("http.request requires `url`")

    method = payload.get("method", "POST").upper()
    headers = payload.get("headers", {})
    timeout = int(payload.get("timeout_seconds", get_settings().request_timeout_seconds))
    json_payload = payload.get("json")
    data_payload = payload.get("data")

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_payload,
                data=data_payload,
            )
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "body_preview": response.text[:500],
        }
    except httpx.HTTPError as exc:
        raise ConnectorExecutionError(str(exc)) from exc
