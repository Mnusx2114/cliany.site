# 规划项对账表：模块、CLI、测试、CI、README 一致性核对

**日期：** 2026-04-07
**对账基线：** `docs/brainstorm-iteration-directions.md`
**核对范围：** 模块落点、CLI 入口、测试覆盖、CI 门禁、README 承诺一致性

## 使用说明

本表不再把“有文件 / 有 commit”视为完成，而是按以下维度核对：

- **模块落点**：是否已有实现文件
- **CLI 入口**：用户是否能从主命令直接到达
- **测试覆盖**：是否已有 `tests/` 或 `qa/` 证据
- **CI 门禁**：是否进入 `.github/workflows/ci.yml`
- **README 一致性**：README 是否与真实可达能力一致

状态定义：

- **已闭环**：模块、入口、测试、README 基本一致
- **部分闭环**：已实现核心能力，但主路径或门禁不完整
- **能力在库**：模块存在，但入口或默认调用链未打通
- **承诺超前**：README 或文档叙事超前于实际能力

## 对账表

| 规划项 | 模块落点 | CLI 入口 | 测试覆盖 | CI 门禁 | README 一致性 | 状态 | 备注 |
|--------|----------|----------|----------|---------|---------------|------|------|
| 裸 except 修复 | `src/cliany_site/errors.py`、多热路径文件 | 无独立入口 | 间接覆盖 | `pytest` 进入 CI | README 未直接承诺 | 部分闭环 | `action_runtime.py`、`explorer/engine.py`、`session.py`、`security.py`、`codegen/templates.py` 仍存在宽泛异常捕获 |
| 结构化日志 | `src/cliany_site/logging_config.py`、`src/cliany_site/cli.py` | 全局 `--verbose` / `--debug` | `tests/test_cli_integration.py`、相关模块测试 | `pytest` 进入 CI | README 架构区已体现 | 部分闭环 | 框架已接入，但 `commands/explore.py` 等仍混用 `print` / Rich / logger |
| 统一配置 | `src/cliany_site/config.py` | 根选项与运行时隐式接入 | `tests/test_config.py` | `pytest` 进入 CI | README/架构一致 | 已闭环 | `--cdp-url`、`--headless` 与配置对象衔接清晰 |
| pytest 单元测试 | `tests/`、`pyproject.toml` | 无 CLI 入口 | 大量直接测试 | `pytest tests/ -v` | README/贡献文档一致 | 已闭环 | 已从 shell-only 走向 pytest 主体 |
| CI/CD 流水线 | `.github/workflows/ci.yml` | 无 CLI 入口 | 通过 CI 触发 | 已有 ruff/mypy/pytest | README badge 一致 | 部分闭环 | `qa/` 浏览器 smoke/integration 尚未进入 CI |
| 执行进度反馈 | `src/cliany_site/progress.py` | explore/execute 主路径隐式使用 | `tests/test_progress.py`、集成测试 | 经 `pytest` 进入 CI | README 一致 | 已闭环 | Rich 与 NDJSON 双通道都存在 |
| 错误恢复 UX / 断点续执行 | `src/cliany_site/checkpoint.py`、`src/cliany_site/action_runtime.py`、`src/cliany_site/report.py` | 无显式 `--resume` | `tests/test_checkpoint.py`、`tests/test_report_enhanced.py` | 经 `pytest` 进入 CI | README 承诺 `--resume` | 承诺超前 | 底层能力存在，但 CLI 入口未闭环；运行时日志仍提示“可使用 --resume” |
| Headless & 远程浏览器 | `src/cliany_site/browser/cdp.py`、`src/cliany_site/browser/launcher.py` | 根级 `--cdp-url` / `--headless` | `tests/test_remote_cdp.py` | 经 `pytest` 进入 CI | README 一致 | 已闭环 | 是近期较完整的一条能力链 |
| YAML 工作流编排 | `src/cliany_site/workflow/*.py` | `workflow run/validate/batch` | `tests/test_workflow.py`、`tests/test_batch.py` | 经 `pytest` 进入 CI | README 部分超前 | 部分闭环 | 线性步骤 + when + retry 已实现；README 的列表索引示例超前于当前解析能力 |
| 数据驱动批量执行 | `src/cliany_site/workflow/batch.py` | `workflow batch` | `tests/test_batch.py` | 经 `pytest` 进入 CI | README 一致 | 已闭环 | 命令入口与测试都已具备 |
| Session 加密存储 | `src/cliany_site/security.py`、`src/cliany_site/session.py` | 无独立命令，登录/执行路径隐式使用 | `tests/test_security.py` | 经 `pytest` 进入 CI | README 一致 | 部分闭环 | 已真正落地，但 `session.py` 仍以宽泛异常做回退 |
| 沙箱执行模式 | `src/cliany_site/sandbox.py` | 根级 `--sandbox` 仅进入 `ctx.obj` | `tests/test_security.py` 有 sandbox 单测 | 经 `pytest` 进入 CI | README 明确承诺 | 能力在库 | 目前未看到它进入 `execute_action_steps` 或 SDK 执行主路径的直接证据 |
| 生成代码安全审计 | `src/cliany_site/audit.py` | 无独立 CLI 入口 | `tests/test_security.py` 有 audit 测试 | 经 `pytest` 进入 CI | README 明确承诺 | 能力在库 | 审计模块存在，但未看到 codegen 保存时自动执行审计的主路径证据 |
| 适配器市场 | `src/cliany_site/marketplace.py`、`src/cliany_site/commands/market.py` | `market publish/install/uninstall/info/rollback/backups` | `tests/test_marketplace.py`、CLI 集成测试 | 经 `pytest` 进入 CI | README 基本一致 | 已闭环 | 命令、测试、README 基本同向 |
| Python SDK | `src/cliany_site/sdk.py`、`src/cliany_site/__init__.py` | Python API 可达 | `tests/test_sdk.py` | 经 `pytest` 进入 CI | README 一致 | 已闭环 | 包导出与 README 示例基本一致 |
| HTTP API | `src/cliany_site/server.py`、`src/cliany_site/commands/serve.py` | `serve` | `tests/test_sdk.py` 覆盖 SDK/API 服务层 | 经 `pytest` 进入 CI | README 一致 | 已闭环 | `serve` 命令较薄，但调用链完整 |
| 适配器健康检查 / 智能自愈 | `src/cliany_site/snapshot.py`、`src/cliany_site/healthcheck.py`、`src/cliany_site/commands/check.py` | `check <domain> [--fix]` | `tests/test_snapshot.py`、`tests/test_healthcheck.py`、`tests/test_check.py` | 经 `pytest` 进入 CI | README 倾向更强叙事 | 部分闭环 | 已有快照比对与热修补，但距“执行前主动预检”仍有差距 |
| 交互式探索 / 回放 / 录像 | `src/cliany_site/explorer/interactive.py`、`src/cliany_site/explorer/recording.py`、`src/cliany_site/commands/replay.py` | `explore --interactive --extend --record`、`replay` | `tests/test_interactive.py`、`tests/test_replay.py`、`tests/test_recording.py`、`tests/test_extend.py` | 经 `pytest` 进入 CI | README 一致 | 已闭环 | 这是当前最成熟的体验能力链 |
| iframe / Shadow DOM | `src/cliany_site/browser/axtree.py` 等浏览器层 | 无单独入口，主路径隐式受益 | `tests/test_axtree.py` 等间接覆盖 | 经 `pytest` 进入 CI | README 基本一致 | 部分闭环 | 能力已进入浏览器层，但缺少独立用户级验证入口 |
| TUI 管理界面 | `src/cliany_site/tui/app.py`、`src/cliany_site/commands/tui.py` | `tui` | CLI 集成测试有帮助文本覆盖 | 经 `pytest` 进入 CI | README 一致 | 部分闭环 | 入口存在，但自动化验证更偏表层 |

