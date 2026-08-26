# Project X tasks (Phase 3.1)

手机端可在 GitHub 中向本目录新增 `.json` 文件。Mac mini 每 60 秒检查一次 GitHub，按文件名顺序取一个新任务，结果写入 `results/<task-id>/` 后自动提交并推送。

## V1 task format

```json
{
  "schema_version": 1,
  "id": "demo-readonly-001",
  "title": "Demonstrate the mock loop",
  "objective": "Review the repository documentation and propose three improvements.",
  "risk_level": "low",
  "created_at": "2026-08-26T15:00:00+08:00",
  "authorization": {
    "execute": false
  },
  "execution": {
    "mode": "analysis",
    "write_paths": []
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
- `execution.mode`: `analysis`（默认，只读）或 `workspace-write`。
- `execution.write_paths`: 写任务必须列出允许修改的仓库相对路径；只读任务必须为空。

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

该标记只打开策略闸门，不会突破 Codex 沙箱、路径白名单、密钥扫描或 Git 发布检查。删除、重命名、交易、生产 API、外发消息和系统配置修改在 Phase 3.1 中仍不自动执行。

## Workspace-write 示例

```json
{
  "schema_version": 1,
  "id": "docs-note-001",
  "title": "Create a scoped documentation note",
  "objective": "Create docs/agent-output/example.md with a short status note.",
  "risk_level": "medium",
  "created_at": "2026-08-26T18:00:00+08:00",
  "authorization": {"execute": false},
  "execution": {
    "mode": "workspace-write",
    "write_paths": ["docs/agent-output/example.md"]
  },
  "metadata": {}
}
```

`scripts/`、`tests/`、`src/project_x_agent/`、`tasks/`、`results/`、`work/`、Git 配置及项目控制文件属于受保护范围，不能由普通任务自我修改。

## Safety rules

- Never place passwords, API keys, tokens, cookies, credentials, private keys, or OAuth secrets in a task.
- Sensitive-looking JSON keys are rejected before policy evaluation.
- A terminal result with the same task hash is not executed twice.
- To intentionally revise a task, change its content; for a distinct unit of work, use a new task ID.
- 每次定时唤醒最多处理一个新任务，避免并发和批量失控。
- Priority and dependency scheduling are reserved for a later phase.

See `_example-low-risk.json.example` and `_example-high-risk.json.example`. The `.example` suffix prevents the agent from discovering them as live tasks.
