# Project X Phase 3：Agent 最小闭环架构

## 1. 目标

Phase 3 把 Project X 从“有文档和 Git 的仓库”推进到“有明确任务入口、风险闸门、执行接口、结果证据和发布接口的 Agent 骨架”。

第一版只证明控制流程，不连接真实业务：

```text
tasks/*.json
    ↓ 扫描与校验
安全策略闸门
    ↓
MockCodexExecutor
    ↓
results/<task-id>/
    ↓
MockGitPublisher
```

V1 不调用真实 Codex、不执行 Shell 命令、不访问网络、不连接飞书/IBKR/EnergyMo，也不会自动运行 Git 命令。

## 2. 设计原则

### 默认安全失败

- `high` 和 `critical` 任务没有完整显式授权标记时只生成 `blocked` 结果。
- 授权标记缺少批准人、时间或原因时仍视为未授权。
- V1 即使看到完整授权，也只能进入 mock 执行器。
- 执行器和发布器不是 mock 时，Agent 构造函数直接拒绝启动。

### 任务是声明，不是脚本

任务文件描述目标和风险，而不是携带可执行命令。V1 不支持 `command`、Shell 或任意插件字段。任务中的敏感命名字段会被拒绝，避免秘密通过 tasks/results/Git 扩散。

### 结果是控制证据

Agent 为每个任务保存：

- 输入内容哈希，用于幂等判断；
- 风险与策略决策；
- 实际使用的执行器和发布器；
- 是否为 mock；
- 开始/结束时间；
- 产物相对路径；
- 结构化事件日志；
- Git 发布意图及 mock 回执。

日志不复制完整 objective，降低敏感信息在多处重复的风险。

### 单次扫描优先

默认命令只扫描一次，便于人工验证和外部调度。持续轮询必须显式使用 `--watch`，且最小间隔为 5 秒。Phase 3 不创建 launchd、cron 或 Codex 自动化，因此不会与现有控制入口发生新的调度冲突。

## 3. 组件边界

### Task model / loader

`models.py` 负责 JSON 大小限制、UTF-8/Schema 校验、任务 ID 约束、风险枚举和敏感字段拒绝。任务源被封装为 `TaskEnvelope`，其中保存路径与 SHA-256 内容哈希。

### Safety policy

`policy.py` 只回答“任务能否进入执行器”，不执行动作。当前规则很小，后续可扩展为能力白名单、工作区边界、审批签名和适配器专属策略。

### Executor interface

`TaskExecutor` 是执行接口。V1 唯一实现 `MockCodexExecutor`，它只返回固定结果和 Markdown 产物。

未来真实 Codex 适配器必须额外提供：

- 工作目录白名单；
- 命令/工具权限声明；
- 超时和取消；
- 标准输出脱敏；
- 产物清单；
- 网络和外部写入能力证明。

### Result store

`ResultStore` 使用临时文件加原子替换写 JSON/Markdown，生命周期日志使用 JSONL 追加。所有 artifact 路径必须留在当前任务结果目录内。

### Publisher interface

`ResultPublisher` 是 Git 发布接口。V1 唯一实现 `MockGitPublisher`，只返回“本来会使用的提交信息”，不会运行 Git。

未来真实 Git 发布器应：

1. 只允许任务文件和对应结果目录进入暂存区；
2. 提交前执行 secrets 扫描和 `git diff --check`；
3. 验证当前分支、上游与远端；
4. 使用互斥锁避免并发提交；
5. push 后验证远端提交哈希；
6. 拒绝 force push、历史改写和不相关文件。

## 4. 目录结构

```text
.
├── docs/
│   └── project-x-agent-architecture.md
├── tasks/
│   ├── README.md
│   └── *.json
├── results/
│   ├── README.md
│   └── <task-id>/
│       ├── result.json
│       ├── execution.jsonl
│       ├── publication.json
│       └── mock-output.md
├── scripts/
│   └── run-agent.py
├── src/project_x_agent/
└── tests/
```

## 5. 状态与幂等

任务身份由 `id` 和文件内容哈希共同确定。

- 同一任务 ID、同一哈希已有终态结果：跳过。
- 同一任务 ID 的文件内容改变：视为新尝试，再次评估策略。
- 高风险任务可以先产生 `blocked` 结果，补齐显式授权后再次评估。
- 需要保留每次尝试的完整历史时，后续版本应引入 attempt ID；V1 以 JSONL 日志保留事件线索，`result.json` 表示最新结果。

## 6. 为什么不在 V1 直接调用 Codex 和 Git

当前 Mac mini 已存在 Codex 自动化、一个已加载的量化 LaunchAgent、OpenClaw 历史入口和交易代码。若 V1 同时接入真实 Codex 与真实 Git 自动发布，会在以下能力尚未完成前扩大风险：

- 唯一调度器没有确定；
- 任务审批标记尚未签名或绑定身份；
- 没有完整的工作区和工具权限控制；
- 没有 secrets 后端；
- 没有并发锁和失败恢复；
- 没有自动验收器。

因此 V1 先冻结接口，用测试证明状态机和风险闸门，再逐个替换 mock。

## 7. 后续扩展路线

### 优先级、依赖关系与自动验收

下一版可以在不改变执行器接口的情况下增加：

- `priority` 与公平队列；
- `depends_on` 与有向无环图校验；
- attempt ID 和重试预算；
- acceptance checks 与独立 verifier；
- 任务超时、租约和并发互斥；
- 签名批准记录，替代单纯布尔标记。

### 多 Agent

控制层保持单一，多个 Agent 作为受限 worker 注册能力：

- planner：拆解目标，不执行外部动作；
- coder：仅在指定 Git 工作区修改代码；
- verifier：只读测试与验收；
- publisher：只允许提交已验收路径；
- domain adapter：飞书、IBKR、EnergyMo 等专域能力。

调度器根据能力、风险等级和租约分发任务；worker 不能自行升级权限或调用另一高权限 worker。

### 飞书适配器

先实现白名单对象的只读获取，再实现“草稿写入 → 差异展示 → 人工批准 → 写后读回验证”。消息发送、任务创建和 CRM 更新分别定义权限，不共享笼统的“飞书可写”权限。

### IBKR 适配器

保持六级隔离：离线数据、行情读取、账户只读、建议生成、纸面订单、真实订单。早期只接离线/只读；真实订单必须使用独立项目、独立凭据、订单上限和即时人工确认，不能依靠任务 JSON 中的普通授权字段。

### EnergyMo 适配器

先接本地资料索引、报告生成和 CRM 测试数据。对外发送、发布、生产 CRM/飞书写入必须经过目标对象白名单和写前差异审批。

### Secrets 与身份

任务只保存 secret reference，不保存秘密值。未来由独立凭据适配器按任务身份、能力和时间窗口解析，日志只记录引用 ID 与授权结果。

## 8. 当前运行方式

无需安装依赖：

```text
python3 scripts/run-agent.py
```

显式持续轮询：

```text
python3 scripts/run-agent.py --watch --interval 60
```

两种方式当前都只使用 mock。Phase 3 完成时不启动常驻进程、不创建系统调度配置。
