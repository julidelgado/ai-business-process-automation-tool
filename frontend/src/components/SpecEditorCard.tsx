import { apiRequest } from "../lib/api";
import type { WorkflowSummary } from "../lib/types";

interface Props {
  busy: boolean;
  specText: string;
  onSpecTextChange: (v: string) => void;
  workflowName: string;
  onWorkflowNameChange: (v: string) => void;
  workflowDescription: string;
  onWorkflowDescriptionChange: (v: string) => void;
  selectedWorkflowId: string;
  sourcePrompt: string;
  onWorkflowCreated: () => Promise<void>;
  onVersionCreated: () => Promise<void>;
  onMessage: (msg: string) => void;
  onError: (msg: string) => void;
  onBusyChange: (busy: boolean) => void;
}

export function SpecEditorCard({
  busy,
  specText,
  onSpecTextChange,
  workflowName,
  onWorkflowNameChange,
  workflowDescription,
  onWorkflowDescriptionChange,
  selectedWorkflowId,
  sourcePrompt,
  onWorkflowCreated,
  onVersionCreated,
  onMessage,
  onError,
  onBusyChange,
}: Props) {
  async function createWorkflow() {
    onBusyChange(true);
    try {
      const parsedSpec = JSON.parse(specText);
      await apiRequest<WorkflowSummary>("/api/v1/workflows/from-spec", {
        method: "POST",
        body: JSON.stringify({
          name: workflowName,
          description: workflowDescription,
          source_prompt: sourcePrompt,
          spec: parsedSpec,
        }),
      });
      await onWorkflowCreated();
      onMessage("Workflow created and activated at version 1");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      onBusyChange(false);
    }
  }

  async function createVersion() {
    if (!selectedWorkflowId) return;
    onBusyChange(true);
    try {
      const parsedSpec = JSON.parse(specText);
      await apiRequest(`/api/v1/workflows/${selectedWorkflowId}/versions`, {
        method: "POST",
        body: JSON.stringify({ spec: parsedSpec }),
      });
      await onVersionCreated();
      onMessage("New workflow version created");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      onBusyChange(false);
    }
  }

  return (
    <article className="card">
      <h2>2) Review Spec and Save Workflow</h2>
      <div className="grid-two">
        <label>
          Workflow Name
          <input value={workflowName} onChange={(e) => onWorkflowNameChange(e.target.value)} />
        </label>
        <label>
          Description
          <input value={workflowDescription} onChange={(e) => onWorkflowDescriptionChange(e.target.value)} />
        </label>
      </div>
      <textarea
        value={specText}
        onChange={(e) => onSpecTextChange(e.target.value)}
        rows={16}
        placeholder="Generated JSON spec appears here"
      />
      <div className="row">
        <button onClick={() => void createWorkflow()} disabled={busy || !specText}>
          Create Workflow
        </button>
        <button
          onClick={() => void createVersion()}
          disabled={busy || !specText || !selectedWorkflowId}
        >
          Add Version to Selected
        </button>
      </div>
    </article>
  );
}
