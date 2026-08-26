# Project X

Phase 3.1 uses GitHub as the task inbox. The Mac mini checks `tasks/` every 60 seconds, runs at most one new task in an isolated Codex worktree, records evidence in `results/`, and publishes only validated paths. See `tasks/README.md` for the task format and `docs/project-x-agent-architecture.md` for safety boundaries.

Project X turns this Mac mini into a maintainable, auditable long-running work node operated by Codex.

## Start here

- [`docs/project-x-context-and-execution-charter.md`](docs/project-x-context-and-execution-charter.md) — authoritative context, goals, boundaries, and working agreement
- [`docs/asset-inventory.md`](docs/asset-inventory.md) — read-only inventory of existing automation assets
- [`docs/project-x-roadmap.md`](docs/project-x-roadmap.md) — proposed construction roadmap based on the inventory
- [`docs/project-x-agent-architecture.md`](docs/project-x-agent-architecture.md) — Phase 3 agent architecture and extension boundaries

## Structure

- `src/` — source code
- `docs/` — project documentation
- `scripts/` — development and maintenance scripts
- `tasks/` — versioned task declarations consumed by the agent
- `results/` — structured task results and execution evidence

## Phase 3 mock agent

Run one local scan without installing dependencies:

```bash
python3 scripts/run-agent.py
```

The Phase 3 implementation is deliberately mock-only. It does not invoke Codex, run task commands, call business APIs, or execute Git commits and pushes.

Run the standard-library test suite:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
