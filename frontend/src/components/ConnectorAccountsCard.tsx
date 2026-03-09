import { useState } from "react";
import { apiRequest } from "../lib/api";
import type { ConnectorAccount } from "../lib/types";

interface Props {
  busy: boolean;
  connectors: ConnectorAccount[];
  onConnectorSaved: () => Promise<void>;
  onMessage: (msg: string) => void;
  onError: (msg: string) => void;
  onBusyChange: (busy: boolean) => void;
}

export function ConnectorAccountsCard({
  busy,
  connectors,
  onConnectorSaved,
  onMessage,
  onError,
  onBusyChange,
}: Props) {
  const [connectorName, setConnectorName] = useState("smtp-default");
  const [connectorType, setConnectorType] = useState<"smtp" | "http" | "crm_internal">("smtp");
  const [connectorConfigText, setConnectorConfigText] = useState(
    JSON.stringify({ dry_run: true }, null, 2)
  );

  async function createConnector() {
    onBusyChange(true);
    try {
      const config = JSON.parse(connectorConfigText);
      await apiRequest<ConnectorAccount>("/api/v1/connectors", {
        method: "POST",
        body: JSON.stringify({
          name: connectorName,
          connector_type: connectorType,
          config,
          is_active: true,
        }),
      });
      await onConnectorSaved();
      onMessage("Connector saved");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      onBusyChange(false);
    }
  }

  return (
    <article className="card">
      <h2>5) Connector Accounts</h2>
      <div className="grid-two">
        <label>
          Name
          <input value={connectorName} onChange={(e) => setConnectorName(e.target.value)} />
        </label>
        <label>
          Type
          <select
            value={connectorType}
            onChange={(e) =>
              setConnectorType(e.target.value as "smtp" | "http" | "crm_internal")
            }
          >
            <option value="smtp">smtp</option>
            <option value="http">http</option>
            <option value="crm_internal">crm_internal</option>
          </select>
        </label>
      </div>
      <textarea
        value={connectorConfigText}
        onChange={(e) => setConnectorConfigText(e.target.value)}
        rows={5}
      />
      <button onClick={() => void createConnector()} disabled={busy}>
        Save Connector
      </button>

      <ul className="list">
        {connectors.map((c) => (
          <li key={c.id}>
            <span>
              {c.name} [{c.connector_type}] {c.is_active ? "active" : "inactive"}
            </span>
          </li>
        ))}
      </ul>
    </article>
  );
}
