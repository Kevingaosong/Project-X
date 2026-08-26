# Project X：Mac mini 自动化资产盘点

盘点日期：2026-08-26（Asia/Shanghai）  
盘点方式：只读文件系统、项目标记、文件名、非敏感清单和运行状态检查。

## 1. 范围与安全边界

本次覆盖：

- `/Users/kevin/Desktop`
- `/Users/kevin/Documents`
- `/Users/kevin/Downloads`
- `/Users/kevin/.codex`
- `/Users/kevin/.openclaw` 及三个历史备份目录
- `/Users/kevin/.lark-cli`
- `/Users/kevin/.agents/skills`
- `/Users/kevin/.venvs`
- `/Users/kevin/.local/bin`
- `/Users/kevin/prod_template`
- `/Users/kevin/Library/LaunchAgents`
- `/Users/kevin/Applications` 中的交易客户端

`/Users/kevin/Projects` 与 `/Users/kevin/Developer` 当前不存在。

本次没有启动 OpenClaw、交易程序或任何项目，没有执行测试、安装依赖、调用外部 API、提交订单或修改系统配置。扫描跳过了 `node_modules`、虚拟环境内部包、缓存、日志正文、会话正文、媒体正文等高噪声内容。

敏感文件只确认存在，不读取内容。本报告不包含 API Key、密码、Token、Cookie、私钥或其他秘密值。

## 2. 关键结论

1. 最完整、最接近可运行状态的业务自动化资产是 `/Users/kevin/Documents/量化炒股`：它是一个 Python 3.11+ 的 IBKR 美股/港股量化框架，包含扫描、因子、组合、风控、回测、通知、Money 同步、纸面及确认式执行相关模块、18 个测试文件和历史运行数据。
2. Codex 已经承担一部分调度工作：存在 3 个本地自动化，其中“美股深度研究补给”为启用状态，两个 IBKR 自动化处于暂停状态；另有一套 IBKR 只读状态报告技能。
3. 飞书能力已具备较完整的工具层：`lark-cli` 已安装，用户级 Lark 技能覆盖文档、表格、Base、日历、任务、IM、邮件、审批、知识库等；认证配置存在，但有效性未调用 API 验证。
4. OpenClaw 历史资产完整但杂乱：主目录约 3.4 GB，含历史工作区、插件、Feishu、IBKR、技能、状态、凭据目录及三个备份。OpenClaw 可执行文件和 LaunchAgent 文件仍在，但此次检查未发现其 LaunchAgent 已加载。
5. EnergyMo 资产丰富，重点不是单一代码库，而是历史增长工作流、战略文档、CRM 表格模板、模型脚本、营销素材和已生成内容，可迁移为 Project X 的业务工作流模板与验收样例。
6. 没有用户级 cron 任务。存在一个已加载的 `com.kevin.quant-ibkr.paper` LaunchAgent；检查时没有常驻进程，记录的最近退出状态为 0，但它仍可能按自身触发条件再次运行。
7. 核心量化目录没有发现独立 `.git` 仓库，版本追踪与变更审计是明显缺口。

## 3. 资产清单

