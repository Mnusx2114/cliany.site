# v0.5.0 端到端测试 + GitHub/官网更新计划

**日期：** 2026-03-30  
**版本：** v0.5.0（从 v0.1.1 升级）  
**关联计划：** [迭代计划](iteration-plan-v02-v05.md)

---

## 一、现状摸底

### 1.1 版本跨度

从 v0.1.1 到 v0.5.0，经历 4 个 Phase，112 个文件变更，25,314 行新增代码。

| 维度 | v0.1.1 | v0.5.0 |
|------|--------|--------|
| 源码模块数 | ~15 | 64 |
| pytest 用例数 | 0 | 583 (全部通过) |
| qa/ 集成脚本 | ~5 | 23 |
| ruff lint | - | 0 error |
| mypy typecheck | - | 0 error |
| CI/CD | 无 | GitHub Actions (lint + mypy + pytest) |

### 1.2 新增功能清单

| Phase | 版本 | 新增功能 |
|-------|------|----------|
| 1 | v0.2.0 | 异常层级体系、结构化日志、统一配置中心、pytest 单元测试 |
| 2 | v0.3.0 | 进度反馈、智能自愈(AXTree 快照)、断点续执行、CI/CD 流水线 |
| 3 | v0.4.0 | Headless/远程 CDP、YAML 工作流编排、数据驱动批量执行、generator 重构 |
| 4 | v0.5.0 | 适配器市场、Python SDK + HTTP API、安全加固(加密/沙箱/审计)、iframe/Shadow DOM |

### 1.3 现有测试覆盖分析

**已覆盖（pytest 583 用例）：**
- 单元级：config、axtree、action_runtime、codegen、engine、progress、checkpoint、snapshot、healthcheck、security、marketplace、sdk、workflow、batch、remote_cdp、report
- 冒烟测试：test_smoke.py（极简）

**已覆盖（qa/ 23 个 shell 脚本）：**
- 命令级：doctor、explore、login、list、tui
- 功能级：adapter merge、atom 系统、action 分区、浏览器自动启动

**未覆盖或覆盖不足的关键路径：**
1. **端到端全链路**：explore → 生成 adapter → list 查看 → 执行命令 → JSON 输出验证（需要真实 Chrome + LLM）
2. **新命令 CLI 冒烟**：`market`、`serve`、`workflow`、`check`、`report` 命令的 `--help` 和基本参数校验
3. **跨功能集成**：sandbox 模式下 explore → execute、加密 session + adapter 执行
4. **SDK 端到端**：Python SDK 的 `async with ClanySite()` 完整流程
5. **HTTP API 端到端**：`serve` 启动 → REST 调用 → 响应验证
6. **工作流端到端**：YAML 文件 → `workflow run` → 步骤串行 → 汇总报告
7. **错误降级路径**：无 Chrome 时 doctor 报错、无 API key 时 explore 报错、无效 adapter 时 list 报错

### 1.4 发现的问题

| # | 问题 | 严重级别 | 说明 |
|---|------|---------|------|
| 1 | errors.py 缺少 `ActionError` | 低 | 迭代计划中提到但实际未定义，不影响运行（代码中未直接使用） |
| 2 | checkpoint.py 缺少 `CheckpointManager` 导出名 | 低 | 可能类名不同，需确认实际导出 |
| 3 | 官网未反映 v0.2~v0.5 新功能 | 高 | 官网仍只展示 v0.1.1 的 10 个基础特性 |
| 4 | README 未列出新命令 | 中 | `market`、`serve`、`workflow`、`check`、`report` 未在命令参考表中 |
| 5 | README.en.md 严重过时 | 高 | 英文版仍停留在早期阶段 |

---

## 二、端到端测试计划

### 2.1 测试策略分层

```
┌─────────────────────────────────────────────┐
│  L4: 真实端到端 (需 Chrome + LLM)           │  ← 手动 / 少量自动化
│  explore → adapter 生成 → 命令执行 → 验证    │
├─────────────────────────────────────────────┤
│  L3: CLI 集成测试 (无外部依赖)               │  ← 新增重点
│  每个命令的 --help / 无参调用 / 错误参数      │
├─────────────────────────────────────────────┤
│  L2: 模块集成测试 (Mock 外部)                │  ← 现有 tests/ 已覆盖
│  config+logging / sdk+server / workflow+batch│
├─────────────────────────────────────────────┤
│  L1: 单元测试                                │  ← 现有 583 用例
│  纯逻辑函数、数据模型、工具类                  │
└─────────────────────────────────────────────┘
```

