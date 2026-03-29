# cliany-site v0.2 ~ v0.5 迭代计划

**制定日期：** 2026-03-29  
**基线版本：** v0.1.1  
**关联决策：** [ADR-001](decisions/001-v02-iteration-plan.md)  
**关联分析：** [头脑风暴](brainstorm-iteration-directions.md)

---

## Phase 1 — 稳固地基 (v0.2.0)

> 目标：让项目可调试、可测试、可配置，为后续迭代打下坚实基础。

### 1.1 异常治理

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 1.1.1 | 定义异常层级体系 | `errors.py` | 新增 `CdpError`, `ActionError`, `CodegenError` 等异常基类，继承自 `ClanySiteError` |
| 1.1.2 | 修复 `cdp.py` 裸 except | `browser/cdp.py` L30,54,62,69 | 替换为 `ConnectionRefusedError`, `TimeoutError`, `aiohttp.ClientError` 等具体类型；关键失败写日志 |
| 1.1.3 | 修复 `action_runtime.py` 裸 except | `action_runtime.py` L562,614 | 替换为具体异常类型；执行失败时保留上下文信息供调试 |
| 1.1.4 | 全局异常审查 | 所有 `*.py` | `grep -r "except Exception"` 结果为零（除 `SafeGroup` 顶层兜底外） |

### 1.2 结构化日志

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 1.2.1 | 引入日志模块 | 新增 `logging_config.py` | 基于标准库 `logging` + JSON formatter；支持 `--verbose` 和 `--debug` 全局选项 |
| 1.2.2 | CLI 集成日志开关 | `cli.py` | 根 group 添加 `--verbose`/`--debug` 选项，控制日志级别 |
| 1.2.3 | 关键路径埋点 | `engine.py`, `action_runtime.py`, `generator.py` | explore/execute/codegen 流程的入口、出口、异常点均有日志；含耗时信息 |
| 1.2.4 | 敏感信息脱敏 | `logging_config.py` | 日志中自动过滤 cookie value、api key、password 等字段 |

### 1.3 统一配置中心

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 1.3.1 | 创建配置 dataclass | 新增 `config.py` | `@dataclass ClanySiteConfig`：cdp_port、action_timeout、retry_count、resolve_retry_delay 等 |
| 1.3.2 | 环境变量绑定 | `config.py` | 支持 `CLIANY_CDP_PORT`、`CLIANY_ACTION_TIMEOUT`、`CLIANY_RETRY_COUNT` 等环境变量覆盖默认值 |
| 1.3.3 | 消除硬编码 | `cdp.py`, `action_runtime.py` | 所有 `9222`、`1.5`、`2.0`、`2.5`、`1.0`、`2` 等魔术数字替换为配置引用 |
| 1.3.4 | doctor 输出配置信息 | `commands/doctor.py` | `doctor --json` 输出中包含当前生效的配置值 |

### 1.4 pytest 单元测试

| # | 任务 | 文件 | 验收标准 |
|---|------|------|----------|
| 1.4.1 | 测试基础设施 | `pyproject.toml`, 新增 `tests/` | 添加 pytest + pytest-asyncio 依赖；`tests/conftest.py` 提供公共 fixture |
| 1.4.2 | axtree 解析测试 | `tests/test_axtree.py` | 覆盖 AXTree 序列化、截断、selector map 生成；>=5 个 case |
| 1.4.3 | action_runtime 测试 | `tests/test_action_runtime.py` | 覆盖元素模糊匹配、分数计算、动作分发逻辑；Mock CDP 连接 |
| 1.4.4 | codegen 模板测试 | `tests/test_codegen.py` | 覆盖 Click 命令生成、参数推导、metadata 输出；验证生成代码语法正确 |
| 1.4.5 | merger 合并测试 | `tests/test_merger.py` | 覆盖新增/冲突/删除场景；验证合并后 adapter 可加载 |
| 1.4.6 | config 配置测试 | `tests/test_config.py` | 覆盖默认值、环境变量覆盖、无效值处理 |

**Phase 1 交付标准：**
- `pytest` 全部通过，核心模块覆盖率 > 60%
- `grep -r "except Exception" src/` 仅保留 `SafeGroup` 一处
- `cliany-site doctor --json` 输出含配置信息和日志级别

---

## Phase 2 — 体验升级 (v0.3.0)

> 目标：让用户操作有反馈、有信心、有保障。

### 2.1 执行进度反馈

| # | 任务 | 验收标准 |
|---|------|----------|
| 2.1.1 | explore 实时进度 | 探索过程中终端显示当前步骤编号、动作描述、耗时（rich Status/Spinner） |
| 2.1.2 | execute 步骤进度条 | 执行过程中显示 rich 进度条 + 每步状态标记 (✓/▶/✗) |
| 2.1.3 | JSON 流式事件 | `--json` 模式下输出 NDJSON 流式事件：`{"event":"step_start","index":3,...}` |