| 资产 | 路径 | 大致用途 | 技术栈/形态 | 仍可能运行 | 与 Project X 的关系 | 建议 |
|---|---|---|---|---|---|---|
| IBKR 量化主项目 | `/Users/kevin/Documents/量化炒股` | 美股/港股扫描、因子、研究、回测、组合、风控、通知、账户读取、Money 同步及受控执行 | Python 包，`pyproject.toml`，APScheduler、ib-insync、pandas、Pydantic、yfinance、pytest | 高；2026-08-18 仍有代码、测试和扫描记录更新，但本次未执行验证 | 可作为 Project X 的交易研究与只读账户适配器来源 | **迁移后复用**；先冻结执行能力，只迁移只读、研究、报告和风控部分 |
| IBKR 专用虚拟环境 | `/Users/kevin/.venvs/quant-ibkr` | 量化项目运行环境 | Python 3.13.12 venv，已安装为可编辑包 | 高；环境结构完整 | 可作为依赖基线证据，不应直接成为长期唯一运行环境 | **记录并重建**；后续从锁定清单复现，不直接搬运环境目录 |
| 量化 LaunchAgent | `/Users/kevin/Library/LaunchAgents/com.kevin.quant-ibkr.paper.plist` | 纸面量化任务的用户级调度 | macOS launchd | 中高；标签已加载，检查时 PID 为空，最近退出状态 0 | 是 Project X 接管调度前必须处理的既有控制面 | **优先审计**；在得到明确授权前不修改，后续避免与 Codex 重复调度 |
| Codex 自动化 | `/Users/kevin/.codex/automations` | 定时研究、IBKR 提示和收盘日报 | Codex automation TOML + memory | 高；1 个 ACTIVE、2 个 PAUSED | 可直接作为未来调度定义的参考 | **复用定义、重做权限**；先审计活跃研究任务的网络和写入边界 |
| IBKR 只读状态技能 | `/Users/kevin/.codex/memories/skills/ibkr-readonly-status-report` | 生成 IBKR 只读状态报告 | Codex Skill Markdown | 高；结构完整 | 很适合作为 Project X 的第一批低风险验收任务 | **优先复用**；迁入项目并补充固定输出契约与脱敏规则 |
| Codex 运行资产 | `/Users/kevin/.codex` | Codex 会话、技能、插件、自动化、缓存和本地数据库 | Codex 桌面运行目录 | 当前正在使用 | Project X 的主要调度控制面 | **原地使用、不要整体迁移**；只抽取经过审核的技能和自动化定义 |
| OpenClaw 主历史资产 | `/Users/kevin/.openclaw` | 历史代理、Feishu、插件、流程、任务、技能、IBKR 工作区及状态 | Node/Python/Markdown/JSON/插件混合，约 3.4 GB | 未验证；二进制仍存在，但未启动，LaunchAgent 未见加载 | 是迁移知识与工作流的来源，不应作为 Project X 的并行控制面 | **只读归档并选择性迁移**；禁止整体恢复或启动 |
| OpenClaw 历史备份 | `/Users/kevin/.openclaw-backup-20260331-201029`、`...201812`、`...20260401-004927` | OpenClaw 会话和配置历史快照 | 目录备份，约 2.0 MB、2.7 MB、4 KB | 不作为运行资产 | 可用于追溯配置演变 | **归档**；后续先做去重清单和校验和，不直接合并 |
| OpenClaw IBKR Bootstrap | `/Users/kevin/.openclaw/workspace/ibkr-quant` | TWS/IBKR 健康检查、账户探测、策略、仪表盘、回测、纸面下单测试 | Python 脚本、Shell、旧 venv、`.env` 配置 | 中；结构完整但较旧，最后目录时间为 2026-04-09 | 可补充主量化项目早期设计与连接诊断 | **迁移有价值模块，随后归档**；不要运行其中下单测试 |
| OpenClaw 金融技能库 | `/Users/kevin/.openclaw/workspace/skills` | 市场环境、新闻、证券研究、回测、量化决策、交易风控、RSS、记忆等 | 多个 `SKILL.md`，少量 Node 插件 | 中；文档型技能大多可移植 | 可形成 Project X 的研究和风控知识层 | **选择性迁移**；优先交易风险清单、量化决策、证券研究和多源新闻 |
| 飞书 CLI 状态 | `/Users/kevin/.lark-cli` | 飞书 CLI 配置、缓存、认证日志 | Node CLI 本地状态 | 可能；`lark-cli` 命令已安装，认证有效性未验证 | 是 Project X 对飞书进行受控读写的基础 | **复用工具，不迁移秘密**；后续先做只读认证探针和权限清单 |
| 飞书技能套件 | `/Users/kevin/.agents/skills/lark-*` | Docs、Sheets、Base、Calendar、Task、IM、Mail、Wiki、审批、会议等 | Codex/Lark 技能 | 高；技能文件齐全 | 可直接构成 Project X 的协作适配器层 | **优先复用**；按最小权限逐项启用，写操作必须审批 |
| Feishu 桌面应用 | 当前已加载标签 `application.com.bytedance.macos.feishu...` | 人工协作入口 | macOS 应用 | 是 | 可作为人工确认和结果交付通道 | **保留**；不要把桌面登录态当作自动化凭据来源 |
| EnergyMo 增长自动化包 | `/Users/kevin/Documents/Codex/2026-05-15/energymo` | 90 天增长、站点审计、SEO、达人外联、UGC、广告测试和周复盘 | Markdown 工作流、CSV 模板、Shell/Command 启动器、旧 OpenClaw 入口 | 部分；内容可用，OpenClaw 启动器不应运行 | 可迁移为 Project X 的营销业务流程与验收样例 | **迁移内容、归档启动器** |
| EnergyMo 战略与 CRM 模板 | `/Users/kevin/Documents/2026 下半年战略部署与实施` | 战略执行、渠道漏斗、海外达人、渠道 CRM、库存、现金流和周度看板 | Markdown、CSV、XLSX、Node `.mjs` 模型脚本 | 内容高可用；脚本未执行验证 | 是 Project X 建立 CRM/经营工作流的最佳业务数据模型来源 | **优先复用模板**；先定义字段字典，再迁入正式系统 |
| EnergyMo 市场资料 | `/Users/kevin/Desktop/EnergyMo资料包`、`/Users/kevin/Documents/EnergyMo市场资料物料`、`/Users/kevin/Documents/Seblong/EnergyMo` | 品牌、产品、渠道、培训、合同和营销素材 | PDF、PPTX、DOCX、XLSX、图片、视频 | 文档资产可用 | 可作为内容生成、检索和视觉验收的素材库 | **整理后复用**；建立来源、版本、授权和敏感级别元数据 |
| EnergyMo 医疗测试资料 | `/Users/kevin/Desktop/医疗器械测试数据` | 心率一致性、测试记录、论文草稿和数据包 | Pages、CSV、DOCX、PDF、ZIP | 可能可用，未打开内容 | 可作为高敏业务数据治理的验收场景 | **暂不处理**；先明确隐私、合规和数据授权 |
| Money 机器人线索 | `/Users/kevin/Documents/Codex/2026-08-11/money-ibtws-api`、`/Users/kevin/Documents/Codex/2026-08-24/tws-money` | 名称显示为 Money 与 TWS/IBKR 的连接尝试 | 当前目录为空 | 否 | 不能作为实现来源，只能作为历史命名线索 | **归档说明**；真正可复用实现位于量化项目的 `money_sync.py` 及相关测试 |
| CRM 线索 | `/Users/kevin/Documents/2026 下半年战略部署与实施/execution_templates/10_海外网红开发CRM.csv`、`13_渠道CRM与动销闸门表.csv` | 达人和渠道 CRM 数据模板 | CSV | 是，作为模板 | 可定义 Project X 的 CRM 最小数据模型 | **复用**；不要直接把历史业务数据导入生产系统 |
| TWS 与 IB Gateway | `/Users/kevin/Applications/Trader Workstation`、`/Users/kevin/Applications/IB Gateway 10.48` | IBKR 桌面与网关连接客户端 | macOS Java 应用 | 可能；仅确认安装存在 | 是未来账户只读、纸面和交易隔离的外部执行端 | **保留但默认关闭**；任何连接或下单需单独授权 |
| Lamma 应用原型 | `/Users/kevin/Documents/Codex/2026-05-16/ugc-app-hapi-yali-token-arr` | 移动应用、落地页和 Supabase 后端草案 | Expo、React Native、TypeScript、Supabase、HTML | 中高；脚手架与文档完整，未运行 | 与 Project X 业务无直接关系，但可复用项目规范和安全文档结构 | **暂不迁移，参考架构** |
| Bible Electron 项目 | `/Users/kevin/Desktop/Cursor/Bible` | AI 助手桌面应用及音频生成 | Electron、HTML/CSS/JS、Python | 中；依赖锁文件存在，未运行 | 与 Project X 关系较弱，可作为桌面包装参考 | **暂不处理** |
| 生产模板骨架 | `/Users/kevin/prod_template` | `bin/config/logs/scripts/state` 目录骨架 | 空目录结构 | 低；未发现实现文件 | 目录分层思路可参考，但没有可复用逻辑 | **归档或仅参考** |
| 当前 Project X 仓库 | `/Users/kevin/Documents/Codex/2026-08-26/referenced-chatgpt-conversation-this-is-an` | Project X 建设入口 | Git、Markdown、空的 `src/scripts` | 是 | 未来唯一受控建设仓库 | **继续建设**；下一阶段先做治理和验收骨架，不接生产能力 |

