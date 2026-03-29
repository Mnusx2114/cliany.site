# cliany-site 迭代优化方向 — 头脑风暴

**日期：** 2026-03-29  
**基线版本：** v0.1.1 (commit ee9bbf6)  
**分析范围：** 架构、代码质量、功能完备度、用户体验、安全性、可观测性、测试、生态

---

## 一、工程质量与技术债

### 1.1 消除裸 except — 高优先级

**现状：** `browser/cdp.py` (L30-31, L54-55, L62-63, L69-70) 和 `action_runtime.py` (L562-563, L614-617) 存在多处 `except Exception` 静默吞异常，导致 CDP 连接失败、动作执行失败时用户无任何反馈。

**方向：**
- 替换为具体异常类型 (`ConnectionRefusedError`, `TimeoutError`, `websockets.exceptions.WebSocketException` 等)
- 关键路径失败时写入结构化日志 + 返回可操作的错误提示
- 引入自定义异常层级体系，统一异常传播链

### 1.2 结构化日志系统 — 高优先级

**现状：** 输出依赖 `print()` 和 `rich.console`，无统一日志框架，无法按级别过滤、无法导出到外部系统。

**方向：**
- 引入 `structlog` 或标准库 `logging` + JSON formatter
- 分离用户交互输出（stdout/rich）与系统日志（stderr/file）
- 为 explore、execute、codegen 等关键路径添加 span/trace 上下文
- 支持 `--verbose` / `--debug` 全局开关

### 1.3 拆分超大文件 — 中优先级

**现状：** `codegen/generator.py` 达 1223 行，模板渲染、参数处理、去重逻辑、代码生成全部混在一起。

**方向：**
- 拆分为 `template_renderer.py`（Click 代码模板）、`param_resolver.py`（参数推导）、`dedup.py`（命令去重）
- 提取 Jinja2 模板替代字符串拼接，提升可读性和可测试性

### 1.4 硬编码值外置 — 中优先级

**现状：**
- CDP 端口 `9222` 硬编码在 `cdp.py`
- `action_runtime.py` 散落多个超时常量 (1.0s, 1.5s, 2.0s, 2.5s)
- 重试次数硬编码为 2

**方向：**
- 收敛到统一的 `config.py` 或 dataclass 配置对象
- 支持环境变量 / .env 覆盖：`CLIANY_CDP_PORT`, `CLIANY_ACTION_TIMEOUT`, `CLIANY_RETRY_COUNT`
- 为不同网络环境提供 preset profile（fast/normal/slow）

---

## 二、测试与质量保障

### 2.1 引入 pytest 单元测试 — 高优先级

**现状：** 仅有 `qa/` 下 23 个 shell 集成脚本，无单元测试，无法验证单个模块逻辑。

**方向：**
- 为核心模块建立 pytest 套件：`axtree` 解析、`action_runtime` 元素匹配、`codegen` 模板渲染、`merger` 合并逻辑
- 使用 `pytest-asyncio` 覆盖异步代码路径
- Mock CDP 连接和 LLM 响应，实现离线可测
- 目标：核心模块行覆盖率 > 80%

### 2.2 CI/CD 流水线 — 高优先级

**现状：** 无自动化 CI，测试和发布全靠手动。

**方向：**
- GitHub Actions：lint (ruff) → type check (mypy/pyright) → unit test → integration test
- 发版自动化：tag push → build wheel → publish to PyPI/SkillsMP
- PR 卡控：测试不过不允许合并

### 2.3 类型标注补全 — 中优先级

**现状：** 核心模块有类型标注，但参数/返回值覆盖不完整。

**方向：**
- 启用 `mypy --strict` 或 `pyright` 逐模块推进
- 为复杂嵌套结构提取 `TypedDict` / `NamedTuple`
- 在 CI 中添加类型检查关卡

---

## 三、功能增强

### 3.1 多浏览器 & 无头模式支持 — 高价值

**现状：** 仅支持本地 Chrome + `localhost:9222`，无法在服务器/容器环境运行。

**方向：**
- 支持远程 CDP 地址 (`--cdp-url ws://remote:9222`)
- 集成 headless Chrome / Playwright 后端，支持无 GUI 环境
- Docker 镜像：`cliany-site` + headless Chrome 一体化部署
- 为 CI/CD 场景提供批处理模式

### 3.2 工作流编排 — 高价值

**现状：** 每个命令独立执行，无法串联多步骤工作流。

**方向：**
- 支持 YAML/JSON 工作流定义文件，声明式编排多个 adapter 命令
- 步骤间数据传递：上一步 output → 下一步 input（管道模式）
- 条件分支、循环、错误重试策略
- 示例：`登录 GitHub → 搜索仓库 → 获取 Star 数 → 写入本地文件`

### 3.3 iframe / Shadow DOM 支持 — 中价值

**现状：** README 明确标注"不支持 iframe 内元素的自动操作"。

**方向：**
- 递归采集 iframe 内 AXTree 并标注来源 frame
- Shadow DOM 穿透选择器
- 提升对现代 SPA 框架（React Portal、Web Components）的兼容性

### 3.4 智能自愈与适配 — 高价值

**现状：** 已有模糊匹配和 LLM 自适应修复能力，但仅在执行失败时被动触发。

