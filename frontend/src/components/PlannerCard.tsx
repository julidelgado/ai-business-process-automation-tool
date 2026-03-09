import { useState } from "react";
import { apiRequest } from "../lib/api";
import type { PlannerResponse } from "../lib/types";

interface Props {
  initialPrompt: string;
  busy: boolean;
  onGenerated: (result: PlannerResponse, prompt: string) => void;
  onError: (msg: string) => void;
  onBusyChange: (busy: boolean) => void;
}

export function PlannerCard({ initialPrompt, busy, onGenerated, onError, onBusyChange }: Props) {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [planner, setPlanner] = useState<PlannerResponse | null>(null);

  async function generateSpec() {
    onBusyChange(true);
    try {
      const data = await apiRequest<PlannerResponse>("/api/v1/planner/generate", {
        method: "POST",
        body: JSON.stringify({ prompt }),
      });
      setPlanner(data);
      onGenerated(data, prompt);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      onBusyChange(false);
    }
  }

  return (
    <article className="card">
      <h2>1) Prompt and Generate</h2>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={4}
        placeholder="Describe the business process you want to automate..."
      />
      <div className="row">
        <button onClick={() => void generateSpec()} disabled={busy}>
          Generate Spec
        </button>
        {planner && (
          <p className="muted">
            Provider: <strong>{planner.provider}</strong> | Confidence:{" "}
            <strong>{Math.round(planner.confidence * 100)}%</strong>
          </p>
        )}
      </div>
      {planner?.warnings?.length ? (
        <ul className="warnings">
          {planner.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}