## 4. 自动化与调度现状

### Codex 自动化

| 名称 | 状态 | 周期概况 | 风险判断 |
|---|---|---|---|
| 美股深度研究补给 | ACTIVE | 工作日每小时 | 可能持续访问外部数据或写入研究资产；提示正文未纳入报告，需要后续专项审计 |
| IBKR 美股收盘日报 | PAUSED | 每周二至周六 06:15 | 暂停状态降低即时风险，但恢复前需检查数据源和输出去向 |
| IBKR 选股与交易提示 | PAUSED | 每日多个晚间时段 | 名称涉及交易提示；恢复前必须确认其绝不自动提交订单 |

### launchd 与 cron

- 用户级 `cron`：0 条非注释任务。
- `com.kevin.quant-ibkr.paper`：LaunchAgent 文件存在且标签已加载；检查时 PID 为空，最近退出状态为 0。它不是持续运行进程，但仍可能由定时或其他条件唤醒。
- `ai.openclaw.gateway.plist`：文件存在，但未在当前已加载标签中发现。没有启动或恢复 OpenClaw。
- 其他用户 LaunchAgent 包括 Google 更新、Ollama 和网盘服务，不属于本次 Project X 核心范围。

## 5. 技术运行环境

已确认存在：

- Git：`/opt/homebrew/bin/git`
- 系统默认 Python：3.14.3
- 量化专用 Python venv：3.13.12
- Node.js：24.15.0
- npm：11.12.1
- uv：0.11.17
- `lark-cli`
- `openclaw` 可执行文件（仅确认存在，未执行）
- Trader Workstation 与 IB Gateway 10.48

