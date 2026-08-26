# Project X tasks

The agent scans this directory for files ending in `.json`. Phase 3 V1 processes files in filename order and records terminal state in `results/<task-id>/result.json`.

## V1 task format

```json
{
  "schema_version": 1,
  "id": "demo-readonly-001",
  "title": "Demonstrate the mock loop",
  "objective": "Produce a deterministic mock result without external side effects.",
  "risk_level": "low",
  "created_at": "2026-08-26T15:00:00+08:00",
  "authorization": {
    "execute": false
  },
  "metadata": {}
}
```

Required fields:

- `schema_version`: must be `1`.
- `id`: 3-64 lowercase letters, numbers, dots, dashes, or underscores.
- `title`: short human-readable name.
- `objective`: desired outcome. Do not put secrets in it.
- `risk_level`: `low`, `medium`, `high`, or `critical`.
- `created_at`: an ISO 8601 timestamp supplied by the task author.

Optional fields:

- `authorization`: explicit approval marker for high-risk work.
- `metadata`: non-sensitive labels or correlation data. V1 does not schedule by metadata.

## High-risk authorization marker

High and critical tasks are blocked unless all four fields below are present:

```json
{
  "authorization": {
    "execute": true,
    "approved_by": "human-approver",
    "approved_at": "2026-08-26T15:00:00+08:00",
    "reason": "Explicit approval for this exact task scope"
  }
}
```

This marker only opens the policy gate. Phase 3 V1 still calls a mock executor and cannot perform real actions.

## Safety rules

- Never place passwords, API keys, tokens, cookies, credentials, private keys, or OAuth secrets in a task.
- Sensitive-looking JSON keys are rejected before policy evaluation.
- A terminal result with the same task hash is not executed twice.
- To intentionally revise a task, change its content; for a distinct unit of work, use a new task ID.
- Priority and dependency scheduling are reserved for a later phase.

See `_example-low-risk.json.example` and `_example-high-risk.json.example`. The `.example` suffix prevents the agent from discovering them as live tasks.
