# Project X — Context & Execution Charter

> 用途：把本文件交给 Mac mini 上的 ChatGPT / Codex，使新的会话快速理解 Project X 的背景、目标、边界、当前进度和下一步工作方式。
>
> 更新时间：2026-08-26

## 1. 项目背景

用户有一台长期运行的 Mac mini，设备名称为“All money back my home”。

过去这台机器承担过自动化工作，并使用过 OpenClaw。现在的方向已经改变：

- OpenClaw 已停止作为当前执行环境。
- 后续优先使用 Codex 作为本机执行环境。
- 用户希望减少“手机 ChatGPT → 人工复制 → Mac mini Codex → 再复制结果回来”的操作。
- 最终希望形成一套长期工作机制：
  - ChatGPT：需求理解、规划、拆解、决策、验收。
  - Codex：在 Mac mini 上读取文件、写代码、执行命令、测试、生成结果。
  - Mac mini：长期工作节点。
  - Git：记录代码、配置和变更历史。
  - 后续可按需要接入飞书等通知/业务入口。

Project X 就是为实现这套工作方式建立的长期项目。

## 2. 最终目标

把这台 Mac mini 建设成一个可持续维护、可审计、可由 Codex 执行任务的工作节点。

理想工作流：

1. 用户提出目标，而不是逐条操作电脑。
2. ChatGPT/Codex 将目标拆解为可执行任务。
3. Codex 在 Mac mini 本机完成：
   - 文件检索
   - 代码修改
   - 脚本执行
   - 测试
   - 数据处理
   - 文档生成
   - Git 版本管理
4. 对高风险动作设置明确的人工确认边界。
5. 执行完成后自动形成结构化结果和验收报告。
6. 用户主要负责：
   - 提目标
   - 做关键决策
   - 批准高风险动作
   - 验收最终结果

原则：尽量减少用户充当两个 AI 会话之间的“复制粘贴中间人”。

## 3. 当前已完成状态

已在 Mac mini 上建立新的 Project X 项目。

初始化时目录为空且不是 Git 仓库，已经执行：

- `git init`
- 创建基础目录
- 创建 README
- 创建 `.gitignore`

初始化后的基础结构为：

```text
.
├── .git/
├── .gitignore
├── README.md
├── docs/
│   └── .gitkeep
├── scripts/
│   └── .gitkeep
├── src/
│   └── .gitkeep
├── outputs/
└── work/
```

其中：

- `src/`：正式代码
- `scripts/`：运维、自动化和辅助脚本
- `docs/`：项目文档、架构、盘点结果、SOP
- `outputs/`：任务输出
- `work/`：临时工作区，原则上不进入 Git

Git 当前尚未进行首次正式提交。

资产盘点现已完成，并生成：

- `docs/asset-inventory.md`
- `docs/project-x-roadmap.md`

## 4. 当前阶段：先盘点，不要急着重建

这台 Mac mini 过去已经存在大量自动化资产。

因此 Project X 的第一原则不是“从零重新开发”，而是：

> **先把旧资产摸清楚，再决定复用、迁移、重构、归档或废弃。**

尤其关注：

- Codex
- OpenClaw 历史资产
- 飞书 / Feishu / Lark
- Money 机器人
- 股票、美股、港股、IBKR
- 自动下单/交易相关程序
- EnergyMo
- CRM
- Python 自动化
- Node 项目
- cron
- launchd
- shell scripts
- API 集成
- 各类历史项目目录

## 5. 第一阶段任务：Mac mini 资产盘点

Codex 应首先进行只读盘点。

优先检查：

```text
~/Desktop
~/Documents
~/Downloads
~/Projects
~/Developer
~/.codex
```

以及用户目录中其他明显属于项目、机器人、自动化或开发工作的目录。

### 需要识别的信息

对于发现的资产，尽量记录：

- 名称
- 路径
- 大致用途
- 技术栈
- 最后修改时间（可获得时）
- 是否可能仍可运行
- 是否依赖外部服务
- 与 Project X 的关系
- 建议：复用、迁移、重构、归档或暂不处理

### 输出

生成：

```text
docs/asset-inventory.md
docs/project-x-roadmap.md
```

`project-x-roadmap.md` 根据真实盘点结果提出后续建设路线。

## 6. 安全边界

在没有用户明确批准之前，Codex 不得：

- 删除历史文件
- 覆盖无法恢复的重要文件
- 大规模移动历史目录
- 启动或恢复 OpenClaw
- 执行真实股票交易
- 下真实订单
- 调用可能造成资金变化的生产 API
- 修改券商账户
- 修改支付账户
- 修改生产环境关键配置
- 对外发送真实业务消息
- 对外发布内容
- 更改系统关键安全设置

### Secrets

如果发现：

- `.env`
- API Key
- Token
- Cookie
- Password
- Credentials
- SSH private key
- OAuth secret

原则是：

