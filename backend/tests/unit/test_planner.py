from app.services.planner import PlannerService


def test_fallback_planner_generates_expected_actions() -> None:
    planner = PlannerService()
    result = planner.generate(
        "When a new client signs up, create a CRM entry and send a welcome email."
    )
    step_types = [step.type for step in result.spec.steps]
    assert "crm.create_contact" in step_types
    assert "email.send" in step_types
