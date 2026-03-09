from fastapi.testclient import TestClient


def test_end_to_end_workflow_create_and_run(client: TestClient, auth_headers: dict[str, str]) -> None:
    create_payload = {
        "name": "onboarding-test",
        "description": "test workflow",
        "source_prompt": "When a new client signs up, create a CRM entry and send welcome email.",
        "spec": {
            "name": "onboarding-test",
            "version": 1,
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "create_crm_contact",
                    "type": "crm.create_contact",
                    "input": {
                        "email": "{{trigger.payload.email}}",
                        "first_name": "{{trigger.payload.first_name}}",
                        "last_name": "{{trigger.payload.last_name}}",
                    },
                    "retry": {"max_attempts": 2, "backoff_seconds": 1},
                },
                {
                    "id": "send_welcome_email",
                    "type": "email.send",
                    "depends_on": ["create_crm_contact"],
                    "input": {
                        "to": "{{trigger.payload.email}}",
                        "subject": "Welcome",
                        "variables": {"first_name": "{{trigger.payload.first_name}}"},
                    },
                    "retry": {"max_attempts": 2, "backoff_seconds": 1},
                },
            ],
        },
    }
    create_response = client.post("/api/v1/workflows/from-spec", json=create_payload, headers=auth_headers)
    assert create_response.status_code == 201
    workflow_id = create_response.json()["id"]

    run_response = client.post(
        f"/api/v1/workflows/{workflow_id}/run/manual",
        json={"payload": {"email": "client@example.com", "first_name": "Ana", "last_name": "Lopez"}},
        headers=auth_headers,
    )
    assert run_response.status_code == 201
    run_id = run_response.json()["id"]

    process_response = client.post("/api/v1/runs/process", headers=auth_headers)
    assert process_response.status_code == 200

    run_detail = client.get(f"/api/v1/runs/{run_id}", headers=auth_headers)
    assert run_detail.status_code == 200
    assert run_detail.json()["status"] in {"running", "success"}

    steps = client.get(f"/api/v1/runs/{run_id}/steps", headers=auth_headers)
    assert steps.status_code == 200
    step_statuses = {row["step_id"]: row["status"] for row in steps.json()}
    assert "create_crm_contact" in step_statuses
