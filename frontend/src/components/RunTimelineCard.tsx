import { useState } from "react";
import { apiRequest } from "../lib/api";
import type { WorkflowRun, StepRun } from "../lib/types";

interface Props {
  busy: boolean;
  selectedWorkflowId: string;
  runs: WorkflowRun[];
  selectedRunId: string;
  runSteps: StepRun[];
  onRunTriggered: (runId: string) => Promise<void>;
  onRunSelected: (runId: string) => void;
  onMessage: (msg: string) => void;
  onError: (msg: string) => void;
  onBusyChange: (busy: boolean) => void;
}

const defaultTriggerPayload = JSON.stringify(
  { email: "client@example.com", first_name: "Alex", last_name: "Rivera" },
  null,
  2
);

export function RunTimelineCard({
  busy,
  selectedWorkflowId,
  runs,
  selectedRunId,
  runSteps,
  onRunTriggered,
  onRunSelected,
  onMessage,
  onError,
  onBusyChange,
}: Props) {
  const [triggerPayloadText, setTriggerPayloadText] = useState(defaultTriggerPayload);

  async function triggerManualRun() {
    if (!selectedWorkflowId) return;
    onBusyChange(true);
    try {
      const payload = JSON.parse(triggerPayloadText);
      const run = await apiRequest<WorkflowRun>(
        `/api/v1/workflows/${selectedWorkflowId}/run/manual`,
        { method: "POST", body: JSON.stringify({ payload }) }
      );
      await onRunTriggered(run.id);
      onMessage("Manual run triggered");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      onBusyChange(false);
    }
  }

  return (
    <article className="card">
      <h2>4) Trigger and Run Timeline</h2>
      <textarea
        value={triggerPayloadText}
        onChange={(e) => setTriggerPayloadText(e.target.value)}
        rows={6}
      />
      <div className="row">
        <button
          onClick={() => void triggerManualRun()}
          disabled={busy || !selectedWorkflowId}
        >
          Trigger Manual Run
        </button>
      </div>

      <h3>Runs</h3>
      <ul className="list">
        {runs.map((run) => (
          <li key={run.id}>
            <button
              className="link"
              onClick={() => onRunSelected(run.id)}
              style={{ fontWeight: run.id === selectedRunId ? 800 : undefined }}
            >
              {run.status.toUpperCase()} - {run.id.slice(0, 8)} ({run.trigger_type})
            </button>
          </li>
        ))}
      </ul>

      <h3>Selected Run Steps</h3>
      <ul className="list compact">
        {runSteps.map((step) => (
          <li key={step.id}>
            <span>
              {step.step_id} [{step.status}] attempt {step.attempt_count}/{step.max_attempts}
            </span>
            {step.last_error ? <small>{step.last_error}</small> : null}
          </li>
        ))}
      </ul>
    </article>
  );
}
