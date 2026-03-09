import { apiRequest } from "../lib/api";
import type { WorkflowSummary, WorkflowVersion } from "../lib/types";

interface Props {
  busy: boolean;
  workflows: WorkflowSummary[];
  selectedWorkflowId: string;
  onSelectWorkflow: (id: string) => void;
  versions: WorkflowVersion[];
  onVersionActivated: () => Promise<void>;
  onMessage: (msg: string) => void;
  onError: (msg: string) => void;
  onBusyChange: (busy: boolean) => void;
}

export function WorkflowVersionsCard({
  busy,
  workflows,
  selectedWorkflowId,
  onSelectWorkflow,
  versions,
  onVersionActivated,
  onMessage,
  onError,
  onBusyChange,
}: Props) {
  const selectedWorkflow = workflows.find((w) => w.id === selectedWorkflowId) ?? null;

  async function activateVersion(versionNumber: number) {
    if (!selectedWorkflowId) return;
    onBusyChange(true);
    try {
      await apiRequest(`/api/v1/workflows/${selectedWorkflowId}/activate/${versionNumber}`, {
        method: "POST",
      });
      await onVersionActivated();
      onMessage(`Activated version ${versionNumber}`);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      onBusyChange(false);
    }
  }

  return (
    <article className="card">
      <h2>3) Workflows and Versions</h2>
      <select value={selectedWorkflowId} onChange={(e) => onSelectWorkflow(e.target.value)}>
        <option value="">Select workflow</option>
        {workflows.map((w) => (
          <option key={w.id} value={w.id}>
            {w.name} (active v{w.active_version ?? "-"})
          </option>
        ))}
      </select>

      {selectedWorkflow && (
        <div className="summary">
          <p>
            <strong>Status:</strong> {selectedWorkflow.status}
          </p>
          <p>
            <strong>Description:</strong> {selectedWorkflow.description || "n/a"}
          </p>
        </div>
      )}

      <ul className="list">
        {versions.map((v) => (
          <li key={v.id}>
            <span>
              Version {v.version_number} {v.is_active ? "(active)" : ""}
            </span>
            <button onClick={() => void activateVersion(v.version_number)} disabled={busy}>
              Activate
            </button>
          </li>
        ))}
      </ul>
    </article>
  );
}
