from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.connectors.base import ConnectorExecutionError
from app.connectors.registry import execute_connector_action
from app.core.config import get_settings
from app.models.entities import StepRun, Workflow, WorkflowRun, WorkflowVersion
from app.schemas.planner import WorkflowSpec
from app.schemas.workflow import WorkflowCreateFromSpecRequest
from app.services.audit import write_audit_event
from app.services.template import render_value

settings = get_settings()
logger = logging.getLogger(__name__)


class WorkflowEngine:
    def create_workflow_from_spec(
        self,
        db: Session,
        *,
        request: WorkflowCreateFromSpecRequest,
        actor: str,
    ) -> tuple[Workflow, WorkflowVersion]:
        workflow_name = request.name or request.spec.name
        existing = db.query(Workflow).filter(Workflow.name == workflow_name).one_or_none()
        if existing is not None:
            raise ValueError(f"Workflow with name '{workflow_name}' already exists")

        workflow = Workflow(
            name=workflow_name,
            description=request.description,
            status="draft",
            source_prompt=request.source_prompt,
        )
        db.add(workflow)
        db.flush()

        version = WorkflowVersion(
            workflow_id=workflow.id,
            version_number=1,
            is_active=True,
            spec_json=request.spec.model_dump(),
        )
        workflow.status = "active"
        db.add(version)

        write_audit_event(
            db,
            actor=actor,
            action="workflow.created",
            entity_type="workflow",
            entity_id=workflow.id,
            metadata={"version": 1},
        )
        db.commit()
        db.refresh(workflow)
        db.refresh(version)
        logger.info("Created workflow '%s' (id=%s, version=1)", workflow.name, workflow.id)
        return workflow, version

    def create_new_version(
        self,
        db: Session,
        *,
        workflow: Workflow,
        spec: WorkflowSpec,
        actor: str,
    ) -> WorkflowVersion:
        latest = (
            db.query(WorkflowVersion)
            .filter(WorkflowVersion.workflow_id == workflow.id)
            .order_by(WorkflowVersion.version_number.desc())
            .first()
        )
        next_version = 1 if latest is None else latest.version_number + 1
        version = WorkflowVersion(
            workflow_id=workflow.id,
            version_number=next_version,
            is_active=False,
            spec_json=spec.model_dump(),
        )
        db.add(version)
        write_audit_event(
            db,
            actor=actor,
            action="workflow.version.created",
            entity_type="workflow",
            entity_id=workflow.id,
            metadata={"version": next_version},
        )
        db.commit()
        db.refresh(version)
        logger.info("Created version %d for workflow '%s'", next_version, workflow.id)
        return version

    def activate_version(self, db: Session, *, workflow: Workflow, version_number: int, actor: str) -> WorkflowVersion:
        version = (
            db.query(WorkflowVersion)
            .filter(
                WorkflowVersion.workflow_id == workflow.id,
                WorkflowVersion.version_number == version_number,
            )
            .one_or_none()
        )
        if version is None:
            raise ValueError(f"Version {version_number} not found for workflow {workflow.id}")

        (
            db.query(WorkflowVersion)
            .filter(WorkflowVersion.workflow_id == workflow.id, WorkflowVersion.is_active.is_(True))
            .update({WorkflowVersion.is_active: False})
        )
        version.is_active = True
        workflow.status = "active"

        write_audit_event(
            db,
            actor=actor,
            action="workflow.version.activated",
            entity_type="workflow",
            entity_id=workflow.id,
            metadata={"version": version_number},
        )
        db.commit()
        db.refresh(version)
        logger.info("Activated version %d for workflow '%s'", version_number, workflow.id)
        return version

    def get_active_version(self, db: Session, workflow_id: str) -> WorkflowVersion:
        version = (
            db.query(WorkflowVersion)
            .filter(WorkflowVersion.workflow_id == workflow_id, WorkflowVersion.is_active.is_(True))
            .one_or_none()
        )
        if version is None:
            raise ValueError("No active workflow version found")
        return version

    def create_run(
        self,
        db: Session,
        *,
        workflow: Workflow,
        version: WorkflowVersion,
        trigger_type: str,
        payload: dict[str, Any],
        actor: str,
    ) -> WorkflowRun:
        spec = WorkflowSpec.model_validate(version.spec_json)
        run = WorkflowRun(
            workflow_id=workflow.id,
            workflow_version_id=version.id,
            trigger_type=trigger_type,
            trigger_payload=payload,
            status="running",
        )
        db.add(run)
        db.flush()

        for step in spec.steps:
            retry = step.retry
            max_attempts = retry.max_attempts if retry else settings.default_retry_attempts
            backoff = retry.backoff_seconds if retry else settings.default_retry_backoff_seconds
            db.add(
                StepRun(
                    workflow_run_id=run.id,
                    step_id=step.id,
                    step_type=step.type,
                    status="pending",
                    depends_on=step.depends_on,
                    input_payload=step.input,
                    max_attempts=max_attempts,
                    backoff_seconds=backoff,
                    scheduled_for=datetime.now(UTC),
                )
            )

        write_audit_event(
            db,
            actor=actor,
            action="workflow.run.created",
            entity_type="workflow_run",
            entity_id=run.id,
            metadata={"workflow_id": workflow.id, "trigger_type": trigger_type},
        )
        db.commit()
        db.refresh(run)
        logger.info("Created run '%s' for workflow '%s' (trigger=%s)", run.id, workflow.id, trigger_type)
        return run

    def process_pending_steps(self, db: Session, *, limit: int | None = None) -> int:
        max_items = limit or settings.worker_batch_size
        now = datetime.now(UTC)
        pending_steps = (
            db.query(StepRun)
            .filter(StepRun.status == "pending", StepRun.scheduled_for <= now)
            .order_by(StepRun.scheduled_for.asc())
            .limit(max_items)
            .all()
        )

        processed = 0
        for step_run in pending_steps:
            run = db.query(WorkflowRun).filter(WorkflowRun.id == step_run.workflow_run_id).one()
            if run.status in {"failed", "success", "dead_letter"}:
                continue
            if not self._dependencies_satisfied(db, run.id, step_run.depends_on):
                continue

            step_run.status = "running"
            step_run.started_at = datetime.now(UTC)
            step_run.attempt_count += 1
            db.commit()

            logger.info(
                "Executing step '%s' (type=%s, run=%s, attempt=%d/%d)",
                step_run.step_id,
                step_run.step_type,
                run.id,
                step_run.attempt_count,
                step_run.max_attempts,
            )

            try:
                output = self._execute_step(db, run, step_run)
                step_run.status = "success"
                step_run.output_payload = output
                step_run.finished_at = datetime.now(UTC)
                step_run.last_error = None
                logger.info("Step '%s' succeeded (run=%s)", step_run.step_id, run.id)
            except ConnectorExecutionError as exc:
                self._handle_step_failure(db, run, step_run, str(exc))
            except Exception as exc:  # noqa: BLE001
                self._handle_step_failure(db, run, step_run, f"Unhandled error: {exc!s}")

            self._refresh_run_status(db, run)
            db.commit()
            processed += 1

        return processed

    def _dependencies_satisfied(self, db: Session, run_id: str, depends_on: list[str]) -> bool:
        if not depends_on:
            return True
        success_ids = {
            row.step_id
            for row in db.query(StepRun).filter(
                StepRun.workflow_run_id == run_id,
                StepRun.status == "success",
            )
        }
        return all(dep in success_ids for dep in depends_on)

    def _build_context(self, run: WorkflowRun, step_runs: list[StepRun]) -> dict[str, Any]:
        context_steps = {step.step_id: (step.output_payload or {}) for step in step_runs if step.status == "success"}
        return {
            "trigger": {"payload": run.trigger_payload or {}},
            "steps": context_steps,
        }

    def _execute_step(self, db: Session, run: WorkflowRun, step_run: StepRun) -> dict:
        related_steps = db.query(StepRun).filter(StepRun.workflow_run_id == run.id).all()
        context = self._build_context(run, related_steps)
        rendered_input = render_value(step_run.input_payload, context)
        return execute_connector_action(step_run.step_type, rendered_input, db=db)

    def _handle_step_failure(self, db: Session, run: WorkflowRun, step_run: StepRun, error_msg: str) -> None:
        step_run.last_error = error_msg
        if step_run.attempt_count < step_run.max_attempts:
            step_run.status = "pending"
            step_run.scheduled_for = datetime.now(UTC) + timedelta(seconds=step_run.backoff_seconds)
            step_run.started_at = None
            logger.warning(
                "Step '%s' failed (attempt %d/%d), retrying in %ds: %s",
                step_run.step_id,
                step_run.attempt_count,
                step_run.max_attempts,
                step_run.backoff_seconds,
                error_msg,
            )
        else:
            step_run.status = "dead_letter"
            step_run.finished_at = datetime.now(UTC)
            run.status = "failed"
            run.error_message = f"Step '{step_run.step_id}' failed: {error_msg}"
            run.finished_at = datetime.now(UTC)
            logger.error(
                "Step '%s' exhausted all %d attempts (run=%s): %s",
                step_run.step_id,
                step_run.max_attempts,
                run.id,
                error_msg,
            )

        write_audit_event(
            db,
            actor="worker",
            action="workflow.step.failed",
            entity_type="step_run",
            entity_id=step_run.id,
            metadata={"step_id": step_run.step_id, "error": error_msg, "attempt": step_run.attempt_count},
        )

    def _refresh_run_status(self, db: Session, run: WorkflowRun) -> None:
        steps = db.query(StepRun).filter(StepRun.workflow_run_id == run.id).all()
        if not steps:
            return
        if any(step.status == "dead_letter" for step in steps):
            run.status = "failed"
            run.finished_at = datetime.now(UTC)
            return
        if all(step.status == "success" for step in steps):
            run.status = "success"
            run.finished_at = datetime.now(UTC)
            return
        run.status = "running"
