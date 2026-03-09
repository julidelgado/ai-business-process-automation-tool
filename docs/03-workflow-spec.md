# Workflow Specification and NL Pipeline

## Workflow JSON Model (MVP)

```json
{
  "name": "new-client-onboarding",
  "version": 1,
  "trigger": {
    "type": "webhook",
    "event": "client.created"
  },
  "steps": [
    {
      "id": "create_crm_contact",
      "type": "crm.create_contact",
      "input": {
        "email": "{{trigger.payload.email}}",
        "first_name": "{{trigger.payload.first_name}}",
        "last_name": "{{trigger.payload.last_name}}"
      },
      "retry": {
        "max_attempts": 3,
        "backoff_seconds": 10
      }
    },
    {
      "id": "send_welcome_email",
      "type": "email.send",
      "depends_on": ["create_crm_contact"],
      "input": {
        "to": "{{trigger.payload.email}}",
        "template_id": "welcome_v1",
        "variables": {
          "first_name": "{{trigger.payload.first_name}}"
        }
      }
    }
  ]
}
```

## NL-to-Workflow Pipeline
1. Intent extraction
- Parse entities, trigger conditions, and actions.

2. Schema generation
- LLM returns strict JSON only (no prose).

3. Deterministic validation
- JSON schema validation.
- Supported connector and action checks.
- Dependency graph validation (no cycles).

4. Confidence and warnings
- Surface ambiguous mappings for manual review.

5. Human approval
- User can edit before activation.

## Validation Rules
- Each step id must be unique.
- `depends_on` must reference existing step ids.
- Trigger type must be supported.
- Action type must map to installed connector handler.
- Retry policy must respect global limits.

## Error Handling Model
- Step states: `pending`, `running`, `success`, `failed`, `dead_letter`.
- On failure, worker retries based on policy.
- Exhausted retries move step to dead-letter and mark run as failed.

## Prompting Strategy (MVP)
- Use a system prompt that defines strict schema output.
- Inject available connector capability catalog.
- Reject output if schema invalid and reprompt once.