### 2.2 智能自愈增强

| # | 任务 | 验收标准 |
|---|------|----------|
| 2.2.1 | AXTree 快照存储 | explore 时保存每步的 AXTree 快照到 adapter 目录 |
| 2.2.2 | 执行前预检 | execute 前对比当前 AXTree 与快照，超过阈值(30%)差异时警告用户 |
| 2.2.3 | selector 热修复 | 预检发现差异时自动尝试更新 selector map，无需重新 explore |
| 2.2.4 | 适配器健康检查命令 | 新增 `cliany-site check <domain>` 命令，报告适配器各命令的可用性 |

### 2.3 错误恢复 UX

| # | 任务 | 验收标准 |
|---|------|----------|
| 2.3.1 | 断点续执行 | execute 失败时记录断点（已完成步骤索引），支持 `--resume` 从断点恢复 |
| 2.3.2 | dry-run 模式 | 新增 `--dry-run` 选项，仅验证 selector 是否存在，不实际执行操作 |
| 2.3.3 | 执行回放日志 | 每次 execute 记录完整执行日志（步骤、耗时、页面 URL），存入 `~/.cliany-site/logs/` |

### 2.4 CI/CD 流水线

| # | 任务 | 验收标准 |
|---|------|----------|
| 2.4.1 | GitHub Actions PR 检查 | PR 触发：ruff lint → mypy → pytest → 状态通过才可合并 |
| 2.4.2 | 发版自动化 | tag push 触发：build wheel → publish to PyPI |
| 2.4.3 | 类型标注补全 | mypy strict 模式下 `src/cliany_site/` 零 error |

**Phase 2 交付标准：**
- explore/execute 过程有实时进度反馈
- 支持 `--dry-run` 和 `--resume` 选项
- GitHub PR 自动跑 lint + test + type check

---

## Phase 3 — 场景拓展 (v0.4.0)

> 目标：突破本地 Chrome 限制，支持更复杂的自动化场景。

### 3.1 Headless & 远程浏览器

| # | 任务 | 验收标准 |
|---|------|----------|
| 3.1.1 | 远程 CDP 支持 | 所有命令支持 `--cdp-url ws://host:port` 参数，替代本地 localhost |
| 3.1.2 | Headless Chrome 模式 | launcher 支持 `--headless` 启动无 GUI Chrome |
| 3.1.3 | Docker 镜像 | 提供 `Dockerfile`：cliany-site + headless Chrome 一体化，可直接 `docker run` |

### 3.2 工作流编排

| # | 任务 | 验收标准 |
|---|------|----------|
| 3.2.1 | 工作流 YAML 定义 | 支持 YAML 文件声明多步骤工作流，含 adapter/command/params 配置 |
| 3.2.2 | 步骤间数据传递 | 上一步 output 中的字段可通过 `$prev.data.field` 语法传递给下一步 |
| 3.2.3 | 条件与重试策略 | 支持 `when` 条件判断和 `retry` 重试配置 |
| 3.2.4 | workflow 命令 | 新增 `cliany-site workflow run <file.yaml> --json` 命令 |

### 3.3 数据驱动批量执行

| # | 任务 | 验收标准 |
|---|------|----------|
| 3.3.1 | 批量参数输入 | 支持 `--batch <file.csv>` 从 CSV/JSON 文件读取参数列表 |
| 3.3.2 | 并发控制 | 支持 `--concurrency N` 控制并行度 |
| 3.3.3 | 汇总报告 | 批量执行完成后输出汇总报告（成功/失败/跳过计数 + 失败明细） |

### 3.4 generator.py 拆分重构

| # | 任务 | 验收标准 |
|---|------|----------|
| 3.4.1 | 提取模板渲染层 | 新建 `codegen/templates.py`，Click 代码模板用 Jinja2 管理 |
| 3.4.2 | 提取参数推导层 | 新建 `codegen/params.py`，参数类型推导和默认值逻辑独立 |
| 3.4.3 | 提取去重逻辑 | 新建 `codegen/dedup.py`，命令去重和冲突检测逻辑独立 |
| 3.4.4 | generator.py 瘦身 | `generator.py` 行数 < 300，仅作为协调层调用上述模块 |

**Phase 3 交付标准：**
- 可通过 Docker 在无 GUI 服务器上完成 explore + execute 全流程
- YAML 工作流可编排多个 adapter 命令串行/并行执行
- generator.py 拆分后所有现有 qa/ 测试仍通过

---

## Phase 4 — 生态建设 (v0.5.0)

