# Testing Strategy

## Unit Tests
- Workflow schema validation.
- Dependency graph and cycle checks.
- Retry policy behavior.
- Connector input mapping utilities.

## Integration Tests
- API + DB for workflow CRUD.
- Trigger ingestion to run creation.
- Worker execution with mocked connectors.

## End-to-End Tests
- Prompt to approved workflow.
- Trigger to completed run with expected side effects.
- Failure path with retries and dead-letter.

## Non-Functional Tests
- Load smoke test for concurrent runs.
- Basic reliability test for worker restarts.

## Test Data Strategy
- Seed deterministic sample workflows.
- Use synthetic trigger payloads for replayability.

## Quality Gate Before Release
- Unit and integration tests must pass in CI.
- At least one green end-to-end scenario per connector type.
- No high severity security findings in dependency scan.