## 高优先级断裂项

以下几项最值得优先修复，因为它们直接体现“模块存在但默认路径未闭合”。

### 1. `--resume`

- README 明确承诺 `--resume`
- `action_runtime.py` 运行时文案也提示用户使用 `--resume`
- 但 CLI 中没有真实的 `--resume` 入口

这是最典型的“产品承诺已完成，用户路径尚未完成”。

### 2. `--sandbox`

- 根命令已暴露 `--sandbox`
- `sandbox.py` 也有完整单元测试
- 但目前只看到 flag 被放入 `ctx.obj`
- 尚未看到执行主路径明确调用 `validate_action_steps()`

这属于“安全能力在库，但未被默认执行”。

### 3. `audit.py`

- 审计规则和测试都已存在
- README 也已承诺“生成代码安全审计”
- 但当前缺少“生成后自动审计并阻断”证据

这会造成“安全说明先于安全机制闭环”。

### 4. 工作流 README 示例

- `workflow run/validate/batch` 都真实存在
- 但 README 使用 `$prev.data.results[0].name`
- 当前 `workflow/engine.py` 的变量解析只支持按点号逐级访问，未支持数组索引

这是一处典型的文档超前问题。

### 5. `qa/` 未进入 CI

- 浏览器/CDP 相关经验很多沉淀在 `qa/` 脚本里
- 当前 CI 只运行 ruff/mypy/pytest
- 导致最依赖 tacit know-how 的场景还没有门禁保护

## 总体判断

从这张对账表看，项目已经不是“规划未落地”，而是进入了新的阶段：

- **第一阶段已经完成不少：** 把规划转成模块和命令
- **第二阶段尚未完成：** 把这些能力压实为默认路径、默认测试、默认门禁

因此，后续迭代的重点不应只是继续扩功能，而应优先处理这些“能力在库但主路径未闭合”的断裂项。

## 建议的修复顺序

1. 补 `--resume` CLI 闭环，并同步修正 README 示例
2. 将 `--sandbox` 接入 execute/SDK 主路径，确保 flag 真正生效
3. 将 `audit.py` 接入 codegen 保存链路，形成默认审计
4. 修正 workflow README 中超前的数据引用示例，或补齐数组索引支持
5. 选择一批可稳定运行的 `qa/` smoke 脚本接入 CI，补齐浏览器侧门禁