> 目标：从个人工具走向可协作、可集成的平台。

### 4.1 适配器市场

| # | 任务 | 验收标准 |
|---|------|----------|
| 4.1.1 | 适配器打包格式 | 定义 adapter 分发格式（tarball + manifest.json），含版本、依赖、签名 |
| 4.1.2 | publish 命令 | `cliany-site publish <domain>` 打包并上传适配器到 registry |
| 4.1.3 | install 命令 | `cliany-site install <domain>` 从 registry 下载并安装适配器 |
| 4.1.4 | 版本管理 | 支持 adapter 版本号、升级、回滚 |

### 4.2 Python SDK

| # | 任务 | 验收标准 |
|---|------|----------|
| 4.2.1 | 核心 API 封装 | `from cliany_site import explore, execute` 程序化调用，返回结构化结果 |
| 4.2.2 | 异步上下文管理 | `async with ClanySite() as cs: result = await cs.execute(...)` |
| 4.2.3 | HTTP API 模式 | 可选 `cliany-site serve --port 8080` 启动 REST API 服务 |

### 4.3 安全加固

| # | 任务 | 验收标准 |
|---|------|----------|
| 4.3.1 | Session 加密存储 | cookies 文件使用 Fernet 对称加密，密钥存系统 Keychain |
| 4.3.2 | 动作沙箱模式 | `--sandbox` 执行时限制 navigate 同域、禁止文件下载 |
| 4.3.3 | 生成代码审计 | codegen 输出自动做 AST 静态分析，检测危险模式（eval/exec/os.system） |

### 4.4 iframe / Shadow DOM

| # | 任务 | 验收标准 |
|---|------|----------|
| 4.4.1 | iframe 递归 AXTree 采集 | 自动检测 iframe 并递归采集内部 AXTree，标注 frameId |
| 4.4.2 | Shadow DOM 穿透 | 支持通过 CDP 穿透 Shadow DOM 定位元素 |

**Phase 4 交付标准：**
- 适配器可发布到 registry、可被其他用户安装
- Python SDK 可编程调用，不依赖 CLI
- Session 加密存储，sandbox 模式可限制危险操作

---

## 里程碑时间线（建议）

```
v0.1.1 (当前) ──→ Phase 1 (v0.2.0) ──→ Phase 2 (v0.3.0) ──→ Phase 3 (v0.4.0) ──→ Phase 4 (v0.5.0)
  2026-03         ~2 周                ~3 周                ~3 周                ~4 周
                 异常/日志/配置/测试   进度/自愈/CI        headless/编排/重构   市场/SDK/安全
```

## 依赖关系

```
Phase 1 (地基)
  ├── 1.1 异常治理 ← 无依赖，可立即开始
  ├── 1.2 日志系统 ← 依赖 1.1（异常类型确定后埋点）
  ├── 1.3 配置中心 ← 无依赖，可与 1.1 并行
  └── 1.4 pytest   ← 依赖 1.1 + 1.3（需要 Mock 新异常和配置）

Phase 2 (体验)
  ├── 2.1 进度反馈 ← 依赖 1.2（日志基础设施）
  ├── 2.2 智能自愈 ← 依赖 1.3（配置化阈值）
  ├── 2.3 错误恢复 ← 依赖 1.1 + 1.2
  └── 2.4 CI/CD   ← 依赖 1.4（有测试才能跑 CI）

Phase 3 (拓展)
  ├── 3.1 headless ← 依赖 1.3（CDP URL 配置化）
  ├── 3.2 工作流   ← 依赖 2.1（需要流式事件）
  ├── 3.3 批量执行 ← 依赖 3.2（复用编排引擎）
  └── 3.4 拆分重构 ← 依赖 1.4（需要测试保障回归）

Phase 4 (生态)
  ├── 4.1 适配器市场 ← 依赖 3.4（adapter 格式稳定）
  ├── 4.2 SDK      ← 依赖 Phase 1~3 全部稳定
  ├── 4.3 安全加固  ← 无强依赖，可提前
  └── 4.4 iframe   ← 依赖 3.1（headless 测试环境）
```

## 度量指标

| 指标 | v0.1.1 现状 | v0.2.0 目标 | v0.5.0 目标 |
|------|------------|------------|------------|
| 单元测试数量 | 0 | ≥30 | ≥100 |
| 核心模块覆盖率 | 0% | ≥60% | ≥80% |
| 裸 except 数量 | 6+ | 1 (SafeGroup) | 1 |
| CI 自动化 | 无 | pytest 本地 | 全流程 GitHub Actions |
| 最大单文件行数 | 1223 | 1223 | <400 |
| 支持的运行环境 | 本地 macOS | 本地 macOS | macOS + Linux + Docker |