### 2.2 L3 — CLI 集成测试（新增，无需外部依赖）

**目标：** 确保所有 CLI 命令可正常启动、帮助文本正确、错误参数优雅降级。

| # | 测试场景 | 验证方式 | 预期结果 |
|---|---------|---------|---------|
| 3.1 | `cliany-site --version` | exit 0, 输出含 "0.5.0" | 版本号正确 |
| 3.2 | `cliany-site --help` | exit 0, 输出含所有 12+ 命令 | 命令列表完整 |
| 3.3 | `cliany-site doctor --help` | exit 0 | 帮助正常 |
| 3.4 | `cliany-site explore --help` | exit 0 | 帮助正常 |
| 3.5 | `cliany-site login --help` | exit 0 | 帮助正常 |
| 3.6 | `cliany-site list --json` | exit 0, 有效 JSON | 空列表或已有 adapter |
| 3.7 | `cliany-site market --help` | exit 0, 含 install/uninstall/pack | 子命令完整 |
| 3.8 | `cliany-site workflow --help` | exit 0, 含 run | 子命令完整 |
| 3.9 | `cliany-site serve --help` | exit 0 | 帮助正常 |
| 3.10 | `cliany-site check --help` | exit 0 | 帮助正常 |
| 3.11 | `cliany-site report --help` | exit 0 | 帮助正常 |
| 3.12 | `cliany-site tui --help` | exit 0 | 帮助正常 |
| 3.13 | `cliany-site 不存在的命令` | exit ≠ 0, 错误提示 | 优雅报错 |
| 3.14 | `cliany-site explore` (缺参数) | exit ≠ 0, 提示缺少 URL | 参数校验 |
| 3.15 | `cliany-site --json doctor` (无 Chrome) | exit 1, JSON 含 error | 结构化错误 |
| 3.16 | 全局选项传递 `--verbose`/`--debug`/`--sandbox` | 不崩溃 | 选项正常解析 |

**实现方式：** 新增 `tests/test_cli_integration.py`，使用 Click 的 `CliRunner` 测试。

### 2.3 L3 — 模块间集成测试（新增）

| # | 测试场景 | 涉及模块 | 验证重点 |
|---|---------|---------|---------|
| 3.20 | SDK 同步接口调用 | sdk.py + config.py | `doctor()` 返回结构化结果 |
| 3.21 | HTTP API 启动 + 路由注册 | server.py + sdk.py | 所有路由可达、返回正确 Content-Type |
| 3.22 | YAML 工作流解析 + 执行引擎 | workflow/parser.py + engine.py | 解析有效 YAML → 生成 Step 列表 |
| 3.23 | 批量执行 CSV 解析 | workflow/batch.py | 读取 CSV → 生成参数列表 |
| 3.24 | 适配器打包 + 解包 | marketplace.py | pack → tarball → install → 文件完整 |
| 3.25 | Session 加密 + 解密往返 | security.py + session.py | 加密后解密数据一致 |
| 3.26 | 代码审计检测危险模式 | audit.py | 含 eval/exec 的代码被标记 |
| 3.27 | 沙箱策略判定 | sandbox.py | 跨域 navigate 被拦截 |
| 3.28 | AXTree iframe 标注 | browser/axtree.py | iframe 节点含 frameId 标注 |

### 2.4 L4 — 真实端到端测试（手动执行，可选自动化）

> 需要真实 Chrome (CDP:9222) + 有效的 LLM API key。

