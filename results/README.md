# Project X results

Each discovered task receives a directory at `results/<task-id>/` containing:

- `result.json`: terminal status, policy decision, adapter identity, timestamps, and artifact paths.
- `execution.jsonl`: append-only structured lifecycle events without the full task objective.
- `publication.json`: commit/push intent and publisher receipt.
- `mock-output.md`: deterministic mock artifact for tasks allowed through the V1 policy gate.

Invalid task files are recorded under `results/_invalid/` using only the source filename and validation error.

Phase 3 V1 results are intended to be versioned eventually, but the included publisher is a mock: running the agent does not stage, commit, or push anything.