> **可以确认其存在，但不要把秘密值写入报告、Git、聊天记录或日志。**

任何 secrets 都不得提交到 Git。

## 7. OpenClaw 的处理原则

OpenClaw 在这台机器上属于历史资产。

当前原则：

- 可以扫描。
- 可以分析配置和历史代码。
- 可以识别其中值得复用的逻辑。
- 不应默认启动。
- 不应默认恢复 Gateway/Agent。
- 不应因为发现旧配置就把 Project X 重新建立在 OpenClaw 上。

如果旧 OpenClaw 中存在有价值能力，应优先考虑：

> **抽取能力 → 迁移到 Project X / Codex 架构**

而不是恢复整个旧系统。

## 8. Money / 股票自动化属于高优先级历史资产

过去存在与以下方向有关的自动化：

- 飞书机器人
- Money
- 美股
- 港股
- IBKR
- 自动化交易/下单

盘点时应优先寻找相关资产。

但是：

> **发现交易代码 ≠ 允许执行交易。**

所有真实资金操作都属于高风险动作。

后续即使恢复交易链路，也必须至少区分：

1. 数据读取
2. 分析
3. 生成交易建议
4. 模拟执行
5. 待确认订单
6. 真实订单

默认不得直接跨越到第 6 步。

## 9. EnergyMo 与业务自动化

Project X 后续也可能承担 EnergyMo 相关工作，例如：

- 产品资料整理
- 市场研究
- 销售支持
- CRM
- 渠道资料
- 数据分析
- 文件生成
- 报告/PPT 数据准备
- 飞书业务流程
- 自动化运营

因此如果 Mac mini 中发现 EnergyMo 相关历史项目，应纳入资产盘点，不要随意移动或删除。

## 10. Project X 推荐工作方式

以后收到用户目标时，不要机械地要求用户执行大量终端命令。

### A. Codex 能自己完成

直接：

1. 检查环境
2. 制定简短计划
3. 执行
4. 测试
5. 验收
6. 汇报

### B. 涉及风险

停止在风险动作之前，明确告诉用户：

- 准备做什么
- 会影响什么
- 是否可逆
- 需要用户批准什么

获得批准后再继续。

### C. 信息不足

先尽可能通过以下来源自行获取上下文：

- 本地文件
- Git
- README
- docs
- 配置
- 日志
- 代码

只有确实无法判断时才询问用户。

目标是：

> **减少用户操作次数，而不是把 Codex 的工作拆成几十条命令让用户手动执行。**

## 11. Git 原则

Project X 的正式资产应逐步进入 Git 管理。

建议：

- 小步提交
- 提交信息清晰
- 重大改动前先检查 `git status`
- 不提交 secrets
- 不提交临时文件
- 不提交大体积无意义产物

在项目结构和第一阶段文档稳定后，可以进行首次 baseline commit。

不要为了“保持干净”而删除用户历史资产。

## 12. 建议的后续阶段

### Phase 1 — Discovery

盘点 Mac mini 历史资产。

### Phase 2 — Architecture

根据真实资产设计 Project X 架构。

### Phase 3 — Migration

迁移值得保留的自动化能力。

### Phase 4 — Execution Layer

建立统一任务执行、日志、状态和错误处理机制。

### Phase 5 — Safety & Approval

为交易、外发消息、生产 API 等增加确认机制。

### Phase 6 — Integrations

按价值逐步恢复或建设：

- 飞书
- Money
- IBKR
- EnergyMo
- CRM
- 其他业务系统

### Phase 7 — Long-running Worker

让 Mac mini 成为稳定的长期工作节点，包括：

- 开机恢复
- 健康检查
- 日志
- 故障恢复
- Git 版本控制
- 任务状态
- 必要的通知机制

## 13. 当前立即执行的任务

如果本文件是第一次交给新的 Codex 会话：

先不要重新初始化 Project X。

首先检查当前 Project X 状态和 `git status`。

如果资产盘点尚未完成，则继续完成：

```text
docs/asset-inventory.md
docs/project-x-roadmap.md
```

盘点结束后汇报：

1. 找到了哪些关键资产。
2. 最值得复用的 5 项资产。
3. 哪些旧系统已经失效或存在风险。
4. 是否找到了 Money / 飞书 / IBKR / 股票交易相关链路。
5. 是否找到了 EnergyMo / CRM 相关资产。
6. 推荐的 Project X 架构。
7. 下一步最值得执行的 3 项任务。

然后停止，等待用户批准下一阶段。

## 14. 给 Codex 的核心指令

Project X 不是一次性的脚本项目。

它的目标是逐渐形成：

> **ChatGPT 负责理解、规划和验收；Codex 负责在 Mac mini 上执行；Git 负责记录；Mac mini 负责长期运行；用户只处理真正需要人做决策的事情。**

每次设计方案时，都优先问自己：

> “能不能让用户少操作一步？”

如果答案是能，就应该优先自动化那一步。