| # | 场景 | 步骤 | 验收标准 |
|---|------|------|---------|
| 4.1 | **核心流程：探索到执行** | 1. `doctor --json` 确认环境<br>2. `explore "https://example.com" "查看页面标题" --json`<br>3. `list --json` 确认 adapter<br>4. 执行生成的命令 `--json` | 每步 exit 0 + 有效 JSON |
| 4.2 | **登录 + Session 持久化** | 1. `login "https://github.com"`<br>2. 手动登录<br>3. 确认 `~/.cliany-site/sessions/` 有文件<br>4. 后续 explore 复用 session | Session 持久化有效 |
| 4.3 | **适配器增量合并** | 1. 第一次 explore 生成 adapter<br>2. 第二次 explore 同域不同工作流<br>3. 验证两个命令都存在 | 合并不丢失已有命令 |
| 4.4 | **Headless 模式** | `--headless explore "https://example.com" "获取标题"` | 无 GUI 下正常完成 |
| 4.5 | **远程 CDP** | `--cdp-url ws://localhost:9222 doctor --json` | 远程连接成功 |
| 4.6 | **TUI 启动** | `tui` 启动后显示 adapter 列表 | 界面正常渲染、可退出 |
| 4.7 | **HTTP API** | 1. `serve --port 8080`<br>2. `curl localhost:8080/api/doctor`<br>3. `curl localhost:8080/api/adapters` | REST 响应正确 |
| 4.8 | **YAML 工作流** | 编写 2 步工作流 YAML → `workflow run xxx.yaml --json` | 按序执行、输出报告 |
| 4.9 | **批量执行** | 准备 CSV → `--batch data.csv --concurrency 2` | 并发执行、汇总报告 |
| 4.10 | **适配器市场** | 1. `market pack github.com`<br>2. `market install ./github.com.tar.gz`<br>3. 验证安装后可用 | 打包/安装/可用 |

### 2.5 回归测试检查清单

在所有新测试之外，确保原有功能不受影响：

- [ ] `pytest tests/ -v` — 583 用例全部通过
- [ ] `ruff check src/` — 0 error
- [ ] `mypy src/cliany_site/` — 0 error
- [ ] `cliany-site --version` — 输出 0.5.0
- [ ] `cliany-site doctor --json` — 环境检查通过
- [ ] `cliany-site list --json` — 输出有效 JSON
- [ ] 已有 qa/ 脚本运行通过（需 Chrome 环境）

---

## 三、GitHub README 更新计划

### 3.1 需要更新的内容

| 区域 | 当前状态 | 更新内容 |
|------|---------|---------|
| **版本徽章** | 无 | 添加 PyPI version、Python version、CI status 徽章 |
| **特性列表** | 10 项（v0.1.1 水平） | 扩展到 20+ 项，涵盖 Phase 1-4 所有新功能 |
| **命令参考表** | 6 个命令 | 扩展到 10+ 命令（新增 market/serve/workflow/check/report） |
| **快速开始** | 基础安装 | 补充 pip install from PyPI、Docker 运行方式 |
| **架构图** | 基础目录树 | 更新为完整的模块结构图 |
| **使用示例** | 6 个基础示例 | 新增 SDK 用法、工作流编排、批量执行、HTTP API 示例 |
| **限制说明** | 基础限制 | 更新为当前实际限制（Headless 已支持等） |
| **贡献指南** | 无 | 新增基本贡献流程（clone → install → test → PR） |
| **Changelog** | 无 | 新增 v0.2.0 ~ v0.5.0 变更摘要或链接到 releases |

### 3.2 新增 README 章节结构

```markdown
# cliany-site

[徽章行：PyPI | Python | CI | License]

> 将任意网页操作自动化为可调用的 CLI 命令

## 特性亮点（分类展示）
### 核心能力
### 开发体验
### 企业级特性
### 生态集成

## 快速开始
### 方式一：pip 安装
### 方式二：源码安装
### 方式三：Docker（新增）

## 配置
### LLM Provider
### Chrome CDP
### 环境变量完整列表（新增）

## 使用示例
### 基础流程（原有）
### Python SDK（新增）
### HTTP API（新增）
### YAML 工作流编排（新增）
### 批量执行（新增）
### 适配器市场（新增）

## 命令参考（完整表格）

## 架构概览（更新）

## 安全特性（新增）

## 贡献指南（新增）

## Changelog（新增）

## 限制说明（更新）
```

### 3.3 README.en.md 同步

英文 README 需要与中文版同步更新，确保内容一致。建议采用中文先行、英文同步翻译的流程。

---

## 四、官网 (cliany.site) 更新计划

### 4.1 当前官网分析

- **位置：** `site/index.html` + `site/style.css` + `site/script.js`
- **托管：** Vercel（`site/vercel.json`）
- **语言：** 中英双语切换
- **内容：** 仅反映 v0.1.1 的 10 个基础特性

### 4.2 需要更新/新增的部分

