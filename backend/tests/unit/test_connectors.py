import pytest

from app.connectors.base import ConnectorExecutionError
from app.connectors.email import execute_email_action
from app.connectors.http_action import execute_http_action


class TestEmailConnector:
    def test_dry_run_does_not_send(self) -> None:
        result = execute_email_action("email.send", {"to": "a@b.com", "subject": "Hi"}, {"dry_run": True})
        assert result["sent"] is False
        assert result["dry_run"] is True
        assert result["to"] == "a@b.com"

    def test_missing_to_raises(self) -> None:
        with pytest.raises(ConnectorExecutionError, match="requires `to`"):
            execute_email_action("email.send", {}, {"dry_run": True})

    def test_unsupported_action_raises(self) -> None:
        with pytest.raises(ConnectorExecutionError, match="Unsupported email action"):
            execute_email_action("email.unknown", {"to": "a@b.com"}, {"dry_run": True})

    def test_welcome_template_body(self) -> None:
        result = execute_email_action(
            "email.send",
            {"to": "a@b.com", "subject": "Welcome", "template_id": "welcome_v1", "variables": {"first_name": "Ana"}},
            {"dry_run": True},
        )
        assert result["sent"] is False

    def test_missing_smtp_host_raises_when_not_dry_run(self) -> None:
        with pytest.raises(ConnectorExecutionError, match="SMTP host is missing"):
            execute_email_action("email.send", {"to": "a@b.com"}, {"dry_run": False, "host": None})


class TestHttpConnector:
    def test_missing_url_raises(self) -> None:
        with pytest.raises(ConnectorExecutionError, match="requires `url`"):
            execute_http_action("http.request", {})

    def test_unsupported_action_raises(self) -> None:
        with pytest.raises(ConnectorExecutionError, match="Unsupported HTTP action"):
            execute_http_action("http.unknown", {"url": "http://example.com"})
