import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.entities import StepRun, Workflow, WorkflowRun, WorkflowVersion
from app.schemas.planner import WorkflowSpec
from app.schemas.workflow import WorkflowCreateFromSpecRequest
from app.services.workflow_engine import WorkflowEngine

_SIMPLE_SPEC: dict = {
    "name": "engine-test-workflow",
    "version": 1,
    "trigger": {"type": "manual"},
    "steps": [
        {
            "id": "create_contact",
            "type": "crm.create_contact",
            "input": {
                "email": "{{trigger.payload.email}}",
                "first_name": "{{trigger.payload.first}}",
            },
            "retry": {"max_attempts": 2, "backoff_seconds": 1},
        }
    ],
}

_TWO_STEP_SPEC: dict = {
    "name": "two-step-workflow",
    "version": 1,
    "trigger": {"type": "manual"},
    "steps": [
        {
            "id": "create_contact",
            "type": "crm.create_contact",
            "input": {"email": "{{trigger.payload.email}}"},
            "retry": {"max_attempts": 2, "backoff_seconds": 1},
        },
        {
            "id": "send_email",
            "type": "email.send",
            "depends_on": ["create_contact"],
            "input": {"to": "{{trigger.payload.email}}", "subject": "Welcome"},
            "retry": {"max_attempts": 2, "backoff_seconds": 1},
        },
    ],
}


@pytest.fixture
def engine() -> WorkflowEngine:
    return WorkflowEngine()


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


class TestCreateWorkflow:
    def test_creates_workflow_and_version(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate(_SIMPLE_SPEC)
        request = WorkflowCreateFromSpecRequest(name="engine-test-workflow", spec=spec)
        workflow, version = engine.create_workflow_from_spec(db, request=request, actor="pytest")

        assert workflow.id is not None
        assert workflow.name == "engine-test-workflow"
        assert workflow.status == "active"
        assert version.version_number == 1
        assert version.is_active is True

    def test_duplicate_name_raises(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate({**_SIMPLE_SPEC, "name": "dup-workflow"})
        request = WorkflowCreateFromSpecRequest(name="dup-workflow", spec=spec)
        engine.create_workflow_from_spec(db, request=request, actor="pytest")
        with pytest.raises(ValueError, match="already exists"):
            engine.create_workflow_from_spec(db, request=request, actor="pytest")


class TestVersionManagement:
    def test_create_new_version_increments(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate({**_SIMPLE_SPEC, "name": "versioned-wf"})
        request = WorkflowCreateFromSpecRequest(name="versioned-wf", spec=spec)
        workflow, _v1 = engine.create_workflow_from_spec(db, request=request, actor="pytest")

        v2 = engine.create_new_version(db, workflow=workflow, spec=spec, actor="pytest")
        assert v2.version_number == 2
        assert v2.is_active is False

    def test_activate_version_deactivates_others(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate({**_SIMPLE_SPEC, "name": "activate-test"})
        request = WorkflowCreateFromSpecRequest(name="activate-test", spec=spec)
        workflow, v1 = engine.create_workflow_from_spec(db, request=request, actor="pytest")
        v2 = engine.create_new_version(db, workflow=workflow, spec=spec, actor="pytest")

        engine.activate_version(db, workflow=workflow, version_number=v2.version_number, actor="pytest")

        db.refresh(v1)
        db.refresh(v2)
        assert v1.is_active is False
        assert v2.is_active is True

    def test_activate_nonexistent_version_raises(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate({**_SIMPLE_SPEC, "name": "no-version-wf"})
        request = WorkflowCreateFromSpecRequest(name="no-version-wf", spec=spec)
        workflow, _ = engine.create_workflow_from_spec(db, request=request, actor="pytest")

        with pytest.raises(ValueError, match="not found"):
            engine.activate_version(db, workflow=workflow, version_number=999, actor="pytest")


class TestCreateRun:
    def test_creates_run_with_steps(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate({**_TWO_STEP_SPEC, "name": "run-step-test"})
        request = WorkflowCreateFromSpecRequest(name="run-step-test", spec=spec)
        workflow, version = engine.create_workflow_from_spec(db, request=request, actor="pytest")

        run = engine.create_run(
            db,
            workflow=workflow,
            version=version,
            trigger_type="manual",
            payload={"email": "test@example.com"},
            actor="pytest",
        )

        assert run.id is not None
        assert run.status == "running"
        steps = db.query(StepRun).filter(StepRun.workflow_run_id == run.id).all()
        assert len(steps) == 2
        step_ids = {s.step_id for s in steps}
        assert {"create_contact", "send_email"} == step_ids

    def test_steps_are_pending_initially(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate({**_SIMPLE_SPEC, "name": "pending-steps-test"})
        request = WorkflowCreateFromSpecRequest(name="pending-steps-test", spec=spec)
        workflow, version = engine.create_workflow_from_spec(db, request=request, actor="pytest")

        run = engine.create_run(
            db,
            workflow=workflow,
            version=version,
            trigger_type="manual",
            payload={"email": "x@y.com"},
            actor="pytest",
        )
        steps = db.query(StepRun).filter(StepRun.workflow_run_id == run.id).all()
        assert all(s.status == "pending" for s in steps)


class TestDependencySatisfied:
    def test_no_dependencies_always_satisfied(self, engine: WorkflowEngine, db) -> None:
        assert engine._dependencies_satisfied(db, "any-run-id", []) is True

    def test_missing_dependency_not_satisfied(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate({**_TWO_STEP_SPEC, "name": "dep-check-wf"})
        request = WorkflowCreateFromSpecRequest(name="dep-check-wf", spec=spec)
        workflow, version = engine.create_workflow_from_spec(db, request=request, actor="pytest")
        run = engine.create_run(
            db,
            workflow=workflow,
            version=version,
            trigger_type="manual",
            payload={"email": "a@b.com"},
            actor="pytest",
        )
        assert engine._dependencies_satisfied(db, run.id, ["create_contact"]) is False


class TestProcessPendingSteps:
    def test_processes_crm_step_successfully(self, engine: WorkflowEngine, db) -> None:
        spec = WorkflowSpec.model_validate({**_SIMPLE_SPEC, "name": "process-crm-test"})
        request = WorkflowCreateFromSpecRequest(name="process-crm-test", spec=spec)
        workflow, version = engine.create_workflow_from_spec(db, request=request, actor="pytest")
        run = engine.create_run(
            db,
            workflow=workflow,
            version=version,
            trigger_type="manual",
            payload={"email": "proc@test.com", "first": "Alice"},
            actor="pytest",
        )

        processed = engine.process_pending_steps(db, limit=10)
        assert processed >= 1

        db.refresh(run)
        assert run.status in {"success", "running"}