| 区域 | 优先级 | 更新内容 |
|------|--------|---------|
| **Hero 区域** | 高 | 更新 tagline，强调"企业级"能力（SDK、API、安全） |
| **特性卡片** | 高 | 从 10 个扩展到 14-16 个，新增 Phase 2-4 关键特性 |
| **命令演示** | 中 | 更新 terminal demo 添加新命令示例（workflow、serve） |
| **快速开始** | 高 | 新增 PyPI 安装方式、Docker 方式 |
| **新增：SDK 代码示例** | 中 | Python 代码片段展示程序化调用 |
| **新增：版本演进时间线** | 低 | 可视化展示 v0.1 → v0.5 的演进过程 |
| **新增：Changelog/Release 链接** | 中 | 链接到 GitHub Releases 页面 |
| **页脚** | 低 | 添加 PyPI 链接、版本号 |
| **i18n 文案** | 高 | script.js 中的中英文翻译同步更新 |

### 4.3 建议新增的特性卡片

在现有 10 张卡片基础上，追加以下内容：

| # | 特性名 | 图标关键词 | 描述 |
|---|--------|-----------|------|
| 11 | Headless & 远程浏览器 | cloud/server | 支持 Headless Chrome 和远程 CDP，可在服务器/Docker 中运行 |
| 12 | YAML 工作流编排 | workflow/git-branch | 通过 YAML 声明式编排多步骤工作流，支持步骤间数据传递和条件判断 |
| 13 | 数据驱动批量执行 | database/spreadsheet | CSV/JSON 批量参数输入，并发控制，汇总报告 |
| 14 | Python SDK & HTTP API | code/globe | 程序化调用 `from cliany_site import explore`，或启动 REST API 服务集成到任意系统 |
| 15 | 安全加固 | shield/lock | Session 加密存储、沙箱执行模式、生成代码自动安全审计 |
| 16 | 适配器市场 | package/store | 打包、发布、安装、回滚适配器，团队共享自动化能力 |

---

## 五、执行优先级与工作量估算

### 阶段一：测试稳固（优先级最高）

| 任务 | 预估工时 | 产出 |
|------|---------|------|
| 新增 `tests/test_cli_integration.py` L3 测试 | 2h | ~30 用例 |
| 新增/补充模块间集成测试 | 2h | ~20 用例 |
| 修复发现的导入/导出问题 | 1h | 代码修复 |
| 手动跑 L4 真实端到端测试 | 2h | 测试报告 |
| **小计** | **7h** | |

### 阶段二：GitHub README 更新

| 任务 | 预估工时 | 产出 |
|------|---------|------|
| 更新 README.md 中文版 | 2h | 完整中文文档 |
| 更新 README.en.md 英文版 | 2h | 同步英文文档 |
| 添加 CI/PyPI 徽章 | 0.5h | 徽章配置 |
| **小计** | **4.5h** | |

### 阶段三：官网更新

| 任务 | 预估工时 | 产出 |
|------|---------|------|
| 新增特性卡片（HTML + CSS） | 2h | 6 张新卡片 |
| 更新快速开始和命令演示 | 1h | 新安装方式 + 命令 |
| 更新 i18n 文案（script.js） | 1.5h | 中英文翻译 |
| SDK/API 代码示例区域 | 1h | 新增展示区块 |
| 测试双语切换和响应式布局 | 0.5h | 兼容性验证 |
| **小计** | **6h** | |

### 总工时估算：~17.5h

---

## 六、风险与注意事项

1. **L4 测试依赖外部服务**：真实端到端测试需要 Chrome + LLM API key，不适合在 CI 中自动运行。建议标记为 `@pytest.mark.manual` 或放在 qa/ 脚本中。

2. **官网部署验证**：修改 `site/` 后需在 Vercel preview 中验证双语切换、响应式布局、terminal 动画等。

3. **README 图片/GIF**：考虑录制一段 terminal 操作 GIF（asciicast / asciinema），比纯文字更直观。

4. **破坏性变更检查**：v0.5.0 的新全局选项（`--cdp-url`、`--headless`、`--sandbox`）不应影响已有 adapter 的运行。

5. **文档一致性**：README、官网、`--help` 文本三处命令描述需保持一致。

6. **迭代计划中"裸 except 数量"**：目标是 1，实际是 17 — 这是一个技术债，但不阻塞本次测试和发布。

---

## 七、建议的立即行动

1. **先跑回归**：确认 pytest 583 通过 + ruff + mypy 零错误 ← **已确认通过**
2. **写 L3 CLI 集成测试**：最大投入产出比，能发现命令注册和参数解析问题
3. **更新 README**：用户感知最直接，新功能不写文档等于不存在
4. **更新官网特性卡片**：6 张新卡片 + 快速开始更新
5. **手动跑 L4 端到端**：确认核心流程在真实环境下可用