**方向：**
- 执行前预检：对比当前页面 AXTree 与录制时的快照，主动检测 UI 变更
- 变更热修复：自动更新 selector 而无需重新 explore
- 适配器健康度评分：定期检测已生成命令是否仍然可用
- 变更通知：UI 结构变化超过阈值时推送告警

### 3.5 参数化与数据驱动 — 中价值

**现状：** 已支持 `{{param}}` 参数化，但无批量执行和数据驱动能力。

**方向：**
- 支持从 CSV/JSON 文件批量灌入参数，循环执行
- 并发执行多组参数（线程池 / asyncio.gather）
- 执行结果汇总报告（成功/失败/跳过）

---

## 四、用户体验

### 4.1 执行进度与反馈 — 高优先级

**现状：** explore 和 execute 过程中用户看不到中间进度，长时间等待无反馈。

**方向：**
- 探索阶段：实时显示当前步骤（"正在分析页面结构..."、"第 3/7 步：点击搜索按钮..."）
- 执行阶段：rich 进度条 + 步骤状态（✓ 已完成 / ▶ 进行中 / ✗ 失败）
- `--json` 模式下输出 NDJSON 流式事件

### 4.2 交互式探索模式 — 高价值

**现状：** explore 是全自动的，用户只能事后看结果。

**方向：**
- `--interactive` 模式：LLM 每规划一步后暂停，用户确认/修改/跳过
- 实时页面截图预览（终端内 Sixel/Kitty 图片协议 或 本地 HTML 预览）
- 支持用户中途插入自定义动作

### 4.3 错误恢复 UX — 中优先级

**现状：** 执行失败后需要从头重来。

**方向：**
- 断点续执行：从失败步骤恢复
- 执行回放日志：记录每步的页面状态，失败时可回溯
- `--dry-run` 模式：仅验证 selector 是否存在，不实际执行

### 4.4 TUI 增强 — 低优先级

**现状：** TUI 已具备基本管理功能。

**方向：**
- 实时 explore 可视化（步骤树 + 页面缩略图）
- 适配器在线编辑 / 参数调整
- 执行历史统计面板

---

## 五、安全与可靠性

### 5.1 凭证安全 — 高优先级

**现状：** Session cookies 以明文存储在 `~/.cliany-site/sessions/`。

**方向：**
- 支持系统 Keychain / Secret Manager 集成（macOS Keychain, Linux libsecret）
- Session 文件加密存储，启动时解密
- 敏感信息脱敏日志（自动过滤 cookie value、token、password）

### 5.2 输入验证与沙箱 — 中优先级

**现状：** LLM 返回的动作直接执行，无安全边界检查。

**方向：**
- 动作白名单：限制 navigate 只能访问同域 URL
- 生成代码审计：对 codegen 输出做静态分析，检测危险模式
- 可选沙箱模式：在隔离 Chrome profile 中执行

---

## 六、生态与分发

### 6.1 适配器市场 — 高价值

**现状：** 适配器仅本地存储和使用。

**方向：**
- 适配器 registry：用户可发布/安装他人创建的适配器
- `cliany-site install github.com/search` 一键安装
- 版本管理：适配器可升级/回滚
- 社区贡献：热门网站的 adapter 预制

### 6.2 SDK / API 模式 — 中价值

**现状：** 仅 CLI 调用方式。

**方向：**
- Python SDK：`from cliany_site import execute; result = await execute("github.com", "search", query="test")`
- HTTP API 模式：起一个本地 FastAPI 服务，REST 调用
- 便于集成到其他自动化工具（Airflow、n8n、Zapier）

### 6.3 多语言 CLI 输出 — 低优先级

**现状：** 用户交互文案全中文。

**方向：**
- i18n 支持：根据 `LANG` 环境变量切换语言
- 至少支持中/英双语
- 生成的 adapter help text 保持原始语言

---

## 七、性能优化

### 7.1 AXTree 采集优化 — 中优先级

**现状：** 完整采集页面 AXTree 可能很大，对 LLM token 消耗高。

**方向：**
- 智能裁剪：只采集视口内 + 交互元素的子树
- 增量采集：页面变化时只传递 diff
- 缓存：同一页面短时间内复用 AXTree 快照

### 7.2 LLM 调用优化 — 中优先级

**现状：** 每步探索都完整调用 LLM。

**方向：**
- 流式响应：explore 过程中边生成边执行
- 本地小模型 fallback：简单动作（点击已知按钮）无需调用远程 LLM
- 上下文压缩：历史步骤摘要化，减少 token 消耗
- 多模型策略：规划用大模型，执行确认用小模型

### 7.3 并行执行 — 低优先级

**现状：** 所有动作串行执行。

**方向：**
- 独立动作并行化（如同时填充多个表单字段）
- 多 tab 并行探索

---

## 优先级总览

| 优先级 | 方向 | 预期收益 |
|--------|------|----------|
| **P0 紧急** | 裸 except 修复、结构化日志、pytest 套件 | 可调试性和稳定性质变 |
| **P1 重要** | CI/CD、执行进度反馈、凭证安全、智能自愈 | 用户信任度 + 工程效率 |
| **P2 增值** | 工作流编排、交互式探索、适配器市场、headless 模式 | 使用场景大幅拓展 |
| **P3 远期** | SDK/API、多语言、并行执行、TUI 增强 | 生态建设与极致体验 |

---

> 建议先从 **P0（工程基础）** 入手稳固地基，再推进 **P1（核心体验）** 提升用户价值，最后用 **P2/P3** 打开增长空间。
