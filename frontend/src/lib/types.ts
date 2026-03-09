export type TriggerType = "webhook" | "manual" | "schedule";

export interface RetryPolicy {
  max_attempts: number;
  backoff_seconds: number;
}

export interface WorkflowStepSpec {
  id: string;
  type: "crm.create_contact" | "email.send" | "http.request";
  depends_on?: string[];
  input: Record<string, unknown>;
  retry?: RetryPolicy;
}

export interface WorkflowSpec {
  name: string;
  version: number;
  trigger: {
    type: TriggerType;
    event?: string;
    cron?: string;
  };
  steps: WorkflowStepSpec[];
  warnings?: string[];
}

export interface PlannerResponse {
  spec: WorkflowSpec;
  confidence: number;
  warnings: string[];
  provider: string;
}

export interface WorkflowSummary {
  id: string;
  name: string;
  description: string | null;
  status: string;
  active_version: number | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowVersion {
  id: string;
  workflow_id: string;
  version_number: number;
  is_active: boolean;
  spec_json: WorkflowSpec;
  created_at: string;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  workflow_version_id: string;
  trigger_type: string;
  status: string;
  trigger_payload: Record<string, unknown>;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
  created_at: string;
}

export interface StepRun {
  id: string;
  workflow_run_id: string;
  step_id: string;
  step_type: string;
  status: string;
  depends_on: string[];
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown> | null;
  attempt_count: number;
  max_attempts: number;
  backoff_seconds: number;
  scheduled_for: string;
  started_at: string | null;
  finished_at: string | null;
  last_error: string | null;
}

export interface ConnectorAccount {
  id: string;
  name: string;
  connector_type: "smtp" | "http" | "crm_internal";
  is_active: boolean;
  has_config: boolean;
  created_at: string;
  updated_at: string;
}
