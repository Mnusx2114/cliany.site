# 工作流编排 — Phase 3.2

**日期**: 2026-03-29
**阶段**: Phase 3 — 场景拓展 (v0.4.0)

## 背景

cliany-site 已能为单个网站生成 CLI 命令，但跨域名、多步骤的自动化场景需要手动串联。Phase 3.2 新增 YAML 工作流编排引擎，支持：

1. **YAML 声明式工作流** — 用 YAML 文件定义多步骤任务
2. **步骤间数据传递** — `$prev.data.field` / `$steps.name.data.field` / `$env.VAR`
3. **条件判断** — `when` 表达式控制步骤是否执行
4. **重试策略** — `retry.max_attempts` / `delay` / `backoff` 指数退避
5. **CLI 命令** — `workflow run` / `workflow validate`

## 新增文件

| 文件 | 行数 | 职责 |
|------|------|------|
| `workflow/__init__.py` | 1 | 包入口 |
| `workflow/models.py` | 26 | `RetryPolicy` / `StepDef` / `WorkflowDef` 数据模型 |
| `workflow/parser.py` | 88 | YAML 解析 + 字段验证 |
| `workflow/engine.py` | 329 | 变量插值、条件求值、重试执行、工作流引擎 |
| `commands/workflow.py` | 103 | `workflow run` / `workflow validate` CLI 命令 |
| `tests/test_workflow.py` | 630 | 65 个测试 |

## YAML 工作流格式

```yaml
name: "搜索并收藏仓库"
description: "在 GitHub 搜索仓库后收藏"
steps:
  - name: "搜索仓库"
    adapter: github.com
    command: search
    params:
      query: "cliany-site"

  - name: "收藏仓库"
    adapter: github.com
    command: star
    params:
      repo: "$prev.data.repo_name"
    when: "$prev.success == true"
    retry:
      max_attempts: 3
      delay: 2.0
      backoff: 1.5
```

## 变量插值语法

| 表达式 | 含义 |
|--------|------|
| `$prev.data.field` | 上一步结果的 data 中的 field |
| `$prev.success` | 上一步是否成功 |
| `$steps.step_name.data.field` | 按步骤名引用特定步骤的结果 |
| `$env.VAR_NAME` | 环境变量 |

支持嵌入式使用：`"item-$prev.data.id-done"` → `"item-42-done"`

## 条件表达式

支持 `==`、`!=`、`>`、`<`、`>=`、`<=` 操作符：

```yaml
when: "$prev.success == true"
when: "$prev.data.count > 5"
when: "$steps.login.data.role != 'guest'"
when: "$prev.data.status == none"
```

## 重试策略

```yaml
retry:
  max_attempts: 3   # 最多尝试 3 次（默认 1 = 不重试）
  delay: 2.0        # 首次重试延迟秒数（默认 1.0）
  backoff: 1.5      # 指数退避倍数（默认 1.0 = 固定延迟）
```

实际延迟 = `delay * backoff^(attempt-1)`

## 执行引擎架构

```
WorkflowDef
  ├── parser.py: YAML → WorkflowDef (验证 + 构造)
  └── engine.py:
      ├── resolve_variable()   — $expr → value
      ├── interpolate_params() — 批量插值
      ├── evaluate_condition() — when 表达式求值
      ├── _run_step_with_retry() — 单步重试执行
      └── run_workflow()       — 编排主循环
          └── StepExecutor (协议)
              └── ClickAdapterExecutor (调用 CLI)
```

`StepExecutor` 是可替换的协议，测试中使用 `MockExecutor`，生产环境使用 `ClickAdapterExecutor`（通过 `click.testing.CliRunner` 调用 adapter 命令）。

## 使用示例

```bash
# 验证工作流文件
cliany-site workflow validate my-workflow.yaml --json

# 预览执行（不实际运行）
cliany-site workflow run my-workflow.yaml --dry-run --json

# 执行工作流
cliany-site workflow run my-workflow.yaml --json
```

## 测试覆盖

65 个测试覆盖：

| 测试类 | 数量 | 覆盖范围 |
|--------|------|----------|
| `TestRetryPolicy` | 2 | 默认值 / 自定义 |
| `TestStepDef` | 2 | 最小 / 完整构造 |
| `TestWorkflowDef` | 2 | 空步骤 / 有步骤 |
| `TestParseWorkflowYaml` | 11 | 有效/缺失字段/无效YAML/类型错误 |
| `TestLoadWorkflowFile` | 4 | 文件不存在/错误扩展名/yaml/yml |
| `TestResolveVariable` | 9 | prev/steps/env/missing/unknown |
| `TestInterpolateValue` | 5 | 纯文本/完整变量/嵌入/null/多变量 |
| `TestInterpolateParams` | 1 | 批量替换 |
| `TestEvaluateCondition` | 13 | 所有操作符/类型/边界 |
| `TestStepResult` | 1 | 默认值 |
| `TestWorkflowResult` | 2 | to_dict 成功/失败 |
| `TestRunWorkflow` | 10 | 成功/失败停止/数据传递/条件跳过/重试/异常 |
| `TestWorkflowCLI` | 3 | validate/invalid/dry-run |

## 验证结果

```
ruff check:  All checks passed!
mypy:        Success: no issues found in 55 source files
pytest:      411 passed in 0.71s
```
