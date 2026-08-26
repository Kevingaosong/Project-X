# Project X Phase 3.1：Git ↔ Codex 最小闭环

## 1. 目标与边界

Phase 3.1 让 GitHub 成为任务入口，让 Mac mini 每 60 秒检查一次 `tasks/`，调用本机 Codex，把结果写入 `results/`，再自动提交并推送。

这一阶段只接通仓库内闭环，不连接飞书、IBKR、EnergyMo、OpenClaw、交易、支付、生产 API 或外发消息，也不修改现有自动化服务。

```text
GitHub tasks/*.json
  ↓ fetch + fast-forward only
主仓库（必须干净）
  ↓ detached temporary worktree
风险策略 → Codex read-only / workspace-write sandbox
  ↓ only explicitly allowed paths
越界检查 → secrets 扫描 → diff 检查
  ↓
commit → push → remote SHA verification
```

## 2. 调度模型

`com.projectx.agent` 使用 launchd 的 `StartInterval=60`。每次唤醒只运行一个短生命周期进程，一次最多处理一个新任务；不使用永久驻留循环。非阻塞文件锁避免两个运行重叠。

服务使用独立 label 和独立日志目录，不加载、不停止、也不修改现有 OpenClaw 或量化 LaunchAgent。

## 3. Git 同步

每次运行开始时要求主工作树干净且位于 `main`：

1. `fetch origin main`；
2. 本地落后时只允许 fast-forward；
3. 本地和远端分叉时停止，等待人工检查；
4. 不使用 force push，不重写远端历史；
5. push 后重新 fetch，并比较本地和远端 commit SHA。

任务运行期间若手机端又推送了提交，发布器会在本地任务提交后基于最新远端进行普通 rebase；冲突时失败关闭，不自动解决业务冲突。

## 4. 隔离执行

真实 Codex 不直接在主工作树运行。协调器为当前 HEAD 建立一次性 detached worktree，任务完成后只把通过验证的文件复制回主仓库，再移除临时工作区。

任务有两种模式：

- `analysis`：默认模式，Codex 使用只读沙箱，只把最终回答和执行事件保存到结果目录。
- `workspace-write`：必须显式列出 `execution.write_paths`，Codex 使用 workspace-write 沙箱。

无论任务提示怎么写，控制层都会独立复核 Git 变更。超出白名单的修改不会进入主仓库。删除、重命名、复制、二进制文件和超过 1 MB 的文件在本阶段一律阻断。

以下控制范围不能由普通任务自我修改：`.git`、`.github`、`.codex`、`.ssh`、`tasks/`、`results/`、`work/`、`scripts/`、`tests/`、`src/project_x_agent/`、`.gitignore`、`pyproject.toml`。

## 5. Codex 与凭据

`CodexCliExecutor` 使用 ChatGPT 应用内置的 Codex CLI 和已有本机登录态；不创建 `OPENAI_API_KEY`，不读取或复制认证文件内容。每次会话使用 `--ephemeral`，并忽略用户级运行配置，减少意外插件、hook 或额外能力进入无人值守任务。

固定安全提示禁止：访问工作树外文件、读取 secrets、使用外部网络和生产 API、交易、支付、消息外发、Git 发布、系统调度及持久进程。提示不是唯一防线；临时 worktree、沙箱、路径验证和 Git 发布检查共同构成执行边界。

## 6. 风险与审批

`low`、`medium` 可进入相应沙箱。`high`、`critical` 必须同时包含 `authorization.execute=true`、`approved_by`、带时区的 `approved_at` 和 `reason`。

该 JSON 标记当前不是密码学签名，只适合仓库内受限任务，不能作为真实资金、生产写入或外发消息的充分授权。即使标记完整，也不能扩大写路径或越过本阶段关闭的能力。

## 7. 结果与审计

每个任务在 `results/<task-id>/` 记录输入 SHA-256、风险与策略决策、execution mode 与写路径、执行器、时间、Codex 最终回答、JSONL 生命周期日志和发布排队回执。

发布前再次扫描常见私钥、GitHub/OpenAI token、AWS access key 和 Bearer token 模式。日志做长度限制和敏感模式替换。检测信息只报告“疑似秘密存在”和内容摘要，不输出原值。

## 8. 失败恢复

- 主工作树不干净：停止同步，避免覆盖人工修改。
- 远端分叉或 rebase 冲突：停止并等待人工检查。
- Codex 超时或失败：写失败结果，不扩大权限重试。
- 越界修改或疑似 secret：临时工作树被丢弃，不复制、不提交。
- push 验证失败：返回非零状态，后续运行不会 force push。

launchd 标准输出和错误日志位于被 Git 忽略的 `work/launchd/`。

## 9. 后续扩展

下一阶段应依次增加任务 attempt ID 与重试预算、优先级和依赖 DAG、独立 verifier、批准签名、健康状态通知。多 Agent 应保持单一控制层，把 planner、coder、verifier、publisher 和领域适配器分为不同能力。

飞书先做只读和草稿；IBKR 继续严格区分离线数据、行情、账户只读、建议、纸面订单、真实订单；EnergyMo 先接本地资料和测试数据。任何生产写入都要另建适配器级审批，不能复用普通任务标记。

## 10. 手动运行

Mock 骨架：

```text
python3 scripts/run-agent.py
```

真实同步周期：

```text
python3 scripts/run-sync-worker.py \
  --repo-root /Users/kevin/Documents/Codex/2026-08-26/referenced-chatgpt-conversation-this-is-an \
  --codex-binary /Applications/ChatGPT.app/Contents/Resources/codex
```

定时配置的版本化来源是 `config/com.projectx.agent.plist`，安装位置是 `~/Library/LaunchAgents/com.projectx.agent.plist`。
