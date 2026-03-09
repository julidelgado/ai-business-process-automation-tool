# Risk and Security Plan

## Top Risks
1. Incorrect workflow generation from ambiguous prompts.
Mitigation:
- Strict schema output and validator.
- Mandatory human approval before activation.

2. Connector failures and flaky third-party APIs.
Mitigation:
- Retries with capped backoff.
- Dead-letter state and actionable logs.

3. Prompt injection through payload data.
Mitigation:
- Never treat runtime payload as planner instructions.
- Escape and sanitize template variables.

4. Secret leakage in logs.
Mitigation:
- Secrets stored encrypted at rest.
- Redaction rules in all logs and API responses.

5. Unsafe or destructive action execution.
Mitigation:
- Allowlist supported action types.
- Policy engine blocks prohibited operations.

## Security Baseline (MVP)
- Environment-based secret management.
- API authentication for management endpoints.
- Audit events for create/update/activate/run operations.
- Connector credentials never returned in plain text.