环境存在版本分叉：量化项目声明 Python `>=3.11`，已用 venv 为 3.13，而当前默认 Python 为 3.14。后续不能假定默认 Python 可直接替代现有环境。

## 6. 敏感资产存在性

以下只记录“存在”，未读取内容：

- `/Users/kevin/Documents/量化炒股`：存在 `.env` / 环境配置类文件。
- `/Users/kevin/.openclaw`：存在凭据、身份、服务环境及多类敏感命名文件；扫描计数为 52 个敏感命名文件，且另有配置备份。
- `/Users/kevin/.codex`：存在 3 个敏感命名文件；Codex 本地状态和数据库整体也应按敏感资产处理。
- `/Users/kevin/.lark-cli/config.json`：配置文件存在，按敏感认证状态处理。
- 战略目录中存在飞书认证二维码图片；只确认文件存在，未打开。
- Lamma 项目中存在 `.env.example` 类配置示例；未读取。

## 7. 最值得复用的 5 项资产

1. **`量化炒股` 的研究、风控、报告和测试框架**：模块边界最完整，拥有真实历史运行痕迹。
2. **Codex 的 `ibkr-readonly-status-report` 技能**：风险低、目标清晰，适合作为 Project X 第一条端到端验收链路。
3. **完整的 Lark 技能套件与已安装的 `lark-cli`**：覆盖协作、文档、表格、任务和消息，可作为工作节点的人机协同层。
4. **EnergyMo 增长工作流、CRM/经营模板和战略模型**：可直接转化为标准任务、输入模板和验收标准。
5. **OpenClaw 历史金融技能与运行经验**：交易风险清单、量化决策、证券研究、多源新闻等知识资产可迁移，但运行时本身应归档。

## 8. 明显风险

- **调度冲突风险**：launchd 与 Codex 自动化同时存在，若未来重复接管可能造成同一任务多次执行。
- **交易权限风险**：主量化项目含确认执行、人工执行、纸面交易、Broker 接口和历史订单日志；TWS/IB Gateway 也已安装。
- **潜在自动唤醒风险**：量化 LaunchAgent 已加载，即使检查时没有进程，仍可能在触发条件满足时运行。
- **活跃自动化风险**：有一个 Codex 研究自动化仍处于 ACTIVE；其外部访问、写入位置和失败行为尚未专项审计。
- **秘密扩散风险**：OpenClaw 主目录、备份、Codex 状态、Lark 配置和量化 `.env` 分散保存，可能存在重复或过期凭据。
- **OpenClaw 双控制面风险**：二进制和 LaunchAgent 文件仍存在；误启动会与 Codex 形成并行调度与状态冲突。
- **版本与可复现性风险**：默认 Python 3.14 与既有 venv 3.13 不同；核心量化项目没有发现独立 Git 仓库或锁定依赖文件。
- **路径污染风险**：量化项目中存在字面名称为 `$CODEX_HOME` 的目录，可能来自旧自动化的变量展开错误。
- **数据治理风险**：交易日志、账户状态、CRM、医疗测试、合同和认证材料混放在用户目录，敏感等级与保留策略未定义。
- **资产重复风险**：EnergyMo 和 OpenClaw 文件存在多个日期副本、输出版本和备份，当前缺少权威来源标记。

## 9. 建议处置顺序

1. 在任何执行能力接入前，先专项审计已加载的量化 LaunchAgent和仍为 ACTIVE 的 Codex 自动化。
2. 选择 `ibkr-readonly-status-report` 作为 Project X 第一个端到端任务，只允许读取本地状态并生成脱敏报告。
3. 把 `量化炒股` 纳入独立版本管理，但第一批只迁移研究、风控、报告和测试；执行模块保持隔离。
4. 建立统一的 secrets 引用规范，禁止复制 OpenClaw、Lark、Codex 或 `.env` 中的秘密到 Project X 仓库。
5. 为 EnergyMo 与 CRM 模板建立资产索引、字段字典、来源和验收标准，然后再考虑接入飞书。
6. 对 OpenClaw 做离线清单、校验和与去重，迁移知识资产后整体归档，保持不启动。

